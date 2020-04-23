#!/usr/bin/env python3
import dataclasses
import datetime
import json
import logging
import typing as T
from pathlib import Path

import jinja2
import numpy as np

from oc_stats import dedibox
from oc_stats.cache import CACHE_DIR
from oc_stats.common import ROOT_DIR, BaseComment, BaseTorrent
from oc_stats.data import Data
from oc_stats.markdown import render_markdown
from oc_stats.anidb import AniDBInfo
from oc_stats.dedibox import AnimeRequest


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
    value_avg: float


@dataclasses.dataclass
class ExtendedAnimeRequest:
    anidb_info: AniDBInfo
    request: AnimeRequest

    @property
    def date(self) -> T.Optional[datetime.datetime]:
        return self.request.date

    @property
    def title(self) -> str:
        return self.anidb_info.title if self.anidb_info else self.request.title

    @property
    def link(self) -> str:
        return self.request.link

    @property
    def comment(self) -> T.Optional[str]:
        return self.request.comment

    @property
    def picture(self) -> T.Optional[str]:
        return f"anidb/{self.anidb_info.id}.jpg" if self.anidb_info else None

    @property
    def synopsis(self) -> T.Optional[str]:
        return self.anidb_info.synopsis if self.anidb_info else None

    @property
    def type(self) -> T.Optional[str]:
        return self.anidb_info.type if self.anidb_info else None

    @property
    def episodes(self) -> T.Optional[int]:
        return self.anidb_info.episodes if self.anidb_info else None

    @property
    def year(self) -> T.Optional[int]:
        return (
            self.anidb_info.start_date.year
            if self.anidb_info and self.anidb_info.start_date
            else None
        )


@dataclasses.dataclass
class ReportContext:
    date: datetime.datetime
    comments: T.List[BaseComment]
    torrents: T.List[BaseTorrent]
    anime_requests: T.List[ExtendedAnimeRequest]
    transmission_stats: dedibox.TransmissionStats
    page_views: T.List[SmoothedStat]
    downloads: T.List[SmoothedStat]


def convert_to_diffs(
    items: T.List[T.Tuple[datetime.date, T.Union[int, float]]]
) -> T.Iterable[T.Tuple[datetime.date, T.Union[int, float]]]:
    prev_value = items[0][1] if len(items) else 0
    for item in items:
        day, value = item
        yield day, value - prev_value
        prev_value = value


def build_trendline(
    items: T.List[T.Tuple[datetime.date, T.Union[int, float]]],
) -> T.List[SmoothedStat]:
    values = [item[1] for item in items]
    values_avg = smooth(values)
    return [
        SmoothedStat(day=day, value=value, value_avg=value_avg)
        for (day, value), value_avg in zip(items, values_avg)
    ]


def build_report_context(data: T.Any) -> ReportContext:
    comments = list(data.guestbook_comments) + list(data.nyaa_si_comments)
    torrents = {
        (torrent.source, torrent.torrent_id): torrent
        for torrent in data.anidex_torrents + data.nyaa_si_torrents
    }

    page_views = build_trendline(
        [
            (day, stat.traffic_stat.page_views if stat.traffic_stat else 0)
            for day, stat in data.daily_stats.items()
        ]
    )
    downloads = build_trendline(
        list(
            convert_to_diffs(
                [
                    (day, (stat.nyaa_si_dl or 0) + (stat.anidex_dl or 0))
                    for day, stat in data.daily_stats.items()
                    if stat.nyaa_si_dl is not None
                    or stat.anidex_dl is not None
                ]
            )
        )
    )

    anime_requests: T.List[ExtendedAnimeRequest] = []
    for request in data.anime_requests:
        anidb_info = (
            data.anidb_titles[request.anidb_id] if request.anidb_id else None
        )
        anime_requests.append(
            ExtendedAnimeRequest(request=request, anidb_info=anidb_info)
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
        transmission_stats=data.transmission_stats,
        page_views=page_views,
        downloads=downloads,
    )


def percent(
    dividend: T.Union[int, float], divisor: T.Union[int, float]
) -> str:
    if not divisor:
        return "0.0"
    return f"{dividend / divisor:.2f}"


def write_report(output_dir: Path, data: Data) -> None:
    logging.info(f"Writing output to {output_dir}…")
    output_dir.mkdir(parents=True, exist_ok=True)

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(ROOT_DIR / "data"))
    )
    env.filters["markdown"] = lambda text: render_markdown(text)
    env.filters["tojson"] = lambda obj: json.dumps(obj, default=json_default)
    env.globals.update(percent=percent)

    index_path = output_dir / "index.html"
    index_path.write_text(
        env.get_template("report.jinja").render(
            **build_report_context(data).__dict__
        )
    )

    anidb_path = output_dir / "anidb"
    if not anidb_path.exists():
        anidb_path.symlink_to(CACHE_DIR / "anidb", target_is_directory=True)
