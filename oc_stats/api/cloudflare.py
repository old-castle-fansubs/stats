import logging
import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta

import dateutil.parser
import requests
from cachetools.func import ttl_cache

CLOUDFLARE_ZONE = os.environ["CLOUDFLARE_ZONE"]
CLOUDFLARE_API_USER = os.environ["CLOUDFLARE_API_USER"]
CLOUDFLARE_API_KEY = os.environ["CLOUDFLARE_API_KEY"]
CLOUDFLARE_API_URL = "https://api.cloudflare.com/client/v4/graphql"


@dataclass
class TrafficStat:
    requests: int
    page_views: int
    unique_visitors: int


@ttl_cache()
def get_recent_hits() -> dict[date, TrafficStat]:
    logging.info("cloudflare: fetching hit stats")

    start = datetime.today().date() - timedelta(days=10)
    end = datetime.today().date() + timedelta(days=1)

    query = """{
    viewer {
        zones(filter: {zoneTag: "%s"}) {
            httpRequests1dGroups(
                orderBy: [date_DESC]
                limit: 1000
                filter: {date_gt: "%s", date_lt: "%s"}
            ) {
                date: dimensions {
                    date
                }
                sum {
                    pageViews
                    requests
                }
                uniq { uniques }
            }
        }
    }
}
    """ % (
        CLOUDFLARE_ZONE,
        start,
        end,
    )

    response = requests.post(
        CLOUDFLARE_API_URL,
        headers={
            "X-Auth-Email": CLOUDFLARE_API_USER,
            "X-Auth-Key": CLOUDFLARE_API_KEY,
            "Content-Type": "application/json",
        },
        json={"query": query},
    )
    response.raise_for_status()

    ret: dict[date, TrafficStat] = {}
    for item in response.json()["data"]["viewer"]["zones"][0][
        "httpRequests1dGroups"
    ]:
        ret[dateutil.parser.parse(item["date"]["date"]).date()] = TrafficStat(
            requests=item["sum"]["requests"],
            page_views=item["sum"]["pageViews"],
            unique_visitors=item["uniq"]["uniques"],
        )
    return ret
