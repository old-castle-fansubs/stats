#!/usr/bin/env python3
import dataclasses
import datetime
import json
import sys
import typing as T
from pathlib import Path

import jinja2
import numpy as np

from oc_stats import dedibox
from oc_stats.common import CACHE_DIR, ROOT_DIR, BaseComment, BaseTorrent
from oc_stats.data import Data
from oc_stats.markdown import render_markdown


def smooth(source: np.array) -> np.array:
    window_len = 45
    if len(source) < window_len:
        return source
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
class SmoothedStat:
    day: datetime.date
    value: T.Union[int, float]
    diff: T.Union[int, float]
    diff_avg: float


@dataclasses.dataclass
class AnimeRequest:
    date: T.Optional[datetime.datetime]
    title: str
    link: str
    comment: str
    picture: T.Optional[str]
    synopsis: T.Optional[str]
    type: T.Optional[str]
    episodes: T.Optional[int]


@dataclasses.dataclass
class ReportContext:
    date: datetime.datetime
    comments: T.List[BaseComment]
    torrents: T.List[BaseTorrent]
    anime_requests: T.List[AnimeRequest]
    torrent_stats: dedibox.TorrentStats
    hits: T.List[SmoothedStat]
    downloads: T.List[SmoothedStat]


def build_trendline(
    items: T.List[T.Tuple[datetime.date, T.Union[int, float]]],
) -> SmoothedStat:
    diffs: T.List[float] = []
    prev_value = items[0][1] if len(items) else 0
    for item in items:
        _day, value = item
        diffs.append(value - prev_value)
        prev_value = value
    diffs_avg = smooth(diffs)
    return [
        SmoothedStat(day=day, value=value, diff=diff, diff_avg=diff_avg)
        for (day, value), diff, diff_avg in zip(items, diffs, diffs_avg)
    ]


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

    daily_stats = list(sorted(data.daily_stats, key=lambda stat: stat.day))
    min_day = (
        min(stat.day for stat in daily_stats)
        if daily_stats
        else datetime.datetime.today().date()
    )
    max_day = datetime.datetime.today().date()
    num_days = (max_day - min_day).days + 1
    days = [min_day + datetime.timedelta(days=i) for i in range(num_days)]

    hits = build_trendline([(stat.day, stat.hits) for stat in daily_stats])
    downloads = build_trendline(
        [
            (stat.day, (stat.nyaa_si_dl or 0) + (stat.anidex_dl or 0))
            for stat in daily_stats
            if stat.nyaa_si_dl is not None or stat.anidex_dl is not None
        ]
    )

    anime_requests: T.List[AnimeRequest] = []
    for request in data.anime_requests:
        anidb_info = (
            data.anidb_titles[request.anidb_id] if request.anidb_id else None
        )
        anime_requests.append(
            AnimeRequest(
                date=request.date,
                title=anidb_info.title if anidb_info else request.title,
                link=request.link,
                comment=request.comment,
                synopsis=anidb_info.synopsis if anidb_info else None,
                type=anidb_info.type if anidb_info else None,
                picture=f"anidb/{anidb_info.id}.jpg" if anidb_info else None,
                episodes=anidb_info.episodes if anidb_info else None,
            )
        )
    anime_requests.sort(
        key=lambda request: request.date.replace(tzinfo=None)
        if request.date
        else datetime.datetime.min,
        reverse=True,
    )

    return ReportContext(
        date=datetime.datetime.now(),
        comments=list(
            sorted(
                comments,
                key=lambda comment: comment.comment_date,
                reverse=True,
            )
        ),
        torrents=list(torrents.values()),
        anime_requests=anime_requests,
        torrent_stats=daily_stats[-1].torrent_stats if daily_stats else None,
        hits=hits,
        downloads=downloads,
    )


def percent(
    dividend: T.Union[int, float], divisor: T.Union[int, float]
) -> str:
    if not divisor:
        return "0.0"
    return f"{dividend / divisor:.2f}"


def write_report(output_dir: Path, data: Data) -> None:
    print(f"Writing output to {output_dir}…", file=sys.stderr)
    output_dir.mkdir(parents=True, exist_ok=True)

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(ROOT_DIR / "data"))
    )
    env.filters["markdown"] = lambda text: render_markdown(text)
    env.filters["tojson"] = lambda obj: json.dumps(obj, default=json_default)
    env.globals.update(percent=percent)

    index_path = output_dir / "index.html"
    index_path.write_text(
        env.get_template("report.html").render(
            **dataclasses.asdict(build_report_context(data))
        )
    )

    anidb_path = output_dir / "anidb"
    if not anidb_path.exists():
        anidb_path.symlink_to(CACHE_DIR / "anidb", target_is_directory=True)
