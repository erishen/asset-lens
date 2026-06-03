"""
Base Fetcher - 数据获取基类

提供数据获取的通用接口和公共方法。
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from ..providers.cache import UnifiedCache

logger = logging.getLogger(__name__)


@dataclass
class FetchResult:
    """数据获取结果"""

    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None
    source: str = "unknown"
    timestamp: datetime | None = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class FetcherCacheMixin:
    """
    Fetcher 缓存混入类

    提供统一的缓存接口和 AkShare 懒加载属性，
    替代各 Fetcher 中手写的缓存逻辑和重复的 akshare property。
    """

    _cache: UnifiedCache
    _akshare_raise_on_missing: bool = True

    def _init_cache(self, cache_path: Path | None = None, default_ttl: int = 3600) -> None:
        self._cache = UnifiedCache(cache_dir=cache_path, default_ttl=default_ttl)

    @property
    def cache(self) -> UnifiedCache:
        if not hasattr(self, "_cache") or self._cache is None:
            self._cache = UnifiedCache()
        return self._cache

    @property
    def cache_path(self) -> Path:
        return self.cache.cache_dir

    @property
    def akshare(self):
        from ...utils.akshare_loader import get_akshare

        return get_akshare(raise_on_missing=self._akshare_raise_on_missing)

    def cache_save(self, filename: str, data: dict[str, Any], ttl: int | None = None) -> None:
        self.cache.save_file(filename, data, ttl=ttl)

    def cache_load(self, filename: str, max_age: int | None = None) -> dict[str, Any] | None:
        return self.cache.load_file(filename, max_age=max_age)

    def cache_is_valid(self, filename: str, max_age: int | None = None) -> bool:
        return self.cache.is_file_valid(filename, max_age=max_age)

    def cache_delete(self, filename: str) -> bool:
        return self.cache.delete_file(filename)

    def cache_clear(self) -> None:
        self.cache.clear()


class BaseFetcher(FetcherCacheMixin, ABC):
    """数据获取基类"""

    def __init__(
        self,
        timeout: int = 15,
        max_retries: int = 3,
        cache_path: Path | None = None,
        default_ttl: int = 3600,
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self._init_cache(cache_path, default_ttl)

    @abstractmethod
    def fetch(self, symbol: str, **kwargs) -> FetchResult:
        """获取数据（子类必须实现）"""
        pass

    @abstractmethod
    def fetch_batch(self, symbols: list[str], **kwargs) -> dict[str, FetchResult]:
        """批量获取数据（子类必须实现）"""
        pass

    def get_cache(self, key: str) -> dict[str, Any] | None:
        """获取缓存数据（兼容旧接口，返回包含 data/timestamp/ttl 的字典）"""
        return self.cache.load(key)

    def set_cache(self, key: str, data: dict[str, Any], ttl: int = 3600):
        """设置缓存数据（兼容旧接口，包装为包含 data/timestamp/ttl 的字典）"""
        cache_entry = {
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "ttl": ttl,
        }
        self.cache.save(key, cache_entry, ttl=ttl)

    def clear_cache(self):
        """清除缓存"""
        self.cache_clear()

    def _validate_symbol(self, symbol: str | None) -> bool:
        """验证代码格式"""
        if not symbol:
            return False
        return len(symbol) > 0

    def _handle_error(self, error: Exception, context: str = "") -> FetchResult:
        """错误处理"""
        error_msg = f"{context}: {error!s}" if context else str(error)
        logger.error(f"Fetcher error: {error_msg}")
        return FetchResult(
            success=False,
            error=error_msg,
            source=self.__class__.__name__,
        )

    def get_source_name(self) -> str:
        """获取数据源名称"""
        return self.__class__.__name__.replace("Fetcher", "").lower()
