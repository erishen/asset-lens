"""
Intelligent Cache System - 智能缓存系统
支持 TTL、LRU 淘汰策略、缓存预热、缓存统计
"""

import time
import json
import hashlib
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from collections import OrderedDict
from pathlib import Path
import logging
import threading

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: float
    ttl: int
    access_count: int = 0
    last_access: float = field(default_factory=time.time)
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl <= 0:
            return False
        return time.time() - self.created_at > self.ttl
    
    def touch(self):
        """更新访问信息"""
        self.access_count += 1
        self.last_access = time.time()


class IntelligentCache:
    """智能缓存系统"""
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: int = 3600,
        enable_stats: bool = True
    ):
        """
        初始化智能缓存
        
        Args:
            max_size: 最大缓存数量
            default_ttl: 默认 TTL（秒）
            enable_stats: 是否启用统计
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.enable_stats = enable_stats
        
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        
        # 统计信息
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expirations": 0,
            "total_requests": 0
        }
        
        # 缓存预热数据
        self._warmup_data: Dict[str, Any] = {}
    
    def _generate_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(
        self,
        key: str,
        default: Any = None,
        refresh_on_hit: bool = False
    ) -> Any:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            default: 默认值
            refresh_on_hit: 命中时是否刷新 TTL
            
        Returns:
            缓存值
        """
        with self._lock:
            self._stats["total_requests"] += 1
            
            if key not in self._cache:
                self._stats["misses"] += 1
                return default
            
            entry = self._cache[key]
            
            # 检查是否过期
            if entry.is_expired():
                del self._cache[key]
                self._stats["expirations"] += 1
                self._stats["misses"] += 1
                return default
            
            # 更新访问信息
            entry.touch()
            
            # 刷新 TTL
            if refresh_on_hit:
                entry.created_at = time.time()
            
            # 移动到末尾（LRU）
            self._cache.move_to_end(key)
            
            self._stats["hits"] += 1
            return entry.value
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: TTL（秒），None 表示使用默认值
            
        Returns:
            是否成功
        """
        with self._lock:
            # 检查是否需要淘汰
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict()
            
            # 创建缓存条目
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                ttl=ttl if ttl is not None else self.default_ttl
            )
            
            # 如果键已存在，先删除
            if key in self._cache:
                del self._cache[key]
            
            # 添加到缓存
            self._cache[key] = entry
            return True
    
    def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            是否成功
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
    
    def _evict(self):
        """淘汰策略（LRU）"""
        if not self._cache:
            return
        
        # 删除最久未访问的条目
        oldest_key = next(iter(self._cache))
        del self._cache[oldest_key]
        self._stats["evictions"] += 1
    
    def cleanup_expired(self) -> int:
        """
        清理过期缓存
        
        Returns:
            清理的数量
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self._cache[key]
                self._stats["expirations"] += 1
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息
        """
        with self._lock:
            hit_rate = (
                self._stats["hits"] / self._stats["total_requests"]
                if self._stats["total_requests"] > 0
                else 0
            )
            
            return {
                **self._stats,
                "size": len(self._cache),
                "max_size": self.max_size,
                "hit_rate": f"{hit_rate:.2%}",
                "usage": f"{len(self._cache) / self.max_size:.2%}"
            }
    
    def warmup(self, data: Dict[str, Any], ttl: Optional[int] = None):
        """
        缓存预热
        
        Args:
            data: 预热数据 {key: value}
            ttl: TTL
        """
        with self._lock:
            for key, value in data.items():
                self.set(key, value, ttl)
        
        logger.info(f"缓存预热完成: {len(data)} 个条目")
    
    def get_or_set(
        self,
        key: str,
        factory: Callable[[], Any],
        ttl: Optional[int] = None
    ) -> Any:
        """
        获取或设置缓存
        
        Args:
            key: 缓存键
            factory: 工厂函数
            ttl: TTL
            
        Returns:
            缓存值
        """
        value = self.get(key)
        if value is not None:
            return value
        
        value = factory()
        self.set(key, value, ttl)
        return value
    
    def memoize(
        self,
        ttl: Optional[int] = None
    ) -> Callable:
        """
        缓存装饰器
        
        Args:
            ttl: TTL
            
        Returns:
            装饰器函数
        """
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                key = self._generate_key(func.__name__, *args, **kwargs)
                return self.get_or_set(key, lambda: func(*args, **kwargs), ttl)
            return wrapper
        return decorator
    
    def save_to_file(self, file_path: Path):
        """
        保存缓存到文件
        
        Args:
            file_path: 文件路径
        """
        with self._lock:
            data = {
                key: {
                    "value": entry.value,
                    "created_at": entry.created_at,
                    "ttl": entry.ttl,
                    "access_count": entry.access_count
                }
                for key, entry in self._cache.items()
                if not entry.is_expired()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_from_file(self, file_path: Path):
        """
        从文件加载缓存
        
        Args:
            file_path: 文件路径
        """
        if not file_path.exists():
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        with self._lock:
            for key, item in data.items():
                entry = CacheEntry(
                    key=key,
                    value=item["value"],
                    created_at=item["created_at"],
                    ttl=item["ttl"],
                    access_count=item.get("access_count", 0)
                )
                
                if not entry.is_expired():
                    self._cache[key] = entry


# 全局缓存实例
intelligent_cache = IntelligentCache(
    max_size=1000,
    default_ttl=3600,
    enable_stats=True
)


def cached(ttl: Optional[int] = None):
    """
    缓存装饰器
    
    Args:
        ttl: TTL（秒）
        
    Returns:
        装饰器函数
    """
    return intelligent_cache.memoize(ttl)
