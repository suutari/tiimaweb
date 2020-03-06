# -*- coding: utf-8 -*-

from copy import copy
from datetime import date, datetime, time, timedelta, timezone
from types import TracebackType
from typing import Dict, List, Optional, Type

import mechanicalsoup
import pytz
from bs4 import BeautifulSoup
from bs4.element import Tag
from mechanicalsoup.utils import LinkNotFoundError

from .exceptions import Error, LoginFailed, ParseError, UnexpectedResponse
from .types import HtmlResponse, TimeBlock

EPOCH = datetime(1970, 1, 1, 0, 0, tzinfo=timezone.utc)


class Client:
    def __init__(
            self,
            *,
            url: str = 'https://www.tiima.com',
            tz: str = 'Europe/Helsinki',
    ) -> None:
        self.url = url
        self.tz = pytz.timezone(tz)

    def login(
            self,
            username: str,
            password: str,
            customer: str,
    ) -> 'Connection':
        browser = mechanicalsoup.StatefulBrowser()
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
            browser: mechanicalsoup.StatefulBrowser,
            client: Client,
    ) -> None:
        self._browser: Optional[mechanicalsoup.StatefulBrowser] = browser
        self.client = client

        self._last_response: Optional[HtmlResponse] = None

        tiima_form = browser.select_form('[name="tiima"]')
        self._tiima_form = type(tiima_form)(copy(tiima_form.form))
        self._tiima_form_page_url = browser.get_url()

        soup = self.browser.get_current_page()
        if not soup:
            raise UnexpectedResponse('Error: Got Non-HTML front page')

        self._time_blocks: List[TimeBlock]
        self._current_date: date
        self._time_blocks = self._parse_and_store_time_blocks(soup)

    def __enter__(self) -> 'Connection':
        return self

    def __exit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc_value: Optional[Exception],
            traceback: Optional[TracebackType],
    ) -> None:
        self.logout()

    @property
    def browser(self) -> mechanicalsoup.StatefulBrowser:
        if not self._browser:
            raise ValueError('Connection already logged out')
        return self._browser

    def logout(self) -> None:
        if self._browser:
            response = self.browser.follow_link(id='Logout')
            response.raise_for_status()
            self._browser = None

    def get_time_blocks_of_date(self, day: date) -> List[TimeBlock]:
        return self._select_date(day)

    def delete_time_block(self, block: TimeBlock) -> List[TimeBlock]:
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
            start: datetime,
            end: datetime,
            description: str = '',
    ) -> List[TimeBlock]:
        start = self._ensure_tz(start)
        end = self._ensure_tz(end)
        if start.date() != self._current_date:
            self._select_date(start.date())
        temp_lunch = self._add_temporary_lunch_if_needed(start, end)
        result = self._add_time_block(start, end, description)
        if temp_lunch:
            result = self.delete_time_block(temp_lunch)
        return result

    def _ensure_tz(self, dt: datetime) -> datetime:
        if not dt.tzinfo:
            return self.client.tz.localize(dt)
        return dt.astimezone(self.client.tz)

    def _select_date(self, day: date) -> List[TimeBlock]:
        dt = self.client.tz.localize(datetime.combine(day, time(0, 0)))
        unix_time = (dt - EPOCH).total_seconds()
        date_value = f'{int(unix_time * 1000)}'
        response = self.post_action('action_select_date', {
            'AjaxId': 'CalendarStrip',
            'SelectedStampingDate': date_value,
        })
        result = self._parse_and_store_time_blocks(response.soup)
        assert self._current_date == day
        return result

    def _add_temporary_lunch_if_needed(
            self,
            new_start: datetime,
            new_end: datetime,
            max_block_len: timedelta = timedelta(hours=6),
            lunch_len: timedelta = timedelta(minutes=30),
    ) -> Optional[TimeBlock]:
        if new_end - new_start < max_block_len:
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
            start: datetime,
            end: datetime,
            description: str = '',
            type: str = 'normal',
    ) -> List[TimeBlock]:
        reason_code = {'normal': '1', 'lunch': '13'}[type]
        self.post_action('action_edit_open', {'EditPanelActive': '1'})
        response = self.post_action('action_save', {
            'EditPanelActive': '1',
            'EditStartTime': f'{start:%H:%M}',
            'EditStartDate': f'{start:%d.%m.%Y}',
            'EditEndTime': f'{end:%H:%M}',
            'EditEndDate': f'{end:%d.%m.%Y}',
            'EditDescription': description,
            'EditStampType': '0',
            'EditReasonCodeId': reason_code,
        })
        return self._parse_blocks_or_select_date(start.date(), response.soup)

    def _parse_blocks_or_select_date(
            self,
            day: date,
            soup: BeautifulSoup,
    ) -> List[TimeBlock]:
        soup_date = self._parse_selected_date(soup)
        if soup_date == day:
            return self._parse_and_store_time_blocks(soup)
        else:
            return self._select_date(day)

    def post_action(self, action: str, params: Dict[str, str]) -> HtmlResponse:
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

    def _parse_and_store_time_blocks(
            self,
            soup: BeautifulSoup,
    ) -> List[TimeBlock]:
        day = self._parse_selected_date(soup)
        self._current_date = day.date()
        self._time_blocks = result = self._parse_time_blocks(soup, day)
        return result

    def _parse_selected_date(self, soup: BeautifulSoup) -> datetime:
        # Parse the selected date
        date_input = soup.find('input', attrs={'name': 'SelectedStampingDate'})
        if not date_input:
            raise ParseError('Cannot find selected date input element')
        date_input_value = date_input.get('value')
        if not date_input_value or not date_input_value.isdigit():
            raise ParseError(f'Selected date is invalid: {date_input_value}')
        day_timestamp = int(date_input_value) / 1000.0
        day_utc_datetime = (EPOCH + timedelta(seconds=day_timestamp))
        day = day_utc_datetime.astimezone(self.client.tz)
        return day

    def _parse_time_blocks(
            self,
            soup: BeautifulSoup,
            day: datetime,
    ) -> List[TimeBlock]:
        time_block_table = self._find_time_block_table(soup)
        items = self._parse_tds_of_time_block_table(time_block_table)
        result = [_parse_time_block_item(item, day) for item in items]
        return result

    def _find_time_block_table(self, soup: BeautifulSoup) -> Tag:
        # Find the time block table
        table_list = soup.find(id='PanelTableList')
        if not table_list:
            raise ParseError('Cannot find element with id "PanelTableList"')
        inner_table = table_list.find('table')
        if not inner_table:
            raise ParseError('Cannot find table in PanelTableList')
        time_block_table = inner_table.find('table')
        if not time_block_table:
            raise ParseError('Cannot find time block table')
        return time_block_table

    def _parse_tds_of_time_block_table(
            self,
            time_block_table: Tag,
    ) -> List[Dict[str, Tag]]:
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


def _parse_time_block_item(item: Dict[str, Tag], day: datetime) -> TimeBlock:
    def get_text(td: Tag) -> str:
        text = td.text.strip() or td.get('title')
        return (text or '').replace('\xa0', '')

    data = {key: get_text(td) for (key, td) in item.items() if key != 'id'}

    id_input = item['id'].find(id='SelectedRowStampId')
    data['id'] = id_input.get('value', '') if id_input else ''
    if not data['id']:
        raise ParseError('Cannot find id for a time block row')

    reason = data.pop('reason')
    (text, code) = reason.rstrip(')').split('(')

    times = data.pop('time_range').split('-')
    start = time.fromisoformat(times[0])
    end = time.fromisoformat(times[1])

    return TimeBlock(
        start_time=day + timedelta(hours=start.hour, minutes=start.minute),
        end_time=day + timedelta(hours=end.hour, minutes=end.minute),
        reason_code=code,
        reason_text=text,
        **data,
    )
