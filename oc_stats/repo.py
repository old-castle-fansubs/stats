import logging
import typing as T

from oc_stats.context import BaseContextBuilder

MISSING = object()


class ContextBuilderRepository:
    def __init__(self) -> None:
        self.data: dict[T.Any, T.Any] = {}
        self.builders = [cls() for cls in BaseContextBuilder.__subclasses__()]

    def load_data(self) -> None:
        for builder in self.builders:
            if builder.db_path.exists():
                value = builder.deserialize(builder.db_path.read_text())
            else:
                value = builder.deserialize(None)
            self.data[builder.context_key] = value

    def update_data(self) -> None:
        for builder in self.builders:
            try:
                value = self.data.get(builder.context_key)
                value = builder.update(value)
                self.data[builder.context_key] = value
            except Exception as ex:
                logging.exception(ex)

    def save_data(self) -> None:
        for builder in self.builders:
            value = self.data.get(builder.context_key, MISSING)
            if value is not MISSING:
                builder.db_path.parent.mkdir(parents=True, exist_ok=True)
                builder.db_path.write_text(builder.serialize(value))

    def build_context(self) -> dict[str, T.Any]:
        return {
            builder.context_key: builder.transform_context(
                self.data.get(builder.context_key)
            )
            for builder in self.builders
        }
