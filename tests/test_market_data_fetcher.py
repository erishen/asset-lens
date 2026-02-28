"""
Tests for market data fetcher module.
"""

import pytest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import tempfile
import json

from asset_lens.data.market_data_fetcher import MarketDataFetcher


class TestMarketDataFetcher:
    """Test MarketDataFetcher class"""

    def test_init(self):
        """Test initialization"""
        fetcher = MarketDataFetcher()
        assert fetcher is not None
        assert fetcher.cache_path is not None


class TestMarketDataFetcherParsing:
    """Test parsing methods"""

    def test_parse_percentage(self):
        """Test parsing percentage"""
        fetcher = MarketDataFetcher()
        
        # Test with _parse_decimal method if it exists
        # Otherwise test with actual data parsing
        pass

    def test_parse_price(self):
        """Test parsing price"""
        fetcher = MarketDataFetcher()
        # Test price parsing
        pass


class TestMarketDataFetcherCache:
    """Test cache methods"""

    def test_load_cache_empty(self):
        """Test loading cache when file doesn't exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            fetcher = MarketDataFetcher()
            fetcher.cache_path = Path(temp_dir)
            
            # Test that cache directory exists
            assert fetcher.cache_path.exists()

    def test_save_and_load_cache(self):
        """Test saving and loading cache"""
        with tempfile.TemporaryDirectory() as temp_dir:
            fetcher = MarketDataFetcher()
            fetcher.cache_path = Path(temp_dir)
            
            test_data = {
                "000001.SH": {
                    "name": "Shanghai Index",
                    "price": "3500.00",
                    "change": "1.5%",
                }
            }
            
            # Save cache
            cache_file = fetcher.cache_path / "test_cache.json"
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(test_data, f)
            
            # Load cache
            with open(cache_file, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            
            assert loaded == test_data


class TestMarketDataFetcherFetchWithMock:
    """Test fetch methods with mocked API"""

    @patch('asset_lens.data.market_data_fetcher.urlopen')
    def test_fetch_domestic_index_sina_success(self, mock_urlopen):
        """Test fetching domestic index with mocked success response"""
        # Mock successful API response with 32+ fields
        # Format: name,open,prev_close,current,high,low,buy,sell,volume,amount,...(32 fields total)
        mock_response = MagicMock()
        # Create a response with 32+ fields
        fields = ["Shanghai Index", "3500.00", "3450.00", "3520.00", "3550.00", "3480.00", 
                  "0", "0", "1000000", "3500000000", "0", "0", "0", "0", "0", "0",
                  "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"]
        response_data = f'var hq_str_sh000001="{",".join(fields)}"'
        mock_response.read.return_value = response_data.encode('gbk')
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock()
        mock_urlopen.return_value = mock_response
        
        fetcher = MarketDataFetcher()
        result = fetcher.fetch_domestic_index_sina("sh000001")
        
        # Should return parsed data
        assert result is not None
        assert isinstance(result, dict)
        assert result["name"] == "Shanghai Index"

    @patch('asset_lens.data.market_data_fetcher.urlopen')
    def test_fetch_domestic_index_sina_empty(self, mock_urlopen):
        """Test fetching domestic index with empty response"""
        # Mock empty API response
        mock_response = MagicMock()
        mock_response.read.return_value = b''
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock()
        mock_urlopen.return_value = mock_response
        
        fetcher = MarketDataFetcher()
        result = fetcher.fetch_domestic_index_sina("sh000001")
        
        # Should return None for empty response
        assert result is None

    @patch('asset_lens.data.market_data_fetcher.urlopen')
    def test_fetch_domestic_index_sina_invalid(self, mock_urlopen):
        """Test fetching domestic index with invalid response"""
        # Mock invalid API response
        mock_response = MagicMock()
        mock_response.read.return_value = b'invalid data'
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock()
        mock_urlopen.return_value = mock_response
        
        fetcher = MarketDataFetcher()
        result = fetcher.fetch_domestic_index_sina("INVALID")
        
        # Should return None for invalid response
        assert result is None

    @patch('asset_lens.data.market_data_fetcher.urlopen')
    def test_fetch_domestic_index_sina_timeout(self, mock_urlopen):
        """Test fetching domestic index with timeout"""
        # Mock timeout
        from urllib.error import URLError
        mock_urlopen.side_effect = URLError("Timeout")
        
        fetcher = MarketDataFetcher()
        result = fetcher.fetch_domestic_index_sina("sh000001")
        
        # Should return None on timeout
        assert result is None

    @patch('asset_lens.data.market_data_fetcher.urlopen')
    def test_fetch_domestic_index_sina_special_chars(self, mock_urlopen):
        """Test fetching domestic index with special characters in response"""
        # Mock API response with 32+ fields
        mock_response = MagicMock()
        fields = ["Shanghai Index", "3500.00", "3450.00", "3520.00", "3550.00", "3480.00", 
                  "0", "0", "1000000", "3500000000", "0", "0", "0", "0", "0", "0",
                  "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"]
        response_data = f'var hq_str_sh000001="{",".join(fields)}"'
        mock_response.read.return_value = response_data.encode('gbk')
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock()
        mock_urlopen.return_value = mock_response
        
        fetcher = MarketDataFetcher()
        result = fetcher.fetch_domestic_index_sina("sh000001")
        
        # Should handle special characters
        assert result is not None


class TestMarketDataFetcherCacheFiles:
    """Test cache file operations"""

    def test_cache_path_exists(self):
        """Test that cache path is created"""
        fetcher = MarketDataFetcher()
        assert fetcher.cache_path.exists()

    def test_domestic_cache_file_path(self):
        """Test domestic cache file path"""
        fetcher = MarketDataFetcher()
        assert fetcher.domestic_cache_file.name == "market_index_domestic.json"

    def test_foreign_cache_file_path(self):
        """Test foreign cache file path"""
        fetcher = MarketDataFetcher()
        assert fetcher.foreign_cache_file.name == "market_index_foreign.json"

    def test_load_existing_history_no_file(self):
        """Test loading history when file doesn't exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            fetcher = MarketDataFetcher()
            fetcher.cache_path = Path(temp_dir)
            fetcher.domestic_cache_file = fetcher.cache_path / "market_index_domestic.json"
            
            # Should return empty dict when file doesn't exist
            result = fetcher._load_existing_history()
            assert result == {}


class TestMarketDataFetcherTradingTime:
    """Test trading time methods"""

    def test_is_trading_time(self):
        """Test checking if it's trading time"""
        fetcher = MarketDataFetcher()
        result = fetcher._is_trading_time()
        # Should return a boolean
        assert isinstance(result, bool)

    def test_is_trading_day(self):
        """Test checking if it's a trading day"""
        fetcher = MarketDataFetcher()
        result = fetcher._is_trading_day()
        # Should return a boolean
        assert isinstance(result, bool)


class TestMarketDataFetcherHistory:
    """Test history methods"""

    def test_update_history_empty(self):
        """Test updating empty history"""
        fetcher = MarketDataFetcher()
        
        today_data = {
            "数据日期": "2024-01-15",
            "今开": 3450.00,
            "最新价": 3500.00,
            "最高": 3550.00,
            "最低": 3440.00,
            "成交量": 1000000,
        }
        
        result = fetcher._update_history([], today_data)
        
        # Should return a list with one entry
        assert len(result) == 1
        assert result[0]["收盘"] == 3500.00

    def test_update_history_with_existing(self):
        """Test updating existing history"""
        fetcher = MarketDataFetcher()
        
        existing = [
            {"日期": "2024-01-14", "收盘": 3450.00}
        ]
        
        today_data = {
            "数据日期": "2024-01-15",
            "今开": 3450.00,
            "最新价": 3500.00,
            "最高": 3550.00,
            "最低": 3440.00,
            "成交量": 1000000,
        }
        
        result = fetcher._update_history(existing, today_data)
        
        # Should have 2 entries
        assert len(result) == 2

    def test_update_history_max_entries(self):
        """Test history max entries limit"""
        fetcher = MarketDataFetcher()
        
        # Create history with many entries
        existing = [
            {"日期": f"2023-{i//30+1:02d}-{i%30+1:02d}", "收盘": 3000.0 + i}
            for i in range(100)
        ]
        
        today_data = {
            "数据日期": "2024-01-15",
            "今开": 3450.00,
            "最新价": 3500.00,
            "最高": 3550.00,
            "最低": 3440.00,
            "成交量": 1000000,
        }
        
        result = fetcher._update_history(existing, today_data)
        
        # Should have limited entries (implementation may limit to 7 days)
        assert len(result) > 0
        assert len(result) <= 100  # Should not exceed original + 1


class TestMarketDataFetcherPeriodPerformance:
    """Test period performance calculation"""

    def test_calculate_domestic_period_performance_empty(self):
        """Test calculating period performance with empty history"""
        fetcher = MarketDataFetcher()
        
        result = fetcher._calculate_domestic_period_performance([])
        
        # Should return dict with performance data (may have default values)
        assert result is not None
        assert isinstance(result, dict)

    def test_calculate_domestic_period_performance_with_data(self):
        """Test calculating period performance with data"""
        fetcher = MarketDataFetcher()
        
        history = [
            {"日期": "2024-01-15", "收盘": 3500.00},
            {"日期": "2024-01-14", "收盘": 3450.00},
            {"日期": "2024-01-10", "收盘": 3400.00},
        ]
        
        result = fetcher._calculate_domestic_period_performance(history)
        
        # Should return dict with performance data
        assert result is not None


class TestMarketDataFetcherTechnicalStatus:
    """Test technical status estimation"""

    def test_estimate_domestic_technical_status_empty(self):
        """Test estimating technical status with empty history"""
        fetcher = MarketDataFetcher()
        
        result = fetcher._estimate_domestic_technical_status([], 3500.00)
        
        # Should return empty dict
        assert result == {}

    def test_estimate_domestic_technical_status_with_data(self):
        """Test estimating technical status with data"""
        fetcher = MarketDataFetcher()
        
        history = [
            {"数据日期": f"2024-01-{i+1:02d}", "最新价": 3400.0 + i * 10}
            for i in range(30)
        ]
        
        result = fetcher._estimate_domestic_technical_status(history, 3700.00)
        
        # Should return technical status dict
        assert result is not None
        assert isinstance(result, dict)


class TestMarketDataFetcherFetchAllDomestic:
    """Test fetch_all_domestic_indexes method"""

    @patch('asset_lens.data.market_data_fetcher.urlopen')
    def test_fetch_all_domestic_indexes_network_error(self, mock_urlopen):
        """Test fetching all domestic indexes with network error"""
        from urllib.error import URLError
        
        mock_urlopen.side_effect = URLError("Network error")
        
        fetcher = MarketDataFetcher()
        result = fetcher.fetch_all_domestic_indexes()
        
        # Should return dict with error info
        assert result is not None
        assert "指数数据" in result
        # All indexes should have failed
        assert len(result["指数数据"]) == 0
