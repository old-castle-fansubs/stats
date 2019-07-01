#!/usr/bin/env python3
import dataclasses
import datetime
import json
import sys
import typing as T
from pathlib import Path

import jinja2
import numpy as np

from oc_stats.common import (
    ROOT_PATH,
    BaseComment,
    BaseTorrent,
    BaseTrafficStat,
)
from oc_stats.data import Data
from oc_stats.markdown import render_markdown

from . import dedibox


def smooth(source: np.array) -> np.array:
    window_len = 45
    x = np.array(source)
    s = np.r_[
        2 * x[0] - x[window_len - 1 :: -1], x, 2 * x[-1] - x[-1:-window_len:-1]
    ]
    window = np.hamming(window_len)
    y = np.convolve(window / window.sum(), s, mode="same")
    return y[window_len : -window_len + 1]


def json_default(obj: T.Any) -> T.Any:
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    if isinstance(obj, (datetime.datetime, datetime.timedelta)):
        return str(obj)
    return None


@dataclasses.dataclass
class ReportTrafficStat(BaseTrafficStat):
    views: int
    hits_avg: float
    views_avg: float


@dataclasses.dataclass
class ReportContext:
    date: datetime.datetime
    comments: T.List[BaseComment]
    torrent_stats: dedibox.TorrentStats
    torrent_requests: T.List[dedibox.TorrentRequest]
    traffic_stats: T.List[ReportTrafficStat]
    torrents: T.List[BaseTorrent]


def build_report_context(data: T.Any) -> ReportContext:
    comments = list(data.guestbook_comments)
    torrents = {
        (torrent.source, torrent.torrent_id): torrent
        for torrent in data.anidex_torrents + data.nyaa_si_torrents
    }

    for torrent_id, nyaa_si_comments in data.nyaa_si_comments.items():
        for nyaa_si_comment in nyaa_si_comments:
            torrent = torrents.get(("nyaa.si", torrent_id))
            comments.append(nyaa_si_comment)

    min_day = min(
        stat.day
        for stat in data.neocities_traffic_stats + data.dedibox_traffic_stats
    )
    max_day = datetime.datetime.today().date()
    days = (max_day - min_day).days + 1

    hits = [0] * days
    views = [0] * days

    for stat in data.neocities_traffic_stats:
        idx = (stat.day - min_day).days
        hits[idx] += stat.hits
        views[idx] += stat.views

    for stat in data.dedibox_traffic_stats:
        idx = (stat.day - min_day).days
        hits[idx] += stat.hits

    hits_avg = smooth(hits)
    views_avg = smooth(views)

    traffic_stats = [
        ReportTrafficStat(
            day=min_day + datetime.timedelta(days=i),
            hits=hits[i],
            views=views[i],
            hits_avg=hits_avg[i],
            views_avg=views_avg[i],
        )
        for i in range(days)
    ]

    return ReportContext(
        date=datetime.datetime.now(),
        comments=comments,
        torrents=list(torrents.values()),
        torrent_stats=data.torrent_stats,
        torrent_requests=data.torrent_requests,
        traffic_stats=traffic_stats,
    )


def percent(
    dividend: T.Union[int, float], divisor: T.Union[int, float]
) -> str:
    if not divisor:
        return "0.0"
    return f"{dividend / divisor:.2f}"


def write_report(output: Path, data: Data) -> None:
    print(f"Writing output to {output}…", file=sys.stderr)
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(ROOT_PATH / "data"))
    )
    env.filters["markdown"] = lambda text: render_markdown(text)
    env.filters["tojson"] = lambda obj: json.dumps(obj, default=json_default)
    env.globals.update(percent=percent)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        env.get_template("report.html").render(
            **dataclasses.asdict(build_report_context(data))
        )
    )
