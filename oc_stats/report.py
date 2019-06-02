#!/usr/bin/env python3
import dataclasses
import datetime
import json
import sys
import typing as T

import configargparse
import jinja2
import markdown
import xdg

from oc_stats.common import ROOT_PATH, BaseComment, BaseTorrent
from oc_stats.data import Data

from . import anidex, dedibox, neocities, nyaa_si


def json_default(obj: T.Any) -> T.Any:
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    if isinstance(obj, (datetime.datetime, datetime.timedelta)):
        return str(obj)
    print(obj, type(obj))
    return None


@dataclasses.dataclass
class ReportTorrent(BaseTorrent):
    @classmethod
    def build_from(cls: T.Any, other: T.Any, **kwargs: T.Any) -> T.Any:
        return cls(
            source=other.source,
            torrent_id=other.torrent_id,
            torrent_link=other.torrent_link,
            magnet_link=other.magnet_link,
            name=other.name,
            size=other.size,
            upload_date=other.upload_date,
            seeder_count=other.seeder_count,
            leecher_count=other.leecher_count,
            download_count=other.download_count,
            comment_count=other.comment_count,
            visible=other.visible,
            **kwargs,
        )


@dataclasses.dataclass
class ReportComment(BaseComment):
    torrent: T.Optional[ReportTorrent] = None

    @classmethod
    def build_from(cls: T.Any, other: T.Any, **kwargs: T.Any) -> T.Any:
        return cls(
            source=other.source,
            comment_date=other.comment_date,
            author_name=other.author_name,
            author_avatar_url=other.author_avatar_url,
            text=other.text,
            torrent_id=other.torrent_id,
            **kwargs,
        )


@dataclasses.dataclass
class ReportTrafficStat:
    day: datetime.datetime
    hits: int
    views: int
    hits_avg: float
    views_avg: float


@dataclasses.dataclass
class ReportContext:
    date: datetime.datetime
    comments: T.List[ReportComment]
    torrent_stats: dedibox.TorrentStats
    traffic_stats: T.List[ReportTrafficStat]
    torrents: T.List[ReportTorrent]


def build_report_context(data: T.Any) -> ReportContext:
    comments = [
        ReportComment.build_from(comment)
        for comment in data.guestbook_comments
    ]
    torrent_stats = data.torrent_stats
    torrents = {
        (torrent.source, torrent.torrent_id): ReportTorrent.build_from(torrent)
        for torrent in data.anidex_torrents + data.nyaa_si_torrents
    }

    for torrent_id, nyaa_si_comments in data.nyaa_si_comments.items():
        for nyaa_si_comment in nyaa_si_comments:
            comments.append(
                ReportComment.build_from(
                    nyaa_si_comment,
                    torrent=torrents.get(("nyaa.si", torrent_id)),
                )
            )

    traffic_stats: T.List[ReportTrafficStat] = []
    try:
        import scipy.signal

        weights = {
            key - 21: value
            for key, value in enumerate(
                scipy.signal.gaussian(M=21 * 2 + 1, std=7)
            )
        }
    except ImportError:
        weights = {
            -21: 0.011_108,
            -20: 0.016_879,
            -19: 0.025_130,
            -18: 0.036_658,
            -17: 0.052_393,
            -16: 0.073_369,
            -15: 0.100_668,
            -14: 0.135_335,
            -13: 0.178_263,
            -12: 0.230_066,
            -11: 0.290_923,
            -10: 0.360_447,
            -9: 0.437_564,
            -8: 0.520_450,
            -7: 0.606_530,
            -6: 0.692_569,
            -5: 0.774_837,
            -4: 0.849_365,
            -3: 0.912_254,
            -2: 0.960_005,
            -1: 0.989_847,
            0: 1.0,
            1: 0.989_847,
            2: 0.960_005,
            3: 0.912_254,
            4: 0.849_365,
            5: 0.774_837,
            6: 0.692_569,
            7: 0.606_530,
            8: 0.520_450,
            9: 0.437_564,
            10: 0.360_447,
            11: 0.290_923,
            12: 0.230_066,
            13: 0.178_263,
            14: 0.135_335,
            15: 0.100_668,
            16: 0.073_369,
            17: 0.052_393,
            18: 0.036_658,
            19: 0.025_130,
            20: 0.016_879,
            21: 0.011_108,
        }

    for i, item in enumerate(data.neocities_traffic_stats):
        total_weight = 0
        hits_avg = 0
        views_avg = 0
        for delta, weight in weights.items():
            try:
                other_item = data.neocities_traffic_stats[i + delta]
            except LookupError:
                continue
            hits_avg += other_item.hits * weight
            views_avg += other_item.views * weight
            total_weight += weight

        traffic_stats.append(
            ReportTrafficStat(
                day=item.day,
                hits=item.hits,
                views=item.views,
                hits_avg=hits_avg / max(1, total_weight),
                views_avg=views_avg / max(1, total_weight),
            )
        )

    return ReportContext(
        date=datetime.datetime.now(),
        comments=comments,
        torrents=list(torrents.values()),
        torrent_stats=torrent_stats,
        traffic_stats=traffic_stats,
    )


def percent(
    dividend: T.Union[int, float], divisor: T.Union[int, float]
) -> str:
    if not divisor:
        return "0.0"
    return f"{dividend / divisor:.2f}"


def write_report(args: configargparse.Namespace, data: Data) -> None:
    print(f"Writing output to {args.output}…", file=sys.stderr)
    md = markdown.Markdown(extensions=["meta"])
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(ROOT_PATH / "data"))
    )
    env.filters["markdown"] = lambda text: jinja2.Markup(md.convert(text))
    env.filters["tojson"] = lambda obj: json.dumps(obj, default=json_default)
    env.globals.update(percent=percent)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        env.get_template("report.html").render(
            **dataclasses.asdict(build_report_context(data))
        )
    )
