import json
import typing as T
from datetime import date

import dateutil.parser

from oc_stats.api.nyaa_si import get_user_torrents
from oc_stats.common import convert_to_diffs, json_default
from oc_stats.context.base import BaseContextBuilder


class DailyNyaaSiStatsContextBuilder(BaseContextBuilder):
    context_key = "daily_nyaa_si_stats"

    @staticmethod
    def deserialize(value: T.Optional[str]) -> T.Any:
        if not value:
            return {}
        return {
            dateutil.parser.parse(key).date(): value
            for key, value in json.loads(value).items()
        }

    @staticmethod
    def serialize(value: T.Any) -> str:
        return json.dumps(
            {key.isoformat(): value for key, value in value.items()},
            default=json_default,
            indent=4,
        )

    @staticmethod
    def transform_context(value: T.Any) -> T.Any:
        return {
            key.isoformat(): value
            for key, value in convert_to_diffs(value).items()
        }

    def update(self, original_value: T.Any) -> T.Any:
        torrents = list(get_user_torrents())
        original_value[date.today()] = sum(
            torrent.download_count for torrent in torrents
        )
        return original_value
