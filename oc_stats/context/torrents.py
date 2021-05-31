import json
import typing as T
from dataclasses import dataclass

from oc_stats.api import anidex, nyaa_si
from oc_stats.context.base import BaseContextBuilder


@dataclass
class TorrentDTO:
    source: str
    name: str
    size: int
    seeder_count: int
    leecher_count: int
    download_count: int
    comment_count: int
    visible: bool


class TorrentsContextBuilder(BaseContextBuilder):
    context_key = "torrents"

    @staticmethod
    def deserialize(value: T.Optional[str]) -> T.Any:
        if not value:
            return {}
        return [TorrentDTO(**item) for item in json.loads(value)]

    def update(self, original_value: T.Any) -> T.Any:
        ret = []

        try:
            nyaa_si_torrents = list(nyaa_si.get_user_torrents())
        except Exception as ex:
            logging.exception(ex)
        else:
            for torrent in nyaa_si_torrents:
                ret.append(
                    TorrentDTO(
                        source="nyaa.si",
                        name=torrent.name,
                        size=torrent.size,
                        seeder_count=torrent.seeder_count,
                        leecher_count=torrent.leecher_count,
                        download_count=torrent.download_count,
                        comment_count=torrent.comment_count,
                        visible=torrent.visible,
                    )
                )

        try:
            anidex_torrents = list(anidex.get_group_torrents())
        except Exception as ex:
            logging.exception(ex)
        else:
            for torrent in anidex_torrents:
                ret.append(
                    TorrentDTO(
                        source="anidex.info",
                        name=torrent.name,
                        size=torrent.size,
                        seeder_count=torrent.seeder_count,
                        leecher_count=torrent.leecher_count,
                        download_count=torrent.download_count,
                        comment_count=torrent.comment_count,
                        visible=torrent.visible,
                    )
                )

        return ret
