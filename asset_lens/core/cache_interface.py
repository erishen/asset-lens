"""
Unified Cache Interface - 统一缓存接口
提供统一的缓存抽象，支持多种后端
"""

import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class CacheBackend(ABC):
    """缓存后端抽象基类"""

    @abstractmethod
    def get(self, key: str) -> Any | None:
        """获取缓存值"""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """设置缓存值"""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除缓存"""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        pass

    @abstractmethod
    def clear(self) -> None:
        """清空缓存"""
        pass

    @abstractmethod
    def stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        pass


class UnifiedCache:
    """统一缓存管理器"""

    def __init__(self, backend: CacheBackend):
        self._backend = backend

    def get(self, key: str) -> Any | None:
        """获取缓存值"""
        return self._backend.get(key)

    def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """设置缓存值"""
        return self._backend.set(key, value, ttl)

    def delete(self, key: str) -> bool:
        """删除缓存"""
        return self._backend.delete(key)

    def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        return self._backend.exists(key)

    def clear(self) -> None:
        """清空缓存"""
        self._backend.clear()

    def stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        return self._backend.stats()

    def get_or_set(
        self,
        key: str,
        factory: Callable[[], Any],
        ttl: int | None = None,
    ) -> Any:
        """
        获取缓存，如果不存在则通过 factory 创建并缓存

        Args:
            key: 缓存键
            factory: 创建值的工厂函数
            ttl: 缓存时间（秒）

        Returns:
            缓存值或新创建的值
        """
        value = self.get(key)
        if value is not None:
            return value

        value = factory()
        if value is not None:
            self.set(key, value, ttl)
        return value

    def get_or_set_async(
        self,
        key: str,
        factory: Callable[[], Any],
        ttl: int | None = None,
    ) -> Any:
        """
        异步获取缓存，如果不存在则通过 factory 创建并缓存

        Args:
            key: 缓存键
            factory: 创建值的异步工厂函数
            ttl: 缓存时间（秒）

        Returns:
            缓存值或新创建的值
        """
        import asyncio

        value = self.get(key)
        if value is not None:
            return value

        if asyncio.iscoroutinefunction(factory):
            loop = asyncio.get_event_loop()
            value = loop.run_until_complete(factory())
        else:
            value = factory()

        if value is not None:
            self.set(key, value, ttl)
        return value


__all__ = ["CacheBackend", "UnifiedCache"]
