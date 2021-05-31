import json
import typing as T
from dataclasses import dataclass
from datetime import timedelta

from oc_stats.api.dedibox import get_transmission_stats
from oc_stats.context.base import BaseContextBuilder


@dataclass
class TransmissionStatsDTO:
    torrent_count: int
    active_torrent_count: int
    downloaded_bytes: int
    uploaded_bytes: int
    uptime: timedelta


class TransmissionStatsContextBuilder(BaseContextBuilder):
    context_key = "transmission_stats"

    @staticmethod
    def deserialize(value: T.Optional[str]) -> T.Any:
        if not value:
            return None
        item = json.loads(value)
        return TransmissionStatsDTO(
            uptime=timedelta(seconds=item.pop("uptime")), **item
        )

    def update(self, original_value: T.Any) -> T.Any:
        stats = get_transmission_stats()
        return TransmissionStatsDTO(
            torrent_count=stats.torrent_count,
            active_torrent_count=stats.active_torrent_count,
            downloaded_bytes=stats.downloaded_bytes,
            uploaded_bytes=stats.uploaded_bytes,
            uptime=stats.uptime,
        )
