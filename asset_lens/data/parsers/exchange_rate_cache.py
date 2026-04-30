"""
Exchange rate cache for asset-lens.
汇率缓存管理器
"""

from datetime import datetime, timedelta
from typing import Any


class ExchangeRateCache:
    """汇率缓存管理器"""

    def __init__(self, ttl_seconds: int = 3600):
        """
        初始化缓存

        Args:
            ttl_seconds: 缓存有效期（秒），默认 1 小时
        """
        self._cache: dict[str, tuple[float, float]] = {}
        self._timestamps: dict[str, datetime] = {}
        self._ttl = ttl_seconds

    def get(self, key: str) -> tuple[float, float] | None:
        """获取缓存的汇率"""
        if key not in self._cache:
            return None

        if datetime.now() - self._timestamps[key] > timedelta(seconds=self._ttl):
            del self._cache[key]
            del self._timestamps[key]
            return None

        return self._cache[key]

    def set(self, key: str, value: tuple[float, float]) -> None:
        """缓存汇率"""
        self._cache[key] = value
        self._timestamps[key] = datetime.now()

    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()
        self._timestamps.clear()

    def get_stats(self) -> dict[str, Any]:
        """获取缓存统计信息"""
        return {"size": len(self._cache), "ttl": self._ttl, "entries": list(self._cache.keys())}


exchange_rate_cache = ExchangeRateCache(ttl_seconds=3600)
