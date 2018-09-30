import datetime
import typing as T
from dataclasses import dataclass

import humanfriendly
import lxml.html
import requests


@dataclass
class Torrent:
    torrent_id: int
    name: str
    magnet_link: str
    size: int
    upload_date: datetime.datetime
    seeder_count: int
    leecher_count: int
    download_count: int
    comment_count: int
    like_count: int
    visible: bool

    @property
    def torrent_link(self) -> str:
        return f'https://anidex.info/dl/{self.torrent_id}'


class ApiError(RuntimeError):
    pass


class GroupNotFound(ApiError):
    def __init__(self, group_id: int) -> None:
        super().__init__(f'group "{group_id}" was not found')


class InvalidAuth(ApiError):
    pass


class UnexpectedHttpCode(ApiError):
    def __init__(self, code: int) -> None:
        super().__init__(f'unexpected status code "{code}"')


class AnidexApi:
    def __init__(self) -> None:
        self.session = requests.Session()

    def login(self, user_name: str, password: str) -> None:
        self.session = requests.Session()

        response = self.session.post(
            'https://anidex.info/ajax/actions.ajax.php?function=login',
            headers={
                'x-requested-with': 'XMLHttpRequest',
            },
            data={
                'login_username': user_name,
                'login_password': password,
            },
        )
        if response.status_code != 200:
            raise UnexpectedHttpCode(response.status_code)

    def list_group_torrents(self, group_id: int) -> T.Iterable[Torrent]:
        offset = 0
        while True:
            response = self.session.get(
                f'https://anidex.info/?page=group&id={group_id}&offset={offset}'
            )

            if response.status_code == 404:
                raise GroupNotFound(group_id)
            if response.status_code != 200:
                raise UnexpectedHttpCode(response.status_code)

            tree = lxml.html.fromstring(response.content)
            done = 0
            for row in tree.xpath('//table/tbody/tr'):
                yield self._make_torrent(row)
                done += 1

            if not done:
                break
            offset += done

    def _make_torrent(self, row: lxml.html.HtmlElement) -> Torrent:
        return Torrent(
            torrent_id=int(row.xpath('.//td[3]/a/@id')[0]),
            name=row.xpath('.//td[3]//span/@title')[0],
            magnet_link=row.xpath('.//a[contains(@href, "magnet")]/@href')[0],
            size=humanfriendly.parse_size(row.xpath('.//td[7]/text()')[0]),
            upload_date=datetime.datetime(
                *humanfriendly.parse_date(
                    row.xpath('.//td[8]/@title')[0]
                )
            ),
            seeder_count=int(row.xpath('.//td[9]/text()')[0]),
            leecher_count=int(row.xpath('.//td[10]/text()')[0]),
            download_count=int(row.xpath('.//td[11]/text()')[0]),
            like_count=int((row.xpath('./td[4]/span/text()') + ['+0'])[0][1:]),
            comment_count=0,
            visible=len(row.xpath('.//span[@title="Hidden"]')) == 0,
        )
