import contextlib
import dataclasses
import logging
import typing as T

from dataclasses_json import dataclass_json

from oc_stats.common import ROOT_PATH

from . import anidex, dedibox, neocities, nyaa_si

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
DATA_PATH = ROOT_PATH.parent / "cache.json"


@dataclass_json
@dataclasses.dataclass
class Data:
    guestbook_comments: T.List[dedibox.Comment]
    torrent_stats: T.Optional[dedibox.TorrentStats]
    torrent_requests: T.List[dedibox.TorrentRequest]
    neocities_traffic_stats: T.List[neocities.TrafficStat]
    dedibox_traffic_stats: T.List[dedibox.TrafficStat]
    nyaa_si_torrents: T.List[nyaa_si.Torrent]
    nyaa_si_comments: T.Dict[int, T.List[nyaa_si.Comment]]
    anidex_torrents: T.List[anidex.Torrent]


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

    if not dev or not data.torrent_requests:
        logger.info("Getting request list…")
        with exception_guard():
            data.torrent_requests = list(dedibox.list_torrent_requests())
            yield

    if not dev or not data.torrent_stats:
        logger.info("Getting transmission stats…")
        with exception_guard():
            data.torrent_stats = dedibox.get_torrent_stats()
            yield

    if not dev or not data.neocities_traffic_stats:
        logger.info("Getting neocities traffic stats…")
        with exception_guard():
            data.neocities_traffic_stats = list(neocities.get_traffic_stats())
            yield

    if not dev or not data.dedibox_traffic_stats:
        logger.info("Getting website traffic stats…")
        data.dedibox_traffic_stats = list(dedibox.get_traffic_stats())
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
