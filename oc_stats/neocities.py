import csv
import dataclasses
import os
import typing as T

import dateutil.parser
import lxml.html
import requests
from dataclasses_json import dataclass_json

from oc_stats.common import BaseTrafficStat

NEOCITIES_USER = os.environ["NEOCITIES_USER"]
NEOCITIES_PASS = os.environ["NEOCITIES_PASS"]


@dataclass_json
@dataclasses.dataclass
class TrafficStat(BaseTrafficStat):
    views: int
    comments: int
    follows: int
    site_updates: int
    bandwidth: int


class ApiError(RuntimeError):
    pass


class NotLoggedIn(ApiError):
    def __init__(self) -> None:
        super().__init__("not logged in")


class InvalidAuth(ApiError):
    def __init__(self) -> None:
        super().__init__("invalid credentials")


def get_traffic_stats() -> T.Iterable[TrafficStat]:
    session = requests.session()

    response = session.get("https://neocities.org/signin")
    response.raise_for_status()

    tree = lxml.html.fromstring(response.content)
    csrf_token = tree.xpath('//input[@name="csrf_token"]/@value')[0]
    response = session.post(
        f"https://neocities.org/signin",
        data={
            "csrf_token": csrf_token,
            "username": NEOCITIES_USER,
            "password": NEOCITIES_PASS,
        },
    )
    if "Invalid login" in response.text:
        raise InvalidAuth

    response = session.get(
        f"https://neocities.org/site/{NEOCITIES_USER}"
        f"/stats?days=sincethebigbang&format=csv"
    )
    response.raise_for_status()

    reader = csv.DictReader(response.text.splitlines())
    for row in reader:
        yield TrafficStat(
            day=dateutil.parser.parse(row["day"]).date(),
            hits=int(row.get("hits", 0)),
            views=int(row.get("views", 0)),
            comments=int(row.get("comments", 0)),
            follows=int(row.get("follows", 0)),
            site_updates=int(row.get("site_updates", 0)),
            bandwidth=int(row.get("bandwidth", 0)),
        )
