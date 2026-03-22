"""
AI Cache Manager - AI 缓存管理器

负责管理 AI 分析结果的缓存。
"""

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    data: dict[str, Any]
    timestamp: datetime
    ttl: int = 3600

    def is_expired(self) -> bool:
        """检查是否过期"""
        elapsed = (datetime.now() - self.timestamp).total_seconds()
        return elapsed > self.ttl


class AICacheManager:
    """AI 缓存管理器 - 管理 AI 分析结果的缓存"""

    def __init__(
        self,
        cache_dir: Path | None = None,
        ttl: int = 3600,
        enabled: bool = True,
    ):
        """
        初始化缓存管理器

        Args:
            cache_dir: 缓存目录
            ttl: 缓存有效期（秒）
            enabled: 是否启用缓存
        """
        self.enabled = enabled
        self.ttl = ttl
        self.cache_dir = cache_dir or Path.home() / ".cache" / "asset_lens" / "ai"

        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._memory_cache: dict[str, CacheEntry] = {}

    def generate_key(self, data: dict[str, Any], prefix: str = "ai") -> str:
        """
        生成缓存键

        Args:
            data: 数据字典
            prefix: 键前缀

        Returns:
            缓存键字符串
        """
        key_data = json.dumps(
            {
                "total_value": str(data.get("total_value", 0)),
                "total_profit": str(data.get("total_profit", 0)),
                "product_count": data.get("total_products", 0),
            },
            sort_keys=True,
        )
        hash_value = hashlib.md5(key_data.encode()).hexdigest()
        return f"{prefix}_{hash_value}"

    def get(self, key: str) -> dict[str, Any] | None:
        """
        获取缓存数据

        Args:
            key: 缓存键

        Returns:
            缓存的数据，如果不存在或已过期则返回 None
        """
        if not self.enabled:
            return None

        # 先检查内存缓存
        memory_entry = self._memory_cache.get(key)
        if memory_entry and not memory_entry.is_expired():
            return memory_entry.data

        # 检查文件缓存
        cache_file = self.cache_dir / f"{key}.json"
        if not cache_file.exists():
            return None

        try:
            with open(cache_file, encoding="utf-8") as f:
                cached = json.load(f)

            cache_time = datetime.fromisoformat(cached.get("timestamp", "2000-01-01"))
            elapsed = (datetime.now() - cache_time).total_seconds()

            if elapsed > self.ttl:
                return None

            data: dict[str, Any] = cached.get("data", {})

            # 更新内存缓存
            self._memory_cache[key] = CacheEntry(
                key=key,
                data=data,
                timestamp=cache_time,
                ttl=self.ttl,
            )

            return data

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"缓存读取失败: {e}")
            return None

    def set(self, key: str, data: dict[str, Any]) -> bool:
        """
        设置缓存数据

        Args:
            key: 缓存键
            data: 要缓存的数据

        Returns:
            是否设置成功
        """
        if not self.enabled:
            return False

        # 更新内存缓存
        self._memory_cache[key] = CacheEntry(
            key=key,
            data=data,
            timestamp=datetime.now(),
            ttl=self.ttl,
        )

        # 更新文件缓存
        cache_file = self.cache_dir / f"{key}.json"
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "data": data,
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
            return True
        except Exception as e:
            logger.warning(f"缓存写入失败: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        删除缓存

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        # 删除内存缓存
        if key in self._memory_cache:
            del self._memory_cache[key]

        # 删除文件缓存
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                cache_file.unlink()
                return True
            except Exception:
                return False

        return True

    def clear(self) -> int:
        """
        清除所有缓存

        Returns:
            清除的缓存数量
        """
        count = 0

        # 清除内存缓存
        count += len(self._memory_cache)
        self._memory_cache.clear()

        # 清除文件缓存
        if self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    cache_file.unlink()
                    count += 1
                except Exception:
                    pass

        return count

    def cleanup_expired(self) -> int:
        """
        清理过期缓存

        Returns:
            清理的缓存数量
        """
        count = 0

        # 清理内存缓存
        expired_keys = [
            key for key, entry in self._memory_cache.items()
            if entry.is_expired()
        ]
        for key in expired_keys:
            del self._memory_cache[key]
            count += 1

        # 清理文件缓存
        if self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, encoding="utf-8") as f:
                        cached = json.load(f)

                    cache_time = datetime.fromisoformat(cached.get("timestamp", "2000-01-01"))
                    elapsed = (datetime.now() - cache_time).total_seconds()

                    if elapsed > self.ttl:
                        cache_file.unlink()
                        count += 1
                except Exception:
                    pass

        return count

    def get_stats(self) -> dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        memory_count = len(self._memory_cache)

        file_count = 0
        total_size = 0
        if self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("*.json"):
                file_count += 1
                total_size += cache_file.stat().st_size

        return {
            "enabled": self.enabled,
            "ttl": self.ttl,
            "memory_cache_count": memory_count,
            "file_cache_count": file_count,
            "total_size_bytes": total_size,
            "cache_dir": str(self.cache_dir),
        }
