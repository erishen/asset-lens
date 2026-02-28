"""
Tests for custom exceptions.
"""

import pytest

from asset_lens.core.exceptions import (
    AssetLensError,
    ConfigurationError,
    DataLoadError,
    DataParseError,
    ValidationError,
    APIError,
    RateLimitError,
    CacheError,
    CalculationError,
    InsufficientDataError,
    FileFormatError,
)


class TestAssetLensError:
    """Test AssetLensError base class"""

    def test_basic_error(self):
        error = AssetLensError("测试错误")
        assert str(error) == "测试错误"

    def test_error_with_details(self):
        error = AssetLensError("测试错误", {"key": "value"})
        assert "测试错误" in str(error)
        assert "key" in error.details

    def test_error_details_empty(self):
        error = AssetLensError("测试错误")
        assert error.details == {}


class TestConfigurationError:
    """Test ConfigurationError"""

    def test_config_error_no_key(self):
        error = ConfigurationError("配置错误")
        assert str(error) == "配置错误"

    def test_config_error_with_key(self):
        error = ConfigurationError("配置错误", config_key="DATA_MODE")
        assert "config_key" in error.details
        assert error.details["config_key"] == "DATA_MODE"


class TestDataLoadError:
    """Test DataLoadError"""

    def test_data_load_error_no_path(self):
        error = DataLoadError("加载失败")
        assert str(error) == "加载失败"

    def test_data_load_error_with_path(self):
        error = DataLoadError("加载失败", file_path="/path/to/file.csv")
        assert "file_path" in error.details


class TestDataParseError:
    """Test DataParseError"""

    def test_parse_error_no_details(self):
        error = DataParseError("解析失败")
        assert str(error) == "解析失败"

    def test_parse_error_with_row(self):
        error = DataParseError("解析失败", row_number=10)
        assert error.details["row_number"] == 10

    def test_parse_error_with_raw_data(self):
        error = DataParseError("解析失败", raw_data="test data")
        assert "raw_data" in error.details

    def test_parse_error_truncates_long_data(self):
        long_data = "x" * 200
        error = DataParseError("解析失败", raw_data=long_data)
        assert len(error.details["raw_data"]) == 100


class TestValidationError:
    """Test ValidationError"""

    def test_validation_error_no_details(self):
        error = ValidationError("验证失败")
        assert str(error) == "验证失败"

    def test_validation_error_with_field(self):
        error = ValidationError("验证失败", field="amount", value="abc")
        assert error.details["field"] == "amount"
        assert error.details["value"] == "abc"


class TestAPIError:
    """Test APIError"""

    def test_api_error_no_details(self):
        error = APIError("API调用失败")
        assert str(error) == "API调用失败"

    def test_api_error_with_details(self):
        error = APIError("API调用失败", api_name="Finnhub", status_code=429)
        assert error.details["api_name"] == "Finnhub"
        assert error.details["status_code"] == 429


class TestRateLimitError:
    """Test RateLimitError"""

    def test_rate_limit_error(self):
        error = RateLimitError("速率限制", api_name="AlphaVantage", retry_after=60)
        assert error.details["status_code"] == 429
        assert error.retry_after == 60
        assert error.details["retry_after"] == 60


class TestCacheError:
    """Test CacheError"""

    def test_cache_error_no_key(self):
        error = CacheError("缓存错误")
        assert str(error) == "缓存错误"

    def test_cache_error_with_key(self):
        error = CacheError("缓存错误", cache_key="market_index")
        assert error.details["cache_key"] == "market_index"


class TestCalculationError:
    """Test CalculationError"""

    def test_calculation_error_no_details(self):
        error = CalculationError("计算错误")
        assert str(error) == "计算错误"

    def test_calculation_error_with_type(self):
        error = CalculationError("计算错误", calculation_type="IRR", inputs={"rate": 0.1})
        assert error.details["calculation_type"] == "IRR"
        assert "inputs" in error.details


class TestInsufficientDataError:
    """Test InsufficientDataError"""

    def test_insufficient_data_error(self):
        error = InsufficientDataError("数据不足", required=10, actual=5)
        assert error.details["required"] == 10
        assert error.details["actual"] == 5


class TestFileFormatError:
    """Test FileFormatError"""

    def test_file_format_error_no_details(self):
        error = FileFormatError("文件格式错误")
        assert str(error) == "文件格式错误"

    def test_file_format_error_with_formats(self):
        error = FileFormatError("文件格式错误", expected_format="CSV", actual_format="XLSX")
        assert error.expected_format == "CSV"
        assert error.actual_format == "XLSX"


class TestExceptionInheritance:
    """Test exception inheritance"""

    def test_all_inherit_from_base(self):
        errors = [
            ConfigurationError("test"),
            DataLoadError("test"),
            DataParseError("test"),
            ValidationError("test"),
            APIError("test"),
            RateLimitError("test"),
            CacheError("test"),
            CalculationError("test"),
            InsufficientDataError("test", 1, 0),
            FileFormatError("test"),
        ]
        for error in errors:
            assert isinstance(error, AssetLensError)
            assert isinstance(error, Exception)
