"""
Enhanced Cache Manager with TTL and statistics.
增强版缓存管理器 - 支持TTL和统计监控
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class CacheStats:
    """缓存统计信息"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_requests: int = 0
    
    @property
    def hit_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "total_requests": self.total_requests,
            "hit_rate": f"{self.hit_rate:.2%}"
        }


@dataclass
class CacheConfig:
    """缓存配置"""
    ttl: int = 3600
    max_size: int = 100
    enabled: bool = True
    

CACHE_CONFIG = {
    'momentum_screen': CacheConfig(ttl=3600, max_size=100),
    'stock_prices': CacheConfig(ttl=300, max_size=1000),
    'fund_nav': CacheConfig(ttl=86400, max_size=500),
    'market_data': CacheConfig(ttl=1800, max_size=200),
    'portfolio_analysis': CacheConfig(ttl=600, max_size=50),
}


class EnhancedCacheManager:
    """增强版缓存管理器 - 支持TTL和统计监控"""
    
    DEFAULT_EXPIRY_HOURS = 24
    OFFLINE_MODE = False
    
    def __init__(self, cache_path: Path):
        self.cache_path = cache_path
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self._stats: Dict[str, CacheStats] = {}
        self._config = CACHE_CONFIG
        
    def get_cache_config(self, cache_name: str) -> CacheConfig:
        """获取缓存配置"""
        return self._config.get(cache_name, CacheConfig())
    
    def set_cache_config(self, cache_name: str, config: CacheConfig):
        """设置缓存配置"""
        self._config[cache_name] = config
        
    def get_cache_file(self, cache_name: str) -> Path:
        return self.cache_path / f"{cache_name}.json"
    
    def get_stats_file(self, cache_name: str) -> Path:
        return self.cache_path / f"{cache_name}_stats.json"
    
    def _record_hit(self, cache_name: str):
        """记录缓存命中"""
        if cache_name not in self._stats:
            self._stats[cache_name] = CacheStats()
        self._stats[cache_name].hits += 1
        self._stats[cache_name].total_requests += 1
        
    def _record_miss(self, cache_name: str):
        """记录缓存未命中"""
        if cache_name not in self._stats:
            self._stats[cache_name] = CacheStats()
        self._stats[cache_name].misses += 1
        self._stats[cache_name].total_requests += 1
        
    def _record_eviction(self, cache_name: str):
        """记录缓存淘汰"""
        if cache_name not in self._stats:
            self._stats[cache_name] = CacheStats()
        self._stats[cache_name].evictions += 1

    def is_cache_valid(
        self,
        cache_name: str,
        expiry_hours: int | None = None,
    ) -> bool:
        if self.OFFLINE_MODE:
            cache_file = self.get_cache_file(cache_name)
            valid = cache_file.exists()
            if valid:
                self._record_hit(cache_name)
            else:
                self._record_miss(cache_name)
            return valid

        cache_file = self.get_cache_file(cache_name)
        if not cache_file.exists():
            self._record_miss(cache_name)
            return False

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            update_time_str = data.get("更新时间")
            if not update_time_str:
                self._record_miss(cache_name)
                return False

            update_time = datetime.strptime(update_time_str, "%Y-%m-%d %H:%M:%S")
            
            config = self.get_cache_config(cache_name)
            ttl_seconds = config.ttl
            if expiry_hours:
                ttl_seconds = expiry_hours * 3600
            
            expiry_time = update_time + timedelta(seconds=ttl_seconds)

            is_valid = datetime.now() < expiry_time
            if is_valid:
                self._record_hit(cache_name)
            else:
                self._record_miss(cache_name)
                self._record_eviction(cache_name)
                
            return is_valid

        except (json.JSONDecodeError, ValueError, KeyError):
            self._record_miss(cache_name)
            return False

    def get_cache_age(self, cache_name: str) -> Optional[timedelta]:
        cache_file = self.get_cache_file(cache_name)
        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            update_time_str = data.get("更新时间")
            if not update_time_str:
                return None

            update_time = datetime.strptime(update_time_str, "%Y-%m-%d %H:%M:%S")
            return datetime.now() - update_time

        except (json.JSONDecodeError, ValueError, KeyError):
            return None

    def get_cache_age_hours(self, cache_name: str) -> Optional[float]:
        age = self.get_cache_age(cache_name)
        if age is None:
            return None
        return age.total_seconds() / 3600

    def read_cache(self, cache_name: str) -> Optional[Dict[str, Any]]:
        cache_file = self.get_cache_file(cache_name)
        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data: Dict[str, Any] = json.load(f)
                return data
        except json.JSONDecodeError:
            return None

    def write_cache(
        self,
        cache_name: str,
        data: Dict[str, Any],
        update_time: datetime | None = None,
    ) -> bool:
        cache_file = self.get_cache_file(cache_name)

        if update_time:
            data["更新时间"] = update_time.strftime("%Y-%m-%d %H:%M:%S")
        elif "更新时间" not in data:
            data["更新时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"缓存已写入: {cache_name}")
            return True
        except Exception as e:
            logger.error(f"缓存写入失败: {cache_name}, {e}")
            return False

    def clear_cache(self, cache_name: str) -> bool:
        cache_file = self.get_cache_file(cache_name)
        if cache_file.exists():
            try:
                cache_file.unlink()
                logger.info(f"缓存已清除: {cache_name}")
                return True
            except Exception as e:
                logger.error(f"缓存清除失败: {cache_name}, {e}")
                return False
        return True

    def clear_all_caches(self) -> int:
        cleared = 0
        for cache_file in self.cache_path.glob("*.json"):
            try:
                cache_file.unlink()
                cleared += 1
            except Exception:
                pass
        logger.info(f"已清除 {cleared} 个缓存文件")
        return cleared

    def refresh_cache(self, cache_name: str) -> bool:
        """手动刷新缓存（清除并标记为需要更新）"""
        return self.clear_cache(cache_name)

    def get_cache_status(self, cache_name: str) -> Dict[str, Any]:
        cache_file = self.get_cache_file(cache_name)
        config = self.get_cache_config(cache_name)

        status = {
            "name": cache_name,
            "exists": cache_file.exists(),
            "valid": False,
            "age_hours": None,
            "file_size": None,
            "ttl_seconds": config.ttl,
            "max_size": config.max_size,
            "stats": self._stats.get(cache_name, CacheStats()).to_dict()
        }

        if cache_file.exists():
            status["file_size"] = cache_file.stat().st_size
            status["valid"] = self.is_cache_valid(cache_name)
            status["age_hours"] = self.get_cache_age_hours(cache_name)

        return status

    def get_all_cache_status(self) -> Dict[str, Dict[str, Any]]:
        status = {}
        for cache_file in self.cache_path.glob("*.json"):
            cache_name = cache_file.stem
            if not cache_name.endswith("_stats"):
                status[cache_name] = self.get_cache_status(cache_name)
        return status

    def get_cache_stats(self, cache_name: str) -> CacheStats:
        """获取缓存统计信息"""
        return self._stats.get(cache_name, CacheStats())
    
    def get_all_stats(self) -> Dict[str, CacheStats]:
        """获取所有缓存统计信息"""
        return self._stats
    
    def save_stats(self):
        """保存统计信息到文件"""
        stats_file = self.cache_path / "cache_stats.json"
        stats_data: Dict[str, Any] = {
            name: stat.to_dict()
            for name, stat in self._stats.items()
        }
        stats_data["update_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            with open(stats_file, "w", encoding="utf-8") as f:
                json.dump(stats_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存统计信息失败: {e}")
    
    def load_stats(self):
        """从文件加载统计信息"""
        stats_file = self.cache_path / "cache_stats.json"
        if not stats_file.exists():
            return
            
        try:
            with open(stats_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            for name, stat_data in data.items():
                if name != "update_time":
                    self._stats[name] = CacheStats(
                        hits=stat_data.get("hits", 0),
                        misses=stat_data.get("misses", 0),
                        evictions=stat_data.get("evictions", 0),
                        total_requests=stat_data.get("total_requests", 0)
                    )
        except Exception as e:
            logger.error(f"加载统计信息失败: {e}")

    @classmethod
    def enable_offline_mode(cls):
        """启用离线模式"""
        cls.OFFLINE_MODE = True

    @classmethod
    def disable_offline_mode(cls):
        """禁用离线模式"""
        cls.OFFLINE_MODE = False


enhanced_cache_manager = EnhancedCacheManager(Path("cache"))
