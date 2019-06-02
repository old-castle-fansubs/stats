import csv
import dataclasses
import datetime
import typing as T

import dateutil.parser
import lxml.html
import requests
from dataclasses_json import dataclass_json


@dataclass_json
@dataclasses.dataclass
class TrafficStat:
    day: datetime.date = dataclasses.field(
        metadata={
            "dataclasses_json": {
                "encoder": datetime.date.isoformat,
                "decoder": datetime.date.fromisoformat,
            }
        }
    )
    hits: int
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


def get_traffic_stats(
    user_name: str, password: str
) -> T.Iterable[TrafficStat]:
    session = requests.session()

    response = session.get("https://neocities.org/signin")
    response.raise_for_status()

    tree = lxml.html.fromstring(response.content)
    csrf_token = tree.xpath('//input[@name="csrf_token"]/@value')[0]
    response = session.post(
        f"https://neocities.org/signin",
        data={
            "csrf_token": csrf_token,
            "username": user_name,
            "password": password,
        },
    )
    if "Invalid login" in response.text:
        raise InvalidAuth

    response = session.get(
        f"https://neocities.org/site/{user_name}"
        f"/stats?days=sincethebigbang&format=csv"
    )
    response.raise_for_status()

    reader = csv.DictReader(response.text.splitlines())
    for row in reader:
        yield TrafficStat(
            day=dateutil.parser.parse(row["day"]).date(),
            hits=int(row["hits"]),
            views=int(row["views"]),
            comments=int(row["comments"]),
            follows=int(row["follows"]),
            site_updates=int(row["site_updates"]),
            bandwidth=int(row["bandwidth"]),
        )
