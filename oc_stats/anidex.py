import datetime
import logging
import os
import pickle
import typing as T
from dataclasses import dataclass

import humanfriendly
import lxml.html
import requests

from oc_stats.cache import CACHE_DIR, is_global_cache_enabled
from oc_stats.common import BaseTorrent

ANIDEX_USER = os.environ["ANIDEX_USER"]
ANIDEX_PASS = os.environ["ANIDEX_PASS"]
ANIDEX_GROUP_ID = os.environ["ANIDEX_GROUP_ID"]


@dataclass
class Torrent(BaseTorrent):
    like_count: int = 0


def bypass_ddos_guard(session: requests.Session) -> None:
    response = session.post("https://check.ddos-guard.net/check.js")
    response.raise_for_status()
    # make the cookies work across all domains
    for key, value in session.cookies.items():
        session.cookies.set_cookie(requests.cookies.create_cookie(key, value))


def list_group_torrents() -> T.Iterable[Torrent]:
    cache_path = CACHE_DIR / "anidex" / "torrents.dat"

    if cache_path.exists() and is_global_cache_enabled():
        logging.info("anidex: using cached torrent list")
        return pickle.loads(cache_path.read_bytes())

    logging.info("anidex: fetching torrent list")
    session = requests.Session()
    bypass_ddos_guard(session)

    response = session.post(
        "https://anidex.info/ajax/actions.ajax.php?function=login",
        headers={"x-requested-with": "XMLHttpRequest"},
        data={"login_username": ANIDEX_USER, "login_password": ANIDEX_PASS},
    )
    response.raise_for_status()

    ret: T.List[Torrent] = []
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

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(pickle.dumps(ret))
    return ret


def _make_torrent(row: lxml.html.HtmlElement) -> Torrent:
    torrent_id = int(row.xpath(".//td[3]/a/@id")[0])

    return Torrent(
        source="anidex.info",
        torrent_id=torrent_id,
        name=row.xpath(".//td[3]//span/@title")[0],
        website_link=f"https://anidex.info/torrent/{torrent_id}",
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
