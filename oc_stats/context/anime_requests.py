import json
import typing as T
from dataclasses import dataclass
from datetime import datetime

import dateutil.parser
from flask import url_for

from oc_stats.api.anidb import get_anidb_info
from oc_stats.api.dedibox import get_anime_requests
from oc_stats.common import CACHE_DIR, STATIC_DIR
from oc_stats.context.base import BaseContextBuilder


@dataclass
class AnimeRequestDTO:
    date: T.Optional[datetime]
    title: str
    link: str
    anidb_id: T.Optional[int]
    comment: T.Optional[str]
    synopsis: T.Optional[str]
    type: T.Optional[str]
    episodes: T.Optional[int]
    year: T.Optional[int]

    @property
    def picture(self) -> T.Optional[str]:
        return (
            url_for("static", filename=f"anidb/{self.anidb_id}.jpg")
            if self.synopsis
            else None
        )


class AnimeRequestsContextBuilder(BaseContextBuilder):
    context_key = "anime_requests"

    @staticmethod
    def deserialize(value: T.Optional[str]) -> T.Any:
        if not value:
            return []
        return [
            AnimeRequestDTO(
                date=(
                    dateutil.parser.parse(item_date)
                    if (item_date := item.pop("date"))
                    else None
                ),
                **item,
            )
            for item in json.loads(value)
        ]

    def update(self, original_value: T.Any) -> T.Any:
        requests = list(get_anime_requests())

        ret = []
        for request in requests:
            if request.anidb_id:
                anidb_info = get_anidb_info(request.anidb_id)
            else:
                anidb_info = None

            ret.append(
                AnimeRequestDTO(
                    date=request.date,
                    title=anidb_info.title if anidb_info else request.title,
                    link=request.link,
                    anidb_id=request.anidb_id,
                    comment=request.comment,
                    synopsis=anidb_info.synopsis if anidb_info else None,
                    type=anidb_info.type if anidb_info else None,
                    episodes=anidb_info.episodes if anidb_info else None,
                    year=anidb_info.start_date.year
                    if anidb_info and anidb_info.start_date
                    else None,
                )
            )

        images_dir = STATIC_DIR / "anidb"
        if not images_dir.exists():
            images_dir.symlink_to(
                CACHE_DIR / "anidb", target_is_directory=True
            )

        ret.sort(
            key=(
                lambda request: request.date.replace(tzinfo=None)
                if request.date
                else datetime.min
            ),
            reverse=True,
        )

        return ret
