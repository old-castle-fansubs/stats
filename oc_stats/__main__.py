#!/usr/bin/env python3
import argparse
import logging
from pathlib import Path

from oc_stats.cache import set_global_cache_enabled
from oc_stats.data import Data
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

    set_global_cache_enabled(args.dev)
    data = Data()
    write_report(args.output_dir, data)


if __name__ == "__main__":
    main()
