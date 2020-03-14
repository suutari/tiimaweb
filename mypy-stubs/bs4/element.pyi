from typing import (
    Iterable,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Text,
    TypeVar,
    Union,
    overload,
)

_Str = Union[str, Text]
_T = TypeVar('_T')
_MatchAgainst = Union[_Str, bool]  # incomplete (e.g. Callable, Iterable, ...)


class SoupStrainer:
    ...


class ResultSet(List[_T]):
    def __init__(
            self,
            source: SoupStrainer,
            result: Iterable[_T] = ...,
    ) -> None: ...


class PageElement:
    ...


class Tag(PageElement):
    @overload
    def get(self, key: _Str) -> Optional[_Str]: ...

    @overload
    def get(self, key: _Str, default: _T) -> Union[_Str, _T]: ...

    def get_text(
            self,
            separator: _Str = ...,
            strip: bool = ...,
            types: Optional[Sequence[type]] = ...
    ) -> _Str: ...

    @property
    def text(self) -> _Str: ...

    def find(
            self,
            name: Optional[_Str] = ...,
            attrs: Mapping[_Str, _MatchAgainst] = ...,
            recursive: bool = ...,
            text: Optional[_Str] = ...,
            **kwargs: _MatchAgainst,
    ) -> Optional['Tag']: ...

    def find_all(
            self,
            name: _Str = ...,
            attrs: Mapping[_Str, _MatchAgainst] = ...,
            recursive: bool = ...,
            text: Optional[_Str] = ...,
            limit: Optional[int] = ...,
            **kwargs: _MatchAgainst,
    ) -> ResultSet['Tag']: ...

    def select_one(
            self,
            selector: _Str,
            # namespaces=None, **kwargs,
    ) -> Optional['Tag']: ...

    def replace_with(self, replace_with: Union[_Str, 'Tag']) -> 'Tag': ...

    def __iter__(self) -> Iterator['Tag']: ...
