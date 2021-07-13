import logging
import os
import typing as T
from dataclasses import dataclass
from datetime import datetime

import humanfriendly
import lxml.html
import requests
from cachetools.func import ttl_cache

ANIDEX_USER = os.environ["ANIDEX_USER"]
ANIDEX_PASS = os.environ["ANIDEX_PASS"]
ANIDEX_GROUP_ID = os.environ["ANIDEX_GROUP_ID"]


@dataclass
class Torrent:
    torrent_id: int
    website_link: str
    torrent_link: str
    magnet_link: T.Optional[str]
    name: str
    size: int
    upload_date: datetime
    seeder_count: int
    leecher_count: int
    download_count: int
    like_count: int
    comment_count: int
    visible: bool


def bypass_ddos_guard(session: requests.Session) -> None:
    response = session.post("https://check.ddos-guard.net/check.js")
    response.raise_for_status()
    # make the cookies work across all domains
    for key, value in session.cookies.items():
        session.cookies.set_cookie(requests.cookies.create_cookie(key, value))


@ttl_cache()
def get_group_torrents() -> T.Iterable[Torrent]:
    logging.info("anidex: fetching torrent list")
    session = requests.Session()
    bypass_ddos_guard(session)

    response = session.post(
        "https://anidex.info/ajax/actions.ajax.php?function=login",
        headers={"x-requested-with": "XMLHttpRequest"},
        data={"login_username": ANIDEX_USER, "login_password": ANIDEX_PASS},
    )
    response.raise_for_status()

    ret: list[Torrent] = []
    offset = 0
    while True:
        response = session.get(
            f"https://anidex.info/?page=group&id={ANIDEX_GROUP_ID}&offset={offset}"
        )
        response.raise_for_status()

        tree = lxml.html.fromstring(response.content)
        done = 0
        for row in tree.xpath("//table/tbody/tr"):
            ret.append(_make_torrent(row))
            done += 1

        if not done:
            break
        offset += done

    return ret


def _make_torrent(row: lxml.html.HtmlElement) -> Torrent:
    torrent_id = int(row.xpath(".//td[3]/a/@id")[0])

    return Torrent(
        torrent_id=torrent_id,
        name=row.xpath(".//td[3]//span/@title")[0],
        website_link=f"https://anidex.info/torrent/{torrent_id}",
        torrent_link=f"https://anidex.info/dl/{torrent_id}",
        magnet_link=row.xpath('.//a[contains(@href, "magnet")]/@href')[0],
        size=humanfriendly.parse_size(row.xpath(".//td[7]/text()")[0]),
        upload_date=datetime(
            *humanfriendly.parse_date(row.xpath(".//td[8]/@title")[0])
        ),
        seeder_count=int(row.xpath(".//td[9]/text()")[0]),
        leecher_count=int(row.xpath(".//td[10]/text()")[0]),
        download_count=int(row.xpath(".//td[11]/text()")[0]),
        like_count=int((row.xpath("./td[4]/span/text()") + ["+0"])[0][1:]),
        comment_count=0,
        visible=len(row.xpath('.//span[@title="Hidden"]')) == 0,
    )
