#!/usr/bin/env python3
import pickle
import typing as T
from pathlib import Path

import configargparse
import xdg

from oc_stats.data import DATA_PATH, Data, refresh_data
from oc_stats.report import write_report


def parse_args() -> configargparse.Namespace:
    parser = configargparse.ArgumentParser(
        formatter_class=configargparse.RawTextHelpFormatter,
        default_config_files=[str(Path(xdg.XDG_CONFIG_HOME) / "oc-tools.yml")],
    )

    parser.add_argument("--neocities-user", required=True)
    parser.add_argument("--neocities-pass", required=True)
    parser.add_argument("--dedibox-user", required=True)
    parser.add_argument("--dedibox-pass", required=True)
    parser.add_argument("--anidex-user", required=True)
    parser.add_argument("--anidex-pass", required=True)
    parser.add_argument("--anidex-group", type=int, required=True)
    parser.add_argument("--nyaasi-user", required=True)
    parser.add_argument("--nyaasi-pass", required=True)
    parser.add_argument("-d", "--dev", action="store_true")
    parser.add_argument(
        "-o", "--output", default=Path("stats.html"), type=Path, required=False
    )

    return parser.parse_known_args()[0]


def main() -> None:
    args = parse_args()

    if DATA_PATH.exists():
        data = Data.from_json(DATA_PATH.read_text())
    else:
        data = Data(
            guestbook_comments=[],
            torrent_stats=None,
            neocities_traffic_stats=[],
            nyaa_si_torrents=[],
            anidex_torrents=[],
            nyaa_si_comments={},
        )

    for _ in refresh_data(args, data):
        DATA_PATH.write_text(data.to_json(indent=4))

    write_report(args, data)


if __name__ == "__main__":
    main()
