from typing import Text, Union

import bs4.element

_Str = Union[str, Text]


class Form:
    form: bs4.element.Tag

    def __init__(self, form: bs4.element.Tag) -> None: ...

    def new_control(
            self,
            type: _Str,
            name: _Str,
            value: _Str,
            **kwargs: _Str,
    ) -> bs4.BeautifulSoup: ...

    def __setitem__(self, name: _Str, value: _Str) -> None: ...

    def set(self, name: _Str, value: _Str, force: bool = ...) -> None: ...
