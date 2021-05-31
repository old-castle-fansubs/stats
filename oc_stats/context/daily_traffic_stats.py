import json
import typing as T
from dataclasses import dataclass
from datetime import date

import dateutil.parser

from oc_stats.api.cloudflare import get_recent_hits
from oc_stats.context.base import BaseContextBuilder


@dataclass
class DailyTrafficStatDTO:
    day: date
    requests: int
    page_views: int
    unique_visitors: int


class DailyTrafficStatsContextBuilder(BaseContextBuilder):
    context_key = "daily_traffic_stats"

    @staticmethod
    def deserialize(value: T.Optional[str]) -> T.Any:
        if not value:
            return []
        return [
            DailyTrafficStatDTO(
                day=dateutil.parser.parse(item.pop("day")).date(),
                **item,
            )
            for item in json.loads(value)
        ]

    def update(self, original_value: T.Any) -> T.Any:
        mapping = {stat.day: stat for stat in original_value}
        for day, stat in get_recent_hits().items():
            mapping[day] = DailyTrafficStatDTO(
                day=day,
                requests=stat.requests,
                page_views=stat.page_views,
                unique_visitors=stat.unique_visitors,
            )
        return list(mapping.values())
