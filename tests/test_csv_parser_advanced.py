"""
Additional tests for csv_parser.py to improve coverage
"""

import os
import tempfile
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from asset_lens.data.csv_parser import CSVParser, days360
from asset_lens.data.models import InvestmentProduct, InvestmentType, RiskLevel


class TestDays360Advanced:
    """Advanced tests for days360 function"""

    def test_days360_february_to_march(self):
        """Test days360 from February to March"""
        result = days360(date(2024, 2, 28), date(2024, 3, 31))
        assert result >= 30

    def test_days360_leap_year(self):
        """Test days360 in leap year"""
        result = days360(date(2024, 2, 29), date(2024, 3, 31))
        assert result >= 30

    def test_days360_cross_year(self):
        """Test days360 across year boundary"""
        result = days360(date(2023, 12, 31), date(2024, 1, 31))
        assert result >= 30

    def test_days360_multiple_years(self):
        """Test days360 across multiple years"""
        result = days360(date(2022, 1, 1), date(2024, 1, 1))
        assert result == 720

    def test_days360_start_30_end_31(self):
        """Test days360 with start day 30 and end day 31"""
        result = days360(date(2024, 1, 30), date(2024, 3, 31))
        assert result >= 60

    def test_days360_european_both_31(self):
        """Test days360 European mode with both dates on 31st"""
        result = days360(date(2024, 1, 31), date(2024, 3, 31), european=True)
        assert result >= 58


class TestParseInvestmentDays:
    """Test parse_investment_days method"""

    def test_parse_investment_days_with_tian(self):
        """Test parsing investment days with '天' suffix"""
        result = CSVParser.parse_investment_days("328天")
        assert result == 328

    def test_parse_investment_days_numeric(self):
        """Test parsing numeric investment days"""
        result = CSVParser.parse_investment_days("180")
        assert result == 180

    def test_parse_investment_days_empty(self):
        """Test parsing empty investment days"""
        result = CSVParser.parse_investment_days("")
        assert result is None

    def test_parse_investment_days_none(self):
        """Test parsing None investment days"""
        result = CSVParser.parse_investment_days(None)
        assert result is None

    def test_parse_investment_days_invalid(self):
        """Test parsing invalid investment days"""
        result = CSVParser.parse_investment_days("abc")
        assert result is None

    def test_parse_investment_days_whitespace(self):
        """Test parsing investment days with whitespace"""
        result = CSVParser.parse_investment_days("  180天  ")
        assert result == 180


class TestIsDcaProduct:
    """Test _is_dca_product method"""

    def test_is_dca_product_by_type(self):
        """Test DCA product detection by investment type"""
        product = InvestmentProduct(
            name="测试定投",
            investment_type=InvestmentType.DCA_FUND,
            risk_level=RiskLevel.MEDIUM,
        )
        assert CSVParser._is_dca_product(product) is True

    def test_is_dca_product_by_records(self):
        """Test DCA product detection by transaction records"""
        product = InvestmentProduct(
            name="测试基金",
            investment_type=InvestmentType.FUND,
            risk_level=RiskLevel.MEDIUM,
            transaction_records="2024/1/1-now:buy:1000",
        )
        assert CSVParser._is_dca_product(product) is True

    def test_is_dca_product_not_dca(self):
        """Test non-DCA product"""
        product = InvestmentProduct(
            name="测试基金",
            investment_type=InvestmentType.FUND,
            risk_level=RiskLevel.MEDIUM,
            transaction_records="2024/1/1:buy:1000;2024/6/1:sell:500",
        )
        assert CSVParser._is_dca_product(product) is False

    def test_is_dca_product_no_records(self):
        """Test product without transaction records"""
        product = InvestmentProduct(
            name="测试基金",
            investment_type=InvestmentType.FUND,
            risk_level=RiskLevel.MEDIUM,
        )
        assert CSVParser._is_dca_product(product) is False


class TestCalculateCashflowsWithDays:
    """Test _calculate_cashflows_with_days method"""

    def test_calculate_cashflows_with_days_basic(self):
        """Test basic cashflow calculation with days"""
        transactions = [
            {"date": "2024/1/15", "type": "buy", "amount": 1000},
            {"date": "2024/6/15", "type": "sell", "amount": 500},
        ]
        result = CSVParser._calculate_cashflows_with_days(
            transactions, date(2024, 1, 1), Decimal("600"), 360
        )
        assert len(result) == 3
        assert result[0]["amount"] == -1000
        assert result[1]["amount"] == 500
        assert result[2]["amount"] == 600

    def test_calculate_cashflows_with_days_no_start_date(self):
        """Test cashflow calculation without start date"""
        transactions = [
            {"date": "2024/1/15", "type": "buy", "amount": 1000},
        ]
        result = CSVParser._calculate_cashflows_with_days(
            transactions, None, Decimal("1200"), 360
        )
        assert len(result) == 0

    def test_calculate_cashflows_with_days_no_current_amount(self):
        """Test cashflow calculation without current amount"""
        transactions = [
            {"date": "2024/1/15", "type": "buy", "amount": 1000},
        ]
        result = CSVParser._calculate_cashflows_with_days(
            transactions, date(2024, 1, 1), None, 360
        )
        assert len(result) == 1


class TestCalculateCashflowsWithDaysForDca:
    """Test _calculate_cashflows_with_days_for_dca method"""

    def test_calculate_cashflows_dca_basic(self):
        """Test DCA cashflow calculation"""
        transactions = []
        result = CSVParser._calculate_cashflows_with_days_for_dca(
            transactions, date(2024, 1, 1), Decimal("12000"), 360, Decimal("10000")
        )
        assert len(result) == 2
        assert result[0]["amount"] == -10000
        assert result[0]["days"] == 0
        assert result[1]["amount"] == 12000
        assert result[1]["days"] == 360

    def test_calculate_cashflows_dca_no_start_date(self):
        """Test DCA cashflow calculation without start date"""
        transactions = []
        result = CSVParser._calculate_cashflows_with_days_for_dca(
            transactions, None, Decimal("12000"), 360, Decimal("10000")
        )
        assert len(result) == 0

    def test_calculate_cashflows_dca_no_current_amount(self):
        """Test DCA cashflow calculation without current amount"""
        transactions = []
        result = CSVParser._calculate_cashflows_with_days_for_dca(
            transactions, date(2024, 1, 1), None, 360, Decimal("10000")
        )
        assert len(result) == 1
        assert result[0]["amount"] == -10000


class TestGetExchangeRatesAdvanced:
    """Advanced tests for get_exchange_rates method"""

    def test_get_exchange_rates_from_investment_file(self):
        """Test getting exchange rates from investment file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            csv_file = temp_path / "投资产品-表格 1.csv"
            with open(csv_file, "w", encoding="utf-8-sig") as f:
                f.write("类型,名称,风险,美元汇率,港元汇率\n")
                f.write("理财,测试产品,低,7.25,0.93\n")

            usd, hkd = CSVParser.get_exchange_rates(temp_path)
            assert usd == 7.25
            assert hkd == 0.93

    def test_get_exchange_rates_from_multiple_rows(self):
        """Test getting exchange rates from multiple rows"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            csv_file = temp_path / "投资产品-表格 1.csv"
            with open(csv_file, "w", encoding="utf-8-sig") as f:
                f.write("类型,名称,风险,美元汇率,港元汇率\n")
                f.write("理财,产品1,低,,\n")
                f.write("理财,产品2,低,7.25,0.93\n")

            usd, hkd = CSVParser.get_exchange_rates(temp_path)
            assert usd == 7.25
            assert hkd == 0.93

    def test_get_exchange_rates_invalid_values(self):
        """Test getting exchange rates with invalid values"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            csv_file = temp_path / "投资产品-表格 1.csv"
            with open(csv_file, "w", encoding="utf-8-sig") as f:
                f.write("类型,名称,风险,美元汇率,港元汇率\n")
                f.write("理财,产品1,低,invalid,invalid\n")

            usd, hkd = CSVParser.get_exchange_rates(temp_path)
            # Should return default rates
            assert usd > 0
            assert hkd > 0

    def test_get_exchange_rates_out_of_range(self):
        """Test getting exchange rates with out of range values"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            csv_file = temp_path / "投资产品-表格 1.csv"
            with open(csv_file, "w", encoding="utf-8-sig") as f:
                f.write("类型,名称,风险,美元汇率,港元汇率\n")
                f.write("理财,产品1,低,100,100\n")

            usd, hkd = CSVParser.get_exchange_rates(temp_path)
            # Should return default rates since values are out of range
            assert usd > 0
            assert hkd > 0

    def test_get_exchange_rates_empty_file(self):
        """Test getting exchange rates from empty file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            csv_file = temp_path / "投资产品-表格 1.csv"
            with open(csv_file, "w", encoding="utf-8-sig") as f:
                f.write("类型,名称,风险\n")

            usd, hkd = CSVParser.get_exchange_rates(temp_path)
            assert usd > 0
            assert hkd > 0

    def test_get_exchange_rates_ws2_alternative_name(self):
        """Test getting exchange rates from worksheet 2 with alternative name"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            csv_file = temp_path / "工作表2-表格 1.csv"
            with open(csv_file, "w", encoding="utf-8-sig") as f:
                f.write("日期,美元汇率,港元汇率\n")
                f.write("2024/01/15,7.25,0.93\n")

            usd, hkd = CSVParser.get_exchange_rates(temp_path)
            assert usd == 7.25
            assert hkd == 0.93


class TestParseRowAdvanced:
    """Advanced tests for parse_row method"""

    def setup_method(self):
        """Setup method - ensure platform config is loaded"""
        from asset_lens.core.platform_loader import PlatformLoader
        from asset_lens.config import config

        config.data_mode = "sample"
        PlatformLoader.reset()
        PlatformLoader.load(data_mode="sample")

    def test_parse_row_summary_row(self):
        """Test parsing summary rows (should return None)"""
        row = {
            "类型": "指数基金",
            "名称": "小计",
            "风险": "中",
        }
        result = CSVParser.parse_row(row)
        assert result is None

    def test_parse_row_total_row(self):
        """Test parsing total rows (should return None)"""
        row = {
            "类型": "",
            "名称": "合计",
            "风险": "",
        }
        result = CSVParser.parse_row(row)
        assert result is None

    def test_parse_row_with_start_date_calculates_days(self):
        """Test that start date triggers investment days calculation"""
        row = {
            "类型": "理财",
            "名称": "测试理财",
            "风险": "低",
            "开始日期": "2024/01/01",
        }
        result = CSVParser.parse_row(row, reference_date=date(2024, 6, 30))
        assert result is not None
        assert result.investment_days is not None
        assert result.investment_days > 0

    def test_parse_row_with_initial_amount_only(self):
        """Test parsing row with only initial amount"""
        row = {
            "类型": "理财",
            "名称": "测试理财",
            "风险": "低",
            "初始金额": "10000",
        }
        result = CSVParser.parse_row(row)
        assert result is not None
        assert result.current_amount == Decimal("10000")

    def test_parse_row_with_invalid_default_order(self):
        """Test parsing row with invalid default order"""
        row = {
            "类型": "基金",
            "名称": "测试基金",
            "风险": "中",
            "默认顺序": "invalid",
        }
        result = CSVParser.parse_row(row)
        assert result is not None
        assert result.default_order is None

    def test_parse_row_exception_handling(self):
        """Test parse_row exception handling"""
        row = {
            "类型": "指数基金",
            "名称": "测试产品",
            "风险": "中",
        }
        result = CSVParser.parse_row(row)
        assert result is not None


class TestCalculateIrrForProducts:
    """Test _calculate_irr_for_products method"""

    def test_calculate_irr_basic(self):
        """Test basic IRR calculation"""
        products = [
            InvestmentProduct(
                name="测试产品",
                investment_type=InvestmentType.WEALTH,
                risk_level=RiskLevel.LOW,
                initial_amount=Decimal("10000"),
                current_amount=Decimal("10500"),
                investment_days=180,
            )
        ]
        result = CSVParser._calculate_irr_for_products(products)
        assert len(result) == 1
        assert result[0].return_rate is not None

    def test_calculate_irr_with_transactions(self):
        """Test IRR calculation with transactions"""
        products = [
            InvestmentProduct(
                name="测试产品",
                investment_type=InvestmentType.FUND,
                risk_level=RiskLevel.MEDIUM,
                initial_amount=Decimal("10000"),
                current_amount=Decimal("12000"),
                investment_days=360,
                transaction_records="2024/1/1:buy:5000;2024/6/1:buy:5000",
                start_date=date(2024, 1, 1),
            )
        ]
        result = CSVParser._calculate_irr_for_products(products)
        assert len(result) == 1

    def test_calculate_irr_bond_product(self):
        """Test IRR calculation for bond product"""
        products = [
            InvestmentProduct(
                name="测试债券",
                investment_type=InvestmentType.BOND,
                risk_level=RiskLevel.LOW,
                initial_amount=Decimal("10000"),
                current_amount=Decimal("10200"),
                interest_payment=Decimal("300"),
                investment_days=180,
            )
        ]
        result = CSVParser._calculate_irr_for_products(products)
        assert len(result) == 1
        assert result[0].annual_return is not None

    def test_calculate_irr_dca_product(self):
        """Test IRR calculation for DCA product"""
        products = [
            InvestmentProduct(
                name="测试定投",
                investment_type=InvestmentType.DCA_FUND,
                risk_level=RiskLevel.MEDIUM,
                initial_amount=Decimal("12000"),
                current_amount=Decimal("15000"),
                investment_days=360,
                start_date=date(2024, 1, 1),
            )
        ]
        result = CSVParser._calculate_irr_for_products(products)
        assert len(result) == 1

    def test_calculate_irr_short_term(self):
        """Test IRR calculation for short term investment"""
        products = [
            InvestmentProduct(
                name="短期理财",
                investment_type=InvestmentType.WEALTH,
                risk_level=RiskLevel.LOW,
                initial_amount=Decimal("10000"),
                current_amount=Decimal("10100"),
                investment_days=90,
                return_rate=Decimal("1"),
            )
        ]
        result = CSVParser._calculate_irr_for_products(products)
        assert len(result) == 1
        assert result[0].annual_return is not None


class TestLoadDataFromDir:
    """Test load_data_from_dir method"""

    def test_load_data_from_dir_basic(self):
        """Test loading data from directory"""
        csv_content = "类型,名称,风险\n指数基金,测试产品,中"

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            csv_file = temp_path / "投资产品-表格 1.csv"

            with open(csv_file, "w", encoding="utf-8-sig") as f:
                f.write(csv_content)

            result = CSVParser.load_data_from_dir(temp_path)
            assert len(result) == 1
            assert result[0].name == "测试产品"

    def test_load_data_from_dir_with_date(self):
        """Test loading data from directory with date suffix"""
        csv_content = "类型,名称,风险\n指数基金,测试产品,中"

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            csv_file = temp_path / "投资产品-表格 1.csv"

            with open(csv_file, "w", encoding="utf-8-sig") as f:
                f.write(csv_content)

            result = CSVParser.load_data_from_dir(temp_path)
            assert len(result) == 1

    def test_load_data_from_dir_not_found(self):
        """Test loading data from non-existent directory"""
        with pytest.raises(FileNotFoundError):
            CSVParser.load_data_from_dir(Path("/nonexistent/directory"))

    def test_load_data_from_dir_no_csv(self):
        """Test loading data from directory without CSV files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            with pytest.raises(FileNotFoundError):
                CSVParser.load_data_from_dir(temp_path)


class TestParseTransactionRecordsAdvanced:
    """Advanced tests for _parse_transaction_records method"""

    def test_parse_transaction_records_multiple_semicolon(self):
        """Test parsing multiple records with semicolon"""
        result = CSVParser._parse_transaction_records(
            "2024/1/15:buy:1000; 2024/6/15:sell:500; 2024/12/15:buy:2000"
        )
        assert len(result) == 3

    def test_parse_transaction_records_invalid_amount(self):
        """Test parsing records with invalid amount"""
        result = CSVParser._parse_transaction_records("2024/1/15:buy:invalid")
        assert len(result) == 0

    def test_parse_transaction_records_partial_record(self):
        """Test parsing partial records"""
        result = CSVParser._parse_transaction_records("2024/1/15:buy")
        assert len(result) == 0

    def test_parse_transaction_records_empty_parts(self):
        """Test parsing records with empty parts"""
        result = CSVParser._parse_transaction_records(";;")
        assert len(result) == 0


class TestLoadDataRealMode:
    """Test load_data method in real mode"""

    def test_load_data_real_mode_no_data_dir(self):
        """Test loading data in real mode without data directory"""
        with patch('asset_lens.data.csv_parser.config') as mock_config:
            mock_config.is_real_mode = False
            mock_config.project_root = Path("/nonexistent")
            mock_config.data_path = Path("/nonexistent")

            with pytest.raises(FileNotFoundError):
                CSVParser.load_data()


class TestParseDcaTransactions:
    """Test _parse_dca_transactions method"""

    def test_parse_dca_transactions_basic(self):
        """Test parsing DCA transactions"""
        result = CSVParser._parse_dca_transactions(
            "2024/1/1-now:buy:1000",
            InvestmentType.DCA_FUND,
            datetime(2024, 6, 30),
            "测试定投"
        )
        assert len(result) > 0
        assert all(t["type"] == "buy" for t in result)

    def test_parse_dca_transactions_with_reference_date(self):
        """Test parsing DCA transactions with reference date"""
        result = CSVParser._parse_dca_transactions(
            "2024/1/1-2024/6/30:buy:1000",
            InvestmentType.DCA_FUND,
            datetime(2024, 6, 30),
            "测试定投"
        )
        assert len(result) > 0
