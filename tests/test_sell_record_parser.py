"""
Tests for sell record parser module.
"""

import tempfile
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest

from asset_lens.data.models import RiskLevel
from asset_lens.data.parser_utils import parse_date, parse_decimal
from asset_lens.data.sell_record_parser import SellRecordParser


class TestParserUtils:
    """Test parser utility functions"""

    def test_parse_decimal_valid(self):
        """Test parsing valid decimal"""
        result = parse_decimal("10000.50")
        assert result == Decimal("10000.50")

    def test_parse_decimal_with_comma(self):
        """Test parsing decimal with comma"""
        result = parse_decimal("10,000.50")
        assert result == Decimal("10000.50")

    def test_parse_decimal_empty(self):
        """Test parsing empty decimal"""
        result = parse_decimal("")
        assert result is None

    def test_parse_date_valid(self):
        """Test parsing valid date"""
        result = parse_date("2024/01/15")
        assert result == datetime(2024, 1, 15)

    def test_parse_date_with_dash(self):
        """Test parsing date with dash"""
        result = parse_date("2024-01-15")
        assert result == datetime(2024, 1, 15)

    def test_parse_date_with_dot(self):
        """Test parsing date with dot"""
        result = parse_date("2024.01.15")
        assert result == datetime(2024, 1, 15)

    def test_parse_date_empty(self):
        """Test parsing empty date"""
        result = parse_date("")
        assert result is None

    def test_parse_date_invalid(self):
        """Test parsing invalid date"""
        result = parse_date("invalid")
        assert result is None


class TestSellRecordParser:
    """Test SellRecordParser class"""

    def test_parse_boolean_valid(self):
        """Test parsing valid boolean"""
        assert SellRecordParser.parse_boolean("是") is True
        assert SellRecordParser.parse_boolean("True") is True
        assert SellRecordParser.parse_boolean("否") is False
        assert SellRecordParser.parse_boolean("") is False

    def test_parse_int_valid(self):
        """Test parsing valid int"""
        assert SellRecordParser.parse_int("328") == 328
        assert SellRecordParser.parse_int("328天") == 328
        assert SellRecordParser.parse_int("") is None

    def test_parse_risk_level(self):
        """Test parsing risk level"""
        assert SellRecordParser.parse_risk_level("低") == RiskLevel.LOW
        assert SellRecordParser.parse_risk_level("中低") == RiskLevel.MEDIUM_LOW
        assert SellRecordParser.parse_risk_level("中") == RiskLevel.MEDIUM
        assert SellRecordParser.parse_risk_level("中高") == RiskLevel.MEDIUM_HIGH
        assert SellRecordParser.parse_risk_level("高") == RiskLevel.HIGH

    def test_parse_row_valid(self):
        """Test parsing valid row"""
        row = {
            "类型": "理财",
            "名称": "测试产品",
            "风险": "中低",
            "到期时间": "",
            "滚动": "",
            "开始日期": "2024/01/01",
            "初始金额": "10000",
            "收益金额": "500",
            "收益率": "5",
            "结束日期": "2024/06/01",
            "到账日期": "2024/06/03",
            "结束到账间隔": "2天",
            "投资天数": "152",
            "年化收益": "12.5",
            "复利年化": "12.8",
            "利息发放": "",
            "交易记录": "",
            "默认顺序": "1",
        }
        result = SellRecordParser.parse_row(row)
        assert result is not None
        assert result.name == "测试产品"
        assert result.risk_level == RiskLevel.MEDIUM_LOW
        assert result.initial_amount == Decimal("10000")
        assert result.profit_amount == Decimal("500")

    def test_parse_row_empty_date(self):
        """Test parsing row with empty date"""
        row = {
            "类型": "理财",
            "名称": "测试产品",
            "结束日期": "",
        }
        result = SellRecordParser.parse_row(row)
        assert result is None

    def test_parse_csv_file(self):
        """Test parsing CSV file"""
        csv_content = """类型,名称,风险,平台A,平台C,平台B,券商A,银行A,银行I,银行B,银行C,银行D,银行E,银行F,银行G,银行H,到期时间,滚动,开始日期,初始金额,收益金额,收益率,结束日期,到账日期,结束到账间隔,投资天数,年化收益,复利年化,利息发放,交易记录,默认顺序
理财,测试产品1,中低,,,,,,,,,,,,,,2024/01/01,,2024/01/01,10000,500,5,2024/06/01,2024/06/03,2天,152,12.5,12.8,,,1
理财,测试产品2,低,,,,,,,,,,,,,,2024/02/01,,2024/02/01,20000,800,4,2024/06/01,2024/06/03,2天,120,12.0,12.3,,,2"""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "test.csv"
            csv_path.write_text(csv_content, encoding="utf-8-sig")

            records = SellRecordParser.parse_csv_file(csv_path)

            assert len(records) == 2
            assert records[0].name == "测试产品1"
            assert records[1].name == "测试产品2"

    def test_parse_csv_file_not_found(self):
        """Test parsing non-existent CSV file"""
        with pytest.raises(FileNotFoundError):
            SellRecordParser.parse_csv_file(Path("/nonexistent/path.csv"))
