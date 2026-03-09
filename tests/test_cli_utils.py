"""
Tests for CLI Utilities.
CLI 工具函数测试
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestCLIUtils:
    """CLI 工具函数测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.utils.cli_utils import (
            handle_errors,
            format_currency,
            format_percent,
            format_change,
            print_section_header,
            print_success,
            print_error,
            print_warning,
            print_info,
            calculate_profit_metrics,
            safe_divide,
        )
        assert handle_errors is not None
        assert format_currency is not None
        assert format_percent is not None

    def test_format_currency(self):
        """测试货币格式化"""
        from asset_lens.utils.cli_utils import format_currency

        assert format_currency(1000.0) == "¥1,000.00"
        assert format_currency(1000.0, "$") == "$1,000.00"
        assert format_currency(0.0) == "¥0.00"

    def test_format_percent(self):
        """测试百分比格式化"""
        from asset_lens.utils.cli_utils import format_percent

        assert format_percent(10.0) == "10.00%"
        assert format_percent(10.123, 1) == "10.1%"
        assert format_percent(0.0) == "0.00%"

    def test_format_change(self):
        """测试涨跌幅格式化"""
        from asset_lens.utils.cli_utils import format_change

        assert "+" in format_change(10.0)
        assert "-" in format_change(-10.0)
        assert "➡️" in format_change(0.0)

    def test_calculate_profit_metrics(self):
        """测试收益指标计算"""
        from asset_lens.utils.cli_utils import calculate_profit_metrics

        metrics = calculate_profit_metrics(100000, 110000, 365)

        assert metrics["profit"] == 10000
        assert metrics["profit_rate"] == 10.0
        assert metrics["annual_return"] == 10.0
        assert metrics["principal"] == 100000
        assert metrics["current"] == 110000

    def test_calculate_profit_metrics_zero_principal(self):
        """测试收益指标计算 - 本金为零"""
        from asset_lens.utils.cli_utils import calculate_profit_metrics

        metrics = calculate_profit_metrics(0, 10000, 365)

        assert metrics["profit"] == 10000
        assert metrics["profit_rate"] == 0
        assert metrics["principal"] == 0

    def test_safe_divide(self):
        """测试安全除法"""
        from asset_lens.utils.cli_utils import safe_divide

        assert safe_divide(10, 2) == 5.0
        assert safe_divide(10, 0) == 0.0
        assert safe_divide(10, 0, -1) == -1.0

    def test_handle_errors_decorator(self):
        """测试错误处理装饰器"""
        from asset_lens.utils.cli_utils import handle_errors

        @handle_errors
        def will_fail():
            raise ValueError("测试错误")

        result = will_fail()
        assert result is None

    def test_handle_errors_decorator_success(self):
        """测试错误处理装饰器 - 成功情况"""
        from asset_lens.utils.cli_utils import handle_errors

        @handle_errors
        def will_succeed():
            return "success"

        result = will_succeed()
        assert result == "success"


class TestCheckDataFreshness:
    """数据新鲜度检查测试"""

    def test_file_not_exists(self, tmp_path):
        """测试文件不存在"""
        from asset_lens.utils.cli_utils import check_data_freshness

        need_update, update_time = check_data_freshness(tmp_path / "not_exists.json")
        assert need_update is True
        assert update_time is None


class TestEnsureDataDir:
    """数据目录确保测试"""

    def test_ensure_data_dir(self, tmp_path):
        """测试确保数据目录存在"""
        from asset_lens.utils.cli_utils import ensure_data_dir

        with patch("asset_lens.utils.cli_utils.config") as mock_config:
            mock_config.data_path = tmp_path / "data"
            mock_config.cache_path = tmp_path / "cache"
            mock_config.output_path = tmp_path / "output"

            ensure_data_dir()

            assert mock_config.data_path.exists()
            assert mock_config.cache_path.exists()
            assert mock_config.output_path.exists()
