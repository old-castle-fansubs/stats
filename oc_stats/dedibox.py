import dataclasses
import hashlib
import json
import subprocess
import typing as T
from datetime import timedelta

import dateutil.parser
import sshtunnel
import transmissionrpc
from dataclasses_json import dataclass_json

from .common import AuthError, BaseComment

DEDIBOX_HOST = "oldcastle.moe"
DEDIBOX_PORT = 22


@dataclass_json
@dataclasses.dataclass
class Comment(BaseComment):
    like_count: int


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


def get_torrent_stats(user_name: str, password: str) -> TorrentStats:
    transmission_tunnel = sshtunnel.SSHTunnelForwarder(
        (DEDIBOX_HOST, 22),
        ssh_username=user_name,
        ssh_password=password,
        remote_bind_address=("127.0.0.1", 9091),
    )
    transmission_tunnel.start()
    transmission = transmissionrpc.Client(
        "127.0.0.1", port=transmission_tunnel.local_bind_port
    )

    if transmission is None:
        raise NotLoggedIn

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
            comment_date=dateutil.parser.parse(item["created"]),
            author_name=item["author"],
            author_avatar_url=avatar_url,
            text=item["text"],
            torrent_id=None,
            like_count=item["likes"],
        )
