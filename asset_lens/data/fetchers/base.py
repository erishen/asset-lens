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

    提供统一的缓存接口，替代各 Fetcher 中手写的 json.load/dump 缓存逻辑。
    内部使用 UnifiedCache，支持内存 + 文件双级缓存、TTL、批量操作。

    用法:
        class MyFetcher(FetcherCacheMixin, BaseFetcher):
            def __init__(self):
                super().__init__(cache_path=Path("/path/to/cache"))
                # 保存缓存
                self.cache_save("my_data.json", {"data": results}, ttl=3600)
                # 加载缓存
                data = self.cache_load("my_data.json")
                # 检查缓存有效性
                if self.cache_is_valid("my_data.json", max_age=86400):
                    ...
    """

    _cache: UnifiedCache

    def _init_cache(self, cache_path: Path | None = None, default_ttl: int = 3600) -> None:
        """初始化缓存（在 __init__ 中调用）"""
        self._cache = UnifiedCache(cache_dir=cache_path, default_ttl=default_ttl)

    @property
    def cache(self) -> UnifiedCache:
        """获取缓存实例"""
        if not hasattr(self, "_cache") or self._cache is None:
            self._cache = UnifiedCache()
        return self._cache

    @property
    def cache_path(self) -> Path:
        """获取缓存目录路径"""
        return self.cache.cache_dir

    def cache_save(self, filename: str, data: dict[str, Any], ttl: int | None = None) -> None:
        """
        保存缓存到命名文件

        Args:
            filename: 文件名（如 "stock_quotes.json"）
            data: 要缓存的数据
            ttl: 缓存时间（秒），None 使用默认值
        """
        self.cache.save_file(filename, data, ttl=ttl)

    def cache_load(self, filename: str, max_age: int | None = None) -> dict[str, Any] | None:
        """
        从命名文件加载缓存

        Args:
            filename: 文件名（如 "stock_quotes.json"）
            max_age: 最大缓存时间（秒），None 使用文件中的 TTL

        Returns:
            缓存数据，不存在或过期返回 None
        """
        return self.cache.load_file(filename, max_age=max_age)

    def cache_is_valid(self, filename: str, max_age: int | None = None) -> bool:
        """检查缓存文件是否有效"""
        return self.cache.is_file_valid(filename, max_age=max_age)

    def cache_delete(self, filename: str) -> bool:
        """删除缓存文件"""
        return self.cache.delete_file(filename)

    def cache_clear(self) -> None:
        """清空所有缓存"""
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
