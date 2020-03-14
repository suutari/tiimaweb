from typing import Any, Mapping, Optional, Text, Union

import bs4.element
import requests

from .form import Form

_Str = Union[str, Text]


class _Response(requests.Response):
    @property
    def soup(self) -> Optional[bs4.BeautifulSoup]: ...


class Browser:
    def __init__(
            self,
            # TODO: Replace Any with Session
            session: Optional[Any] = ...,
            soup_config: Optional[Mapping[_Str, Any]] = ...,
            # TODO: Replace Any with BaseAdapter below
            requests_adapters: Optional[Mapping[_Str, Any]] = ...,
            raise_on_404: bool = ...,
            user_agent: Optional[_Str] = ...,
    ) -> None: ...

    def request(
            self,
            method: _Str,
            url: _Str,
            headers: Mapping[_Str, _Str] = ...,
            # *args, **kwargs,
    ) -> _Response: ...

    def get(
            self,
            url: _Str,
            headers: Mapping[_Str, _Str] = ...,
            # *args, **kwargs,
    ) -> _Response: ...

    def post(
            self,
            url: _Str,
            headers: Mapping[_Str, _Str] = ...,
            # *args, **kwargs,
    ) -> _Response: ...

    def submit(
            self,
            form: Union[Form, bs4.element.Tag],
            url: Optional[_Str] = ...,
            **kwargs: Any,
    ) -> _Response: ...
