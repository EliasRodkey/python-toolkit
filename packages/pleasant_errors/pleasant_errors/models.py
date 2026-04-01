from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class StructuredError(Protocol):
    @property
    def error_code(self) -> str: ...

    @property
    def context(self) -> dict[str, Any]: ...


@dataclass
class AppError:
    message: str
    code: str
    context: dict[str, Any] = field(default_factory=dict)
