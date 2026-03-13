"""
Tests for Report Components Module
"""

import pytest
from pathlib import Path
from datetime import datetime
from asset_lens.report import (
    format_currency,
    format_percentage,
    format_date,
    format_number,
    ChartGenerator,
    ReportDataCollector,
)


class TestFormatters:
    """格式化工具测试"""

    def test_format_currency(self):
        """测试货币格式化"""
        assert format_currency(12345.67) == "¥12,345.67"
        assert format_currency(12345.67, currency="$") == "$12,345.67"
        assert format_currency(12345.67, decimal_places=0) == "¥12,346"
        assert format_currency(12345.67, show_sign=True) == "+¥12,345.67"
        assert format_currency(-12345.67) == "¥-12,345.67"

    def test_format_currency_string_input(self):
        """测试字符串输入"""
        assert format_currency("12,345.67") == "¥12,345.67"
        assert format_currency("¥12,345.67") == "¥12,345.67"

    def test_format_currency_invalid(self):
        """测试无效输入"""
        assert format_currency("invalid") == "¥0.00"
        assert format_currency(None) == "¥0.00"

    def test_format_percentage(self):
        """测试百分比格式化"""
        assert format_percentage(5.5) == "+5.50%"
        assert format_percentage(-5.5) == "-5.50%"
        assert format_percentage(5.5, show_sign=False) == "5.50%"
        assert format_percentage(5.567, decimal_places=1) == "+5.6%"

    def test_format_percentage_string_input(self):
        """测试字符串输入"""
        assert format_percentage("5.5%") == "+5.50%"
        assert format_percentage("5.5") == "+5.50%"

    def test_format_date(self):
        """测试日期格式化"""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        assert format_date(dt) == "2024-01-15"
        assert format_date(dt, fmt="%Y/%m/%d") == "2024/01/15"

    def test_format_date_date_input(self):
        """测试 date 类型输入"""
        from datetime import date
        d = date(2024, 1, 15)
        assert format_date(d) == "2024-01-15"

    def test_format_number(self):
        """测试数字格式化"""
        assert format_number(12345.67) == "12,345.67"
        assert format_number(12345.67, thousand_separator=False) == "12345.67"
        assert format_number(12345.67, decimal_places=0) == "12,346"

    def test_format_number_string_input(self):
        """测试字符串输入"""
        assert format_number("12,345.67") == "12,345.67"


class TestChartGenerator:
    """图表生成器测试"""

    def test_initialization(self, tmp_path):
        """测试初始化"""
        generator = ChartGenerator(output_dir=tmp_path)
        
        assert generator.output_dir == tmp_path

    def test_generate_pie_chart_data(self, tmp_path):
        """测试饼图数据生成"""
        generator = ChartGenerator(output_dir=tmp_path)
        data = {"股票": 50000, "基金": 30000, "债券": 20000}
        
        result = generator.generate_pie_chart_data(data, title="资产分布")
        
        assert result["chart_type"] == "pie"
        assert result["title"] == "资产分布"
        assert result["total"] == 100000
        assert len(result["data"]) == 3

    def test_generate_bar_chart_data(self, tmp_path):
        """测试柱状图数据生成"""
        generator = ChartGenerator(output_dir=tmp_path)
        labels = ["股票", "基金", "债券"]
        values = [50000, 30000, 20000]
        
        result = generator.generate_bar_chart_data(labels, values, title="收益对比")
        
        assert result["chart_type"] == "bar"
        assert result["title"] == "收益对比"
        assert result["labels"] == labels
        assert len(result["datasets"]) == 1

    def test_generate_line_chart_data(self, tmp_path):
        """测试折线图数据生成"""
        generator = ChartGenerator(output_dir=tmp_path)
        labels = ["1月", "2月", "3月"]
        datasets = [{"label": "收益", "data": [100, 200, 300]}]
        
        result = generator.generate_line_chart_data(labels, datasets, title="收益曲线")
        
        assert result["chart_type"] == "line"
        assert result["title"] == "收益曲线"
        assert result["labels"] == labels

    def test_save_chart_config(self, tmp_path):
        """测试保存图表配置"""
        generator = ChartGenerator(output_dir=tmp_path)
        chart_data = {"chart_type": "pie", "title": "测试"}
        
        result = generator.save_chart_config(chart_data, "test_chart")
        
        assert result is not None
        assert result.exists()
        assert result.suffix == ".json"


class TestReportDataCollector:
    """报告数据收集器测试"""

    def test_initialization(self):
        """测试初始化"""
        collector = ReportDataCollector()
        
        assert collector.collected == {}

    def test_collect_portfolio_data(self):
        """测试投资组合数据收集"""
        collector = ReportDataCollector()
        
        # 创建模拟产品
        class MockProduct:
            def __init__(self, current_amount, initial_amount, investment_type, platform):
                self.current_amount = current_amount
                self.initial_amount = initial_amount
                self.investment_type = investment_type
                self.platform = platform
        
        products = [
            MockProduct(50000, 48000, "股票", "券商A"),
            MockProduct(30000, 29000, "基金", "券商B"),
        ]
        
        result = collector.collect_portfolio_data(products)
        
        assert result["total_amount"] == 80000
        assert result["total_cost"] == 77000
        assert result["total_profit"] == 3000
        assert result["product_count"] == 2

    def test_collect_market_data(self):
        """测试市场数据收集"""
        collector = ReportDataCollector()
        indexes = {
            "上证指数": {"price": 3000, "change": 1.5},
            "深证成指": {"price": 10000, "change": -0.5},
        }
        
        result = collector.collect_market_data(indexes)
        
        assert "indexes" in result
        assert "collect_time" in result

    def test_get_collected_data(self):
        """测试获取已收集数据"""
        collector = ReportDataCollector()
        collector.collected["test"] = type('obj', (object,), {'data': {"key": "value"}})()
        
        result = collector.get_collected_data("test")
        
        assert result is not None
        assert result["key"] == "value"

    def test_clear(self):
        """测试清除数据"""
        collector = ReportDataCollector()
        collector.collected["test"] = "data"
        
        collector.clear()
        
        assert collector.collected == {}
