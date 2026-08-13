# Builtins stub used in tuple-related test cases.

import _typeshed
from typing import Iterable, Iterator, TypeVar, Generic, Sequence, Optional, overload, Tuple, Type, MutableSet, AbstractSet, MutableMapping, SupportsKeysAndGetItem, Union, Any
from typing_extensions import Self, Literal, TypeAlias

_T = TypeVar("_T")
_KT = TypeVar("_KT")  # Key type.
_VT = TypeVar("_VT")  # Value type.
_Tco = TypeVar('_Tco', covariant=True)

_PositiveInteger: TypeAlias = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25]
_NegativeInteger: TypeAlias = Literal[-1, -2, -3, -4, -5, -6, -7, -8, -9, -10, -11, -12, -13, -14, -15, -16, -17, -18, -19, -20]

class object:
    def __init__(self) -> None: pass

class type:
    def __init__(self, *a: object) -> None: pass
    def __call__(self, *a: object) -> object: pass
class tuple(Sequence[_Tco], Generic[_Tco]):
    def __new__(cls: Type[_T], iterable: Iterable[_Tco] = ...) -> _T: ...
    def __iter__(self) -> Iterator[_Tco]: pass
    def __contains__(self, item: object) -> bool: pass
    @overload
    def __getitem__(self, x: int) -> _Tco: pass
    @overload
    def __getitem__(self, x: slice) -> Tuple[_Tco, ...]: ...
    def __mul__(self, n: int) -> Tuple[_Tco, ...]: pass
    def __rmul__(self, n: int) -> Tuple[_Tco, ...]: pass
    def __add__(self, x: Tuple[_Tco, ...]) -> Tuple[_Tco, ...]: pass
    def __len__(self): pass
    def count(self, obj: object) -> int: pass
class function:
    __name__: str
class ellipsis: pass
class classmethod: pass

# We need int and slice for indexing tuples.
class int:
    def __add__(self, value: int, /) -> int: ...
    def __sub__(self, value: int, /) -> int: ...
    def __mul__(self, value: int, /) -> int: ...
    def __floordiv__(self, value: int, /) -> int: ...
    def __truediv__(self, value: int, /) -> float: ...
    def __mod__(self, value: int, /) -> int: ...
    def __divmod__(self, value: int, /) -> tuple[int, int]: ...
    def __radd__(self, value: int, /) -> int: ...
    def __rsub__(self, value: int, /) -> int: ...
    def __rmul__(self, value: int, /) -> int: ...
    def __rfloordiv__(self, value: int, /) -> int: ...
    def __rtruediv__(self, value: int, /) -> float: ...
    def __rmod__(self, value: int, /) -> int: ...
    def __rdivmod__(self, value: int, /) -> tuple[int, int]: ...
    def __neg__(self) -> 'int': pass
    def __pos__(self) -> 'int': pass
    @overload
    def __pow__(self, x: Literal[0], /) -> Literal[1]: ...
    @overload
    def __pow__(self, value: Literal[0], mod: None, /) -> Literal[1]: ...
    @overload
    def __pow__(self, value: _PositiveInteger, mod: None = None, /) -> int: ...
    @overload
    def __pow__(self, value: _NegativeInteger, mod: None = None, /) -> float: ...
    # positive __value -> int; negative __value -> float
    # return type must be Any as `int | float` causes too many false-positive errors
    @overload
    def __pow__(self, value: int, mod: None = None, /) -> Any: ...
    def __index__(self) -> int: pass

class float:
    def __add__(self, value: float, /) -> float: ...
    def __sub__(self, value: float, /) -> float: ...
    def __mul__(self, value: float, /) -> float: ...
    def __floordiv__(self, value: float, /) -> float: ...
    def __truediv__(self, value: float, /) -> float: ...
    def __mod__(self, value: float, /) -> float: ...
    def __divmod__(self, value: float, /) -> tuple[float, float]: ...
    @overload
    def __pow__(self, value: int, mod: None = None, /) -> float: ...
    # positive __value -> float; negative __value -> complex
    # return type must be Any as `float | complex` causes too many false-positive errors
    @overload
    def __pow__(self, value: float, mod: None = None, /) -> Any: ...
    def __radd__(self, value: float, /) -> float: ...
    def __rsub__(self, value: float, /) -> float: ...
    def __rmul__(self, value: float, /) -> float: ...
    def __rfloordiv__(self, value: float, /) -> float: ...
    def __rtruediv__(self, value: float, /) -> float: ...
    def __rmod__(self, value: float, /) -> float: ...
    def __rdivmod__(self, value: float, /) -> tuple[float, float]: ...

    def __float__(self) -> float: pass

class slice: pass
class bool(int): pass
class str: pass # For convenience
class bytes: pass
class bytearray: pass

class list(Sequence[_T], Generic[_T]):
    def __len__(self): pass
    @overload
    def __getitem__(self, i: int) -> _T: ...
    @overload
    def __getitem__(self, s: slice) -> list[_T]: ...
    def __contains__(self, item: object) -> bool: ...
    def __iter__(self) -> Iterator[_T]: ...

class set(MutableSet[_T]):
    def __init__(self, iterable: Iterable[_T] = ...) -> None: ...
    def __iter__(self) -> Iterator[_T]: pass
    def __contains__(self, item: object) -> bool: pass
    # def __ior__(self, value: AbstractSet[_T]) -> Self: ...
    def add(self, x: _T) -> None: pass
    def discard(self, x: _T) -> None: pass
    def update(self, x: set[_T]) -> None: pass
    def __len__(self): pass

def isinstance(x: object, t: type) -> bool: pass

class BaseException: pass

class dict(MutableMapping[_KT, _VT]):
    @overload
    def __init__(self, **kwargs: _VT) -> None: pass

    @overload
    def __init__(self, arg: Iterable[Tuple[_KT, _VT]], **kwargs: _VT) -> None: pass

    def __getitem__(self, key: _KT) -> _VT: pass

    def __setitem__(self, k: _KT, v: _VT) -> None: pass

    def __delitem__(self, key: _KT) -> None: ...

    def __iter__(self) -> Iterator[_KT]: pass

    def __contains__(self, item: object) -> bool: pass

    # def update(self, a: SupportsKeysAndGetItem[_KT, _VT]) -> None: pass

    @overload
    def get(self, k: _KT) -> Optional[_VT]: pass

    @overload
    def get(self, k: _KT, default: Union[_VT, _T]) -> Union[_VT, _T]: pass

    def __len__(self) -> int: ...

property = object()  # Dummy definition

class complex: pass

