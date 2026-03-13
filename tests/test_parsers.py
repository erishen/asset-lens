"""
Tests for Data Parsers Module
"""

import pytest
from datetime import date, datetime
from asset_lens.data.parsers import DataParser, DateParser, InvestmentTypeParser


class TestDateParser:
    """DateParser 测试"""

    def test_parse_standard_format(self):
        """测试标准日期格式"""
        result = DateParser.parse("2024-01-15")
        
        assert result.success is True
        assert result.value == date(2024, 1, 15)

    def test_parse_slash_format(self):
        """测试斜杠日期格式"""
        result = DateParser.parse("2024/01/15")
        
        assert result.success is True
        assert result.value == date(2024, 1, 15)

    def test_parse_chinese_format(self):
        """测试中文日期格式"""
        result = DateParser.parse("2024年1月15日")
        
        assert result.success is True
        assert result.value == date(2024, 1, 15)

    def test_parse_invalid_format(self):
        """测试无效日期格式"""
        result = DateParser.parse("invalid-date")
        
        assert result.success is False
        assert result.error is not None

    def test_parse_empty_string(self):
        """测试空字符串"""
        result = DateParser.parse("")
        
        assert result.success is False

    def test_parse_none(self):
        """测试 None 值"""
        result = DateParser.parse(None)
        
        assert result.success is False

    def test_parse_range(self):
        """测试日期范围解析"""
        result = DateParser.parse_range("2024-01-01", "2024-12-31")
        
        assert result.success is True
        assert result.value == (date(2024, 1, 1), date(2024, 12, 31))

    def test_format_date(self):
        """测试日期格式化"""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        
        assert DateParser.format_date(dt) == "2024-01-15"
        assert DateParser.format_date(dt, "%Y/%m/%d") == "2024/01/15"


class TestInvestmentTypeParser:
    """InvestmentTypeParser 测试"""

    def test_parse_stock(self):
        """测试股票类型"""
        result = InvestmentTypeParser.parse("股票")
        
        assert result.success is True
        assert result.value == "stock"

    def test_parse_fund(self):
        """测试基金类型"""
        result = InvestmentTypeParser.parse("基金")
        
        assert result.success is True
        assert result.value == "fund"

    def test_parse_bond(self):
        """测试债券类型"""
        result = InvestmentTypeParser.parse("债券")
        
        assert result.success is True
        assert result.value == "bond"

    def test_parse_unknown_type(self):
        """测试未知类型"""
        result = InvestmentTypeParser.parse("未知类型")
        
        assert result.success is True
        assert result.value == "other"

    def test_parse_empty_string(self):
        """测试空字符串"""
        result = InvestmentTypeParser.parse("")
        
        assert result.success is False

    def test_parse_none(self):
        """测试 None 值"""
        result = InvestmentTypeParser.parse(None)
        
        assert result.success is False

    def test_get_display_name(self):
        """测试获取显示名称"""
        assert InvestmentTypeParser.get_display_name("stock") == "股票"
        assert InvestmentTypeParser.get_display_name("fund") == "基金"
        assert InvestmentTypeParser.get_display_name("unknown") == "unknown"


class TestDataParser:
    """DataParser 测试"""

    def test_initialization(self):
        """测试初始化"""
        parser = DataParser()
        
        assert parser.date_parser is not None
        assert parser.type_parser is not None

    def test_parse_csv_row(self):
        """测试 CSV 行解析"""
        parser = DataParser()
        row = {
            "date": "2024-01-15",
            "type": "股票",
            "amount": "10000.50",
            "name": "测试产品",
        }
        
        result = parser.parse_csv_row(row)
        
        assert result["date"] == date(2024, 1, 15)
        assert result["investment_type"] == "stock"
        assert result["amount"] == 10000.50
        assert result["name"] == "测试产品"

    def test_parse_csv_row_with_chinese_amount(self):
        """测试带中文符号的金额"""
        parser = DataParser()
        row = {
            "amount": "¥10,000.50",
        }
        
        result = parser.parse_csv_row(row)
        
        assert result["amount"] == 10000.50

    def test_safe_float(self):
        """测试安全浮点数转换"""
        assert DataParser.safe_float("100.50") == 100.50
        assert DataParser.safe_float("1,000.50") == 1000.50
        assert DataParser.safe_float("¥1,000.50") == 1000.50
        assert DataParser.safe_float("invalid") == 0.0
        assert DataParser.safe_float(None) == 0.0
        assert DataParser.safe_float("invalid", default=-1.0) == -1.0

    def test_safe_int(self):
        """测试安全整数转换"""
        assert DataParser.safe_int("100") == 100
        assert DataParser.safe_int("1,000") == 1000
        assert DataParser.safe_int("invalid") == 0
        assert DataParser.safe_int(None) == 0
        assert DataParser.safe_int("invalid", default=-1) == -1

    def test_parse_transaction(self):
        """测试交易记录解析"""
        parser = DataParser()
        row = {
            "date": "2024-01-15",
            "type": "基金",
            "amount": "50000",
            "initial_amount": "48000",
        }
        
        result = parser.parse_transaction(row)
        
        assert result["date"] == date(2024, 1, 15)
        assert result["investment_type"] == "fund"
        assert result["amount"] == 50000.0
        assert result["initial_amount"] == 48000.0
