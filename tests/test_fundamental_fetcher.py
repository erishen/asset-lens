from pathlib import Path
from unittest.mock import MagicMock, patch

from asset_lens.data.fundamental_fetcher import FundamentalData, FundamentalFetcher


class TestFundamentalData:
    def test_defaults(self):
        data = FundamentalData(code="000001")
        assert data.code == "000001"
        assert data.pe_ratio == 0.0
        assert data.pb_ratio == 0.0
        assert data.roe == 0.0
        assert data.revenue_growth == 0.0
        assert data.profit_growth == 0.0
        assert data.debt_ratio == 0.0
        assert data.gross_margin == 0.0
        assert data.net_margin == 0.0
        assert data.total_market_value == 0.0
        assert data.circulating_market_value == 0.0

    def test_custom_values(self):
        data = FundamentalData(
            code="600519",
            pe_ratio=35.5,
            pb_ratio=10.2,
            roe=28.3,
            revenue_growth=15.0,
            profit_growth=18.5,
            debt_ratio=22.0,
            gross_margin=92.0,
            net_margin=48.0,
            total_market_value=4400000000000,
            circulating_market_value=4400000000000,
        )
        assert data.pe_ratio == 35.5
        assert data.roe == 28.3
        assert data.total_market_value == 4400000000000

    def test_to_dict(self):
        data = FundamentalData(code="000001", pe_ratio=12.5, pb_ratio=1.2)
        d = data.to_dict()
        assert d["code"] == "000001"
        assert d["pe_ratio"] == 12.5
        assert d["pb_ratio"] == 1.2
        assert all(
            k in d
            for k in [
                "code",
                "pe_ratio",
                "pb_ratio",
                "roe",
                "revenue_growth",
                "profit_growth",
                "debt_ratio",
                "gross_margin",
                "net_margin",
                "total_market_value",
                "circulating_market_value",
            ]
        )


class TestFundamentalFetcher:
    @patch("asset_lens.data.fundamental_fetcher.FundamentalFetcher.akshare", None)
    @patch.object(FundamentalFetcher, "_load_cache", lambda self: None)
    def test_get_fundamental_no_akshare(self):
        fetcher = FundamentalFetcher.__new__(FundamentalFetcher)
        fetcher._fundamental_cache = {}
        fetcher._cache = MagicMock()

        with patch.object(fetcher, "_save_cache"):
            data = fetcher.get_fundamental("000001")

        assert data.code == "000001"
        assert data.pe_ratio == 0.0

    @patch("asset_lens.data.fundamental_fetcher.FundamentalFetcher.akshare", None)
    @patch.object(FundamentalFetcher, "_load_cache", lambda self: None)
    def test_cached_result(self):
        fetcher = FundamentalFetcher.__new__(FundamentalFetcher)
        cached = FundamentalData(code="000001", pe_ratio=15.0, pb_ratio=1.5)
        fetcher._fundamental_cache = {"000001": cached}
        fetcher._cache = MagicMock()

        result = fetcher.get_fundamental("000001")
        assert result.pe_ratio == 15.0
        assert result.pb_ratio == 1.5

    @patch("asset_lens.data.fundamental_fetcher.FundamentalFetcher.akshare", None)
    @patch.object(FundamentalFetcher, "_load_cache", lambda self: None)
    def test_batch_get_fundamentals(self):
        fetcher = FundamentalFetcher.__new__(FundamentalFetcher)
        fetcher._fundamental_cache = {}
        fetcher._cache = MagicMock()

        with patch.object(fetcher, "_save_cache"), patch.object(fetcher, "get_fundamental") as mock_get:
            mock_get.return_value = FundamentalData(code="mock")
            codes = ["000001", "000002", "000003"]
            results = fetcher.batch_get_fundamentals(codes)

        assert len(results) == 3
        assert all(c in results for c in codes)
        assert mock_get.call_count == 3

    @patch("asset_lens.data.fundamental_fetcher.FundamentalFetcher.akshare", None)
    def test_get_realtime_pe_pb_no_akshare(self):
        fetcher = FundamentalFetcher.__new__(FundamentalFetcher)
        fetcher._akshare_instance = None
        pe, pb = fetcher.get_realtime_pe_pb("000001")
        assert pe == 0.0
        assert pb == 0.0


class TestFundamentalFetcherProperties:
    def test_properties_exist(self):
        fetcher = FundamentalFetcher.__new__(FundamentalFetcher)
        fetcher._cache = MagicMock(cache_dir=Path("/tmp/test_cache"))
        assert hasattr(fetcher, "cache_path")
        assert hasattr(fetcher, "cache_file")
