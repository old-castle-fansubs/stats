import datetime
import sqlite3
import tempfile
import typing as T
from dataclasses import dataclass
from pathlib import Path

import paramiko
import sshtunnel
import transmissionrpc

DEDIBOX_HOST = 'oldcastle.moe'
DEDIBOX_PORT = 22


class ApiError(RuntimeError):
    pass


class NotLoggedIn(ApiError):
    def __init__(self) -> None:
        super().__init__('not logged in')


@dataclass
class TorrentStats:
    active_torrents: int
    downloaded_bytes: int
    uploaded_bytes: int
    uptime: datetime.timedelta


@dataclass
class GuestbookComment:
    id: int
    parent_id: T.Optional[int]
    comment_date: datetime.datetime
    author_name: str
    author_email: T.Optional[str]
    author_website: T.Optional[str]
    text: str
    likes: int
    dislikes: int


class DediboxApi:
    def __init__(self) -> None:
        self.transport = paramiko.Transport((DEDIBOX_HOST, DEDIBOX_PORT))
        self.sftp = None
        self.transmission = None

    def login(self, user_name: str, password: str) -> None:
        self.transport.start_client(event=None, timeout=15)
        self.transport.get_remote_server_key()
        self.transport.auth_password(
            username=user_name,
            password=password,
            event=None
        )
        self.sftp = paramiko.SFTPClient.from_transport(self.transport)

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
            active_torrents=self.transmission.session_stats().activeTorrentCount,
            downloaded_bytes=stats['downloadedBytes'],
            uploaded_bytes=stats['uploadedBytes'],
            uptime=datetime.timedelta(seconds=stats['secondsActive'])
        )

    def list_guestbook_comments(self) -> T.Iterable[GuestbookComment]:
        if self.sftp is None:
            raise NotLoggedIn

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir) / 'comments.db'
            self.sftp.get('/var/isso/comments.db', str(tmp_path))
            conn = sqlite3.connect(tmp_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                'select * from comments inner join threads on tid=threads.id'
            )
            for row in cursor.fetchall():
                yield GuestbookComment(
                    id=row['id'],
                    parent_id=row['parent'],
                    comment_date=datetime.datetime.utcfromtimestamp(row['created']),
                    author_name=row['author'],
                    author_email=row['email'],
                    author_website=row['website'],
                    text=row['text'],
                    likes=row['likes'],
                    dislikes=row['dislikes'],
                )

    def __del__(self) -> None:
        self.transport.close()
        if self.transmission_tunnel is not None:
            self.transmission_tunnel.close()
