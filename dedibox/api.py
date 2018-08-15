import datetime
import sqlite3
import tempfile
import typing as T
from dataclasses import dataclass
from pathlib import Path

import paramiko


class ApiError(RuntimeError):
    pass


class NotLoggedIn(ApiError):
    def __init__(self) -> None:
        super().__init__('not logged in')


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
        self.transport = paramiko.Transport(('oldcastle.moe', 22))
        self.sftp = None

    def login(self, user_name: str, password: str) -> None:
        self.transport.start_client(event=None, timeout=15)
        self.transport.get_remote_server_key()
        self.transport.auth_password(
            username=user_name,
            password=password,
            event=None
        )
        self.sftp = paramiko.SFTPClient.from_transport(self.transport)

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
