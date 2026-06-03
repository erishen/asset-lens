import pytest

from asset_lens.data.parsers.exchange_rate_cache import ExchangeRateCache


class TestExchangeRateCache:
    def test_init_default_ttl(self):
        cache = ExchangeRateCache()
        stats = cache.get_stats()
        assert stats["ttl"] == 3600
        assert stats["size"] == 0

    def test_custom_ttl(self):
        cache = ExchangeRateCache(ttl_seconds=7200)
        assert cache.get_stats()["ttl"] == 7200

    def test_get_and_set(self):
        cache = ExchangeRateCache(ttl_seconds=3600)
        cache.set("USD/CNY", (7.25, 7.30))
        result = cache.get("USD/CNY")
        assert result is not None
        assert result[0] == pytest.approx(7.25)
        assert result[1] == pytest.approx(7.30)

    def test_get_missing_key(self):
        cache = ExchangeRateCache()
        result = cache.get("NONEXISTENT")
        assert result is None

    def test_expired_entry(self):
        cache = ExchangeRateCache(ttl_seconds=1)
        cache.set("EUR/CNY", (7.80, 7.85))
        result = cache.get("EUR/CNY")
        assert result is not None

    def test_clear(self):
        cache = ExchangeRateCache()
        cache.set("USD/CNY", (7.2, 7.3))
        cache.set("EUR/CNY", (7.8, 7.9))
        assert cache.get_stats()["size"] == 2
        cache.clear()
        assert cache.get_stats()["size"] == 0

    def test_overwrite_existing_key(self):
        cache = ExchangeRateCache()
        cache.set("USD/CNY", (7.20, 7.25))
        cache.set("USD/CNY", (7.28, 7.33))
        result = cache.get("USD/CNY")
        assert result[0] == pytest.approx(7.28)

    def test_multiple_keys(self):
        cache = ExchangeRateCache()
        keys = ["USD/CNY", "EUR/CNY", "GBP/CNY", "JPY/CNY"]
        values = [(7.2, 7.3), (7.8, 7.9), (9.1, 9.2), (0.048, 0.05)]
        for k, v in zip(keys, values):
            cache.set(k, v)
        for k, v in zip(keys, values):
            result = cache.get(k)
            assert result is not None
            assert result[0] == pytest.approx(v[0])

    def test_stats_entries_list(self):
        cache = ExchangeRateCache()
        cache.set("USD/CNY", (7.2, 7.3))
        cache.set("EUR/CNY", (7.8, 7.9))
        stats = cache.get_stats()
        assert "USD/CNY" in stats["entries"]
        assert "EUR/CNY" in stats["entries"]

    def test_float_values(self):
        cache = ExchangeRateCache()
        cache.set("HKD/CNY", (0.92, 0.93))
        val = cache.get("HKD/CNY")
        assert isinstance(val[0], float)
        assert isinstance(val[1], float)
