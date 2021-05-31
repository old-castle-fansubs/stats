import hashlib
import json
import logging
import re
import shlex
import subprocess
import typing as T
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import dateutil.parser

DEDIBOX_HOST = "oc"


@dataclass
class Comment:
    website_link: T.Optional[str]
    comment_date: datetime
    author_name: str
    author_avatar_url: T.Optional[str]
    text: str


@dataclass
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
    def uptime(self) -> timedelta:
        return timedelta(
            seconds=self.raw_data["cumulative-stats"]["secondsActive"]
        )


@dataclass
class AnimeRequest:
    date: T.Optional[datetime]
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

    match = re.search(r"X-Transmission-Session-Id: (\S+)", content)
    assert match
    transmission_session_id = match.group(1)

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
        ["ssh", DEDIBOX_HOST, command],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout.decode()

    stats = json.loads(content)["arguments"]
    return TransmissionStats(raw_data=stats)


def get_guestbook_comments() -> T.Iterable[Comment]:
    logging.info("dedibox: fetching guestbook comments")
    content = subprocess.run(
        ["ssh", DEDIBOX_HOST, "cat", "srv/website/data/comments.json"],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout.decode()

    items = json.loads(content)
    for item in items:
        chksum = hashlib.md5(
            (item["email"] or item["author"]).encode()
        ).hexdigest()
        avatar_url = f"https://www.gravatar.com/avatar/{chksum}?d=retro"
        yield Comment(
            website_link=f"https://oldcastle.moe/guest_book.html#comment-{item['id']}",
            comment_date=dateutil.parser.parse(item["created"]).replace(
                tzinfo=timezone.utc
            ),
            author_name=item["author"],
            author_avatar_url=avatar_url,
            text=item["text"],
        )


def get_anime_requests() -> T.Iterable[AnimeRequest]:
    logging.info("dedibox: fetching anime requests")
    content = subprocess.run(
        ["ssh", DEDIBOX_HOST, "cat", "srv/website/data/requests.json"],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout.decode()

    items = json.loads(content)
    for item in items:
        yield AnimeRequest(
            date=dateutil.parser.parse(item["date"]) if item["date"] else None,
            title=item["title"],
            link=item["anidb_link"],
            comment=item["comment"],
        )
