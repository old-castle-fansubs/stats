import csv
import datetime
import typing as T
from dataclasses import dataclass

import dateutil.parser
import lxml.html
import requests


@dataclass
class TrafficStat:
    day: datetime.date
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
        super().__init__('not logged in')


class InvalidAuth(ApiError):
    def __init__(self) -> None:
        super().__init__('invalid credentials')


class UnexpectedHttpCode(ApiError):
    def __init__(self, code: int) -> None:
        super().__init__(f'unexpected status code "{code}"')


class NeocitiesApi:
    def __init__(self) -> None:
        self.session = requests.Session()

    def login(self, user_name: str, password: str) -> None:
        response = self.session.get('https://neocities.org/signin')
        if response.status_code != 200:
            raise UnexpectedHttpCode(response.status_code)

        tree = lxml.html.fromstring(response.content)
        csrf_token = tree.xpath('//input[@name="csrf_token"]/@value')[0]
        response = self.session.post(
            f'https://neocities.org/signin',
            data={
                'csrf_token': csrf_token,
                'username': user_name,
                'password': password
            },
        )
        if 'Invalid login' in response.text:
            raise InvalidAuth
        self.user_name = user_name

    def get_traffic_stats(self) -> T.Iterable[TrafficStat]:
        if not self.user_name:
            raise NotLoggedIn

        response = self.session.get(
            f'https://neocities.org/site/{self.user_name}'
            f'/stats?days=sincethebigbang&format=csv'
        )
        if response.status_code != 200:
            raise UnexpectedHttpCode(response.status_code)
        reader = csv.DictReader(response.text.splitlines())
        for row in reader:
            yield TrafficStat(
                day=dateutil.parser.parse(row['day']).date(),
                hits=int(row['hits']),
                views=int(row['views']),
                comments=int(row['comments']),
                follows=int(row['follows']),
                site_updates=int(row['site_updates']),
                bandwidth=int(row['bandwidth'])
            )
