"""
Tests for Enhanced Cache Manager.
增强版缓存管理器测试
"""

import pytest
import json
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil

from asset_lens.core.enhanced_cache_manager import (
    EnhancedCacheManager,
    CacheStats,
    CacheConfig
)


class TestEnhancedCacheManager:
    """测试增强版缓存管理器"""

    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cache_manager = EnhancedCacheManager(self.temp_dir)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cache_creation(self):
        assert self.cache_manager.cache_path.exists()

    def test_get_cache_config(self):
        config = self.cache_manager.get_cache_config('momentum_screen')
        assert config.ttl == 3600
        assert config.max_size == 100

    def test_set_cache_config(self):
        new_config = CacheConfig(ttl=7200, max_size=200)
        self.cache_manager.set_cache_config('test_cache', new_config)
        
        config = self.cache_manager.get_cache_config('test_cache')
        assert config.ttl == 7200
        assert config.max_size == 200

    def test_write_and_read_cache(self):
        data = {"key": "value", "number": 123}
        result = self.cache_manager.write_cache("test", data)
        assert result is True

        read_data = self.cache_manager.read_cache("test")
        assert read_data is not None
        assert read_data["key"] == "value"
        assert read_data["number"] == 123

    def test_cache_validity(self):
        data = {"key": "value"}
        self.cache_manager.write_cache("test", data)
        
        is_valid = self.cache_manager.is_cache_valid("test")
        assert is_valid is True

    def test_cache_expiry(self):
        data = {"key": "value"}
        self.cache_manager.write_cache("test", data)
        
        config = CacheConfig(ttl=1)
        self.cache_manager.set_cache_config('test', config)
        
        import time
        time.sleep(2)
        
        is_valid = self.cache_manager.is_cache_valid("test")
        assert is_valid is False

    def test_cache_stats(self):
        data = {"key": "value"}
        self.cache_manager.write_cache("test", data)
        
        # 第一次调用：缓存有效，记录为 hit
        self.cache_manager.is_cache_valid("test")
        # 第二次调用：缓存不存在，记录为 miss（记录到 "nonexistent" 的统计中）
        self.cache_manager.is_cache_valid("nonexistent")
        
        # 检查 "test" 缓存的统计
        stats_test = self.cache_manager.get_cache_stats("test")
        assert stats_test.hits == 1
        assert stats_test.misses == 0
        assert stats_test.total_requests == 1
        
        # 检查 "nonexistent" 缓存的统计
        stats_nonexistent = self.cache_manager.get_cache_stats("nonexistent")
        assert stats_nonexistent.hits == 0
        assert stats_nonexistent.misses == 1
        assert stats_nonexistent.total_requests == 1

    def test_cache_hit_rate(self):
        stats = CacheStats(hits=8, misses=2, total_requests=10)
        assert stats.hit_rate == 0.8

    def test_clear_cache(self):
        data = {"key": "value"}
        self.cache_manager.write_cache("test", data)
        
        result = self.cache_manager.clear_cache("test")
        assert result is True
        
        read_data = self.cache_manager.read_cache("test")
        assert read_data is None

    def test_clear_all_caches(self):
        self.cache_manager.write_cache("test1", {"key": "value1"})
        self.cache_manager.write_cache("test2", {"key": "value2"})
        
        cleared = self.cache_manager.clear_all_caches()
        assert cleared == 2

    def test_refresh_cache(self):
        data = {"key": "value"}
        self.cache_manager.write_cache("test", data)
        
        result = self.cache_manager.refresh_cache("test")
        assert result is True
        
        read_data = self.cache_manager.read_cache("test")
        assert read_data is None

    def test_get_cache_status(self):
        data = {"key": "value"}
        self.cache_manager.write_cache("test", data)
        
        status = self.cache_manager.get_cache_status("test")
        assert status["exists"] is True
        assert status["valid"] is True
        assert status["name"] == "test"

    def test_get_all_cache_status(self):
        self.cache_manager.write_cache("test1", {"key": "value1"})
        self.cache_manager.write_cache("test2", {"key": "value2"})
        
        all_status = self.cache_manager.get_all_cache_status()
        assert "test1" in all_status
        assert "test2" in all_status

    def test_save_and_load_stats(self):
        data = {"key": "value"}
        self.cache_manager.write_cache("test", data)
        self.cache_manager.is_cache_valid("test")
        
        self.cache_manager.save_stats()
        
        new_manager = EnhancedCacheManager(self.temp_dir)
        new_manager.load_stats()
        
        stats = new_manager.get_cache_stats("test")
        assert stats.hits == 1

    def test_offline_mode(self):
        EnhancedCacheManager.enable_offline_mode()
        
        data = {"key": "value"}
        self.cache_manager.write_cache("test", data)
        
        is_valid = self.cache_manager.is_cache_valid("test")
        assert is_valid is True
        
        EnhancedCacheManager.disable_offline_mode()


class TestCacheStats:
    """测试缓存统计"""

    def test_empty_stats(self):
        stats = CacheStats()
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.evictions == 0
        assert stats.total_requests == 0
        assert stats.hit_rate == 0.0

    def test_hit_rate_calculation(self):
        stats = CacheStats(hits=7, misses=3, total_requests=10)
        assert stats.hit_rate == 0.7

    def test_to_dict(self):
        stats = CacheStats(hits=5, misses=5, total_requests=10)
        stats_dict = stats.to_dict()
        
        assert stats_dict["hits"] == 5
        assert stats_dict["misses"] == 5
        assert stats_dict["hit_rate"] == "50.00%"


class TestCacheConfig:
    """测试缓存配置"""

    def test_default_config(self):
        config = CacheConfig()
        assert config.ttl == 3600
        assert config.max_size == 100
        assert config.enabled is True

    def test_custom_config(self):
        config = CacheConfig(ttl=7200, max_size=200, enabled=False)
        assert config.ttl == 7200
        assert config.max_size == 200
        assert config.enabled is False
