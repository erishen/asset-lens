"""
Base Provider implementation.
数据源基类实现
"""

from abc import ABC, abstractmethod
from typing import Any

from . import DataProvider, DataType, ProviderType


class BaseProvider(ABC, DataProvider):
    """
    数据源基类
    
    提供通用的数据源实现框架
    """

    def __init__(
        self,
        name: str,
        provider_type: ProviderType,
        priority: int = 100,
        supported_data_types: list[DataType] | None = None,
    ) -> None:
        self._name = name
        self._provider_type = provider_type
        self._priority = priority
        self._supported_data_types = supported_data_types or []
        self._available: bool | None = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def provider_type(self) -> ProviderType:
        return self._provider_type

    @property
    def priority(self) -> int:
        return self._priority

    @property
    def supported_data_types(self) -> list[DataType]:
        return self._supported_data_types

    def is_available(self) -> bool:
        """检查数据源是否可用（带缓存）"""
        if self._available is not None:
            return self._available

        self._available = self._check_availability()
        return self._available

    @abstractmethod
    def _check_availability(self) -> bool:
        """检查数据源是否可用（子类实现）"""
        ...

    @abstractmethod
    def fetch(
        self,
        data_type: DataType,
        symbol: str,
        **kwargs,
    ) -> dict[str, Any] | None:
        """获取数据（子类实现）"""
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self._name}, priority={self._priority})"
