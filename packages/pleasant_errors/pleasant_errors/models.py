from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


# TODO: Consider making Structured Error more abstract or adding more different error types? that can get complicated quickly though. This may struggle with custom errors. Maybe try testing.

@runtime_checkable
class StructuredError(Protocol):
    @property
    def error_code(self) -> str: ...

    @property
    def context(self) -> dict[str, Any]: ...


@dataclass
class Error:
    message: str
    code: str
    context: dict[str, Any] = field(default_factory=dict)
