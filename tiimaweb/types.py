from datetime import datetime, timedelta
from typing import NamedTuple

import requests
from bs4 import BeautifulSoup

from .exceptions import UnexpectedResponse

HtmlResponseBase = NamedTuple('HtmlResponseBase', [
    ('response', requests.Response),
    ('soup', BeautifulSoup),
])


class HtmlResponse(HtmlResponseBase):
    @classmethod
    def from_response(
            cls,
            response,  # type: requests.Response
    ):  # type: (...) -> 'HtmlResponse'
        soup = getattr(response, 'soup', None)
        if not soup:
            raise UnexpectedResponse('Got non-HTML response')
        return cls(response=response, soup=soup)


TimeBlockBase = NamedTuple('TimeBlockBase', [
    ('id', str),
    ('start_time', datetime),
    ('end_time', datetime),
    ('reason_code', str),
    ('reason_text', str),
    ('status', str),
    ('description', str),
])


class TimeBlock(TimeBlockBase):
    def __str__(self):  # type: (...) -> str
        return (
            f'{self.start_time} -- {self.end_time} {self.reason_code} '
            f'{self.description}').strip()

    @property
    def duration(self):  # type: (...) -> timedelta
        return self.end_time - self.start_time
