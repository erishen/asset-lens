"""
Tests for sell record parser module.
"""

import pytest
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import tempfile

from asset_lens.data.sell_record_parser import SellRecordParser
from asset_lens.data.models import SellRecord, RiskLevel


class TestSellRecordParser:
    """Test SellRecordParser class"""

    def test_parse_decimal_valid(self):
        """Test parsing valid decimal"""
        result = SellRecordParser.parse_decimal("10000.50")
        assert result == Decimal("10000.50")

    def test_parse_decimal_with_comma(self):
        """Test parsing decimal with comma"""
        result = SellRecordParser.parse_decimal("10,000.50")
        assert result == Decimal("10000.50")

    def test_parse_decimal_empty(self):
        """Test parsing empty decimal"""
        result = SellRecordParser.parse_decimal("")
        assert result is None

    def test_parse_date_valid(self):
        """Test parsing valid date"""
        result = SellRecordParser.parse_date("2024/01/15")
        assert result == datetime(2024, 1, 15)

    def test_parse_date_with_dash(self):
        """Test parsing date with dash"""
        result = SellRecordParser.parse_date("2024-01-15")
        assert result == datetime(2024, 1, 15)

    def test_parse_date_with_dot(self):
        """Test parsing date with dot"""
        result = SellRecordParser.parse_date("2024.01.15")
        assert result == datetime(2024, 1, 15)

    def test_parse_date_empty(self):
        """Test parsing empty date"""
        result = SellRecordParser.parse_date("")
        assert result is None

    def test_parse_date_invalid(self):
        """Test parsing invalid date"""
        result = SellRecordParser.parse_date("invalid")
        assert result is None

    def test_parse_boolean_true(self):
        """Test parsing true boolean"""
        assert SellRecordParser.parse_boolean("是") is True
        assert SellRecordParser.parse_boolean("true") is True
        assert SellRecordParser.parse_boolean("True") is True
        assert SellRecordParser.parse_boolean("yes") is True
        assert SellRecordParser.parse_boolean("1") is True

    def test_parse_boolean_false(self):
        """Test parsing false boolean"""
        assert SellRecordParser.parse_boolean("否") is False
        assert SellRecordParser.parse_boolean("false") is False
        assert SellRecordParser.parse_boolean("") is False

    def test_parse_int_valid(self):
        """Test parsing valid integer"""
        result = SellRecordParser.parse_int("365")
        assert result == 365

    def test_parse_int_with_suffix(self):
        """Test parsing integer with suffix"""
        result = SellRecordParser.parse_int("365天")
        assert result == 365

    def test_parse_int_empty(self):
        """Test parsing empty integer"""
        result = SellRecordParser.parse_int("")
        assert result is None

    def test_parse_int_invalid(self):
        """Test parsing invalid integer"""
        result = SellRecordParser.parse_int("invalid")
        assert result is None

    def test_parse_risk_level(self):
        """Test parsing risk level"""
        assert SellRecordParser.parse_risk_level("高") == RiskLevel.HIGH
        assert SellRecordParser.parse_risk_level("高风险") == RiskLevel.HIGH
        assert SellRecordParser.parse_risk_level("中") == RiskLevel.MEDIUM
        assert SellRecordParser.parse_risk_level("低") == RiskLevel.LOW
        assert SellRecordParser.parse_risk_level("低风险") == RiskLevel.LOW
        assert SellRecordParser.parse_risk_level("中低") == RiskLevel.MEDIUM_LOW
        assert SellRecordParser.parse_risk_level("中高") == RiskLevel.MEDIUM_HIGH
        assert SellRecordParser.parse_risk_level("") == RiskLevel.MEDIUM  # Default

    def test_parse_row_valid(self):
        """Test parsing valid row"""
        row = {
            "名称": "Test Product",
            "风险": "高",
            "结束日期": "2024/01/15",
            "初始金额": "10000",
            "收益金额": "1000",
            "收益率": "10%",
            "投资天数": "365天",
            "年化收益": "10%",
        }
        result = SellRecordParser.parse_row(row)
        
        assert result is not None
        assert result.name == "Test Product"
        assert result.risk_level == RiskLevel.HIGH

    def test_parse_row_missing_name(self):
        """Test parsing row with missing name"""
        row = {
            "名称": "",
            "风险": "高",
            "结束日期": "2024/01/15",
        }
        result = SellRecordParser.parse_row(row)
        # Name can be empty, but sell_date is required
        assert result is not None

    def test_parse_csv_file(self):
        """Test parsing CSV file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "test_sell_records.csv"
            
            # Note: parse_csv_file skips first line (header) and uses predefined fieldnames (31 fields)
            # Actual CSV format: first row is header with date as first field, data rows start with type
            # Header: 日期,名称,风险,... (31 fields)
            # Data: 类型,名称,风险,... (31 fields)
            header = "2025.5.17,名称,风险,微信,中金,支付宝,富途,招商,港招,交通,浦发,建设,中信,民生,工商,中银,到期时间,滚动,开始日期,初始金额,收益金额,收益率,结束日期,到账日期,结束到账间隔,投资天数,年化收益,复利年化,利息发放,交易记录,默认顺序"
            # Data rows (31 values each, matching actual CSV format)
            # Fields: 类型,名称,风险,微信,中金,支付宝,富途,招商,港招,交通,浦发,建设,中信,民生,工商,中银,到期时间,滚动,开始日期,初始金额,收益金额,收益率,结束日期,到账日期,结束到账间隔,投资天数,年化收益,复利年化,利息发放,交易记录,默认顺序
            data1 = "理财,Product A,高,,,,,,,,,,,,,,可赎,,2024/01/15,10000,1000,10%,2024/01/15,2024/01/16,1天,365天,10%,10%,,,1"
            data2 = "理财,Product B,低,,,,,,,,,,,,,,可赎,,2024/02/20,20000,1000,5%,2024/02/20,2024/02/21,1天,180天,10%,10%,,,1"
            
            with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
                f.write(header + "\n")  # Header line (will be skipped)
                f.write(data1 + "\n")
                f.write(data2 + "\n")
            
            result = SellRecordParser.parse_csv_file(csv_path)
            
            assert len(result) == 2
            assert result[0].name == "Product A"
            assert result[1].name == "Product B"

    def test_parse_csv_file_not_found(self):
        """Test parsing non-existent CSV file"""
        with pytest.raises(Exception):
            SellRecordParser.parse_csv_file(Path("/nonexistent/file.csv"))

    def test_parse_csv_file_skip_empty_rows(self):
        """Test parsing CSV file skips empty rows"""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "test_sell_records.csv"
            
            # Note: parse_csv_file skips first line (header) and uses predefined fieldnames (31 fields)
            header = "2025.5.17,名称,风险,微信,中金,支付宝,富途,招商,港招,交通,浦发,建设,中信,民生,工商,中银,到期时间,滚动,开始日期,初始金额,收益金额,收益率,结束日期,到账日期,结束到账间隔,投资天数,年化收益,复利年化,利息发放,交易记录,默认顺序"
            # Data rows (31 values each)
            data1 = "理财,Product A,高,,,,,,,,,,,,,,可赎,,2024/01/15,10000,1000,10%,2024/01/15,2024/01/16,1天,365天,10%,10%,,,1"
            data2 = "理财,,低,,,,,,,,,,,,,,可赎,,2024/02/20,20000,1000,5%,2024/02/20,2024/02/21,1天,180天,10%,10%,,,1"  # Empty name
            data3 = "理财,Product C,低,,,,,,,,,,,,,,可赎,,2024/03/25,30000,1500,5%,2024/03/25,2024/03/26,1天,90天,20%,20%,,,1"
            
            with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
                f.write(header + "\n")  # Header line (will be skipped)
                f.write(data1 + "\n")
                f.write(data2 + "\n")
                f.write(data3 + "\n")
            
            result = SellRecordParser.parse_csv_file(csv_path)
            
            # Should skip row with empty name
            assert len(result) == 2
