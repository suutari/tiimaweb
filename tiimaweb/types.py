from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import NamedTuple

import requests
from bs4 import BeautifulSoup

from .exceptions import UnexpectedResponse


class HtmlResponse(NamedTuple):
    response: requests.Response
    soup: BeautifulSoup

    @classmethod
    def from_response(cls, response: requests.Response) -> 'HtmlResponse':
        soup = getattr(response, 'soup', None)
        if not soup:
            raise UnexpectedResponse('Got non-HTML response')
        return cls(response=response, soup=soup)


@dataclass
class TimeBlock:
    id: str
    start_time: datetime
    end_time: datetime
    reason_code: str
    reason_text: str
    status: str
    description: str

    def __str__(self) -> str:
        return (
            f'{self.start_time} -- {self.end_time} {self.reason_code} '
            f'{self.description}').strip()

    @property
    def duration(self) -> timedelta:
        return self.end_time - self.start_time
