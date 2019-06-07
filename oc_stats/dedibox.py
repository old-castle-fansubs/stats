import collections
import dataclasses
import hashlib
import json
import re
import subprocess
import typing as T
from datetime import datetime, timedelta

import dateutil.parser
import sshtunnel
import transmissionrpc
from dataclasses_json import dataclass_json

from .common import AuthError, BaseComment
from .common import BaseTrafficStat as TrafficStat

NGINX_LOG_RE = re.compile(
    r"(?P<ipaddress>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) "
    r"- - "
    r"\[(?P<time>\d{2}\/[A-Za-z]{3}\/\d{4}:\d{2}:\d{2}:\d{2} (\+|\-)\d{4})\] "
    r'"(?P<request>[^"]*)" '
    r"(?P<status>\d{3}) "
    r"(?P<bytes_sent>\d+) "
    r'("(?P<referer>(\-)|(.+))") '
    r'("(?P<user_agent>.+)")'
)
DEDIBOX_HOST = "oldcastle.moe"
DEDIBOX_PORT = 22


@dataclass_json
@dataclasses.dataclass
class Comment(BaseComment):
    like_count: int = 0


@dataclass_json
@dataclasses.dataclass
class TorrentStats:
    torrents: int
    active_torrents: int
    downloaded_bytes: int
    uploaded_bytes: int
    uptime: timedelta = dataclasses.field(
        metadata={
            "dataclasses_json": {
                "encoder": lambda t: t.total_seconds(),
                "decoder": lambda t: timedelta(seconds=t),
            }
        }
    )


@dataclass_json
@dataclasses.dataclass
class TorrentRequest:
    date: T.Optional[datetime] = dataclasses.field(
        metadata={
            "dataclasses_json": {
                "encoder": lambda x: datetime.isoformat(x)
                if x is not None
                else None,
                "decoder": lambda x: datetime.fromisoformat(x)
                if x is not None
                else None,
            }
        }
    )
    title: str
    anidb_link: str
    comment: T.Optional[str]


def get_torrent_stats(user_name: str, password: str) -> TorrentStats:
    transmission_tunnel = sshtunnel.SSHTunnelForwarder(
        (DEDIBOX_HOST, DEDIBOX_PORT),
        ssh_username=user_name,
        ssh_password=password,
        remote_bind_address=("127.0.0.1", 9091),
    )
    transmission_tunnel.start()
    transmission = transmissionrpc.Client(
        "127.0.0.1", port=transmission_tunnel.local_bind_port
    )

    if transmission is None:
        raise AuthError

    stats = transmission.session_stats()

    ret = TorrentStats(
        torrents=stats.torrentCount,
        active_torrents=stats.activeTorrentCount,
        downloaded_bytes=stats.cumulative_stats["downloadedBytes"],
        uploaded_bytes=stats.cumulative_stats["uploadedBytes"],
        uptime=timedelta(seconds=stats.cumulative_stats["secondsActive"]),
    )

    transmission_tunnel.close()

    return ret


def list_guestbook_comments() -> T.Iterable[Comment]:
    content = subprocess.run(
        ["ssh", DEDIBOX_HOST, "cat", "srv/website/data/comments.json"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout

    items = json.loads(content)
    for item in items:
        chksum = hashlib.md5(
            (item["email"] or item["author"]).encode()
        ).hexdigest()
        avatar_url = f"https://www.gravatar.com/avatar/{chksum}?d=retro"
        yield Comment(
            source="guestbook",
            website_link=f"https://oldcastle.moe/guest_book.html#comment-{item['id']}",
            comment_date=dateutil.parser.parse(item["created"]),
            author_name=item["author"],
            author_avatar_url=avatar_url,
            text=item["text"],
            like_count=item["likes"],
        )


def list_torrent_requests() -> T.Iterable[TorrentRequest]:
    content = subprocess.run(
        ["ssh", DEDIBOX_HOST, "cat", "srv/website/data/requests.json"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout

    items = json.loads(content)
    for item in items:
        yield TorrentRequest(
            date=dateutil.parser.parse(item["date"]) if item["date"] else None,
            title=item["title"],
            anidb_link=item["anidb_link"],
            comment=item["comment"],
        )


def get_traffic_stats() -> T.Iterable[TrafficStat]:
    process = subprocess.Popen(
        [
            "ssh",
            DEDIBOX_HOST,
            "sudo",
            "gzip",
            "--stdout",
            "--decompress",
            "--force",
            "/var/log/nginx/*_oldcastle.moe.log*",
        ],
        text=True,
        stdout=subprocess.PIPE,
    )

    visits: T.Dict[datetime.date, int] = collections.defaultdict(int)

    while True:
        line = process.stdout.readline()
        line = line.rstrip()
        if not line:
            break

        match = NGINX_LOG_RE.search(line)
        if not match:
            raise ValueError("Malformed line:", line)

        request = match.group("request")
        status = int(match.group("status"))

        if "/stats.html" in request:
            continue

        if status in {400, 404}:
            continue

        if status in {200, 304}:
            day = dateutil.parser.parse(
                match.group("time").replace(":", " ", 1)
            ).date()
            visits[day] += 1

    yield from (
        TrafficStat(day=day, hits=hits) for day, hits in visits.items()
    )
