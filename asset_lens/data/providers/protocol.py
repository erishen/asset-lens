from typing import Any, Protocol, runtime_checkable

from .types import DataType, ProviderType


@runtime_checkable
class DataProvider(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def provider_type(self) -> ProviderType: ...

    @property
    def priority(self) -> int:
        raise NotImplementedError

    @property
    def supported_data_types(self) -> list[DataType]:
        raise NotImplementedError

    def is_available(self) -> bool:
        raise NotImplementedError

    def fetch(self, data_type: DataType, symbol: str, **kwargs) -> dict[str, Any] | None:
        raise NotImplementedError
