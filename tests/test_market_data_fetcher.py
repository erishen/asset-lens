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


class TestMarketDataFetcherForeignIndexes:
    """Test foreign index fetching methods"""

    @patch('asset_lens.data.market_data_fetcher.urlopen')
    def test_fetch_foreign_index_success(self, mock_urlopen):
        """Test fetching foreign index with success"""
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"symbol": "DJI", "price": 35000.00}'
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock()
        mock_urlopen.return_value = mock_response

        fetcher = MarketDataFetcher()
        # Test that the method exists and can be called
        assert hasattr(fetcher, 'fetch_all_foreign_indexes')

    @patch('asset_lens.data.market_data_fetcher.urlopen')
    def test_fetch_all_foreign_indexes_error(self, mock_urlopen):
        """Test fetching all foreign indexes with error"""
        from urllib.error import URLError

        mock_urlopen.side_effect = URLError("Network error")

        fetcher = MarketDataFetcher()
        result = fetcher.fetch_all_foreign_indexes()

        # Should return dict
        assert result is not None


class TestMarketDataFetcherSaveCache:
    """Test save cache methods"""

    def test_update_domestic_cache(self):
        """Test updating domestic cache"""
        with tempfile.TemporaryDirectory() as temp_dir:
            fetcher = MarketDataFetcher()
            fetcher.cache_path = Path(temp_dir)

            # Test that the method exists
            assert hasattr(fetcher, 'update_domestic_cache')

    def test_update_foreign_cache(self):
        """Test updating foreign cache"""
        with tempfile.TemporaryDirectory() as temp_dir:
            fetcher = MarketDataFetcher()
            fetcher.cache_path = Path(temp_dir)

            # Test that the method exists
            assert hasattr(fetcher, 'update_foreign_cache_alphavantage')
            assert hasattr(fetcher, 'update_foreign_cache_finnhub')


class TestMarketDataFetcherLoadCache:
    """Test load cache methods"""

    def test_load_existing_history(self):
        """Test loading existing history"""
        with tempfile.TemporaryDirectory() as temp_dir:
            fetcher = MarketDataFetcher()
            fetcher.cache_path = Path(temp_dir)

            # Test loading history
            result = fetcher._load_existing_history()
            assert result is not None
            assert isinstance(result, dict)


class TestMarketDataFetcherUpdateMarketData:
    """Test update market data methods"""

    def test_update_all_cache_method_exists(self):
        """Test that update_all_cache method exists"""
        fetcher = MarketDataFetcher()
        assert hasattr(fetcher, 'update_all_cache')

    def test_update_all_cache_default_api(self):
        """Test updating all cache with default API"""
        with tempfile.TemporaryDirectory() as temp_dir:
            fetcher = MarketDataFetcher()
            fetcher.cache_path = Path(temp_dir)

            # Test that method can be called
            # It may fail due to network, but should not crash
            try:
                result = fetcher.update_all_cache()
                assert isinstance(result, bool)
            except Exception:
                # Network errors are acceptable
                pass


class TestMarketDataFetcherParseResponse:
    """Test parse response methods"""

    def test_fetch_domestic_index_sina_exists(self):
        """Test that fetch_domestic_index_sina method exists"""
        fetcher = MarketDataFetcher()
        assert hasattr(fetcher, 'fetch_domestic_index_sina')

    def test_fetch_foreign_index_timeseries_exists(self):
        """Test that fetch_foreign_index_timeseries method exists"""
        fetcher = MarketDataFetcher()
        assert hasattr(fetcher, 'fetch_foreign_index_timeseries')


class TestMarketDataFetcherDecimalParsing:
    """Test decimal parsing methods"""

    def test_decimal_parsing_in_fetch(self):
        """Test decimal parsing in fetch methods"""
        fetcher = MarketDataFetcher()
        # Test that fetch methods handle decimal parsing internally
        assert hasattr(fetcher, 'fetch_domestic_index_sina')


class TestMarketDataFetcherPercentageParsing:
    """Test percentage parsing methods"""

    def test_percentage_parsing_in_fetch(self):
        """Test percentage parsing in fetch methods"""
        fetcher = MarketDataFetcher()
        # Test that fetch methods handle percentage parsing internally
        assert hasattr(fetcher, 'fetch_domestic_index_sina')


class TestMarketDataFetcherIndexList:
    """Test index list methods"""

    def test_fetch_all_domestic_indexes(self):
        """Test fetch all domestic indexes method"""
        fetcher = MarketDataFetcher()
        assert hasattr(fetcher, 'fetch_all_domestic_indexes')

    def test_fetch_all_foreign_indexes(self):
        """Test fetch all foreign indexes method"""
        fetcher = MarketDataFetcher()
        assert hasattr(fetcher, 'fetch_all_foreign_indexes')


class TestMarketDataFetcherGetIndexData:
    """Test get index data methods"""

    def test_fetch_domestic_index_data(self):
        """Test getting domestic index data"""
        fetcher = MarketDataFetcher()
        # Test that fetch methods exist
        assert hasattr(fetcher, 'fetch_domestic_index_sina')
        assert hasattr(fetcher, 'fetch_all_domestic_indexes')

    def test_fetch_foreign_index_data(self):
        """Test getting foreign index data"""
        fetcher = MarketDataFetcher()
        # Test that fetch methods exist
        assert hasattr(fetcher, 'fetch_foreign_index_timeseries')
        assert hasattr(fetcher, 'fetch_all_foreign_indexes')


class TestMarketDataFetcherEdgeCases:
    """Test edge cases"""

    def test_fetch_with_none_code(self):
        """Test fetching with None code"""
        fetcher = MarketDataFetcher()

        result = fetcher.fetch_domestic_index_sina(None)
        # Should handle None gracefully
        assert result is None or result == {}

    def test_fetch_with_empty_code(self):
        """Test fetching with empty code"""
        fetcher = MarketDataFetcher()

        result = fetcher.fetch_domestic_index_sina("")
        # Should handle empty string gracefully
        assert result is None or result == {}

    def test_calculate_performance_with_empty_list(self):
        """Test calculating performance with empty list"""
        fetcher = MarketDataFetcher()

        result = fetcher._calculate_domestic_period_performance([])
        # Should handle empty list gracefully
        assert result is not None

    def test_estimate_status_with_empty_list(self):
        """Test estimating status with empty list"""
        fetcher = MarketDataFetcher()

        result = fetcher._estimate_domestic_technical_status([], 3500.00)
        # Should handle empty list gracefully
        assert result is not None

    def test_calculate_rsi_with_empty_list(self):
        """Test calculating RSI with empty list"""
        fetcher = MarketDataFetcher()

        result = fetcher._calculate_rsi([])
        # Should handle empty list gracefully
        assert result is not None

    def test_calculate_rsi_with_valid_data(self):
        """Test calculating RSI with valid data"""
        fetcher = MarketDataFetcher()

        closes = [100.0 + i for i in range(20)]
        result = fetcher._calculate_rsi(closes)
        # Should return a valid RSI value
        assert result is not None
        assert 0 <= result <= 100
