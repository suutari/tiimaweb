from typing import Any, Mapping, Optional, Union

import bs4.element
import requests

from .form import Form


class _Response(requests.Response):
    @property
    def soup(self) -> Optional[bs4.BeautifulSoup]: ...


class Browser:
    def __init__(
            self,
            # TODO: Replace Any with Session
            session: Optional[Any] = ...,
            soup_config: Optional[Mapping[str, Any]] = ...,
            # TODO: Replace Any with BaseAdapter below
            requests_adapters: Optional[Mapping[str, Any]] = ...,
            raise_on_404: bool = ...,
            user_agent: Optional[str] = ...,
    ) -> None: ...

    def request(
            self,
            method: str,
            url: str,
            headers: Mapping[str, str] = ...,
            # *args, **kwargs,
    ) -> _Response: ...

    def get(
            self,
            url: str,
            headers: Mapping[str, str] = ...,
            # *args, **kwargs,
    ) -> _Response: ...

    def post(
            self,
            url: str,
            headers: Mapping[str, str] = ...,
            # *args, **kwargs,
    ) -> _Response: ...

    def submit(
            self,
            form: Union[Form, bs4.element.Tag],
            url: Optional[str] = ...,
            **kwargs: Any,
    ) -> _Response: ...
