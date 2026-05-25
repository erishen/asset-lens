import time

from asset_lens.data.providers.cache import (
    CacheConfig,
    CacheEntry,
    CacheLevel,
    FileCache,
    MemoryCache,
    ProviderCache,
    UnifiedCache,
)


class TestCacheEntry:
    def test_not_expired(self):
        entry = CacheEntry(key="test", value="data", created_at=time.time(), ttl=3600)
        assert not entry.is_expired()

    def test_expired(self):
        entry = CacheEntry(key="test", value="data", created_at=time.time() - 4000, ttl=3600)
        assert entry.is_expired()

    def test_to_dict(self):
        entry = CacheEntry(key="test", value="data", created_at=1000.0, ttl=3600, hits=5)
        d = entry.to_dict()
        assert d["key"] == "test"
        assert d["value"] == "data"
        assert d["created_at"] == 1000.0
        assert d["ttl"] == 3600
        assert d["hits"] == 5

    def test_default_hits(self):
        entry = CacheEntry(key="test", value="data", created_at=time.time(), ttl=3600)
        assert entry.hits == 0


class TestCacheLevel:
    def test_levels(self):
        assert CacheLevel.HOT.value == "hot"
        assert CacheLevel.WARM.value == "warm"
        assert CacheLevel.COLD.value == "cold"


class TestCacheConfig:
    def test_defaults(self):
        config = CacheConfig(ttl=300, backend="memory")
        assert config.ttl == 300
        assert config.backend == "memory"
        assert config.max_size == 1000

    def test_custom_max_size(self):
        config = CacheConfig(ttl=300, backend="memory", max_size=500)
        assert config.max_size == 500


class TestMemoryCache:
    def test_set_and_get(self):
        cache = MemoryCache()
        cache.set("key1", "value1", ttl=3600)
        entry = cache.get("key1")
        assert entry is not None
        assert entry.value == "value1"

    def test_get_missing(self):
        cache = MemoryCache()
        assert cache.get("nonexistent") is None

    def test_get_expired(self):
        cache = MemoryCache()
        cache.set("key1", "value1", ttl=1)
        time.sleep(0.1)
        cache._cache["key1"] = CacheEntry(key="key1", value="value1", created_at=time.time() - 2, ttl=1)
        assert cache.get("key1") is None

    def test_hits_increment(self):
        cache = MemoryCache()
        cache.set("key1", "value1", ttl=3600)
        entry = cache.get("key1")
        assert entry is not None
        assert entry.hits == 1
        entry2 = cache.get("key1")
        assert entry2 is not None
        assert entry2.hits == 2

    def test_delete(self):
        cache = MemoryCache()
        cache.set("key1", "value1", ttl=3600)
        assert cache.delete("key1") is True
        assert cache.get("key1") is None

    def test_delete_missing(self):
        cache = MemoryCache()
        assert cache.delete("nonexistent") is False

    def test_clear(self):
        cache = MemoryCache()
        cache.set("key1", "value1", ttl=3600)
        cache.set("key2", "value2", ttl=3600)
        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_evict_lru(self):
        cache = MemoryCache(max_size=2)
        cache.set("key1", "value1", ttl=3600)
        cache.set("key2", "value2", ttl=3600)
        cache.get("key1")
        cache.set("key3", "value3", ttl=3600)
        assert cache.get("key1") is not None
        assert cache.get("key3") is not None

    def test_stats(self):
        cache = MemoryCache()
        cache.set("key1", "value1", ttl=3600)
        stats = cache.stats()
        assert stats["size"] == 1
        assert stats["max_size"] == 1000


class TestFileCache:
    def test_set_and_get(self, tmp_path):
        cache = FileCache(cache_dir=tmp_path)
        cache.set("key1", {"data": "value1"}, ttl=3600)
        entry = cache.get("key1")
        assert entry is not None
        assert entry.value == {"data": "value1"}

    def test_get_missing(self, tmp_path):
        cache = FileCache(cache_dir=tmp_path)
        assert cache.get("nonexistent") is None

    def test_delete(self, tmp_path):
        cache = FileCache(cache_dir=tmp_path)
        cache.set("key1", "value1", ttl=3600)
        assert cache.delete("key1") is True
        assert cache.get("key1") is None

    def test_delete_missing(self, tmp_path):
        cache = FileCache(cache_dir=tmp_path)
        assert cache.delete("nonexistent") is False

    def test_clear(self, tmp_path):
        cache = FileCache(cache_dir=tmp_path)
        cache.set("key1", "value1", ttl=3600)
        cache.set("key2", "value2", ttl=3600)
        cache.clear()
        assert cache.get("key1") is None

    def test_stats(self, tmp_path):
        cache = FileCache(cache_dir=tmp_path)
        cache.set("key1", "value1", ttl=3600)
        stats = cache.stats()
        assert stats["file_count"] >= 1
        assert "total_size_bytes" in stats


class TestProviderCache:
    def test_set_and_get_memory(self, tmp_path):
        config = {"test_type": CacheConfig(ttl=300, backend="memory")}
        cache = ProviderCache(config=config, cache_dir=tmp_path)
        cache.set("test_type", "provider1", "AAPL", value={"price": 150})
        result = cache.get("test_type", "provider1", "AAPL")
        assert result == {"price": 150}

    def test_set_and_get_file(self, tmp_path):
        config = {"test_type": CacheConfig(ttl=3600, backend="file")}
        cache = ProviderCache(config=config, cache_dir=tmp_path)
        cache.set("test_type", "provider1", "AAPL", value={"price": 150})
        result = cache.get("test_type", "provider1", "AAPL")
        assert result == {"price": 150}

    def test_get_missing_type(self, tmp_path):
        cache = ProviderCache(cache_dir=tmp_path)
        result = cache.get("unknown_type", "provider1", "AAPL")
        assert result is None

    def test_delete(self, tmp_path):
        config = {"test_type": CacheConfig(ttl=300, backend="memory")}
        cache = ProviderCache(config=config, cache_dir=tmp_path)
        cache.set("test_type", "provider1", "AAPL", value={"price": 150})
        assert cache.delete("test_type", "provider1", "AAPL") is True

    def test_delete_missing_type(self, tmp_path):
        cache = ProviderCache(cache_dir=tmp_path)
        assert cache.delete("unknown_type", "provider1", "AAPL") is False

    def test_clear_all(self, tmp_path):
        config = {"test_type": CacheConfig(ttl=300, backend="memory")}
        cache = ProviderCache(config=config, cache_dir=tmp_path)
        cache.set("test_type", "provider1", "AAPL", value={"price": 150})
        cache.clear()
        assert cache.get("test_type", "provider1", "AAPL") is None

    def test_stats(self, tmp_path):
        config = {"test_type": CacheConfig(ttl=300, backend="memory")}
        cache = ProviderCache(config=config, cache_dir=tmp_path)
        stats = cache.stats()
        assert "memory" in stats
        assert "file" in stats


class TestUnifiedCache:
    def test_save_and_load(self, tmp_path):
        cache = UnifiedCache(cache_dir=tmp_path)
        cache.save("key1", {"data": "value1"}, ttl=3600)
        result = cache.load("key1")
        assert result == {"data": "value1"}

    def test_load_missing(self, tmp_path):
        cache = UnifiedCache(cache_dir=tmp_path)
        assert cache.load("nonexistent") is None

    def test_delete(self, tmp_path):
        cache = UnifiedCache(cache_dir=tmp_path)
        cache.save("key1", "value1", ttl=3600)
        assert cache.delete("key1") is True
        assert cache.load("key1") is None

    def test_exists(self, tmp_path):
        cache = UnifiedCache(cache_dir=tmp_path)
        cache.save("key1", "value1", ttl=3600)
        assert cache.exists("key1") is True
        assert cache.exists("nonexistent") is False

    def test_save_file_and_load_file(self, tmp_path):
        cache = UnifiedCache(cache_dir=tmp_path)
        data = {"更新时间": "2026-05-25 10:00:00", "指数数据": {"上证": 3200}}
        cache.save_file("market.json", data, ttl=3600)
        result = cache.load_file("market.json")
        assert result is not None
        assert "指数数据" in result

    def test_load_file_missing(self, tmp_path):
        cache = UnifiedCache(cache_dir=tmp_path)
        assert cache.load_file("nonexistent.json") is None

    def test_load_file_with_max_age(self, tmp_path):
        cache = UnifiedCache(cache_dir=tmp_path)
        data = {"更新时间": "2026-05-25 10:00:00"}
        cache.save_file("test.json", data, ttl=3600)
        result = cache.load_file("test.json", max_age=3600)
        assert result is not None

    def test_delete_file(self, tmp_path):
        cache = UnifiedCache(cache_dir=tmp_path)
        cache.save_file("test.json", {"data": 1}, ttl=3600)
        assert cache.delete_file("test.json") is True
        assert cache.load_file("test.json") is None

    def test_is_file_valid(self, tmp_path):
        cache = UnifiedCache(cache_dir=tmp_path)
        cache.save_file("test.json", {"data": 1}, ttl=3600)
        assert cache.is_file_valid("test.json") is True

    def test_save_batch(self, tmp_path):
        cache = UnifiedCache(cache_dir=tmp_path)
        cache.save_batch({"k1": "v1", "k2": "v2"}, ttl=3600)
        assert cache.load("k1") == "v1"
        assert cache.load("k2") == "v2"

    def test_load_batch(self, tmp_path):
        cache = UnifiedCache(cache_dir=tmp_path)
        cache.save("k1", "v1", ttl=3600)
        cache.save("k2", "v2", ttl=3600)
        result = cache.load_batch(["k1", "k2", "k3"])
        assert result == {"k1": "v1", "k2": "v2"}

    def test_clear(self, tmp_path):
        cache = UnifiedCache(cache_dir=tmp_path)
        cache.save("key1", "value1", ttl=3600)
        cache.clear()
        assert cache.load("key1") is None

    def test_stats(self, tmp_path):
        cache = UnifiedCache(cache_dir=tmp_path)
        stats = cache.stats()
        assert "memory" in stats
        assert "file" in stats
        assert "cache_dir" in stats

    def test_cache_dir_property(self, tmp_path):
        cache = UnifiedCache(cache_dir=tmp_path)
        assert cache.cache_dir == tmp_path

    def test_default_ttl(self, tmp_path):
        cache = UnifiedCache(cache_dir=tmp_path, default_ttl=7200)
        cache.save("key1", "value1")
        result = cache.load("key1")
        assert result == "value1"
