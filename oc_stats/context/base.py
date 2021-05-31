import json
import typing as T

from oc_stats.common import DATA_DIR, json_default


class BaseContextBuilder:
    context_key = NotImplemented

    @property
    def db_path(self) -> str:
        return DATA_DIR / f"{self.context_key}.json"

    @staticmethod
    def deserialize(value: T.Optional[str]) -> T.Any:
        raise NotImplementedError("not implemented")

    @staticmethod
    def serialize(value: T.Any) -> str:
        return json.dumps(value, default=json_default, indent=4)

    @staticmethod
    def transform_context(value: T.Optional[str]) -> T.Any:
        return value

    def update(self, original_value: T.Any) -> T.Any:
        raise NotImplementedError("not implemented")
