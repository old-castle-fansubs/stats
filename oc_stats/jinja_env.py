import datetime
import json
import typing as T

import jinja2

from oc_stats.common import json_default
from oc_stats.markdown import render_markdown


def percent(
    dividend: T.Union[int, float], divisor: T.Union[int, float]
) -> str:
    if not divisor:
        return "0.0"
    return f"{dividend / divisor:.2f}"


def setup_jinja_env(jinja_env: jinja2.Environment) -> None:
    jinja_env.lstrip_blocks = True
    jinja_env.trim_blocks = True
    jinja_env.globals["deployment_id"] = datetime.datetime.now().isoformat()
    jinja_env.filters["markdown"] = render_markdown
    jinja_env.filters["tojson"] = lambda obj: json.dumps(
        obj, default=json_default
    )
    jinja_env.globals.update(percent=percent)
