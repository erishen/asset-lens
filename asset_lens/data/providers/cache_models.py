import time
from dataclasses import dataclass
from enum import Enum
from typing import Any


class CacheLevel(Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


@dataclass
class CacheConfig:
    ttl: int
    backend: str
    max_size: int = 1000


DEFAULT_CACHE_CONFIG: dict[str, CacheConfig] = {
    "stock_quote": CacheConfig(ttl=300, backend="memory", max_size=500),
    "stock_history": CacheConfig(ttl=3600, backend="file"),
    "fund_nav": CacheConfig(ttl=3600, backend="file"),
    "fund_history": CacheConfig(ttl=86400, backend="file"),
    "index_quote": CacheConfig(ttl=300, backend="memory", max_size=100),
    "macro_data": CacheConfig(ttl=86400, backend="file"),
    "crypto_quote": CacheConfig(ttl=60, backend="memory", max_size=200),
}


@dataclass
class CacheEntry:
    key: str
    value: Any
    created_at: float
    ttl: int
    hits: int = 0

    def is_expired(self) -> bool:
        return time.time() - self.created_at > self.ttl

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "created_at": self.created_at,
            "ttl": self.ttl,
            "hits": self.hits,
        }
