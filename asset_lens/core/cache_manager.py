"""
Cache manager with expiration support.
支持过期机制的缓存管理器
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional


class CacheManager:
    """缓存管理器，支持过期机制"""

    DEFAULT_EXPIRY_HOURS = 24
    OFFLINE_MODE = False

    def __init__(self, cache_path: Path):
        self.cache_path = cache_path
        self.cache_path.mkdir(parents=True, exist_ok=True)

    def get_cache_file(self, cache_name: str) -> Path:
        return self.cache_path / f"{cache_name}.json"

    def is_cache_valid(
        self,
        cache_name: str,
        expiry_hours: int | None = None,
    ) -> bool:
        if self.OFFLINE_MODE:
            cache_file = self.get_cache_file(cache_name)
            return cache_file.exists()

        cache_file = self.get_cache_file(cache_name)
        if not cache_file.exists():
            return False

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            update_time_str = data.get("更新时间")
            if not update_time_str:
                return False

            update_time = datetime.strptime(update_time_str, "%Y-%m-%d %H:%M:%S")
            expiry_hours = expiry_hours or self.DEFAULT_EXPIRY_HOURS
            expiry_time = update_time + timedelta(hours=expiry_hours)

            return datetime.now() < expiry_time

        except (json.JSONDecodeError, ValueError, KeyError):
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
            return True
        except Exception:
            return False

    def clear_cache(self, cache_name: str) -> bool:
        cache_file = self.get_cache_file(cache_name)
        if cache_file.exists():
            try:
                cache_file.unlink()
                return True
            except Exception:
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
        return cleared

    def get_cache_status(self, cache_name: str) -> Dict[str, Any]:
        cache_file = self.get_cache_file(cache_name)

        status = {
            "name": cache_name,
            "exists": cache_file.exists(),
            "valid": False,
            "age_hours": None,
            "file_size": None,
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
            status[cache_name] = self.get_cache_status(cache_name)
        return status

    @classmethod
    def enable_offline_mode(cls):
        """启用离线模式"""
        cls.OFFLINE_MODE = True

    @classmethod
    def disable_offline_mode(cls):
        """禁用离线模式"""
        cls.OFFLINE_MODE = False
