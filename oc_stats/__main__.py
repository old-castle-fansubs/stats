#!/usr/bin/env python3
import argparse
import logging
from pathlib import Path

from oc_stats.data import DATA_PATH, Data, refresh_data
from oc_stats.report import write_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument("-d", "--dev", action="store_true")
    parser.add_argument(
        "-o", "--output-dir", default=Path("build"), type=Path, required=False
    )

    return parser.parse_known_args()[0]


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    args = parse_args()

    if DATA_PATH.exists():
        data = Data.from_json(DATA_PATH.read_text())
    else:
        data = Data(
            guestbook_comments=[],
            torrent_requests=[],
            nyaa_si_torrents=[],
            nyaa_si_comments={},
            anidex_torrents=[],
            daily_stats={},
            anidb_titles={},
        )

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    for _ in refresh_data(data, args.dev):
        DATA_PATH.write_text(data.to_json(indent=4))

    write_report(args.output_dir, data)


if __name__ == "__main__":
    main()
