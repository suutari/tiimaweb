from typing import Any, Dict, List, Optional, Text, Union

import bs4
import bs4.element

from .browser import Browser, _Response
from .form import Form

_Str = Union[str, Text]


class StatefulBrowser(Browser):
    def absolute_url(self, url: _Str) -> _Str: ...

    def open(
            self,
            url: _Str,
            # *args: ...,
            # **kwargs: ...,
    ) -> _Response: ...

    def open_relative(
            self,
            url: _Str,
            # *args, **kwargs,
    ) -> _Response: ...

    def get_url(self) -> Optional[_Str]: ...

    def select_form(
            self,
            selector: _Str = ...,
            nr: int = ...,
    ) -> Form: ...

    def __setitem__(self, name: _Str, value: _Str) -> None: ...

    def submit_selected(
            self,
            # btnName=None,
            # update_state=True,
            # *args,
            # **kwargs,
    ) -> _Response: ...

    def get_current_page(self) -> Optional[bs4.BeautifulSoup]: ...

    def links(
            self,
            url_regex: Optional[_Str] = ...,
            link_text: Optional[_Str] = ...,
            name: Optional[_Str] = ...,
            attrs: Dict[_Str, _Str] = ...,
            recursive: bool = ...,
            text: Optional[_Str] = ...,
            limit: Optional[int] = ...,
            **kwargs: _Str,
    ) -> List[bs4.element.Tag]: ...

    def find_link(
            self,
            url_regex: Optional[_Str] = ...,
            link_text: Optional[_Str] = ...,
            name: Optional[_Str] = ...,
            attrs: Dict[_Str, _Str] = ...,
            recursive: bool = ...,
            text: Optional[_Str] = ...,
            limit: Optional[int] = ...,
            **kwargs: _Str,
    ) -> bs4.element.Tag: ...

    def follow_link(
            self,
            link: Optional[Union[bs4.element.Tag, _Str]] = ...,
            url_regex: Optional[_Str] = ...,
            link_text: Optional[_Str] = ...,
            name: Optional[_Str] = ...,
            attrs: Dict[_Str, _Str] = ...,
            recursive: bool = ...,
            text: Optional[_Str] = ...,
            limit: Optional[int] = ...,
            **kwargs: _Str,
    ) -> _Response: ...
