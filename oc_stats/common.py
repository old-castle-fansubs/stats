import dataclasses
import datetime
import typing as T
from pathlib import Path

import dateutil.parser

ROOT_PATH = Path(__file__).parent

json_date_metadata = {
    "dataclasses_json": {
        "encoder": (
            lambda t: datetime.date.isoformat(t) if t is not None else None
        ),
        "decoder": (
            lambda t: dateutil.parser.parse(t).date()
            if t is not None
            else None
        ),
    }
}

json_datetime_metadata = {
    "dataclasses_json": {
        "encoder": (
            lambda t: datetime.datetime.isoformat(t) if t is not None else None
        ),
        "decoder": (
            lambda t: dateutil.parser.parse(t) if t is not None else None
        ),
    }
}

json_timedelta_metadata = {
    "dataclasses_json": {
        "encoder": lambda t: t.total_seconds(),
        "decoder": lambda t: datetime.timedelta(seconds=t),
    }
}


@dataclasses.dataclass
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


@dataclasses.dataclass
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


@dataclasses.dataclass
class BaseTrafficStat:
    day: datetime.date = dataclasses.field(metadata=json_date_metadata)
    hits: int
