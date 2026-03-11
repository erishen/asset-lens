"""
Tests for CLI Modules.
CLI 模块测试
"""

import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner


class TestCLIInteractive:
    """CLI 交互式模块测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.cli_modules.interactive import (
            interactive_analyze,
            interactive_calculate,
            interactive_fetch_stock,
            interactive_fetch_fund,
            interactive_search_fund,
            interactive_update_market,
            interactive_report,
            interactive_settings,
            interactive_menu,
        )
        assert interactive_analyze is not None
        assert interactive_calculate is not None
        assert interactive_fetch_stock is not None
        assert interactive_fetch_fund is not None
        assert interactive_search_fund is not None
        assert interactive_update_market is not None
        assert interactive_report is not None
        assert interactive_settings is not None
        assert interactive_menu is not None


class TestCLIReport:
    """CLI 报告模块测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.cli_modules.report import (
            get_data_dir,
            show_asset_summary,
            show_exchange_rate_history,
            show_sell_records,
            export_asset_summary,
            export_sell_records,
        )
        assert get_data_dir is not None
        assert show_asset_summary is not None
        assert show_exchange_rate_history is not None
        assert show_sell_records is not None
        assert export_asset_summary is not None
        assert export_sell_records is not None


class TestCLIData:
    """CLI 数据模块测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.cli_modules.data import (
            fetch_stock_data,
            fetch_fund_data,
            search_fund_data,
            update_market_data,
            update_all_data,
        )
        assert fetch_stock_data is not None
        assert fetch_fund_data is not None
        assert search_fund_data is not None
        assert update_market_data is not None
        assert update_all_data is not None


class TestCLIStrategy:
    """CLI 策略模块测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.cli_modules.strategy import (
            list_strategies,
            show_strategy,
            run_backtest,
            show_stock_pool,
            add_to_stock_pool,
            remove_from_stock_pool,
            screen_stocks_with_strategy,
        )
        assert list_strategies is not None
        assert show_strategy is not None
        assert run_backtest is not None
        assert show_stock_pool is not None
        assert add_to_stock_pool is not None
        assert remove_from_stock_pool is not None
        assert screen_stocks_with_strategy is not None


class TestCLIAnalysis:
    """CLI 分析模块测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.cli_modules.analysis import (
            analyze_portfolio,
            calculate_returns,
            show_pnl,
            calculate_irr,
            estimate_returns,
            show_market_sentiment,
        )
        assert analyze_portfolio is not None
        assert calculate_returns is not None
        assert show_pnl is not None
        assert calculate_irr is not None
        assert estimate_returns is not None
        assert show_market_sentiment is not None
