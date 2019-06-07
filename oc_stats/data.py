import dataclasses
import datetime
import contextlib
import sys
import typing as T

import configargparse
from dataclasses_json import dataclass_json

from oc_stats.common import ROOT_PATH

from . import anidex, dedibox, neocities, nyaa_si

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
        print(ex, file=sys.stderr)


def refresh_data(
    args: configargparse.Namespace, data: Data
) -> T.Iterable[None]:
    if not args.dev or not data.guestbook_comments:
        print("Getting guest book comment list…", file=sys.stderr)
        with exception_guard():
            data.guestbook_comments = list(dedibox.list_guestbook_comments())
            yield

    if not args.dev or not data.torrent_requests:
        print("Getting request list…", file=sys.stderr)
        with exception_guard():
            data.torrent_requests = list(dedibox.list_torrent_requests())
            yield

    if not args.dev or not data.torrent_stats:
        print("Getting transmission stats…", file=sys.stderr)
        with exception_guard():
            data.torrent_stats = dedibox.get_torrent_stats(
                args.dedibox_user, args.dedibox_pass
            )
            yield

    if not args.dev or not data.neocities_traffic_stats:
        print("Getting neocities traffic stats…", file=sys.stderr)
        with exception_guard():
            data.neocities_traffic_stats = list(
                neocities.get_traffic_stats(
                    args.neocities_user, args.neocities_pass
                )
            )
            yield

    if not args.dev or not data.dedibox_traffic_stats:
        print("Getting website traffic stats…", file=sys.stderr)
        data.dedibox_traffic_stats = list(dedibox.get_traffic_stats())
        yield

    if not args.dev or not data.nyaa_si_torrents:
        print("Getting nyaa torrents…", file=sys.stderr)
        with exception_guard():
            data.nyaa_si_torrents = list(
                nyaa_si.list_user_torrents(args.nyaasi_user, args.nyaasi_pass)
            )
            yield

    if not args.dev or not data.nyaa_si_comments:
        print("Getting nyaa comments…", file=sys.stderr)
        if not data.nyaa_si_comments:
            data.nyaa_si_comments = {}
        for torrent in data.nyaa_si_torrents:
            comment_count = len(
                data.nyaa_si_comments.get(torrent.torrent_id, [])
            )
            if comment_count != torrent.comment_count:
                print(
                    f"Getting nyaa comments for {torrent.name}…",
                    file=sys.stderr,
                )
                with exception_guard():
                    data.nyaa_si_comments[torrent.torrent_id] = list(
                        nyaa_si.list_torrent_comments(torrent.torrent_id)
                    )
                    yield

    if not args.dev or not data.anidex_torrents:
        print("Getting anidex torrents…", file=sys.stderr)

        def page_callback(offset: int) -> None:
            print(
                f"Getting anidex.info torrent list… (offset {offset})",
                file=sys.stderr,
            )

        with exception_guard():
            data.anidex_torrents = list(
                anidex.list_group_torrents(
                    args.anidex_user,
                    args.anidex_pass,
                    args.anidex_group,
                    page_callback,
                )
            )
            yield
