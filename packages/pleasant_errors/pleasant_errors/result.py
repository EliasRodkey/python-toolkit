from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E")


@dataclass
class Ok(Generic[T]):
    value: T


@dataclass
class Err(Generic[E]):
    error: E


type Result[T, E] = Ok[T] | Err[E]
