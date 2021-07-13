import json
import typing as T
from dataclasses import dataclass
from datetime import datetime

import dateutil.parser

from oc_stats.api import nyaa_si
from oc_stats.api.dedibox import get_guestbook_comments
from oc_stats.context.base import BaseContextBuilder


@dataclass
class CommentDTO:
    source: str
    website_title: T.Optional[str]
    website_link: T.Optional[str]
    comment_date: datetime
    author_name: str
    author_avatar_url: T.Optional[str]
    text: str


class CommentsContextBuilder(BaseContextBuilder):
    context_key = "comments"

    @staticmethod
    def deserialize(value: T.Optional[str]) -> T.Any:
        if not value:
            return []
        return [
            CommentDTO(
                comment_date=dateutil.parser.parse(item.pop("comment_date")),
                **item,
            )
            for item in json.loads(value)
        ]

    def update(self, original_value: T.Any) -> T.Any:
        ret: list[CommentDTO] = []

        guestbook_comments = get_guestbook_comments()
        ret.extend(
            CommentDTO(
                source="guestbook",
                website_title=None,
                website_link=comment.website_link,
                comment_date=comment.comment_date,
                author_name=comment.author_name,
                author_avatar_url=comment.author_avatar_url,
                text=comment.text,
            )
            for comment in guestbook_comments
        )

        nyaa_si_torrents = list(nyaa_si.get_user_torrents())
        nyaa_si_comments = list(
            sum(
                (
                    list(nyaa_si.get_torrent_comments(torrent))
                    for torrent in nyaa_si_torrents
                ),
                [],
            )
        )

        ret.extend(
            CommentDTO(
                source="nyaa.si",
                website_title=comment.website_title,
                website_link=comment.website_link,
                comment_date=comment.comment_date,
                author_name=comment.author_name,
                author_avatar_url=comment.author_avatar_url,
                text=comment.text,
            )
            for comment in nyaa_si_comments
        )

        ret.sort(key=lambda comment: comment.comment_date, reverse=True)

        return ret
