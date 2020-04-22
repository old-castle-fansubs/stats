import datetime
import json
import logging
import typing as T
from dataclasses import dataclass

import dateutil.parser

from oc_stats import anidb, anidex, cloudflare, dedibox, nyaa_si
from oc_stats.cache import CACHE_DIR, is_global_cache_enabled

DAILY_STATS_CACHE_PATH = CACHE_DIR / "daily-stats.json"


@dataclass
class DailyStat:
    traffic_stat: T.Optional[cloudflare.TrafficStat] = None
    transmission_stats: T.Optional[dedibox.TransmissionStats] = None
    nyaa_si_dl: T.Optional[int] = None
    anidex_dl: T.Optional[int] = None


def load_daily_stats() -> T.Dict[datetime.date, DailyStat]:
    if not DAILY_STATS_CACHE_PATH.exists():
        return {}
    return {
        dateutil.parser.parse(day).date(): DailyStat(
            traffic_stat=(
                cloudflare.TrafficStat(
                    requests=item["traffic-stat"]["requests"],
                    page_views=item["traffic-stat"]["page-views"],
                    unique_visitors=item["traffic-stat"]["unique-visitors"],
                )
                if item.get("traffic-stat")
                else None
            ),
            transmission_stats=(
                dedibox.TransmissionStats(raw_data=item["transmission-stats"])
                if item.get("transmission-stats")
                else None
            ),
            nyaa_si_dl=item["nyaa-si-dl"],
            anidex_dl=item["anidex-dl"],
        )
        for day, item in json.loads(DAILY_STATS_CACHE_PATH.read_text()).items()
    }


def save_daily_stats(daily_stats: T.Dict[datetime.date, DailyStat]) -> None:
    DAILY_STATS_CACHE_PATH.write_text(
        json.dumps(
            {
                str(day): {
                    "traffic-stat": (
                        {
                            "requests": stat.traffic_stat.requests,
                            "page-views": stat.traffic_stat.page_views,
                            "unique-visitors": stat.traffic_stat.unique_visitors,
                        }
                        if stat.traffic_stat
                        else None
                    ),
                    "transmission-stats": (
                        stat.transmission_stats.raw_data
                        if stat.transmission_stats
                        else None
                    ),
                    "nyaa-si-dl": stat.nyaa_si_dl,
                    "anidex-dl": stat.anidex_dl,
                }
                for day, stat in daily_stats.items()
            },
            indent=4,
        )
    )


class Data:
    def __init__(self) -> None:
        self.guestbook_comments = list(dedibox.list_guestbook_comments())
        self.anime_requests = list(dedibox.list_anime_requests())
        self.anidb_titles = {
            request.anidb_id: anidb.get_anidb_info(request.anidb_id)
            for request in self.anime_requests
            if request.anidb_id
        }
        self.anidex_torrents = list(anidex.list_group_torrents())
        self.nyaa_si_torrents = list(nyaa_si.list_user_torrents())
        self.nyaa_si_comments = list(
            sum(
                (
                    list(nyaa_si.list_torrent_comments(torrent))
                    for torrent in self.nyaa_si_torrents
                ),
                [],
            )
        )

        self.daily_stats = load_daily_stats()
        self.update_daily_stats()

    @property
    def transmission_stats(self) -> T.Optional[dedibox.TransmissionStats]:
        today = datetime.datetime.today().date()
        if today not in self.daily_stats:
            return None
        return self.daily_stats[today].transmission_stats

    def update_daily_stats(self) -> None:
        today = datetime.datetime.today().date()
        yesterday = datetime.datetime.today().date() - datetime.timedelta(
            days=1
        )

        if today in self.daily_stats:
            today_stat = self.daily_stats[today]
        else:
            today_stat = DailyStat()

        if is_global_cache_enabled() and today_stat.transmission_stats:
            logging.info("dedibox: using cached transmission stats")
        else:
            today_stat.transmission_stats = dedibox.get_transmission_stats()

        if (
            is_global_cache_enabled()
            and yesterday in self.daily_stats
            and self.daily_stats[yesterday].traffic_stat
        ):
            logging.info("cloudflare: using cached hit stats")
        else:
            for day, traffic_stat in cloudflare.get_recent_hits().items():
                if day not in self.daily_stats:
                    self.daily_stats[day] = DailyStat()
                self.daily_stats[day].traffic_stat = traffic_stat

        today_stat.anidex_dl = sum(
            torrent.download_count for torrent in self.anidex_torrents
        )
        today_stat.nyaa_si_dl = sum(
            torrent.download_count for torrent in self.nyaa_si_torrents
        )

        self.daily_stats[today] = today_stat
        self.daily_stats = dict(sorted(self.daily_stats.items()))
        save_daily_stats(self.daily_stats)
