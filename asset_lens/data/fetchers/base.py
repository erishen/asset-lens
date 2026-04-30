"""
Base Fetcher - 数据获取基类

提供数据获取的通用接口和公共方法。
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any

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


class BaseFetcher(ABC):
    """数据获取基类"""

    def __init__(self, timeout: int = 15, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self._cache: dict[str, dict[str, Any]] = {}

    @abstractmethod
    def fetch(self, symbol: str, **kwargs) -> FetchResult:
        """获取数据（子类必须实现）"""
        pass

    @abstractmethod
    def fetch_batch(self, symbols: list[str], **kwargs) -> dict[str, FetchResult]:
        """批量获取数据（子类必须实现）"""
        pass

    def get_cache(self, key: str) -> dict[str, Any] | None:
        """获取缓存数据"""
        return self._cache.get(key)

    def set_cache(self, key: str, data: dict[str, Any], ttl: int = 3600):
        """设置缓存数据"""
        self._cache[key] = {
            "data": data,
            "timestamp": datetime.now(),
            "ttl": ttl,
        }

    def clear_cache(self):
        """清除缓存"""
        self._cache.clear()

    def _validate_symbol(self, symbol: str | None) -> bool:
        """验证代码格式"""
        if not symbol:
            return False
        return len(symbol) > 0

    def _handle_error(self, error: Exception, context: str = "") -> FetchResult:
        """错误处理"""
        error_msg = f"{context}: {str(error)}" if context else str(error)
        logger.error(f"Fetcher error: {error_msg}")
        return FetchResult(
            success=False,
            error=error_msg,
            source=self.__class__.__name__,
        )

    def get_source_name(self) -> str:
        """获取数据源名称"""
        return self.__class__.__name__.replace("Fetcher", "").lower()
