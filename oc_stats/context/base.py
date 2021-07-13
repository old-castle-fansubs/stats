import json
import typing as T
from pathlib import Path

from oc_stats.common import DATA_DIR, json_default


class BaseContextBuilder:
    context_key: str = NotImplemented

    @property
    def db_path(self) -> Path:
        return DATA_DIR / f"{self.context_key}.json"

    @staticmethod
    def deserialize(value: T.Optional[str]) -> T.Any:
        raise NotImplementedError("not implemented")

    @staticmethod
    def serialize(value: T.Any) -> str:
        return json.dumps(value, default=json_default, indent=4)

    @staticmethod
    def transform_context(value: T.Any) -> T.Any:
        return value

    def update(self, original_value: T.Any) -> T.Any:
        raise NotImplementedError("not implemented")
