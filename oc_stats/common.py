import datetime
import typing as T
from dataclasses import dataclass
from pathlib import Path

ROOT_PATH = Path(__file__).parent


@dataclass
class BaseTorrent:
    source: str
    torrent_id: int
    website_link: str
    torrent_link: str
    magnet_link: T.Optional[str]
    name: str
    size: int
    upload_date: datetime.datetime
    seeder_count: int
    leecher_count: int
    download_count: int
    comment_count: int
    visible: bool


@dataclass
class BaseComment:
    source: str
    comment_date: datetime.datetime
    author_name: str
    author_avatar_url: T.Optional[str]
    text: str
    website_title: T.Optional[str] = None
    website_link: T.Optional[str] = None


class AuthError(RuntimeError):
    def __init__(self) -> None:
        super().__init__("authentication error")
