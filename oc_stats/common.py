import dataclasses
import typing as T
from datetime import date, datetime, timedelta
from pathlib import Path

PROJ_DIR = Path(__file__).parent
ROOT_DIR = PROJ_DIR.parent
DATA_DIR = ROOT_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
STATIC_DIR = PROJ_DIR / "static"


def json_default(obj: T.Any) -> T.Any:
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, timedelta):
        return obj.total_seconds()
    return None


def convert_to_diffs(
    items: dict[date, T.Union[int, float]]
) -> dict[date, T.Union[int, float]]:
    ret: dict[date, T.Union[int, float]] = {}
    if not items:
        return ret
    prev_key = list(items.keys())[0]
    prev_value = None
    for key, value in sorted(items.items(), key=lambda kv: kv[0]):
        if prev_value is not None:
            if abs((key - prev_key).days) <= 1:
                ret[key] = value - prev_value
        prev_key = key
        prev_value = value
    return ret
