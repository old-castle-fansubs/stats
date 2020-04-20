import datetime
import logging
import os
import pickle
import typing as T

import humanfriendly
import lxml.html
import requests

from oc_stats.cache import CACHE_DIR, is_global_cache_enabled
from oc_stats.common import BaseComment as Comment
from oc_stats.common import BaseTorrent as Torrent

NYAA_SI_USER = os.environ["NYAA_SI_USER"]
NYAA_SI_PASS = os.environ["NYAA_SI_PASS"]


def list_user_torrents() -> T.Iterable[Torrent]:
    cache_path = CACHE_DIR / "nyaasi" / "torrents.dat"

    if is_global_cache_enabled() and cache_path.exists():
        logging.info("nyaa.si: using cached torrent list")
        return pickle.loads(cache_path.read_bytes())

    logging.info("nyaa.si: fetching torrent list")
    session = requests.Session()

    response = session.get("https://nyaa.si/login")
    response.raise_for_status()
    tree = lxml.html.fromstring(response.content)
    csrf_token = tree.xpath('//input[@id="csrf_token"]/@value')[0]
    response = session.post(
        "https://nyaa.si/login",
        data={
            "username": NYAA_SI_USER,
            "password": NYAA_SI_PASS,
            "csrf_token": csrf_token,
        },
    )
    response.raise_for_status()

    ret: T.List[Torrent] = []
    page = 1
    page_count = float("inf")
    while page <= page_count:
        response = session.get(
            f"https://nyaa.si/user/{NYAA_SI_USER}?s=id&o=desc&page={page}"
        )
        response.raise_for_status()

        tree = lxml.html.fromstring(response.content)
        for row in tree.xpath("//table/tbody/tr"):
            ret.append(_make_torrent(row))

        page_count = int(
            tree.xpath(
                '//ul[@class="pagination"]/li[position()=last()-1]/a/text()'
            )[0]
        )
        page += 1

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(pickle.dumps(ret))
    return ret


def list_torrent_comments(torrent: Torrent) -> T.Iterable[Comment]:
    cache_path = CACHE_DIR / "nyaasi" / f"torrent-{torrent.torrent_id}.txt"

    if cache_path.exists():
        logging.info(
            f"nyaa.si: using cached torrent info for {torrent.torrent_id}"
        )
        content = cache_path.read_text()
    else:
        logging.info(
            f"nyaa.si: fetching torrent info for {torrent.torrent_id}"
        )
        response = requests.get(f"https://nyaa.si/view/{torrent.torrent_id}")
        response.raise_for_status()
        content = response.text
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(content)

    ret: T.List[Comment] = []
    tree = lxml.html.fromstring(content)
    for row in tree.xpath(
        '//div[@id="comments"]//div[starts-with(@id, "com-")]'
    ):
        ret.append(_make_comment(torrent, row))

    if torrent.comment_count != len(ret) and not is_global_cache_enabled():
        cache_path.unlink()
        return list_torrent_comments(torrent)

    return ret


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
        upload_date=datetime.datetime(
            *humanfriendly.parse_date(row.xpath(".//td[5]/text()")[0])
        ).replace(tzinfo=datetime.timezone.utc),
        seeder_count=int(row.xpath(".//td[6]/text()")[0]),
        leecher_count=int(row.xpath(".//td[7]/text()")[0]),
        download_count=int(row.xpath(".//td[8]/text()")[0]),
        comment_count=int(
            row.xpath('normalize-space(.//a[@class="comments"])') or "0"
        ),
        visible=row.xpath("./@class")[0] != "warning",
    )


def _make_comment(torrent: Torrent, row: lxml.html.HtmlElement) -> Comment:
    return Comment(
        source="nyaa.si",
        comment_date=datetime.datetime(
            *humanfriendly.parse_date(
                row.xpath(
                    './/div[contains(@class, "comment-details")]'
                    "//small/text()"
                )[0]
            )
        ).replace(tzinfo=datetime.timezone.utc),
        author_name=row.xpath('.//a[contains(@href, "/user/")]/text()')[0],
        author_avatar_url=row.xpath('.//img[@class="avatar"]/@src')[0],
        text=row.xpath(".//div[@markdown-text]/text()")[0],
        website_title=torrent.name,
        website_link=torrent.website_link
        + row.xpath('.//a[contains(@href, "#com-")]/@href')[0],
    )
