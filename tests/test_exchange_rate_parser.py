"""
Tests for exchange rate parser module.
"""

import pytest
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import tempfile
import os

from asset_lens.data.exchange_rate_parser import ExchangeRateParser
from asset_lens.data.models import ExchangeRateHistory


class TestExchangeRateParser:
    """Test ExchangeRateParser class"""

    def test_parse_decimal_valid(self):
        """Test parsing valid decimal"""
        result = ExchangeRateParser.parse_decimal("7.25")
        assert result == Decimal("7.25")

    def test_parse_decimal_with_comma(self):
        """Test parsing decimal with comma"""
        result = ExchangeRateParser.parse_decimal("7,250.00")
        assert result == Decimal("7250.00")

    def test_parse_decimal_empty(self):
        """Test parsing empty decimal"""
        result = ExchangeRateParser.parse_decimal("")
        assert result is None

    def test_parse_decimal_whitespace(self):
        """Test parsing whitespace decimal"""
        result = ExchangeRateParser.parse_decimal("   ")
        assert result is None

    def test_parse_decimal_invalid(self):
        """Test parsing invalid decimal"""
        result = ExchangeRateParser.parse_decimal("invalid")
        assert result is None

    def test_parse_date_valid(self):
        """Test parsing valid date"""
        result = ExchangeRateParser.parse_date("2024.01.15")
        assert result == datetime(2024, 1, 15)

    def test_parse_date_with_slash(self):
        """Test parsing date with slash"""
        result = ExchangeRateParser.parse_date("2024/01/15")
        assert result == datetime(2024, 1, 15)

    def test_parse_date_with_dash(self):
        """Test parsing date with dash"""
        result = ExchangeRateParser.parse_date("2024-01-15")
        assert result == datetime(2024, 1, 15)

    def test_parse_date_with_time(self):
        """Test parsing date with time"""
        result = ExchangeRateParser.parse_date("2024.01.15 10:30:00")
        assert result == datetime(2024, 1, 15, 10, 30, 0)

    def test_parse_date_empty(self):
        """Test parsing empty date"""
        result = ExchangeRateParser.parse_date("")
        assert result is None

    def test_parse_date_invalid(self):
        """Test parsing invalid date"""
        result = ExchangeRateParser.parse_date("invalid")
        assert result is None

    def test_parse_row_valid(self):
        """Test parsing valid row"""
        row = {
            "日期": "2024.01.15",
            "美元汇率": "7.25",
            "港元汇率": "0.92",
        }
        result = ExchangeRateParser.parse_row(row)
        
        assert result is not None
        assert result.rate_date == datetime(2024, 1, 15)
        assert result.usd_rate == Decimal("7.25")
        assert result.hkd_rate == Decimal("0.92")

    def test_parse_row_missing_date(self):
        """Test parsing row with missing date"""
        row = {
            "日期": "",
            "美元汇率": "7.25",
            "港元汇率": "0.92",
        }
        result = ExchangeRateParser.parse_row(row)
        assert result is None

    def test_parse_row_missing_rates(self):
        """Test parsing row with missing rates"""
        row = {
            "日期": "2024.01.15",
            "美元汇率": "",
            "港元汇率": "",
        }
        result = ExchangeRateParser.parse_row(row)
        
        assert result is not None
        assert result.rate_date == datetime(2024, 1, 15)
        assert result.usd_rate is None
        assert result.hkd_rate is None

    def test_parse_csv_file(self):
        """Test parsing CSV file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "test_exchange_rate.csv"
            
            with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
                f.write("日期,美元汇率,港元汇率\n")
                f.write("2024.01.15,7.25,0.92\n")
                f.write("2024.01.16,7.26,0.93\n")
                f.write("2024.01.17,7.27,0.94\n")
            
            result = ExchangeRateParser.parse_csv_file(csv_path)
            
            assert len(result) == 3
            assert result[0].rate_date == datetime(2024, 1, 15)
            assert result[0].usd_rate == Decimal("7.25")
            assert result[1].rate_date == datetime(2024, 1, 16)

    def test_parse_csv_file_not_found(self):
        """Test parsing non-existent CSV file"""
        with pytest.raises(FileNotFoundError):
            ExchangeRateParser.parse_csv_file(Path("/nonexistent/file.csv"))

    def test_parse_csv_file_with_invalid_rows(self):
        """Test parsing CSV file with invalid rows"""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "test_exchange_rate.csv"
            
            with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
                f.write("日期,美元汇率,港元汇率\n")
                f.write("2024.01.15,7.25,0.92\n")
                f.write("invalid,7.26,0.93\n")  # Invalid date
                f.write("2024.01.17,7.27,0.94\n")
            
            result = ExchangeRateParser.parse_csv_file(csv_path)
            
            # Should skip invalid row
            assert len(result) == 2
