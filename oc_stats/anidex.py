import datetime
import typing as T
from dataclasses import dataclass

import humanfriendly
import lxml.html
import requests
from dataclasses_json import dataclass_json

from oc_stats.common import BaseTorrent


@dataclass_json
@dataclass
class Torrent(BaseTorrent):
    like_count: int = 0


def list_group_torrents(
    user_name: str,
    password: str,
    group_id: int,
    page_callback: T.Optional[T.Callable[[int], None]],
) -> T.Iterable[Torrent]:
    session = requests.Session()

    response = session.post(
        "https://anidex.info/ajax/actions.ajax.php?function=login",
        headers={"x-requested-with": "XMLHttpRequest"},
        data={"login_username": user_name, "login_password": password},
    )
    response.raise_for_status()

    offset = 0
    while True:
        if page_callback:
            page_callback(offset)

        response = session.get(
            f"https://anidex.info/?page=group&id={group_id}&offset={offset}"
        )
        response.raise_for_status()

        tree = lxml.html.fromstring(response.content)
        done = 0
        for row in tree.xpath("//table/tbody/tr"):
            yield _make_torrent(row)
            done += 1

        if not done:
            break
        offset += done


def _make_torrent(row: lxml.html.HtmlElement) -> Torrent:
    torrent_id = int(row.xpath(".//td[3]/a/@id")[0])

    return Torrent(
        source="anidex.info",
        torrent_id=torrent_id,
        name=row.xpath(".//td[3]//span/@title")[0],
        torrent_link=f"https://anidex.info/dl/{torrent_id}",
        magnet_link=row.xpath('.//a[contains(@href, "magnet")]/@href')[0],
        size=humanfriendly.parse_size(row.xpath(".//td[7]/text()")[0]),
        upload_date=datetime.datetime(
            *humanfriendly.parse_date(row.xpath(".//td[8]/@title")[0])
        ),
        seeder_count=int(row.xpath(".//td[9]/text()")[0]),
        leecher_count=int(row.xpath(".//td[10]/text()")[0]),
        download_count=int(row.xpath(".//td[11]/text()")[0]),
        like_count=int((row.xpath("./td[4]/span/text()") + ["+0"])[0][1:]),
        comment_count=0,
        visible=len(row.xpath('.//span[@title="Hidden"]')) == 0,
    )
