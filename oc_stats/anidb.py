import dataclasses
import datetime
import os
import time
import typing as T
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree

import dateutil.parser
import requests
from dataclasses_json import dataclass_json

from oc_stats.common import CACHE_DIR, json_date_metadata

ANIDB_CLIENT = os.environ["ANIDB_CLIENT"]
ANIDB_CLIENTVER = os.environ["ANIDB_CLIENTVER"]


@dataclass_json
@dataclass
class AniDBInfo:
    id: int
    title: str
    type: str
    episodes: int
    synopsis: str
    start_date: T.Optional[datetime.date] = dataclasses.field(
        metadata=json_date_metadata
    )
    end_date: T.Optional[datetime.date] = dataclasses.field(
        metadata=json_date_metadata
    )


class XmlParser:
    def __init__(self, path: Path) -> None:
        self.doc = ElementTree.parse(str(path)).getroot()

    def get_text(self, xpath: str) -> str:
        node = self.doc.find(xpath)
        assert node is not None
        return node.text or ""


def process_synopsis(synopsis: str) -> str:
    return synopsis.replace("http", " http")


def get_anidb_info(anime_id: int) -> AniDBInfo:
    entry_cache_path = CACHE_DIR / "anidb" / f"{anime_id}.xml"
    image_cache_path = CACHE_DIR / "anidb" / f"{anime_id}.jpg"

    if entry_cache_path.exists():
        content = entry_cache_path.read_text()
    else:
        response = requests.get(
            f"http://api.anidb.net:9001/httpapi?request=anime&aid={anime_id}"
            f"&client={ANIDB_CLIENT}&clientver={ANIDB_CLIENTVER}&protover=1"
        )
        response.raise_for_status()
        time.sleep(2)
        entry_cache_path.parent.mkdir(parents=True, exist_ok=True)
        entry_cache_path.write_text(response.text)
        content = response.text

    doc = XmlParser(entry_cache_path)

    image_url = "http://cdn.anidb.net/images/main/" + doc.get_text(
        ".//picture"
    )
    if not image_cache_path.exists():
        response = requests.get(image_url)
        response.raise_for_status()
        time.sleep(2)
        image_cache_path.write_bytes(response.content)

    return AniDBInfo(
        id=anime_id,
        title=doc.get_text(".//title"),
        type=doc.get_text(".//type"),
        episodes=int(doc.get_text(".//episodecount")),
        synopsis=process_synopsis(doc.get_text(".//description")),
        start_date=dateutil.parser.parse(doc.get_text(".//startdate")).date(),
        end_date=dateutil.parser.parse(doc.get_text(".//enddate")).date(),
    )
