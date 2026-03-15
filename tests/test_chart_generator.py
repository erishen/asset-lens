"""
Tests for chart_generator.py
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestChartConfig:
    """ChartConfig 测试"""

    def test_default_config(self):
        """测试默认配置"""
        from asset_lens.data.chart_generator import ChartConfig
        config = ChartConfig()
        assert config.width == 800
        assert config.height == 400
        assert config.title == ""
        assert config.x_label == ""
        assert config.y_label == ""
        assert config.show_legend is True
        assert config.show_grid is True

    def test_custom_config(self):
        """测试自定义配置"""
        from asset_lens.data.chart_generator import ChartConfig
        config = ChartConfig(
            width=1024,
            height=768,
            title="测试图表",
            x_label="日期",
            y_label="收益率",
            show_legend=False,
            show_grid=False,
        )
        assert config.width == 1024
        assert config.height == 768
        assert config.title == "测试图表"
        assert config.show_legend is False
        assert config.show_grid is False


class TestChartGenerator:
    """ChartGenerator 测试"""

    @pytest.fixture
    def temp_cache_path(self):
        """临时缓存路径"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def generator(self, temp_cache_path):
        """创建测试实例"""
        with patch('asset_lens.config.config') as mock_config:
            mock_config.cache_path = temp_cache_path
            from asset_lens.data.chart_generator import ChartGenerator
            generator = ChartGenerator()
            yield generator

    def test_init(self, generator, temp_cache_path):
        """测试初始化"""
        assert generator.cache_path == temp_cache_path
        assert generator.chart_path == temp_cache_path / "charts"
        assert generator.chart_path.exists()

    def test_print_chart_summary(self, generator):
        """测试打印图表摘要"""
        chart_data = {
            "chart_type": "profit_curve",
            "config": {"title": "测试图表"},
            "statistics": {"total_return": 0.1},
        }

        generator.print_chart_summary(chart_data)

    def test_get_chart_title(self, generator):
        """测试获取图表标题"""
        title = generator._get_chart_title("profit_curve")
        assert isinstance(title, str)

    def test_print_profit_curve(self, generator):
        """测试打印收益曲线"""
        chart_data = {
            "config": {"title": "测试"},
            "data": {
                "dates": ["2024-01-01"],
                "profit_rates": [0.1],
            },
            "statistics": {"total_return": 0.1},
        }

        generator._print_profit_curve(chart_data)

    def test_print_strategy_comparison(self, generator):
        """测试打印策略对比"""
        chart_data = {
            "data": {
                "strategies": ["strategy1"],
                "profit_rates": [0.1],
                "win_rates": [0.6],
            }
        }

        generator._print_strategy_comparison(chart_data)

    def test_print_monster_signal(self, generator):
        """测试打印妖股信号"""
        chart_data = {
            "data": {
                "signals": [],
            }
        }

        generator._print_monster_signal(chart_data)

    def test_print_risk_dashboard(self, generator):
        """测试打印风险仪表盘"""
        chart_data = {
            "data": {
                "risk_score": 50,
                "risk_level": "中等",
                "metrics": {"concentration": 0.5, "win_rate": 0.6},
                "market": {"type": "bull", "risk_level": "low", "sentiment": "positive"},
            },
            "warnings": [],
        }

        generator._print_risk_dashboard(chart_data)

    def test_generate_profit_curve_empty(self, generator):
        """测试生成收益曲线 - 空数据"""
        with patch('asset_lens.trading.stock_pool.StockPool') as mock_pool:
            with patch('asset_lens.data.stock_tracker.StockTracker') as mock_tracker:
                mock_tracker_instance = MagicMock()
                mock_tracker_instance.daily_records = {}
                mock_tracker.return_value = mock_tracker_instance

                mock_pool_instance = MagicMock()
                mock_pool_instance.positions = {}
                mock_pool.return_value = mock_pool_instance

                result = generator.generate_profit_curve("test_pool")
                assert result["chart_type"] == "profit_curve"
                assert result["pool_name"] == "test_pool"

    def test_generate_profit_curve_with_data(self, generator):
        """测试生成收益曲线 - 有数据"""
        mock_record = MagicMock()
        mock_record.date = "2024-01-01"
        mock_record.close_price = 100

        mock_position = MagicMock()
        mock_position.status = "holding"
        mock_position.buy_price = 90

        with patch('asset_lens.trading.stock_pool.StockPool') as mock_pool:
            with patch('asset_lens.data.stock_tracker.StockTracker') as mock_tracker:
                mock_tracker_instance = MagicMock()
                mock_tracker_instance.daily_records = {"sh600519": [mock_record]}
                mock_tracker.return_value = mock_tracker_instance

                mock_pool_instance = MagicMock()
                mock_pool_instance.positions = {"sh600519": mock_position}
                mock_pool.return_value = mock_pool_instance

                result = generator.generate_profit_curve("test_pool", days=30)
                assert result["chart_type"] == "profit_curve"
                assert "chart_file" in result

    def test_generate_strategy_comparison_chart(self, generator):
        """测试生成策略对比图"""
        with patch('asset_lens.trading.stock_pool.StockPool') as mock_pool:
            mock_pool_instance = MagicMock()
            mock_pool_instance.get_performance.return_value = {
                "total_profit_rate": 0.1,
                "win_rate": 0.6,
            }
            mock_pool.return_value = mock_pool_instance

            result = generator.generate_strategy_comparison_chart(["value"])
            assert result["chart_type"] == "strategy_comparison"
            assert "chart_file" in result

    def test_generate_strategy_comparison_chart_default(self, generator):
        """测试生成策略对比图 - 默认策略"""
        with patch('asset_lens.trading.stock_pool.StockPool') as mock_pool:
            mock_pool_instance = MagicMock()
            mock_pool_instance.get_performance.return_value = {
                "total_profit_rate": 0.1,
                "win_rate": 0.6,
            }
            mock_pool.return_value = mock_pool_instance

            result = generator.generate_strategy_comparison_chart()
            assert result["chart_type"] == "strategy_comparison"

    def test_generate_monster_signal_chart_empty(self, generator):
        """测试生成妖股信号图 - 空数据"""
        with patch('asset_lens.data.stock_tracker.StockTracker') as mock_tracker:
            mock_tracker_instance = MagicMock()
            mock_tracker_instance.monster_signals = []
            mock_tracker.return_value = mock_tracker_instance

            result = generator.generate_monster_signal_chart("test_pool")
            assert result["chart_type"] == "monster_signal"
            assert result["pool_name"] == "test_pool"

    def test_generate_monster_signal_chart_with_data(self, generator):
        """测试生成妖股信号图 - 有数据"""
        mock_signal = MagicMock()
        mock_signal.signal_date = "2024-01-01"
        mock_signal.signal_type = "volume_breakout|price_breakout"

        with patch('asset_lens.data.stock_tracker.StockTracker') as mock_tracker:
            mock_tracker_instance = MagicMock()
            mock_tracker_instance.monster_signals = [mock_signal]
            mock_tracker.return_value = mock_tracker_instance

            result = generator.generate_monster_signal_chart("test_pool")
            assert result["chart_type"] == "monster_signal"
            assert "chart_file" in result

    def test_generate_risk_dashboard(self, generator):
        """测试生成风险仪表盘"""
        with patch('asset_lens.trading.stock_pool.StockPool') as mock_pool:
            with patch('asset_lens.data.market_environment.market_environment_analyzer') as mock_analyzer:
                mock_pool_instance = MagicMock()
                mock_pool_instance.get_performance.return_value = {
                    "win_rate": 0.6,
                    "total_profit_rate": 0.1,
                    "holding_count": 5,
                    "total_stocks": 10,
                }
                mock_pool.return_value = mock_pool_instance

                mock_environment = MagicMock()
                mock_environment.market_type = "bull"
                mock_environment.risk_level = "low"
                mock_environment.sentiment = "positive"
                mock_analyzer.analyze_environment.return_value = mock_environment

                result = generator.generate_risk_dashboard("test_pool")
                assert result["chart_type"] == "risk_dashboard"
                assert "chart_file" in result

    def test_generate_risk_dashboard_high_risk(self, generator):
        """测试生成风险仪表盘 - 高风险"""
        with patch('asset_lens.trading.stock_pool.StockPool') as mock_pool:
            with patch('asset_lens.data.market_environment.market_environment_analyzer') as mock_analyzer:
                mock_pool_instance = MagicMock()
                mock_pool_instance.get_performance.return_value = {
                    "win_rate": 0.3,
                    "total_profit_rate": -0.1,
                    "holding_count": 8,
                    "total_stocks": 10,
                }
                mock_pool.return_value = mock_pool_instance

                mock_environment = MagicMock()
                mock_environment.market_type = "bear"
                mock_environment.risk_level = "high"
                mock_environment.sentiment = "negative"
                mock_analyzer.analyze_environment.return_value = mock_environment

                result = generator.generate_risk_dashboard("test_pool")
                assert result["chart_type"] == "risk_dashboard"
                assert len(result["warnings"]) > 0

    def test_get_chart_title_unknown(self, generator):
        """测试获取图表标题 - 未知类型"""
        title = generator._get_chart_title("unknown")
        assert title == "投资图表"

    def test_print_chart_summary_strategy_comparison(self, generator):
        """测试打印图表摘要 - 策略对比"""
        chart_data = {
            "chart_type": "strategy_comparison",
            "generate_time": "2024-01-01 12:00:00",
            "data": {
                "strategies": ["value"],
                "profit_rates": [0.1],
                "win_rates": [0.6],
            },
        }

        generator.print_chart_summary(chart_data)

    def test_print_chart_summary_monster_signal(self, generator):
        """测试打印图表摘要 - 妖股信号"""
        chart_data = {
            "chart_type": "monster_signal",
            "pool_name": "test_pool",
            "generate_time": "2024-01-01 12:00:00",
            "data": {
                "signal_types": {"volume_breakout": 5},
            },
        }

        generator.print_chart_summary(chart_data)

    def test_print_chart_summary_risk_dashboard(self, generator):
        """测试打印图表摘要 - 风险仪表盘"""
        chart_data = {
            "chart_type": "risk_dashboard",
            "pool_name": "test_pool",
            "generate_time": "2024-01-01 12:00:00",
            "data": {
                "risk_score": 50,
                "metrics": {"concentration": 0.5, "win_rate": 0.6},
                "market": {"type": "bull", "risk_level": "low", "sentiment": "positive"},
            },
            "warnings": ["测试警告"],
        }

        generator.print_chart_summary(chart_data)
