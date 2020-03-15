from __future__ import unicode_literals

from datetime import date, datetime, timedelta
from typing import NamedTuple, Text

import requests
from bs4 import BeautifulSoup
from six import python_2_unicode_compatible

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
    ('id', Text),
    ('start_time', datetime),
    ('end_time', datetime),
    ('reason_code', Text),
    ('reason_text', Text),
    ('status', Text),
    ('description', Text),
])


@python_2_unicode_compatible
class TimeBlock(TimeBlockBase):
    def __str__(self):  # type: ignore
        return (
            '{self.start_time} -- {self.end_time} {self.reason_code} '
            '{self.description}').format(self=self).strip()

    @property
    def duration(self):  # type: (...) -> timedelta
        return self.end_time - self.start_time


DaySummaryBase = NamedTuple('DaySummaryBase', [
    ('day', date),
    ('duration', timedelta),
    ('description', Text),
])


@python_2_unicode_compatible
class DaySummary(DaySummaryBase):
    def __str__(self):  # type: ignore
        return (
            '{self.day} {self.duration} '
            '{self.description}').format(self=self).strip()
