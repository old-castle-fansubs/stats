import contextlib
import dataclasses
import datetime
import logging
import typing as T

from dataclasses_json import dataclass_json

from oc_stats import anidb, anidex, dedibox, neocities, nyaa_si
from oc_stats.common import CACHE_DIR, json_date_metadata

logger = logging.getLogger(__name__)
DATA_PATH = CACHE_DIR / "data.json"


@dataclass_json
@dataclasses.dataclass
class DailyStat:
    day: datetime.date = dataclasses.field(metadata=json_date_metadata)
    hits: T.Optional[int] = None
    nyaa_si_dl: T.Optional[int] = None
    anidex_dl: T.Optional[int] = None
    torrent_stats: T.Optional[dedibox.TorrentStats] = None


@dataclass_json
@dataclasses.dataclass
class Data:
    guestbook_comments: T.List[dedibox.Comment]
    anime_requests: T.List[dedibox.AnimeRequest]
    nyaa_si_torrents: T.List[nyaa_si.Torrent]
    nyaa_si_comments: T.Dict[int, T.List[nyaa_si.Comment]]
    anidex_torrents: T.List[anidex.Torrent]
    daily_stats: T.List[DailyStat] = dataclasses.field(default_factory=list)
    anidb_titles: T.Dict[int, anidb.AniDBInfo] = dataclasses.field(
        default_factory=dict
    )


@contextlib.contextmanager
def exception_guard() -> T.Generator:
    try:
        yield
    except Exception as ex:
        logger.error(str(ex))
        logger.exception(ex)


def refresh_data(data: Data, dev: bool) -> T.Iterable[None]:
    if not dev or not data.guestbook_comments:
        logger.info("Getting guest book comment list…")
        with exception_guard():
            data.guestbook_comments = list(dedibox.list_guestbook_comments())
            yield

    if not dev or not data.anime_requests:
        logger.info("Getting request list…")
        with exception_guard():
            data.anime_requests = list(dedibox.list_anime_requests())
            yield

    if not dev or not data.anidb_titles:
        logger.info("Getting AniDB entries…")
        with exception_guard():
            data.anidb_titles = {}
            for request in data.anime_requests:
                if request.anidb_id:
                    data.anidb_titles[request.anidb_id] = anidb.get_anidb_info(
                        request.anidb_id
                    )
            yield

    if not dev or not data.nyaa_si_torrents:
        logger.info("Getting nyaa torrents…")
        with exception_guard():
            data.nyaa_si_torrents = list(nyaa_si.list_user_torrents())
            yield

    if not dev or not data.nyaa_si_comments:
        logger.info("Getting nyaa comments…")
        if not data.nyaa_si_comments:
            data.nyaa_si_comments = {}
        for torrent in data.nyaa_si_torrents:
            comment_count = len(
                data.nyaa_si_comments.get(torrent.torrent_id, [])
            )
            if comment_count != torrent.comment_count:
                logger.info(f"Getting nyaa comments for {torrent.name}…")
                with exception_guard():
                    data.nyaa_si_comments[torrent.torrent_id] = list(
                        nyaa_si.list_torrent_comments(torrent)
                    )
                    yield

    if not dev or not data.anidex_torrents:
        logger.info("Getting anidex torrents…")

        def page_callback(offset: int) -> None:
            logger.info(f"Getting anidex.info torrent list… (offset {offset})")

        with exception_guard():
            data.anidex_torrents = list(
                anidex.list_group_torrents(page_callback)
            )
            yield

    if not dev or not data.daily_stats:
        date_to_stat = {stat.day: stat for stat in data.daily_stats}

        def get_daily_stat(day: datetime.date) -> DailyStat:
            if day in date_to_stat:
                return date_to_stat[day]
            stat = DailyStat(day=day)
            data.daily_stats.append(stat)
            date_to_stat[day] = stat
            return stat

        with exception_guard():
            today_stat = get_daily_stat(datetime.datetime.today().date())
            today_stat.anidex_dl = sum(
                torrent.download_count for torrent in data.anidex_torrents
            )
            today_stat.nyaa_si_dl = sum(
                torrent.download_count for torrent in data.nyaa_si_torrents
            )
            yield

        with exception_guard():
            logger.info("Getting transmission stats…")
            torrent_stats = dedibox.get_torrent_stats()

            logger.info("Getting website traffic stats…")
            dedibox_traffic_stats = list(dedibox.get_traffic_stats())

            logger.info("Getting neocities traffic stats…")
            neocities_traffic_stats = list(neocities.get_traffic_stats())

            min_date = min(
                stat.day
                for stat in dedibox_traffic_stats + neocities_traffic_stats
            )

            day = min_date
            while day <= datetime.datetime.today().date():
                daily_stat = get_daily_stat(day)
                daily_stat.hits = sum(
                    stat.views
                    for stat in neocities_traffic_stats
                    if stat.day <= day
                ) + sum(
                    stat.hits
                    for stat in dedibox_traffic_stats
                    if stat.day <= day
                )

                day += datetime.timedelta(days=1)

            today_stat = get_daily_stat(datetime.datetime.today().date())
            today_stat.torrent_stats = torrent_stats
            yield
