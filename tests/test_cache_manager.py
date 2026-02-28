"""
Tests for cache manager.
"""

import pytest
import json
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import os

from asset_lens.core.cache_manager import CacheManager


class TestCacheManager:
    """Test CacheManager class"""

    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cache_manager = CacheManager(self.temp_dir)

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cache_creation(self):
        assert self.cache_manager.cache_path.exists()

    def test_get_cache_file(self):
        cache_file = self.cache_manager.get_cache_file("test_cache")
        assert cache_file == self.temp_dir / "test_cache.json"

    def test_write_and_read_cache(self):
        data = {"key": "value", "number": 123}
        result = self.cache_manager.write_cache("test", data)
        assert result is True

        read_data = self.cache_manager.read_cache("test")
        assert read_data is not None
        assert read_data["key"] == "value"
        assert read_data["number"] == 123
        assert "更新时间" in read_data

    def test_read_nonexistent_cache(self):
        result = self.cache_manager.read_cache("nonexistent")
        assert result is None

    def test_is_cache_valid_no_file(self):
        result = self.cache_manager.is_cache_valid("nonexistent")
        assert result is False

    def test_is_cache_valid_fresh(self):
        data = {"key": "value"}
        self.cache_manager.write_cache("test", data)
        result = self.cache_manager.is_cache_valid("test")
        assert result is True

    def test_is_cache_valid_expired(self):
        old_time = datetime.now() - timedelta(hours=25)
        data = {"key": "value", "更新时间": old_time.strftime("%Y-%m-%d %H:%M:%S")}
        
        cache_file = self.cache_manager.get_cache_file("test")
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
        
        result = self.cache_manager.is_cache_valid("test", expiry_hours=24)
        assert result is False

    def test_get_cache_age(self):
        data = {"key": "value"}
        self.cache_manager.write_cache("test", data)
        
        age = self.cache_manager.get_cache_age("test")
        assert age is not None
        assert age.total_seconds() < 10

    def test_get_cache_age_nonexistent(self):
        age = self.cache_manager.get_cache_age("nonexistent")
        assert age is None

    def test_get_cache_age_hours(self):
        data = {"key": "value"}
        self.cache_manager.write_cache("test", data)
        
        age_hours = self.cache_manager.get_cache_age_hours("test")
        assert age_hours is not None
        assert age_hours < 1

    def test_clear_cache(self):
        data = {"key": "value"}
        self.cache_manager.write_cache("test", data)
        
        result = self.cache_manager.clear_cache("test")
        assert result is True
        
        assert not self.cache_manager.get_cache_file("test").exists()

    def test_clear_nonexistent_cache(self):
        result = self.cache_manager.clear_cache("nonexistent")
        assert result is True

    def test_clear_all_caches(self):
        self.cache_manager.write_cache("test1", {"key": "value"})
        self.cache_manager.write_cache("test2", {"key": "value"})
        
        cleared = self.cache_manager.clear_all_caches()
        assert cleared == 2

    def test_get_cache_status(self):
        data = {"key": "value"}
        self.cache_manager.write_cache("test", data)
        
        status = self.cache_manager.get_cache_status("test")
        assert status["exists"] is True
        assert status["valid"] is True
        assert status["file_size"] is not None
        assert status["age_hours"] is not None

    def test_get_cache_status_nonexistent(self):
        status = self.cache_manager.get_cache_status("nonexistent")
        assert status["exists"] is False
        assert status["valid"] is False

    def test_get_all_cache_status(self):
        self.cache_manager.write_cache("test1", {"key": "value"})
        self.cache_manager.write_cache("test2", {"key": "value"})
        
        status = self.cache_manager.get_all_cache_status()
        assert "test1" in status
        assert "test2" in status

    def test_offline_mode(self):
        CacheManager.enable_offline_mode()
        assert CacheManager.OFFLINE_MODE is True
        
        data = {"key": "value"}
        self.cache_manager.write_cache("test", data)
        
        result = self.cache_manager.is_cache_valid("test")
        assert result is True
        
        CacheManager.disable_offline_mode()
        assert CacheManager.OFFLINE_MODE is False

    def test_offline_mode_missing_cache(self):
        CacheManager.enable_offline_mode()
        
        result = self.cache_manager.is_cache_valid("nonexistent")
        assert result is False
        
        CacheManager.disable_offline_mode()

    def test_write_cache_with_custom_time(self):
        custom_time = datetime(2024, 1, 1, 12, 0, 0)
        data = {"key": "value"}
        
        self.cache_manager.write_cache("test", data, update_time=custom_time)
        
        read_data = self.cache_manager.read_cache("test")
        assert read_data["更新时间"] == "2024-01-01 12:00:00"
