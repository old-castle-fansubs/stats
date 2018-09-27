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
    visible: bool

    @property
    def torrent_link(self) -> str:
        return f'https://nyaa.si/download/{self.torrent_id}.torrent'


@dataclass
class TorrentComment:
    torrent_id: int
    comment_date: datetime.datetime
    author_name: str
    author_avatar_url: str
    text: str


class ApiError(RuntimeError):
    pass


class UserNotFound(ApiError):
    def __init__(self, user_name: str) -> None:
        super().__init__(f'user "{user_name}" was not found')


class InvalidAuth(ApiError):
    pass


class UnexpectedHttpCode(ApiError):
    def __init__(self, code: int) -> None:
        super().__init__(f'unexpected status code "{code}"')


class NyaaSiApi:
    def __init__(self) -> None:
        self.session = requests.Session()

    def login(self, user_name: str, password: str) -> None:
        self.session = requests.Session()
        response = self.session.get('https://nyaa.si/login')
        if response.status_code != 200:
            raise UnexpectedHttpCode(response.status_code)

        tree = lxml.html.fromstring(response.content)
        csrf_token = tree.xpath('//input[@id="csrf_token"]/@value')[0]

        response = self.session.post(
            'https://nyaa.si/login',
            data={
                'username': user_name,
                'password': password,
                'csrf_token': csrf_token
            }
        )
        if response.status_code != 200:
            raise UnexpectedHttpCode(response.status_code)

        # if 'csrf_token' in response.text:
        #     raise InvalidAuth('Invalid username or password.')

    def list_user_torrents(self, user_name: str) -> T.Iterable[Torrent]:
        page = 1
        while True:
            response = self.session.get(
                f'https://nyaa.si/user/{user_name}?s=id&o=desc&page={page}'
            )

            if response.status_code == 404:
                raise UserNotFound(user_name)
            if response.status_code != 200:
                raise UnexpectedHttpCode(response.status_code)

            tree = lxml.html.fromstring(response.content)
            for row in tree.xpath('//table/tbody/tr'):
                yield self._make_torrent(row)

            page_count = int(tree.xpath(
                '//ul[@class="pagination"]/li[position()=last()-1]/a/text()'
            )[0])

            page += 1
            if page > page_count:
                break

    def list_torrent_comments(
            self,
            torrent_id: int
    ) -> T.Iterable[TorrentComment]:
        response = self.session.get(f'https://nyaa.si/view/{torrent_id}')
        if response.status_code != 200:
            raise UnexpectedHttpCode(response.status_code)

        tree = lxml.html.fromstring(response.content)
        for row in tree.xpath('//div[@id="comments"]/div[@id]'):
            yield self._make_comment(torrent_id, row)

    def _make_torrent(self, row: lxml.html.HtmlElement) -> Torrent:
        return Torrent(
            torrent_id=int(
                row.xpath('.//td[2]/a[last()]/@href')[0].replace('/view/', '')
            ),
            name=row.xpath('.//td[2]/a[not(@class="comments")]/@title')[0],
            magnet_link=row.xpath('.//a[contains(@href, "magnet")]/@href')[0],
            size=humanfriendly.parse_size(row.xpath('.//td[4]/text()')[0]),
            upload_date=datetime.datetime(
                *humanfriendly.parse_date(
                    row.xpath('.//td[5]/text()')[0]
                )
            ),
            seeder_count=int(row.xpath('.//td[6]/text()')[0]),
            leecher_count=int(row.xpath('.//td[7]/text()')[0]),
            download_count=int(row.xpath('.//td[8]/text()')[0]),
            comment_count=int(
                row.xpath('normalize-space(.//a[@class="comments"])')
                or '0'
            ),
            visible=row.xpath('./@class')[0] != 'warning'
        )

    def _make_comment(
            self,
            torrent_id: int,
            row: lxml.html.HtmlElement
    ) -> TorrentComment:
        return TorrentComment(
            torrent_id=torrent_id,
            comment_date=datetime.datetime(
                *humanfriendly.parse_date(
                    row.xpath(
                        './/div[contains(@class, "comment-details")]'
                        '//small/text()'
                    )[0]
                )
            ),
            author_name=row.xpath('.//a[contains(@href, "/user/")]/text()')[0],
            author_avatar_url=row.xpath('.//img[@class="avatar"]/@src')[0],
            text=row.xpath('.//div[@markdown-text]/text()')[0]
        )
