"""
Provider Cache System - 数据源缓存系统
支持多级缓存策略，减少外部 API 调用
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional


class CacheLevel(Enum):
    """缓存级别"""
    HOT = "hot"      # 热缓存 - 内存，TTL 5分钟
    WARM = "warm"    # 温缓存 - 文件，TTL 1小时
    COLD = "cold"    # 冷缓存 - 文件，TTL 1天


@dataclass
class CacheConfig:
    """缓存配置"""
    ttl: int                    # 缓存时间（秒）
    backend: str                # 存储后端: memory, file
    max_size: int = 1000        # 最大缓存条目数（仅内存缓存）


DEFAULT_CACHE_CONFIG: Dict[str, CacheConfig] = {
    "stock_quote": CacheConfig(ttl=300, backend="memory", max_size=500),      # 5分钟
    "stock_history": CacheConfig(ttl=3600, backend="file"),                    # 1小时
    "fund_nav": CacheConfig(ttl=3600, backend="file"),                         # 1小时
    "fund_history": CacheConfig(ttl=86400, backend="file"),                    # 1天
    "index_quote": CacheConfig(ttl=300, backend="memory", max_size=100),       # 5分钟
    "macro_data": CacheConfig(ttl=86400, backend="file"),                      # 1天
    "crypto_quote": CacheConfig(ttl=60, backend="memory", max_size=200),       # 1分钟
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
    
    def to_dict(self) -> Dict[str, Any]:
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
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
    
    def get(self, key: str) -> Optional[CacheEntry]:
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
    
    def stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total_hits = sum(e.hits for e in self._cache.values())
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "total_hits": total_hits,
        }


class FileCache:
    """文件缓存"""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self._cache_dir = cache_dir or Path.home() / ".asset_lens" / "cache"
        self._cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_file_path(self, key: str) -> Path:
        """获取缓存文件路径"""
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self._cache_dir / f"{key_hash}.json"
    
    def get(self, key: str) -> Optional[CacheEntry]:
        """获取缓存"""
        file_path = self._get_file_path(key)
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
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
        except Exception:
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
    
    def stats(self) -> Dict[str, Any]:
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
        config: Optional[Dict[str, CacheConfig]] = None,
        cache_dir: Optional[Path] = None,
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
    ) -> Optional[Any]:
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
        
        if cache_config.backend == "memory":
            entry = self._memory_cache.get(key)
        else:
            entry = self._file_cache.get(key)
        
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
    
    def clear(self, data_type: Optional[str] = None) -> None:
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
    
    def stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return {
            "memory": self._memory_cache.stats(),
            "file": self._file_cache.stats(),
        }


provider_cache = ProviderCache()


__all__ = [
    "CacheLevel",
    "CacheConfig",
    "CacheEntry",
    "MemoryCache",
    "FileCache",
    "ProviderCache",
    "provider_cache",
    "DEFAULT_CACHE_CONFIG",
]
