"""
Tests for asset summary parser module.
"""

import tempfile
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest

from asset_lens.data.asset_summary_parser import AssetSummaryParser
from asset_lens.data.models import AssetSummary
from asset_lens.data.parser_utils import parse_date, parse_decimal


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

    def test_parse_decimal_whitespace(self):
        """Test parsing whitespace decimal"""
        result = parse_decimal("   ")
        assert result is None

    def test_parse_decimal_invalid(self):
        """Test parsing invalid decimal"""
        result = parse_decimal("invalid")
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

    def test_parse_date_with_time(self):
        """Test parsing date with time"""
        result = parse_date("2024/01/15 10:30:00")
        assert result == datetime(2024, 1, 15, 10, 30, 0)

    def test_parse_date_empty(self):
        """Test parsing empty date"""
        result = parse_date("")
        assert result is None

    def test_parse_date_invalid(self):
        """Test parsing invalid date"""
        result = parse_date("invalid")
        assert result is None


class TestAssetSummaryParser:
    """Test AssetSummaryParser class"""

    def test_parse_row_valid(self):
        """Test parsing valid row"""
        row = {
            "日期": "2024/01/15",
            "平台A": "10000",
            "平台C": "20000",
            "平台B": "5000",
            "券商A": "30000",
            "银行A": "15000",
            "银行I": "10000",
            "银行B": "8000",
            "银行C": "12000",
            "银行D": "9000",
            "银行E": "11000",
            "银行F": "7000",
            "银行G": "6000",
            "银行H": "5000",
            "信用卡": "-2000",
            "京东白条": "-1000",
            "抖音月付": "-500",
            "多多后付": "-300",
            "总金额": "150000",
            "美元汇率": "7.25",
            "港元汇率": "0.93",
            "黄金": "50000",
            "兑换美元": "10000",
            "兑换港元": "5000",
            "兑换黄金": "2000",
            "上证指数": "3000",
            "沪深300": "3500",
            "中证500": "5500",
            "纳指100": "18000",
            "标普500": "5000",
            "恐慌VXX": "15",
            "美联基利率": "5.25",
            "房产总价": "1000000",
            "收益率": "5.5",
        }
        result = AssetSummaryParser.parse_row(row)

        assert result is not None
        assert result.summary_date == datetime(2024, 1, 15)
        assert result.total_amount == Decimal("150000")

    def test_parse_row_missing_date(self):
        """Test parsing row with missing date"""
        row = {
            "平台A": "10000",
        }
        result = AssetSummaryParser.parse_row(row)
        assert result is None

    def test_parse_row_partial(self):
        """Test parsing partial row"""
        row = {
            "日期": "2024/01/15",
            "平台A": "10000",
        }
        result = AssetSummaryParser.parse_row(row)

        assert result is not None
        assert result.summary_date == datetime(2024, 1, 15)

    def test_parse_csv_file(self):
        """Test parsing CSV file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "test_asset_summary.csv"

            with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
                f.write("日期,平台A,平台C,平台B,总金额\n")
                f.write("2024/01/15,10000,20000,5000,35000\n")
                f.write("2024/01/16,11000,21000,5500,37500\n")

            result = AssetSummaryParser.parse_csv_file(csv_path)

            assert len(result) == 2
            assert result[0].summary_date == datetime(2024, 1, 15)
            assert result[1].summary_date == datetime(2024, 1, 16)

    def test_parse_csv_file_not_found(self):
        """Test parsing non-existent CSV file"""
        with pytest.raises(FileNotFoundError):
            AssetSummaryParser.parse_csv_file(Path("/nonexistent/file.csv"))

    def test_parse_csv_file_skip_invalid_rows(self):
        """Test parsing CSV file skips invalid rows"""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "test_asset_summary.csv"

            with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
                f.write("日期,平台A,平台C,平台B,总金额\n")
                f.write("2024/01/15,10000,20000,5000,35000\n")
                f.write("invalid,11000,21000,5500,37500\n")
                f.write("2024/01/17,12000,22000,6000,40000\n")

            result = AssetSummaryParser.parse_csv_file(csv_path)

            assert len(result) == 2


class TestAssetSummaryModel:
    """Test AssetSummary model"""

    def test_asset_summary_creation(self):
        """Test creating AssetSummary"""
        summary = AssetSummary(
            summary_date=datetime(2024, 1, 15),
            platform_amounts={"platform_a": Decimal("10000")},
            total_amount=Decimal("150000"),
        )

        assert summary.summary_date == datetime(2024, 1, 15)
        assert summary.get_amount("platform_a") == Decimal("10000")
        assert summary.total_amount == Decimal("150000")

    def test_asset_summary_optional_fields(self):
        """Test AssetSummary with optional fields"""
        summary = AssetSummary(
            summary_date=datetime(2024, 1, 15),
        )

        assert summary.summary_date == datetime(2024, 1, 15)
        assert summary.total_platform_amount == Decimal("0")
        assert summary.total_amount == Decimal("0")
