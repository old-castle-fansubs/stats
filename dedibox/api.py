import json
import tempfile
import typing as T
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import requests
import sshtunnel
import transmissionrpc

DEDIBOX_HOST = 'oldcastle.moe'
DEDIBOX_PORT = 22


class ApiError(RuntimeError):
    pass


class NotLoggedIn(ApiError):
    def __init__(self) -> None:
        super().__init__('not logged in')


class InvalidAuth(ApiError):
    def __init__(self) -> None:
        super().__init__('invalid credentials')


@dataclass
class TorrentStats:
    torrents: int
    active_torrents: int
    downloaded_bytes: int
    uploaded_bytes: int
    uptime: timedelta


@dataclass
class GuestbookComment:
    id: int
    parent_id: T.Optional[int]
    comment_date: datetime
    author_name: str
    author_avatar_url: str
    author_email: T.Optional[str]
    author_website: T.Optional[str]
    text: str
    likes: int
    dislikes: int


class Api:
    def __init__(self) -> None:
        self.transmission_tunnel = None
        self.transmission = None

    def login(self, user_name: str, password: str) -> None:
        self.transmission_tunnel = sshtunnel.SSHTunnelForwarder(
             (DEDIBOX_HOST, 22),
             ssh_username=user_name,
             ssh_password=password,
             remote_bind_address=('127.0.0.1', 9091)
        )
        self.transmission_tunnel.start()
        self.transmission = transmissionrpc.Client(
            '127.0.0.1',
            port=self.transmission_tunnel.local_bind_port
        )

    def get_torrent_stats(self) -> TorrentStats:
        if self.transmission is None:
            raise NotLoggedIn

        stats = self.transmission.session_stats().cumulative_stats
        return TorrentStats(
            torrents=self.transmission.session_stats().torrentCount,
            active_torrents=self.transmission.session_stats().activeTorrentCount,
            downloaded_bytes=stats['downloadedBytes'],
            uploaded_bytes=stats['uploadedBytes'],
            uptime=timedelta(seconds=stats['secondsActive'])
        )

    def list_guestbook_comments(self) -> T.Iterable[GuestbookComment]:
        response = requests.get(
            'https://comments.oldcastle.moe/'
            '?uri=%2Fguest_book.html&nested_limit=5'
        )
        response.raise_for_status()

        items = json.loads(response.text)['replies']
        while items:
            item = items.pop()
            items += item.get('replies', [])
            yield GuestbookComment(
                id=item['id'],
                parent_id=item['parent'],
                comment_date=datetime.utcfromtimestamp(item['created']),
                author_name=item['author'],
                author_avatar_url=item['gravatar_image'],
                author_email=None,
                author_website=item['website'],
                text=item['text'],
                likes=item['likes'],
                dislikes=item['dislikes'],
            )

    def __del__(self) -> None:
        if self.transmission_tunnel is not None:
            self.transmission_tunnel.close()
