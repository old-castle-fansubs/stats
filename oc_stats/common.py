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
    items: T.Dict[datetime.date, T.Union[int, float]]
) -> T.Dict[datetime.date, T.Union[int, float]]:
    ret = {**items}
    if not ret:
        return ret
    prev_key = list(items.keys())[0]
    prev_value = ret.pop(prev_key)
    for key, value in ret.items():
        ret[key] = value - prev_value
        prev_value = value
    return ret
