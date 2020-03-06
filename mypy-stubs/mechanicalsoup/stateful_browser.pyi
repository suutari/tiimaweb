from typing import Any, Dict, List, Optional, Union

import bs4
import bs4.element

from .browser import Browser, _Response
from .form import Form


class StatefulBrowser(Browser):
    def absolute_url(self, url: str) -> str: ...

    def open(
            self,
            url: str,
            # *args: ...,
            # **kwargs: ...,
    ) -> _Response: ...

    def open_relative(
            self,
            url: str,
            # *args, **kwargs,
    ) -> _Response: ...

    def get_url(self) -> Optional[str]: ...

    def select_form(
            self,
            selector: str = ...,
            nr: int = ...,
    ) -> Form: ...

    def __setitem__(self, name: str, value: str) -> None: ...

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
            url_regex: Optional[str] = ...,
            link_text: Optional[str] = ...,
            name: Optional[str] = ...,
            attrs: Dict[str, str] = ...,
            recursive: bool = ...,
            text: Optional[str] = ...,
            limit: Optional[int] = ...,
            **kwargs: str,
    ) -> List[bs4.element.Tag]: ...

    def find_link(
            self,
            url_regex: Optional[str] = ...,
            link_text: Optional[str] = ...,
            name: Optional[str] = ...,
            attrs: Dict[str, str] = ...,
            recursive: bool = ...,
            text: Optional[str] = ...,
            limit: Optional[int] = ...,
            **kwargs: str,
    ) -> bs4.element.Tag: ...

    def follow_link(
            self,
            link: Optional[Union[bs4.element.Tag, str]] = ...,
            url_regex: Optional[str] = ...,
            link_text: Optional[str] = ...,
            name: Optional[str] = ...,
            attrs: Dict[str, str] = ...,
            recursive: bool = ...,
            text: Optional[str] = ...,
            limit: Optional[int] = ...,
            **kwargs: str,
    ) -> _Response: ...
