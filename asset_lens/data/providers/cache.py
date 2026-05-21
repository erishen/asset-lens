"""
Provider Cache System - 数据源缓存系统
支持多级缓存策略，减少外部 API 调用
"""

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class CacheLevel(Enum):
    """缓存级别"""

    HOT = "hot"  # 热缓存 - 内存，TTL 5分钟
    WARM = "warm"  # 温缓存 - 文件，TTL 1小时
    COLD = "cold"  # 冷缓存 - 文件，TTL 1天


@dataclass
class CacheConfig:
    """缓存配置"""

    ttl: int  # 缓存时间（秒）
    backend: str  # 存储后端: memory, file
    max_size: int = 1000  # 最大缓存条目数（仅内存缓存）


DEFAULT_CACHE_CONFIG: dict[str, CacheConfig] = {
    "stock_quote": CacheConfig(ttl=300, backend="memory", max_size=500),  # 5分钟
    "stock_history": CacheConfig(ttl=3600, backend="file"),  # 1小时
    "fund_nav": CacheConfig(ttl=3600, backend="file"),  # 1小时
    "fund_history": CacheConfig(ttl=86400, backend="file"),  # 1天
    "index_quote": CacheConfig(ttl=300, backend="memory", max_size=100),  # 5分钟
    "macro_data": CacheConfig(ttl=86400, backend="file"),  # 1天
    "crypto_quote": CacheConfig(ttl=60, backend="memory", max_size=200),  # 1分钟
}


@dataclass
class CacheEntry:
    """缓存条目"""

    key: str
    value: Any
    created_at: float
    ttl: int
    hits: int = 0

    def is_expired(self) -> bool:
        """检查是否过期"""
        return time.time() - self.created_at > self.ttl

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "key": self.key,
            "value": self.value,
            "created_at": self.created_at,
            "ttl": self.ttl,
            "hits": self.hits,
        }


class MemoryCache:
    """内存缓存"""

    def __init__(self, max_size: int = 1000):
        self._cache: dict[str, CacheEntry] = {}
        self._max_size = max_size

    def get(self, key: str) -> CacheEntry | None:
        """获取缓存"""
        entry = self._cache.get(key)
        if entry is None:
            return None
        if entry.is_expired():
            del self._cache[key]
            return None
        entry.hits += 1
        return entry

    def set(self, key: str, value: Any, ttl: int) -> None:
        """设置缓存"""
        if len(self._cache) >= self._max_size:
            self._evict_expired()
            if len(self._cache) >= self._max_size:
                self._evict_lru()

        self._cache[key] = CacheEntry(
            key=key,
            value=value,
            created_at=time.time(),
            ttl=ttl,
        )

    def delete(self, key: str) -> bool:
        """删除缓存"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()

    def _evict_expired(self) -> None:
        """清理过期条目"""
        expired = [k for k, v in self._cache.items() if v.is_expired()]
        for key in expired:
            del self._cache[key]

    def _evict_lru(self) -> None:
        """清理最少使用的条目"""
        if not self._cache:
            return
        lru_key = min(self._cache.keys(), key=lambda k: self._cache[k].hits)
        del self._cache[lru_key]

    def stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        total_hits = sum(e.hits for e in self._cache.values())
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "total_hits": total_hits,
        }


class FileCache:
    """文件缓存"""

    def __init__(self, cache_dir: Path | None = None):
        self._cache_dir = cache_dir or Path.home() / ".asset_lens" / "cache"
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, key: str) -> Path:
        """获取缓存文件路径"""
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self._cache_dir / f"{key_hash}.json"

    def get(self, key: str) -> CacheEntry | None:
        """获取缓存"""
        file_path = self._get_file_path(key)
        if not file_path.exists():
            return None

        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            entry = CacheEntry(
                key=data["key"],
                value=data["value"],
                created_at=data["created_at"],
                ttl=data["ttl"],
                hits=data.get("hits", 0),
            )

            if entry.is_expired():
                file_path.unlink()
                return None

            entry.hits += 1
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(entry.to_dict(), f, ensure_ascii=False, indent=2)

            return entry
        except Exception as e:
            logger.debug(f"忽略异常: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int) -> None:
        """设置缓存"""
        file_path = self._get_file_path(key)
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=time.time(),
            ttl=ttl,
        )

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(entry.to_dict(), f, ensure_ascii=False, indent=2)

    def delete(self, key: str) -> bool:
        """删除缓存"""
        file_path = self._get_file_path(key)
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def clear(self) -> None:
        """清空缓存"""
        for file_path in self._cache_dir.glob("*.json"):
            file_path.unlink()

    def stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        files = list(self._cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in files)
        return {
            "file_count": len(files),
            "total_size_bytes": total_size,
            "cache_dir": str(self._cache_dir),
        }


class ProviderCache:
    """
    数据源缓存管理器

    支持多级缓存策略:
    - 热缓存: 内存缓存，适用于高频访问数据
    - 温缓存: 文件缓存，适用于中频访问数据
    - 冷缓存: 文件缓存，适用于低频访问数据
    """

    def __init__(
        self,
        config: dict[str, CacheConfig] | None = None,
        cache_dir: Path | None = None,
    ):
        self._config = config or DEFAULT_CACHE_CONFIG
        self._memory_cache = MemoryCache()
        self._file_cache = FileCache(cache_dir)

    def _get_cache_key(
        self,
        data_type: str,
        provider_name: str,
        symbol: str,
        **kwargs,
    ) -> str:
        """生成缓存键"""
        key_parts = [data_type, provider_name, symbol]
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            key_parts.extend(f"{k}={v}" for k, v in sorted_kwargs)
        return ":".join(key_parts)

    def get(
        self,
        data_type: str,
        provider_name: str,
        symbol: str,
        **kwargs,
    ) -> Any | None:
        """
        获取缓存数据

        Args:
            data_type: 数据类型
            provider_name: 数据源名称
            symbol: 代码
            **kwargs: 其他参数

        Returns:
            缓存的数据，如果不存在或过期则返回 None
        """
        cache_config = self._config.get(data_type)
        if cache_config is None:
            return None

        key = self._get_cache_key(data_type, provider_name, symbol, **kwargs)

        entry = self._memory_cache.get(key) if cache_config.backend == "memory" else self._file_cache.get(key)

        return entry.value if entry else None

    def set(
        self,
        data_type: str,
        provider_name: str,
        symbol: str,
        value: Any,
        **kwargs,
    ) -> None:
        """
        设置缓存数据

        Args:
            data_type: 数据类型
            provider_name: 数据源名称
            symbol: 代码
            value: 要缓存的数据
            **kwargs: 其他参数
        """
        cache_config = self._config.get(data_type)
        if cache_config is None:
            return

        key = self._get_cache_key(data_type, provider_name, symbol, **kwargs)

        if cache_config.backend == "memory":
            self._memory_cache.set(key, value, cache_config.ttl)
        else:
            self._file_cache.set(key, value, cache_config.ttl)

    def delete(
        self,
        data_type: str,
        provider_name: str,
        symbol: str,
        **kwargs,
    ) -> bool:
        """删除缓存"""
        cache_config = self._config.get(data_type)
        if cache_config is None:
            return False

        key = self._get_cache_key(data_type, provider_name, symbol, **kwargs)

        if cache_config.backend == "memory":
            return self._memory_cache.delete(key)
        else:
            return self._file_cache.delete(key)

    def clear(self, data_type: str | None = None) -> None:
        """清空缓存"""
        if data_type is None:
            self._memory_cache.clear()
            self._file_cache.clear()
            return

        cache_config = self._config.get(data_type)
        if cache_config is None:
            return

        if cache_config.backend == "memory":
            self._memory_cache.clear()
        else:
            self._file_cache.clear()

    def stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        return {
            "memory": self._memory_cache.stats(),
            "file": self._file_cache.stats(),
        }


class UnifiedCache:
    """
    统一缓存系统

    整合内存缓存和文件缓存，提供简单的 key-value API。
    替代各 Fetcher 中手写的 json.load/dump 缓存逻辑。

    用法:
        cache = UnifiedCache(cache_dir=Path("/path/to/cache"))
        cache.save("stock_quotes", data, ttl=3600)
        data = cache.load("stock_quotes")

        cache.save_file("stock_quotes.json", {"data": results}, ttl=3600)
        data = cache.load_file("stock_quotes.json")
    """

    def __init__(
        self,
        cache_dir: Path | None = None,
        default_ttl: int = 3600,
        max_memory_size: int = 1000,
    ):
        self._cache_dir = cache_dir or Path.home() / ".asset_lens" / "cache"
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._default_ttl = default_ttl
        self._memory = MemoryCache(max_size=max_memory_size)
        self._file = FileCache(self._cache_dir)

    @property
    def cache_dir(self) -> Path:
        return self._cache_dir

    def save(self, key: str, value: Any, ttl: int | None = None) -> None:
        """
        保存缓存（内存 + 文件双写）

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 缓存时间（秒），None 使用默认值
        """
        effective_ttl = ttl if ttl is not None else self._default_ttl
        self._memory.set(key, value, effective_ttl)
        self._file.set(key, value, effective_ttl)

    def load(self, key: str) -> Any | None:
        """
        加载缓存（内存优先，回退到文件）

        Args:
            key: 缓存键

        Returns:
            缓存值，不存在或过期返回 None
        """
        entry = self._memory.get(key)
        if entry is not None:
            return entry.value
        entry = self._file.get(key)
        if entry is not None:
            self._memory.set(key, entry.value, entry.ttl)
            return entry.value
        return None

    def delete(self, key: str) -> bool:
        """删除缓存"""
        m = self._memory.delete(key)
        f = self._file.delete(key)
        return m or f

    def exists(self, key: str) -> bool:
        """检查缓存是否存在且未过期"""
        return self.load(key) is not None

    def save_file(self, filename: str, data: dict[str, Any], ttl: int | None = None) -> None:
        """
        保存到命名文件缓存（兼容现有 Fetcher 的缓存文件格式）

        在数据中注入 _cache_meta 字段用于 TTL 管理，
        但保持与现有 json 格式兼容。

        Args:
            filename: 文件名（如 "stock_quotes.json"）
            data: 要缓存的数据
            ttl: 缓存时间（秒），None 使用默认值，0 表示永不过期
        """
        file_path = self._cache_dir / filename
        effective_ttl = ttl if ttl is not None else self._default_ttl
        cache_data = {
            "_cache_meta": {
                "updated_at": time.time(),
                "ttl": effective_ttl,
            },
            **data,
        }
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存缓存文件失败 {filename}: {e}")

    def load_file(self, filename: str, max_age: int | None = None) -> dict[str, Any] | None:
        """
        从命名文件加载缓存（兼容现有 Fetcher 的缓存文件格式）

        支持两种格式:
        1. 新格式: 包含 _cache_meta 字段，使用 TTL 自动过期
        2. 旧格式: 不包含 _cache_meta，使用 max_age 参数判断过期

        Args:
            filename: 文件名（如 "stock_quotes.json"）
            max_age: 最大缓存时间（秒），None 使用文件中的 TTL 或默认值

        Returns:
            缓存数据（不含 _cache_meta），不存在或过期返回 None
        """
        file_path = self._cache_dir / filename
        if not file_path.exists():
            return None

        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                return dict(data) if data is not None else None

            meta = data.get("_cache_meta")
            if meta:
                updated_at = meta.get("updated_at", 0)
                cache_ttl = meta.get("ttl", self._default_ttl)
                effective_max_age = max_age if max_age is not None else cache_ttl
                if effective_max_age > 0 and time.time() - updated_at > effective_max_age:
                    return None
                result = {k: v for k, v in data.items() if k != "_cache_meta"}
                return result

            if max_age is not None:
                update_time_str = data.get("update_time", "")
                if update_time_str:
                    try:
                        from datetime import datetime

                        update_time = datetime.strptime(update_time_str, "%Y-%m-%d %H:%M:%S")
                        age_seconds = (datetime.now() - update_time).total_seconds()
                        if age_seconds > max_age:
                            return None
                    except (ValueError, TypeError):
                        pass

            return data

        except Exception as e:
            logger.warning(f"加载缓存文件失败 {filename}: {e}")
            return None

    def is_file_valid(self, filename: str, max_age: int | None = None) -> bool:
        """检查命名文件缓存是否有效"""
        return self.load_file(filename, max_age) is not None

    def delete_file(self, filename: str) -> bool:
        """删除命名文件缓存"""
        file_path = self._cache_dir / filename
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def save_batch(self, items: dict[str, Any], ttl: int | None = None) -> None:
        """批量保存缓存"""
        for key, value in items.items():
            self.save(key, value, ttl)

    def load_batch(self, keys: list[str]) -> dict[str, Any]:
        """批量加载缓存"""
        result = {}
        for key in keys:
            value = self.load(key)
            if value is not None:
                result[key] = value
        return result

    def clear(self) -> None:
        """清空所有缓存"""
        self._memory.clear()
        self._file.clear()

    def stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        return {
            "memory": self._memory.stats(),
            "file": self._file.stats(),
            "cache_dir": str(self._cache_dir),
        }


unified_cache = UnifiedCache()


provider_cache = ProviderCache()


__all__ = [
    "DEFAULT_CACHE_CONFIG",
    "CacheConfig",
    "CacheEntry",
    "CacheLevel",
    "FileCache",
    "MemoryCache",
    "ProviderCache",
    "UnifiedCache",
    "provider_cache",
    "unified_cache",
]
