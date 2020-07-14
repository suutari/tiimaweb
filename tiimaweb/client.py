# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
from copy import copy
from datetime import date, datetime, time, timedelta
from typing import TYPE_CHECKING, Dict, List, Optional, Set, Text, Type

import pytz
from bs4 import BeautifulSoup
from bs4.element import Tag
from mechanicalsoup import StatefulBrowser
from mechanicalsoup.utils import LinkNotFoundError

from .exceptions import Error, LoginFailed, ParseError, UnexpectedResponse
from .types import DaySummary, HtmlResponse, TimeBlock

if TYPE_CHECKING:
    from types import TracebackType


EPOCH = datetime(1970, 1, 1, 0, 0, tzinfo=pytz.UTC)


class Client:
    def __init__(
            self,
            url='https://www.tiima.com',  # type: Text
            tz=str('Europe/Helsinki'),  # type: str
    ):  # type: (...) -> None
        self.url = url
        self.tz = pytz.timezone(tz)

    def login(
            self,
            username,  # type: Text
            password,  # type: Text
            customer,  # type: Text
    ):  # type: (...) -> Connection
        browser = StatefulBrowser()
        response = browser.open(self.url)
        response.raise_for_status()
        assert 'login' in (browser.get_url() or '').lower()

        browser.select_form('#loginForm')
        browser['UserName'] = username
        browser['Password'] = password
        browser['CustomerIdentifier'] = customer
        browser['Language'] = 'ENG'
        response = browser.submit_selected()
        response.raise_for_status()

        html_response = HtmlResponse.from_response(response)
        if html_response.soup.find(id='loginForm'):
            # Still on the login form, so login must have failed
            raise LoginFailed('Login failed')

        return Connection(browser, self)


class Connection:
    def __init__(
            self,
            browser,  # type: StatefulBrowser
            client,  # type: Client
    ):  # type: (...) -> None
        self._browser = browser  # type: Optional[StatefulBrowser]
        self.client = client

        self._last_response = None  # type: Optional[HtmlResponse]

        tiima_form = browser.select_form('[name="tiima"]')
        self._tiima_form = type(tiima_form)(copy(tiima_form.form))
        self._tiima_form_page_url = browser.get_url()

        soup = self.browser.get_current_page()
        if not soup:
            raise UnexpectedResponse('Error: Got Non-HTML front page')

        self._time_blocks = []  # type: List[TimeBlock]
        self._current_date = date(1970, 1, 1)  # type: date
        self._time_blocks = self._parse_and_store_time_blocks(soup)

    def __enter__(self):  # type: (...) -> Connection
        return self

    def __exit__(
            self,
            exc_type,  # type: Optional[Type[BaseException]]
            exc_value,  # type: Optional[Exception]
            traceback,  # type: Optional[TracebackType]
    ):  # type: (...) -> None
        self.logout()

    @property
    def browser(self):  # type: (...) -> StatefulBrowser
        if not self._browser:
            raise ValueError('Connection already logged out')
        return self._browser

    def logout(self):  # type: (...) -> None
        if self._browser:
            response = self.browser.follow_link(id='Logout')
            response.raise_for_status()
            self._browser = None

    def get_totals_list(
            self,
            start_date,  # type: date
    ):  # type: (...) -> List[DaySummary]
        """
        Get list of totals for a bunch of dates.

        Each item in the returned list presents total work time
        information of a single day as a DaySummary object.  The listing
        starts from the first day of month of the given start date and
        containts entries for three months in total.
        """
        month_start = start_date.replace(day=1)
        response = self.post_action('action_previous_month', {
            'AjaxId': 'CalendarStrip',
            'CalendarStripStartDate': self._date_to_timestamp(month_start),
        })
        return self._parse_calendar_days(response.soup)

    def get_time_blocks_of_date(
            self,
            day,  # type: date
    ):  # type: (...) -> List[TimeBlock]
        return self._select_date(day)

    def delete_time_block(
            self,
            block,  # type: TimeBlock
    ):  # type: (...) -> List[TimeBlock]
        if not any(x.id == block.id for x in self._time_blocks):
            self._select_date(block.start_time.date())

        if not any(x.id == block.id for x in self._time_blocks):
            raise ValueError('Time block not found')

        response = self.post_action('action_delete_selected', {
            'SelectedRowStampId': block.id,
        })
        day = block.start_time.date()
        return self._parse_blocks_or_select_date(day, response.soup)

    def add_time_block(
            self,
            start,  # type: datetime
            end,  # type: datetime
            description='',  # type: Text
    ):  # type: (...) -> List[TimeBlock]
        start = self._ensure_tz(start)
        end = self._ensure_tz(end)
        if start.date() != self._current_date:
            self._select_date(start.date())
        old_set = set(self._time_blocks)
        temp_lunch = self._add_temporary_lunch_if_needed(start, end)
        result = self._add_time_block(start, end, description)
        if temp_lunch:
            result = self.delete_time_block(temp_lunch)
        self._check_timeblock_add(old_set, set(result), start, end)
        return result

    def _ensure_tz(self, dt):  # type: (datetime) -> datetime
        if not dt.tzinfo:
            return self.client.tz.localize(dt)
        return dt.astimezone(self.client.tz)

    def _select_date(self, day):  # type: (date) -> List[TimeBlock]
        response = self.post_action('action_select_date', {
            'AjaxId': 'CalendarStrip',
            'SelectedStampingDate': self._date_to_timestamp(day),
        })
        result = self._parse_and_store_time_blocks(response.soup)
        assert self._current_date == day
        return result

    def _date_to_timestamp(self, day):  # type: (date) -> Text
        dt = self._ensure_tz(datetime.combine(day, time(0, 0)))
        unix_time = (dt - EPOCH).total_seconds()
        date_value = '{}'.format(int(unix_time * 1000))
        return date_value

    def _add_temporary_lunch_if_needed(
            self,
            new_start,  # type: datetime
            new_end,  # type: datetime
            max_lunchless_day_len=timedelta(hours=6),  # type: timedelta
            lunch_len=timedelta(minutes=30),  # type: timedelta
    ):  # type: (...) -> Optional[TimeBlock]
        prev_total = (
            sum((x.duration for x in self._time_blocks), timedelta(0)))
        new_total = prev_total + (new_end - new_start)
        if new_total < max_lunchless_day_len:
            return None

        starts = [x.start_time for x in self._time_blocks] + [new_start]
        ends = [x.end_time for x in self._time_blocks] + [new_end]
        first_start = min(starts)
        last_end = max(ends)

        before_first_start = first_start - lunch_len
        after_last_end = last_end + lunch_len
        if before_first_start.date() == first_start.date():
            start = before_first_start
            end = first_start
        elif after_last_end.date() == last_end.date():
            start = last_end
            end = after_last_end
        else:
            raise Error('Cannot find space for temporary lunch break')

        time_blocks = self._add_time_block(start, end, type='lunch')
        for tb in time_blocks:
            if tb.start_time == start and tb.end_time == end:
                return tb
        raise Error('Temporary lunch break creation failed')

    def _add_time_block(
            self,
            start,  # type: datetime
            end,  # type: datetime
            description='',  # type: Text
            type='normal',  # type: Text
    ):  # type: (...) -> List[TimeBlock]
        reason_code = {'normal': '1', 'lunch': '13'}[type]
        self.post_action('action_edit_open', {'EditPanelActive': '1'})
        response = self.post_action('action_save', {
            'EditPanelActive': '1',
            'EditStartTime': '{:%H:%M}'.format(start),
            'EditStartDate': '{:%d.%m.%Y}'.format(start),
            'EditEndTime': '{:%H:%M}'.format(end),
            'EditEndDate': '{:%d.%m.%Y}'.format(end),
            'EditDescription': description,
            'EditStampType': '0',
            'EditReasonCodeId': reason_code,
        })
        return self._parse_blocks_or_select_date(start.date(), response.soup)

    def _check_timeblock_add(
            self,
            old_set,  # type: Set[TimeBlock]
            new_set,  # type: Set[TimeBlock]
            new_block_start,  # type: datetime
            new_block_end,  # type: datetime
    ):  # type: (...) -> None
        added_blocks = new_set - old_set
        removed_blocks = old_set - new_set
        if len(added_blocks) != 1 or removed_blocks:
            raise Error(
                'Time block adding failed: added={}, removed={}'.format(
                    added_blocks, removed_blocks))
        tb = list(added_blocks)[0]
        if tb.start_time != new_block_start or tb.end_time != new_block_end:
            raise Error(
                'Time block adding failed: expected={}--{}, got={}'.format(
                    new_block_start, new_block_end, tb))

    def _parse_blocks_or_select_date(
            self,
            day,  # type: date
            soup,  # type: BeautifulSoup
    ):  # type: (...) -> List[TimeBlock]
        soup_date = self._parse_selected_date(soup)
        if soup_date == day:
            return self._parse_and_store_time_blocks(soup)
        else:
            return self._select_date(day)

    def post_action(
            self,
            action,  # type: Text
            params,  # type: Dict[Text, Text]
    ):  # type: (...) -> HtmlResponse
        """
        Post an AJAX action through the tiima form.

        The tiima form already has quite much prefilled data and
        additional field data can be passed with the params argument.

        The fields in the tiima form are:

            <input name="FieldAction" type="hidden" value=""/>
            <input name="FieldShowSubMenu" type="hidden" value="true"/>
            <input name="FieldMenuId1" type="hidden" value="TOP_WORKHOUR"/>
            <input name="FieldMenuId1" type="hidden" value="WORKINGHOURSTAMP"/>
            <input name="UserLanguage" type="hidden" value="1"/>
            <input name="companyIdentifierTiima" type="hidden" value="{CID}"/>
            <input name="PageId" type="hidden" value="1"/>
            <input name="aft(dunno?)???" type="hidden" value="???"/>
            <select name="StampReasonCodeId">
                <option value="1">Normaali työaika (NTYO)</option>
                <option value="31">Oma asia (OA)</option>
                <option value="39">Ylityö (YT)</option>
                <option value="30">Koulutus (osapäivä) (KO)</option>
                <option value="24">Lapsi sairas (osapäivä) (LSA)</option>
                <option value="29">Sairausloma (osapäivä) (SA)</option>
                <option value="28">Työmatka (osapäivä) (TM)</option>
                <option value="13">Lounas (LOU)</option>
            </select>
            <input name="StampDescription" type="text" value=""/>
            <input name="CalendarStripStartDate" type="hidden"
                value="1580508000000"/>
            <input name="EmployeeId" type="hidden" value="{EID}"/>
            <input name="SelectedStampingDate" type="hidden"
                value="1583272800000"/>
            <input name="EditStampId" type="hidden" value="0"/>
            <input name="EditPanelActive" type="hidden" value="0"/>
            <input name="ActiveList" type="hidden" value=""/>
            <input name="lmi" type="hidden" value=""/>
            <input name="DebugDeleteRawStampId" type="hidden" value=""/>
        """
        form = type(self._tiima_form)(copy(self._tiima_form.form))
        form.new_control('text', 'AjaxRequest', '1')
        form['FieldAction'] = action
        form['UserLanguage'] = '3'  # 1 = Finnish, 2 = Swedish, 3 = English
        for (name, value) in params.items():
            try:
                form.set(name, value, force=True)
            except LinkNotFoundError:
                form.new_control('text', name, value=value)
        response = self.browser.submit(form, url=self._tiima_form_page_url)
        response.raise_for_status()
        self._last_response = result = HtmlResponse.from_response(response)
        return result

    def _parse_calendar_days(
            self,
            soup,  # type: BeautifulSoup
    ):  # type: (...) -> List[DaySummary]
        calendar_strip = self._find_inner_table(soup, 'CalendarStrip')
        tds = calendar_strip.find_all('td', attrs={'onclick': True})
        return sorted(self._parse_calendar_day(td) for td in tds)

    def _parse_calendar_day(
            self,
            td,  # type: Tag
    ):  # type: (...) -> DaySummary
        onclick = td.get('onclick') or ''
        m = re.match(r".*SelectedStampingDate.value='(\d+)'", onclick)
        if not m:
            raise ParseError('Cannot parse date from calendar day cell')
        day = self._parse_timestamp(m.group(1)).date()
        description = (td.get('title') or '').strip()
        tds = td.find_all('td')
        day_text = tds[1].text
        if not day_text or not day_text.isdigit() or int(day_text) != day.day:
            raise ParseError('Cannot parse day number of calendar cell')
        duration_str = (tds[2].text or '').strip()
        if duration_str:
            (h_str, m_str) = duration_str.split(':')
            duration = timedelta(hours=int(h_str), minutes=int(m_str))
        else:
            duration = timedelta(0)
        return DaySummary(day, duration, description)

    def _parse_and_store_time_blocks(
            self,
            soup,  # type: BeautifulSoup
    ):  # type: (...) -> List[TimeBlock]
        day = self._parse_selected_date(soup)
        self._current_date = day.date()
        self._time_blocks = result = self._parse_time_blocks(soup, day)
        return result

    def _parse_selected_date(
            self,
            soup,  # type: BeautifulSoup
    ):  # type: (...) -> datetime
        # Parse the selected date
        date_input = soup.find('input', attrs={'name': 'SelectedStampingDate'})
        if not date_input:
            raise ParseError('Cannot find selected date input element')
        return self._parse_timestamp(date_input.get('value'))

    def _parse_timestamp(self, ts):  # type: (Optional[Text]) -> datetime
        if not ts or not ts.isdigit():
            raise ParseError('Cannot parse timestamp: {}'.format(ts))
        utc_datetime = EPOCH + timedelta(seconds=(int(ts) / 1000.0))
        return utc_datetime.astimezone(self.client.tz)

    def _parse_time_blocks(
            self,
            soup,  # type: BeautifulSoup
            day,  # type: datetime
    ):  # type: (...) -> List[TimeBlock]
        time_block_table = self._find_inner_table(soup, 'PanelTableList')
        items = self._parse_tds_of_time_block_table(time_block_table)
        result = [_parse_time_block_item(item, day) for item in items]
        return result

    def _find_inner_table(
            self,
            soup,  # type: BeautifulSoup
            id,  # type: Text
    ):  # type: (...) -> Tag
        element = soup.find(id=id)
        if not element:
            raise ParseError('Cannot find element with id {!r}'.format(id))
        table = element.find('table')
        if not table:
            raise ParseError('Cannot find table in {}'.format(id))
        inner_table = table.find('table')
        if not inner_table:
            raise ParseError('Cannot find inner table within {}'.format(id))
        return inner_table

    def _parse_tds_of_time_block_table(
            self,
            time_block_table,  # type: Tag
    ):  # type: (...) -> List[Dict[Text, Tag]]
        # Parse the time block table
        tr_elements = time_block_table.find_all('tr', recursive=False)
        rows = [
            [td for td in tr.find_all('td', recursive=False)]
            for tr in tr_elements
        ]
        field_texts = (td.text.strip() for td in rows[0])
        header = [TIME_BLOCK_TABLE_FIELD_NAMES[x] for x in field_texts]
        items = [dict(zip(header, row)) for row in rows[1:]]
        return items


TIME_BLOCK_TABLE_FIELD_NAMES = {
    '': 'id',

    'Kello': 'time_range',
    'Syykoodi': 'reason',
    'Tila': 'status',
    'Selite': 'description',

    'Klockan': 'time_range',
    'Orsakskod': 'reason',
    'Status': 'status',
    'Förklaring': 'description',

    'Clock': 'time_range',
    'Reason code': 'reason',
    'Status': 'status',
    'Description': 'description',
}


def _parse_time_block_item(
        item,  # type: Dict[Text, Tag]
        day,  # type: datetime
):  # type: (...) -> TimeBlock
    def get_text(td):  # type: (Tag) -> Text
        text = td.text.strip() or td.get('title')
        return (text or '').replace('\xa0', '')

    data = {key: get_text(td) for (key, td) in item.items() if key != 'id'}

    id_input = item['id'].find(id='SelectedRowStampId')
    id_value = id_input.get('value', '') if id_input else ''
    if not id_value:
        raise ParseError('Cannot find id for a time block row')

    reason = data.pop('reason')
    (text, code) = reason.rstrip(')').rsplit('(', 1)

    times_str = data.pop('time_range')
    m = re.match((
        r'(\((?P<start_date>[0-9.]+)\) )?'
        r'(?P<start>[0-9:]+)-(?P<end>[0-9:]+)'
        r'( \((?P<end_date>[0-9.]+)\))?'), times_str)
    if not m:
        raise ParseError('Cannot parse times: {}'.format(times_str))

    start = datetime.strptime(m.group(str('start')), '%H:%M').time()
    end = datetime.strptime(m.group(str('end')), '%H:%M').time()

    start_time = day + timedelta(hours=start.hour, minutes=start.minute)
    end_time = day + timedelta(hours=end.hour, minutes=end.minute)

    if m.group(str('start_date')):
        sd = datetime.strptime(m.group(str('start_date')), '%d.%m.').date()
        year_delta = 1 if (sd.month == 12 and start_time.month == 1) else 0
        start_time = start_time.replace(
            year=(start_time.year - year_delta),
            month=sd.month,
            day=sd.day,
        )

    if m.group(str('end_date')):
        ed = datetime.strptime(m.group(str('end_date')), '%d.%m.').date()
        year_delta = 1 if (ed.month == 1 and end_time.month == 12) else 0
        end_time = end_time.replace(
            year=(end_time.year + year_delta),
            month=ed.month,
            day=ed.day,
        )

    return TimeBlock(
        id=Text(id_value),
        start_time=start_time,
        end_time=end_time,
        reason_code=code,
        reason_text=text,
        **data
    )
