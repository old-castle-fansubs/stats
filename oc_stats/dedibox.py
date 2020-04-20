import dataclasses
import datetime
import hashlib
import json
import logging
import os
import re
import shlex
import subprocess
import typing as T

import dateutil.parser

from oc_stats.cache import CACHE_DIR, is_global_cache_enabled
from oc_stats.common import BaseComment

NGINX_LOG_RE = re.compile(
    r"(?P<ipaddress>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) "
    r"- (?:[^ ]+) "
    r"\[(?P<time>\d{2}\/[A-Za-z]{3}\/\d{4}:\d{2}:\d{2}:\d{2} (\+|\-)\d{4})\] "
    r'"(?P<request>[^"]*)" '
    r"(?P<status>\d{3}) "
    r"(?P<bytes_sent>\d+) "
    r'("(?P<referer>(\-)|(.+))") '
    r'("(?P<user_agent>.+)")'
)
DEDIBOX_HOST = "oc"
DEDIBOX_PORT = 22
DEDIBOX_USER = os.environ["DEDIBOX_USER"]
DEDIBOX_PASS = os.environ["DEDIBOX_PASS"]


@dataclasses.dataclass
class Comment(BaseComment):
    like_count: int = 0


@dataclasses.dataclass
class TransmissionStats:
    raw_data: T.Dict[str, T.Any]

    @property
    def torrent_count(self) -> int:
        return self.raw_data["torrentCount"]

    @property
    def active_torrent_count(self) -> int:
        return self.raw_data["activeTorrentCount"]

    @property
    def downloaded_bytes(self) -> int:
        return self.raw_data["cumulative-stats"]["downloadedBytes"]

    @property
    def uploaded_bytes(self) -> int:
        return self.raw_data["cumulative-stats"]["uploadedBytes"]

    @property
    def uptime(self) -> datetime.timedelta:
        return datetime.timedelta(
            seconds=self.raw_data["cumulative-stats"]["secondsActive"]
        )


@dataclasses.dataclass
class AnimeRequest:
    date: T.Optional[datetime.datetime]
    title: str
    link: str
    comment: T.Optional[str]

    @property
    def anidb_id(self) -> T.Optional[int]:
        match = re.search(r"(\d+)", self.link)
        if not match:
            return None
        return int(match.group(1))


def get_transmission_stats() -> TransmissionStats:
    logging.info("dedibox: fetching transmission stats")

    content = subprocess.run(
        [
            "ssh",
            DEDIBOX_HOST,
            "curl 'http://127.0.0.1:9091/transmission/rpc' -siI",
        ],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout.decode()

    transmission_session_id = re.search(
        "X-Transmission-Session-Id: (\S+)", content
    ).group(1)

    command = " ".join(
        shlex.quote(arg)
        for arg in [
            "curl",
            "http://127.0.0.1:9091/transmission/rpc",
            "-s",
            "-H",
            f"X-Transmission-Session-Id: {transmission_session_id}",
            "-X",
            "POST",
            "--data",
            '{"method":"session-stats"}',
        ]
    )

    content = subprocess.run(
        ["ssh", DEDIBOX_HOST, command], check=True, stdout=subprocess.PIPE,
    ).stdout.decode()

    stats = json.loads(content)["arguments"]
    return TransmissionStats(raw_data=stats)


def list_guestbook_comments() -> T.Iterable[Comment]:
    cache_path = CACHE_DIR / "dedibox" / "comments.json"

    if cache_path.exists() and is_global_cache_enabled():
        logging.info("dedibox: using cached guestbook comments")
        content = cache_path.read_text()
    else:
        logging.info("dedibox: fetching guestbook comments")
        content = subprocess.run(
            ["ssh", DEDIBOX_HOST, "cat", "srv/website/data/comments.json"],
            check=True,
            stdout=subprocess.PIPE,
        ).stdout.decode()
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(content)

    items = json.loads(content)
    for item in items:
        chksum = hashlib.md5(
            (item["email"] or item["author"]).encode()
        ).hexdigest()
        avatar_url = f"https://www.gravatar.com/avatar/{chksum}?d=retro"
        yield Comment(
            source="guestbook",
            website_link=f"https://oldcastle.moe/guest_book.html#comment-{item['id']}",
            comment_date=dateutil.parser.parse(item["created"]).replace(
                tzinfo=datetime.timezone.utc
            ),
            author_name=item["author"],
            author_avatar_url=avatar_url,
            text=item["text"],
            like_count=item["likes"],
        )


def list_anime_requests() -> T.Iterable[AnimeRequest]:
    cache_path = CACHE_DIR / "dedibox" / "requests.json"

    if cache_path.exists() and is_global_cache_enabled():
        logging.info("dedibox: using cached anime requests")
        content = cache_path.read_text()
    else:
        logging.info("dedibox: fetching anime requests")
        content = subprocess.run(
            ["ssh", DEDIBOX_HOST, "cat", "srv/website/data/requests.json"],
            check=True,
            stdout=subprocess.PIPE,
        ).stdout.decode()
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(content)

    items = json.loads(content)
    for item in items:
        yield AnimeRequest(
            date=dateutil.parser.parse(item["date"]) if item["date"] else None,
            title=item["title"],
            link=item["anidb_link"],
            comment=item["comment"],
        )
