"""
Tests for investment_report.py
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from asset_lens.report.investment_report import (
    InvestmentReportGenerator,
    ReportConfig,
)


class TestReportConfig:
    """ReportConfig 测试"""

    def test_default_values(self):
        """测试默认值"""
        config = ReportConfig()
        assert config.output_dir == "reports"
        assert config.formats == ["json"]
        assert config.include_charts is True

    def test_custom_values(self):
        """测试自定义值"""
        config = ReportConfig(
            output_dir="custom_reports",
            formats=["json", "html"],
            include_charts=False,
        )
        assert config.output_dir == "custom_reports"
        assert config.formats == ["json", "html"]
        assert config.include_charts is False


class TestInvestmentReportGenerator:
    """InvestmentReportGenerator 测试"""

    @pytest.fixture
    def temp_cache_path(self):
        """临时缓存路径"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def generator(self, temp_cache_path):
        """创建测试实例"""
        with patch('asset_lens.report.investment_report.config') as mock_config:
            mock_config.cache_path = temp_cache_path
            generator = InvestmentReportGenerator()
            yield generator

    def test_init(self, generator):
        """测试初始化"""
        assert generator.config is not None
        assert generator.report_path.exists()

    def test_generate_strategy_recommendations(self, generator):
        """测试生成策略建议"""
        pool_status = {
            "win_rate": 0.4,
            "total_profit_rate": -0.05,
        }
        tracking_report = {
            "recent_monsters": [{"code": "sh600519"}],
        }

        result = generator._generate_strategy_recommendations(
            "test_strategy", pool_status, tracking_report
        )

        assert isinstance(result, list)

    def test_get_report_title(self, generator):
        """测试获取报告标题"""
        assert generator._get_report_title("strategy_report") == "策略报告"
        assert generator._get_report_title("pool_report") == "股票池报告"
        assert generator._get_report_title("comparison_report") == "策略对比报告"
        assert generator._get_report_title("risk_report") == "风险评估报告"
        assert generator._get_report_title("unknown") == "投资报告"

    def test_generate_strategy_recommendations_low_win_rate(self, generator):
        """测试生成策略建议 - 低胜率"""
        pool_status = {"win_rate": 0.3, "holding_count": 5}
        tracking_report = {"recent_monsters": []}

        result = generator._generate_strategy_recommendations(
            "test", pool_status, tracking_report
        )
        assert len(result) > 0
        assert any("胜率" in r.get("message", "") for r in result)

    def test_generate_strategy_recommendations_no_holdings(self, generator):
        """测试生成策略建议 - 无持仓"""
        pool_status = {"win_rate": 0.6, "holding_count": 0}
        tracking_report = {"recent_monsters": []}

        result = generator._generate_strategy_recommendations(
            "test", pool_status, tracking_report
        )
        assert any("无持仓" in r.get("message", "") for r in result)

    def test_generate_strategy_recommendations_monster_signals(self, generator):
        """测试生成策略建议 - 妖股信号"""
        pool_status = {"win_rate": 0.6, "holding_count": 5}
        tracking_report = {"recent_monsters": [{"code": "sh600519"}]}

        result = generator._generate_strategy_recommendations(
            "test", pool_status, tracking_report
        )
        assert any("妖股信号" in r.get("message", "") for r in result)

    def test_analyze_pool_risk_empty(self, generator):
        """测试分析股票池风险 - 空池"""
        mock_pool = MagicMock()
        mock_pool.positions = {}

        result = generator._analyze_pool_risk(mock_pool)
        assert result["risk_level"] == "unknown"

    def test_analyze_pool_risk_no_holdings(self, generator):
        """测试分析股票池风险 - 无持仓"""
        mock_pool = MagicMock()
        mock_position = MagicMock()
        mock_position.status = "sold"
        mock_pool.positions = {"sh600519": mock_position}

        result = generator._analyze_pool_risk(mock_pool)
        assert result["risk_level"] == "low"

    def test_analyze_pool_risk_high_concentration(self, generator):
        """测试分析股票池风险 - 高集中度"""
        mock_pool = MagicMock()
        mock_position = MagicMock()
        mock_position.status = "holding"
        mock_position.buy_price = 100
        mock_position.shares = 1000
        mock_position.code = "sh600519"
        mock_pool.positions = {"sh600519": mock_position}

        result = generator._analyze_pool_risk(mock_pool)
        assert result["risk_level"] == "high"

    def test_analyze_pool_risk_medium_concentration(self, generator):
        """测试分析股票池风险 - 中等集中度"""
        mock_pool = MagicMock()
        mock_position1 = MagicMock()
        mock_position1.status = "holding"
        mock_position1.buy_price = 100
        mock_position1.shares = 300
        mock_position1.code = "sh600519"

        mock_position2 = MagicMock()
        mock_position2.status = "holding"
        mock_position2.buy_price = 100
        mock_position2.shares = 700
        mock_position2.code = "sz000001"

        mock_pool.positions = {
            "sh600519": mock_position1,
            "sz000001": mock_position2,
        }

        result = generator._analyze_pool_risk(mock_pool)
        assert result["risk_level"] in ["medium", "high"]

    def test_analyze_pool_risk_zero_value(self, generator):
        """测试分析股票池风险 - 零价值"""
        mock_pool = MagicMock()
        mock_position = MagicMock()
        mock_position.status = "holding"
        mock_position.buy_price = 0
        mock_position.shares = 0
        mock_position.code = "sh600519"
        mock_pool.positions = {"sh600519": mock_position}

        result = generator._analyze_pool_risk(mock_pool)
        assert result["risk_level"] == "unknown"

    def test_calculate_risk_level_high(self, generator):
        """测试计算风险等级 - 高风险"""
        mock_strategy = MagicMock()
        mock_strategy.stop_loss = None
        mock_strategy.take_profit = 0.3
        mock_strategy.max_position = 15

        result = generator._calculate_risk_level(mock_strategy)
        assert result == "high"

    def test_calculate_risk_level_medium(self, generator):
        """测试计算风险等级 - 中等风险"""
        mock_strategy = MagicMock()
        mock_strategy.stop_loss = -0.15
        mock_strategy.take_profit = 0.25
        mock_strategy.max_position = 8

        result = generator._calculate_risk_level(mock_strategy)
        assert result == "medium"

    def test_calculate_risk_level_low(self, generator):
        """测试计算风险等级 - 低风险"""
        mock_strategy = MagicMock()
        mock_strategy.stop_loss = -0.05
        mock_strategy.take_profit = 0.1
        mock_strategy.max_position = 5

        result = generator._calculate_risk_level(mock_strategy)
        assert result == "low"

    def test_generate_risk_recommendations_high_warnings(self, generator):
        """测试生成风险建议 - 高风险警告"""
        report = {
            "warnings": [
                {"level": "high", "message": "高风险警告1"},
                {"level": "high", "message": "高风险警告2"},
            ],
            "risk_metrics": {"concentration": 0.3},
            "market_environment": {"risk_level": "low"},
        }

        result = generator._generate_risk_recommendations(report)
        assert len(result) > 0
        assert any("高风险警告" in r.get("message", "") for r in result)

    def test_generate_risk_recommendations_high_concentration(self, generator):
        """测试生成风险建议 - 高集中度"""
        report = {
            "warnings": [],
            "risk_metrics": {"concentration": 0.8},
            "market_environment": {"risk_level": "low"},
        }

        result = generator._generate_risk_recommendations(report)
        assert any("分散持仓" in r.get("message", "") for r in result)

    def test_generate_risk_recommendations_high_market_risk(self, generator):
        """测试生成风险建议 - 高市场风险"""
        report = {
            "warnings": [],
            "risk_metrics": {"concentration": 0.3},
            "market_environment": {"risk_level": "high"},
        }

        result = generator._generate_risk_recommendations(report)
        assert any("降低整体仓位" in r.get("message", "") for r in result)

    def test_print_report_strategy(self, generator):
        """测试打印报告 - 策略报告"""
        report = {
            "report_type": "strategy_report",
            "generate_time": "2024-01-01 12:00:00",
            "report_file": "/tmp/test.json",
            "strategy_info": {"name": "test_strategy", "description": "测试策略"},
            "pool_status": {"total_stocks": 10, "holding_count": 5},
            "performance": {"total_profit": 1000, "total_profit_rate": 0.1, "win_rate": 0.6},
            "recommendations": [{"message": "测试建议"}],
        }

        generator.print_report(report)

    def test_print_report_pool(self, generator):
        """测试打印报告 - 股票池报告"""
        report = {
            "report_type": "pool_report",
            "pool_name": "test_pool",
            "generate_time": "2024-01-01 12:00:00",
            "report_file": "/tmp/test.json",
            "summary": {"total_stocks": 10, "total_profit": 1000, "total_profit_rate": 0.1},
            "risk_analysis": {"risk_level": "low", "message": "风险较低"},
        }

        generator.print_report(report)

    def test_print_report_comparison(self, generator):
        """测试打印报告 - 对比报告"""
        report = {
            "report_type": "comparison_report",
            "generate_time": "2024-01-01 12:00:00",
            "report_file": "/tmp/test.json",
            "comparison": [
                {"name": "strategy1", "total_stocks": 10, "win_rate": 0.6, "total_profit_rate": 0.1, "risk_level": "low"},
            ],
        }

        generator.print_report(report)

    def test_print_report_risk(self, generator):
        """测试打印报告 - 风险报告"""
        report = {
            "report_type": "risk_report",
            "pool_name": "test_pool",
            "generate_time": "2024-01-01 12:00:00",
            "report_file": "/tmp/test.json",
            "risk_metrics": {"concentration": 0.5, "win_rate": 0.6, "max_loss": -0.05},
            "warnings": [
                {"level": "high", "message": "高风险警告"},
                {"level": "medium", "message": "中等风险警告"},
            ],
        }

        generator.print_report(report)

    def test_generate_strategy_report(self, generator):
        """测试生成策略报告"""
        mock_strategy = MagicMock()
        mock_strategy.name = "test_strategy"
        mock_strategy.description = "测试策略"
        mock_strategy.buy_conditions = []
        mock_strategy.sell_conditions = []
        mock_strategy.stop_loss = -0.1
        mock_strategy.take_profit = 0.2
        mock_strategy.max_positions = 5

        mock_pool_instance = MagicMock()
        mock_pool_instance.get_performance.return_value = {
            "total_stocks": 10,
            "watching_count": 5,
            "holding_count": 3,
            "sold_count": 2,
            "total_profit": 1000,
            "total_profit_rate": 0.1,
            "win_rate": 0.6,
            "avg_profit_rate": 0.05,
        }

        mock_tracker_instance = MagicMock()
        mock_tracker_instance.get_tracking_report.return_value = {
            "recent_monsters": [],
        }

        with patch('asset_lens.strategy.engine.strategy_engine') as mock_engine:
            with patch('asset_lens.trading.stock_pool.StockPool') as mock_pool:
                with patch('asset_lens.data.stock_tracker.StockTracker') as mock_tracker:
                    mock_engine.get_strategy.return_value = mock_strategy
                    mock_pool.return_value = mock_pool_instance
                    mock_tracker.return_value = mock_tracker_instance

                    result = generator.generate_strategy_report("test_strategy")
                    assert result["report_type"] == "strategy_report"
                    assert "report_file" in result

    def test_generate_pool_report(self, generator):
        """测试生成股票池报告"""
        mock_pool_instance = MagicMock()
        mock_pool_instance.get_performance.return_value = {
            "total_stocks": 10,
            "watching_count": 5,
            "holding_count": 3,
            "sold_count": 2,
            "total_profit": 1000,
            "total_profit_rate": 0.1,
            "win_rate": 0.6,
            "avg_profit_rate": 0.05,
            "max_profit": 500,
            "max_loss": -200,
        }
        mock_pool_instance.positions = {}

        mock_tracker_instance = MagicMock()
        mock_tracker_instance.get_tracking_report.return_value = {
            "recent_monsters": [],
            "best_performers": [],
            "worst_performers": [],
        }

        with patch('asset_lens.trading.stock_pool.StockPool') as mock_pool:
            with patch('asset_lens.data.stock_tracker.StockTracker') as mock_tracker:
                mock_pool.return_value = mock_pool_instance
                mock_tracker.return_value = mock_tracker_instance

                result = generator.generate_pool_report("test_pool")
                assert result["report_type"] == "pool_report"
                assert "report_file" in result

    def test_generate_comparison_report(self, generator):
        """测试生成对比报告"""
        mock_strategy = MagicMock()
        mock_strategy.description = "测试策略"
        mock_strategy.stop_loss = -0.1
        mock_strategy.take_profit = 0.2
        mock_strategy.max_position = 5

        mock_pool_instance = MagicMock()
        mock_pool_instance.get_performance.return_value = {
            "total_stocks": 10,
            "holding_count": 3,
            "win_rate": 0.6,
            "total_profit_rate": 0.1,
        }

        with patch('asset_lens.strategy.engine.strategy_engine') as mock_engine:
            with patch('asset_lens.trading.stock_pool.StockPool') as mock_pool:
                mock_engine.get_strategy.return_value = mock_strategy
                mock_pool.return_value = mock_pool_instance

                result = generator.generate_comparison_report(["value"])
                assert result["report_type"] == "comparison_report"
                assert "report_file" in result

    def test_generate_risk_report(self, generator):
        """测试生成风险报告"""
        mock_pool_instance = MagicMock()
        mock_pool_instance.get_performance.return_value = {
            "holding_count": 3,
            "total_stocks": 10,
            "win_rate": 0.6,
            "avg_profit_rate": 0.05,
            "max_loss": -0.05,
        }

        mock_environment = MagicMock()
        mock_environment.market_type = "bull"
        mock_environment.risk_level = "low"
        mock_environment.sentiment = "positive"

        with patch('asset_lens.trading.stock_pool.StockPool') as mock_pool:
            with patch('asset_lens.data.market_environment.market_environment_analyzer') as mock_analyzer:
                mock_pool.return_value = mock_pool_instance
                mock_analyzer.analyze_environment.return_value = mock_environment

                result = generator.generate_risk_report("test_pool")
                assert result["report_type"] == "risk_report"
                assert "report_file" in result

    def test_generate_risk_report_high_risk(self, generator):
        """测试生成风险报告 - 高风险"""
        mock_pool_instance = MagicMock()
        mock_pool_instance.get_performance.return_value = {
            "holding_count": 8,
            "total_stocks": 10,
            "win_rate": 0.3,
            "avg_profit_rate": -0.05,
            "max_loss": -0.15,
        }

        mock_environment = MagicMock()
        mock_environment.market_type = "bear"
        mock_environment.risk_level = "high"
        mock_environment.sentiment = "negative"

        with patch('asset_lens.trading.stock_pool.StockPool') as mock_pool:
            with patch('asset_lens.data.market_environment.market_environment_analyzer') as mock_analyzer:
                mock_pool.return_value = mock_pool_instance
                mock_analyzer.analyze_environment.return_value = mock_environment

                result = generator.generate_risk_report("test_pool")
                assert len(result["warnings"]) > 0

    def test_export_html_report(self, generator):
        """测试导出 HTML 报告"""
        report = {
            "report_type": "strategy_report",
            "generate_time": "2024-01-01 12:00:00",
            "strategy_info": {"name": "test", "description": "测试"},
            "pool_status": {"total_stocks": 10, "holding_count": 5},
            "performance": {"total_profit": 1000, "total_profit_rate": 0.1, "win_rate": 0.6},
            "recommendations": [],
        }

        result = generator.export_html_report(report)
        assert result.endswith(".html")

    def test_export_html_report_custom_file(self, generator):
        """测试导出 HTML 报告 - 自定义文件名"""
        report = {
            "report_type": "pool_report",
            "generate_time": "2024-01-01 12:00:00",
            "summary": {"total_stocks": 10, "total_profit": 1000, "total_profit_rate": 0.1},
            "risk_analysis": {"risk_level": "low", "message": "风险较低"},
        }

        result = generator.export_html_report(report, output_file="custom.html")
        assert result.endswith("custom.html")

    def test_calculate_risk_level_no_stop_loss(self, generator):
        """测试计算风险等级 - 无止损"""
        mock_strategy = MagicMock()
        mock_strategy.stop_loss = None
        mock_strategy.take_profit = 0.15
        mock_strategy.max_position = 12

        result = generator._calculate_risk_level(mock_strategy)
        assert result == "high"

    def test_calculate_risk_level_high_take_profit(self, generator):
        """测试计算风险等级 - 高止盈"""
        mock_strategy = MagicMock()
        mock_strategy.stop_loss = -0.08
        mock_strategy.take_profit = 0.3
        mock_strategy.max_position = 12

        result = generator._calculate_risk_level(mock_strategy)
        assert result == "medium"

    def test_calculate_risk_level_high_max_position(self, generator):
        """测试计算风险等级 - 高最大持仓"""
        mock_strategy = MagicMock()
        mock_strategy.stop_loss = -0.15
        mock_strategy.take_profit = 0.15
        mock_strategy.max_position = 15

        result = generator._calculate_risk_level(mock_strategy)
        assert result == "medium"

    def test_generate_comparison_report_empty_strategies(self, generator):
        """测试生成对比报告 - 空策略列表"""
        mock_strategy = MagicMock()
        mock_strategy.description = "测试策略"
        mock_strategy.stop_loss = -0.1
        mock_strategy.take_profit = 0.2
        mock_strategy.max_position = 5

        mock_pool_instance = MagicMock()
        mock_pool_instance.get_performance.return_value = {
            "total_stocks": 10,
            "holding_count": 3,
            "win_rate": 0.6,
            "total_profit_rate": 0.1,
        }

        with patch('asset_lens.strategy.engine.strategy_engine') as mock_engine:
            with patch('asset_lens.trading.stock_pool.StockPool') as mock_pool:
                mock_engine.get_strategy.return_value = mock_strategy
                mock_pool.return_value = mock_pool_instance

                result = generator.generate_comparison_report()
                assert result["report_type"] == "comparison_report"

    def test_generate_comparison_report_strategy_not_found(self, generator):
        """测试生成对比报告 - 策略不存在"""
        with patch('asset_lens.strategy.engine.strategy_engine') as mock_engine:
            mock_engine.get_strategy.return_value = None

            result = generator.generate_comparison_report(["nonexistent"])
            assert result["report_type"] == "comparison_report"
            assert len(result["comparison"]) == 0

    def test_generate_risk_report_empty_pool(self, generator):
        """测试生成风险报告 - 空股票池"""
        mock_pool_instance = MagicMock()
        mock_pool_instance.get_performance.return_value = {
            "holding_count": 0,
            "total_stocks": 0,
            "win_rate": 0,
            "avg_profit_rate": 0,
            "max_loss": 0,
        }

        mock_environment = MagicMock()
        mock_environment.market_type = "neutral"
        mock_environment.risk_level = "medium"
        mock_environment.sentiment = "neutral"

        with patch('asset_lens.trading.stock_pool.StockPool') as mock_pool:
            with patch('asset_lens.data.market_environment.market_environment_analyzer') as mock_analyzer:
                mock_pool.return_value = mock_pool_instance
                mock_analyzer.analyze_environment.return_value = mock_environment

                result = generator.generate_risk_report("empty_pool")
                assert result["report_type"] == "risk_report"

    def test_export_html_report_comparison(self, generator):
        """测试导出 HTML 报告 - 对比报告"""
        report = {
            "report_type": "comparison_report",
            "generate_time": "2024-01-01 12:00:00",
            "comparison": [
                {"name": "strategy1", "total_stocks": 10, "win_rate": 0.6, "total_profit_rate": 0.1, "risk_level": "low"},
                {"name": "strategy2", "total_stocks": 8, "win_rate": 0.5, "total_profit_rate": -0.05, "risk_level": "medium"},
            ],
            "recommendations": [{"message": "建议1"}],
        }

        result = generator.export_html_report(report)
        assert result.endswith(".html")

    def test_export_html_report_risk(self, generator):
        """测试导出 HTML 报告 - 风险报告"""
        report = {
            "report_type": "risk_report",
            "generate_time": "2024-01-01 12:00:00",
            "pool_name": "test_pool",
            "risk_metrics": {"concentration": 0.5, "win_rate": 0.6, "max_loss": -0.05},
            "warnings": [{"level": "high", "message": "高风险警告"}],
            "recommendations": [{"message": "建议1"}],
        }

        result = generator.export_html_report(report)
        assert result.endswith(".html")
