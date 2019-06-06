import datetime
import json
import typing as T
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import humanfriendly
import lxml.html
import requests
from dataclasses_json import dataclass_json

from .common import BaseComment, BaseTorrent


@dataclass_json
@dataclass
class Torrent(BaseTorrent):
    pass


@dataclass_json
@dataclass
class Comment(BaseComment):
    torrent_id: T.Optional[int] = None


def list_user_torrents(user_name: str, password: str) -> T.Iterable[Torrent]:
    session = requests.Session()

    if password:
        response = session.get("https://nyaa.si/login")
        response.raise_for_status()

        tree = lxml.html.fromstring(response.content)
        csrf_token = tree.xpath('//input[@id="csrf_token"]/@value')[0]

        response = session.post(
            "https://nyaa.si/login",
            data={
                "username": user_name,
                "password": password,
                "csrf_token": csrf_token,
            },
        )
        response.raise_for_status()

    page = 1
    while True:
        response = session.get(
            f"https://nyaa.si/user/{user_name}?s=id&o=desc&page={page}"
        )
        response.raise_for_status()

        tree = lxml.html.fromstring(response.content)
        for row in tree.xpath("//table/tbody/tr"):
            yield _make_torrent(row)

        page_count = int(
            tree.xpath(
                '//ul[@class="pagination"]/li[position()=last()-1]/a/text()'
            )[0]
        )

        page += 1
        if page > page_count:
            break


def list_torrent_comments(torrent_id: int) -> T.Iterable[Comment]:
    response = requests.get(f"https://nyaa.si/view/{torrent_id}")
    response.raise_for_status()

    tree = lxml.html.fromstring(response.content)
    for row in tree.xpath(
        '//div[@id="comments"]//div[starts-with(@id, "com-")]'
    ):
        yield _make_comment(torrent_id, row)


def _make_torrent(row: lxml.html.HtmlElement) -> Torrent:
    torrent_id = int(
        row.xpath(".//td[2]/a[last()]/@href")[0].replace("/view/", "")
    )

    return Torrent(
        source="nyaa.si",
        torrent_id=torrent_id,
        name=row.xpath('.//td[2]/a[not(@class="comments")]/@title')[0],
        website_link=f"https://nyaa.si/view/{torrent_id}",
        torrent_link=f"https://nyaa.si/download/{torrent_id}.torrent",
        magnet_link=row.xpath('.//a[contains(@href, "magnet")]/@href')[0],
        size=humanfriendly.parse_size(row.xpath(".//td[4]/text()")[0]),
        upload_date=datetime(
            *humanfriendly.parse_date(row.xpath(".//td[5]/text()")[0]),
            tzinfo=timezone.utc,
        ).replace(),
        seeder_count=int(row.xpath(".//td[6]/text()")[0]),
        leecher_count=int(row.xpath(".//td[7]/text()")[0]),
        download_count=int(row.xpath(".//td[8]/text()")[0]),
        comment_count=int(
            row.xpath('normalize-space(.//a[@class="comments"])') or "0"
        ),
        visible=row.xpath("./@class")[0] != "warning",
    )


def _make_comment(torrent_id: int, row: lxml.html.HtmlElement) -> Comment:
    return Comment(
        source="nyaa.si",
        torrent_id=torrent_id,
        comment_date=datetime(
            *humanfriendly.parse_date(
                row.xpath(
                    './/div[contains(@class, "comment-details")]'
                    "//small/text()"
                )[0]
            ),
            tzinfo=timezone.utc,
        ),
        author_name=row.xpath('.//a[contains(@href, "/user/")]/text()')[0],
        author_avatar_url=row.xpath('.//img[@class="avatar"]/@src')[0],
        text=row.xpath(".//div[@markdown-text]/text()")[0],
    )
