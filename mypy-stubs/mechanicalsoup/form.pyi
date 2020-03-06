import bs4.element


class Form:
    form: bs4.element.Tag

    def __init__(self, form: bs4.element.Tag) -> None: ...

    def new_control(
            self,
            type: str,
            name: str,
            value: str,
            **kwargs: str,
    ) -> bs4.BeautifulSoup: ...

    def __setitem__(self, name: str, value: str) -> None: ...

    def set(self, name: str, value: str, force: bool = ...) -> None: ...
