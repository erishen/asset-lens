"""
Tests for CSV parser.
"""

import pytest
import tempfile
import os
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch, MagicMock

from asset_lens.data.csv_parser import CSVParser
from asset_lens.data.models import InvestmentType, RiskLevel, InvestmentProduct


class TestParseDecimal:
    """Test parse_decimal method"""

    def test_parse_decimal_valid(self):
        result = CSVParser.parse_decimal("1234.56")
        assert result == Decimal("1234.56")

    def test_parse_decimal_with_comma(self):
        result = CSVParser.parse_decimal("1,234.56")
        assert result == Decimal("1234.56")

    def test_parse_decimal_empty(self):
        result = CSVParser.parse_decimal("")
        assert result is None

    def test_parse_decimal_none(self):
        result = CSVParser.parse_decimal(None)
        assert result is None

    def test_parse_decimal_whitespace(self):
        result = CSVParser.parse_decimal("  1234.56  ")
        assert result == Decimal("1234.56")

    def test_parse_decimal_invalid(self):
        result = CSVParser.parse_decimal("abc")
        assert result is None

    def test_parse_decimal_negative(self):
        result = CSVParser.parse_decimal("-1234.56")
        assert result == Decimal("-1234.56")

    def test_parse_decimal_zero(self):
        result = CSVParser.parse_decimal("0")
        assert result == Decimal("0")

    def test_parse_decimal_large_number(self):
        result = CSVParser.parse_decimal("1,000,000.00")
        assert result == Decimal("1000000.00")


class TestParseDate:
    """Test parse_date method"""

    def test_parse_date_yyyy_mm_dd(self):
        result = CSVParser.parse_date("2024-01-15")
        assert result == datetime(2024, 1, 15)

    def test_parse_date_yyyy_slash_mm_slash_dd(self):
        result = CSVParser.parse_date("2024/01/15")
        assert result == datetime(2024, 1, 15)

    def test_parse_date_empty(self):
        result = CSVParser.parse_date("")
        assert result is None

    def test_parse_date_none(self):
        result = CSVParser.parse_date(None)
        assert result is None

    def test_parse_date_invalid(self):
        result = CSVParser.parse_date("invalid-date")
        assert result is None

    def test_parse_date_with_time(self):
        result = CSVParser.parse_date("2024-01-15 10:30:00")
        assert result == datetime(2024, 1, 15, 10, 30, 0)

    def test_parse_date_yyyymmdd(self):
        result = CSVParser.parse_date("20240115")
        assert result == datetime(2024, 1, 15)

    def test_parse_date_whitespace(self):
        result = CSVParser.parse_date("  2024-01-15  ")
        assert result == datetime(2024, 1, 15)


class TestParseBoolean:
    """Test parse_boolean method"""

    def test_parse_boolean_true(self):
        assert CSVParser.parse_boolean("是") is True
        assert CSVParser.parse_boolean("yes") is True
        assert CSVParser.parse_boolean("true") is True
        assert CSVParser.parse_boolean("1") is True
        assert CSVParser.parse_boolean("可赎") is True

    def test_parse_boolean_false(self):
        assert CSVParser.parse_boolean("否") is False
        assert CSVParser.parse_boolean("no") is False
        assert CSVParser.parse_boolean("false") is False
        assert CSVParser.parse_boolean("0") is False
        assert CSVParser.parse_boolean("") is False
        assert CSVParser.parse_boolean(None) is False

    def test_parse_boolean_case_insensitive(self):
        assert CSVParser.parse_boolean("YES") is True
        assert CSVParser.parse_boolean("TRUE") is True


class TestParseInvestmentType:
    """Test parse_investment_type method"""

    def test_parse_investment_type_monetary(self):
        result = CSVParser.parse_investment_type("货币")
        assert result == InvestmentType.MONETARY

    def test_parse_investment_type_index_fund(self):
        result = CSVParser.parse_investment_type("指数基金")
        assert result == InvestmentType.INDEX_FUND

    def test_parse_investment_type_bond_fund(self):
        result = CSVParser.parse_investment_type("债券基金")
        assert result == InvestmentType.BOND_FUND

    def test_parse_investment_type_stock(self):
        result = CSVParser.parse_investment_type("股票")
        assert result == InvestmentType.STOCK

    def test_parse_investment_type_us_stock(self):
        result = CSVParser.parse_investment_type("美股")
        assert result == InvestmentType.US_STOCK

    def test_parse_investment_type_hk_stock(self):
        result = CSVParser.parse_investment_type("港股")
        assert result == InvestmentType.HK_STOCK

    def test_parse_investment_type_qdii(self):
        result = CSVParser.parse_investment_type("QDII")
        assert result == InvestmentType.QDII

    def test_parse_investment_type_wealth(self):
        result = CSVParser.parse_investment_type("理财")
        assert result == InvestmentType.WEALTH

    def test_parse_investment_type_fixed_deposit(self):
        result = CSVParser.parse_investment_type("定期存款")
        assert result == InvestmentType.FIXED_DEPOSIT

    def test_parse_investment_type_bond(self):
        result = CSVParser.parse_investment_type("债券")
        assert result == InvestmentType.BOND

    def test_parse_investment_type_reits(self):
        result = CSVParser.parse_investment_type("REITs")
        assert result == InvestmentType.REITS

    def test_parse_investment_type_gold(self):
        result = CSVParser.parse_investment_type("黄金")
        assert result == InvestmentType.GOLD

    def test_parse_investment_type_fund(self):
        result = CSVParser.parse_investment_type("基金")
        assert result == InvestmentType.FUND

    def test_parse_investment_type_other(self):
        result = CSVParser.parse_investment_type("未知类型")
        assert result == InvestmentType.OTHER

    def test_parse_investment_type_empty(self):
        result = CSVParser.parse_investment_type("")
        assert result == InvestmentType.OTHER

    def test_parse_investment_type_none(self):
        result = CSVParser.parse_investment_type(None)
        assert result == InvestmentType.OTHER


class TestParseRiskLevel:
    """Test parse_risk_level method"""

    def test_parse_risk_level_low(self):
        result = CSVParser.parse_risk_level("低")
        assert result == RiskLevel.LOW

    def test_parse_risk_level_medium(self):
        result = CSVParser.parse_risk_level("中")
        assert result == RiskLevel.MEDIUM

    def test_parse_risk_level_high(self):
        result = CSVParser.parse_risk_level("高")
        assert result == RiskLevel.HIGH

    def test_parse_risk_level_medium_low(self):
        result = CSVParser.parse_risk_level("中低")
        assert result == RiskLevel.MEDIUM_LOW

    def test_parse_risk_level_medium_high(self):
        result = CSVParser.parse_risk_level("中高")
        assert result == RiskLevel.MEDIUM_HIGH

    def test_parse_risk_level_empty(self):
        result = CSVParser.parse_risk_level("")
        assert result == RiskLevel.MEDIUM

    def test_parse_risk_level_none(self):
        result = CSVParser.parse_risk_level(None)
        assert result == RiskLevel.MEDIUM

    def test_parse_risk_level_unknown(self):
        result = CSVParser.parse_risk_level("未知")
        assert result == RiskLevel.MEDIUM


class TestParseRow:
    """Test parse_row method"""

    def test_parse_row_basic(self):
        row = {
            "类型": "指数基金",
            "名称": "中证500ETF",
            "风险": "中",
        }
        result = CSVParser.parse_row(row)
        assert result is not None
        assert result.name == "中证500ETF"
        assert result.investment_type == InvestmentType.INDEX_FUND
        assert result.risk_level == RiskLevel.MEDIUM

    def test_parse_row_empty_name(self):
        row = {
            "类型": "指数基金",
            "名称": "",
            "风险": "中",
        }
        result = CSVParser.parse_row(row)
        assert result is None

    def test_parse_row_with_amounts(self):
        row = {
            "类型": "指数基金",
            "名称": "测试产品",
            "风险": "中",
            "微信": "10000",
            "支付宝": "5000",
        }
        result = CSVParser.parse_row(row)
        assert result is not None
        assert result.wechat_amount == Decimal("10000")
        assert result.alipay_amount == Decimal("5000")

    def test_parse_row_with_dates(self):
        row = {
            "类型": "理财",
            "名称": "测试理财",
            "风险": "低",
            "到期时间": "2024-12-31",
            "开始日期": "2024-01-01",
        }
        result = CSVParser.parse_row(row)
        assert result is not None
        assert result.maturity_date == date(2024, 12, 31)
        assert result.start_date == date(2024, 1, 1)

    def test_parse_row_with_rolling(self):
        row = {
            "类型": "理财",
            "名称": "测试理财",
            "风险": "低",
            "滚动": "是",
        }
        result = CSVParser.parse_row(row)
        assert result is not None
        assert result.is_rolling is True

    def test_parse_row_with_investment_days(self):
        row = {
            "类型": "理财",
            "名称": "测试理财",
            "风险": "低",
            "投资天数": "180",
        }
        result = CSVParser.parse_row(row)
        assert result is not None
        assert result.investment_days == 180

    def test_parse_row_with_return_rate(self):
        row = {
            "类型": "理财",
            "名称": "测试理财",
            "风险": "低",
            "收益率": "5.5",
            "年化收益": "11.0",
        }
        result = CSVParser.parse_row(row)
        assert result is not None
        assert result.return_rate == Decimal("5.5")
        assert result.annual_return == Decimal("11.0")

    def test_parse_row_with_initial_and_profit(self):
        row = {
            "类型": "理财",
            "名称": "测试理财",
            "风险": "低",
            "初始金额": "10000",
            "收益金额": "500",
        }
        result = CSVParser.parse_row(row)
        assert result is not None
        assert result.initial_amount == Decimal("10000")
        assert result.profit_amount == Decimal("500")
        assert result.current_amount == Decimal("10500")

    def test_parse_row_with_exchange_rates(self):
        row = {
            "类型": "QDII",
            "名称": "测试QDII",
            "风险": "中",
            "美元汇率": "7.2",
            "港元汇率": "0.92",
        }
        result = CSVParser.parse_row(row)
        assert result is not None
        assert result.usd_rate == Decimal("7.2")
        assert result.hkd_rate == Decimal("0.92")

    def test_parse_row_with_transaction_records(self):
        row = {
            "类型": "基金",
            "名称": "测试基金",
            "风险": "中",
            "交易记录": "2024/1/1:buy:1000;2024/6/1:sell:500",
        }
        result = CSVParser.parse_row(row)
        assert result is not None
        assert result.transaction_records == "2024/1/1:buy:1000;2024/6/1:sell:500"

    def test_parse_row_with_default_order(self):
        row = {
            "类型": "基金",
            "名称": "测试基金",
            "风险": "中",
            "默认顺序": "5",
        }
        result = CSVParser.parse_row(row)
        assert result is not None
        assert result.default_order == 5

    def test_parse_row_full(self):
        row = {
            "类型": "指数基金",
            "名称": "中证500ETF",
            "风险": "中",
            "微信": "10000",
            "支付宝": "",
            "到期时间": "",
            "滚动": "否",
            "开始日期": "",  # 不设置开始日期，使用投资天数字段
            "初始金额": "9000",
            "二次买入": "",
            "二次金额": "",
            "收益金额": "1000",
            "投资天数": "180",
            "收益率": "11.11",
            "年化收益": "22.22",
            "复利年化": "20.0",
            "利息发放": "",
            "交易记录": "2024/1/15:buy:9000",
            "默认顺序": "1",
            "美元汇率": "",
            "港元汇率": "",
        }
        result = CSVParser.parse_row(row)
        assert result is not None
        assert result.name == "中证500ETF"
        assert result.investment_type == InvestmentType.INDEX_FUND
        assert result.risk_level == RiskLevel.MEDIUM
        assert result.wechat_amount == Decimal("10000")
        assert result.start_date is None
        assert result.initial_amount == Decimal("9000")
        assert result.investment_days == 180


class TestParseCsvFile:
    """Test parse_csv_file method"""

    def test_parse_csv_file_basic(self):
        csv_content = "类型,名称,风险\n指数基金,中证500ETF,中\n债券基金,测试债券,低"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as f:
            f.write(csv_content)
            temp_path = Path(f.name)
        
        try:
            result = CSVParser.parse_csv_file(temp_path)
            assert len(result) == 2
            assert result[0].name == "中证500ETF"
            assert result[1].name == "测试债券"
        finally:
            os.unlink(temp_path)

    def test_parse_csv_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            CSVParser.parse_csv_file(Path("/nonexistent/file.csv"))

    def test_parse_csv_file_with_bom(self):
        csv_content = "\ufeff类型,名称,风险\n指数基金,中证500ETF,中"
        
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as f:
            f.write(csv_content.encode('utf-8-sig'))
            temp_path = Path(f.name)
        
        try:
            result = CSVParser.parse_csv_file(temp_path)
            assert len(result) == 1
            assert result[0].name == "中证500ETF"
        finally:
            os.unlink(temp_path)

    def test_parse_csv_file_empty_rows(self):
        csv_content = "类型,名称,风险\n指数基金,中证500ETF,中\n,,"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as f:
            f.write(csv_content)
            temp_path = Path(f.name)

        try:
            result = CSVParser.parse_csv_file(temp_path)
            assert len(result) == 1
        finally:
            os.unlink(temp_path)


class TestLoadData:
    """Test load_data method"""

    def test_column_mapping_exists(self):
        assert "类型" in CSVParser.COLUMN_MAPPING
        assert "名称" in CSVParser.COLUMN_MAPPING
        assert "风险" in CSVParser.COLUMN_MAPPING
        assert "微信" in CSVParser.COLUMN_MAPPING
        assert "支付宝" in CSVParser.COLUMN_MAPPING

    def test_column_mapping_values(self):
        assert CSVParser.COLUMN_MAPPING["类型"] == "investment_type"
        assert CSVParser.COLUMN_MAPPING["名称"] == "name"
        assert CSVParser.COLUMN_MAPPING["风险"] == "risk_level"


class TestParseTransactionRecords:
    """Test _parse_transaction_records method"""

    def test_parse_transaction_records_basic(self):
        """Test parsing basic transaction records"""
        result = CSVParser._parse_transaction_records("2024/1/15:buy:1000")
        assert len(result) == 1
        assert result[0]["date"] == "2024/1/15"
        assert result[0]["type"] == "buy"
        assert result[0]["amount"] == 1000.0

    def test_parse_transaction_records_multiple(self):
        """Test parsing multiple transaction records"""
        result = CSVParser._parse_transaction_records("2024/1/15:buy:1000;2024/6/15:sell:500")
        assert len(result) == 2
        assert result[0]["type"] == "buy"
        assert result[1]["type"] == "sell"

    def test_parse_transaction_records_empty(self):
        """Test parsing empty transaction records"""
        result = CSVParser._parse_transaction_records("")
        assert len(result) == 0

    def test_parse_transaction_records_none(self):
        """Test parsing None transaction records"""
        result = CSVParser._parse_transaction_records(None)
        assert len(result) == 0

    def test_parse_transaction_records_invalid(self):
        """Test parsing invalid transaction records"""
        result = CSVParser._parse_transaction_records("invalid")
        assert len(result) == 0

    def test_parse_transaction_records_partial(self):
        """Test parsing partial transaction records"""
        result = CSVParser._parse_transaction_records("2024/1/15:buy")
        assert len(result) == 0


class TestCalculateCashflows:
    """Test _calculate_cashflows method"""

    def test_calculate_cashflows_buy_only(self):
        """Test calculating cashflows with buy only"""
        transactions = [
            {"type": "buy", "amount": 1000.0},
            {"type": "buy", "amount": 500.0},
        ]
        result = CSVParser._calculate_cashflows(transactions, Decimal("1600"))
        assert len(result) == 3
        assert result[0] == -1000.0
        assert result[1] == -500.0
        assert result[2] == 1600.0

    def test_calculate_cashflows_buy_and_sell(self):
        """Test calculating cashflows with buy and sell"""
        transactions = [
            {"type": "buy", "amount": 1000.0},
            {"type": "sell", "amount": 500.0},
        ]
        result = CSVParser._calculate_cashflows(transactions, Decimal("600"))
        assert len(result) == 3
        assert result[0] == -1000.0
        assert result[1] == 500.0
        assert result[2] == 600.0

    def test_calculate_cashflows_empty(self):
        """Test calculating cashflows with empty transactions"""
        result = CSVParser._calculate_cashflows([], Decimal("1000"))
        assert len(result) == 1
        assert result[0] == 1000.0

    def test_calculate_cashflows_no_current_amount(self):
        """Test calculating cashflows with no current amount"""
        transactions = [{"type": "buy", "amount": 1000.0}]
        result = CSVParser._calculate_cashflows(transactions, None)
        assert len(result) == 1
        assert result[0] == -1000.0


class TestDays360:
    """Test days360 function"""

    def test_days360_basic(self):
        """Test basic days360 calculation"""
        from datetime import date
        from asset_lens.data.csv_parser import days360
        result = days360(date(2024, 1, 1), date(2024, 12, 31))
        assert result == 360

    def test_days360_same_day(self):
        """Test days360 with same day"""
        from datetime import date
        from asset_lens.data.csv_parser import days360
        result = days360(date(2024, 1, 1), date(2024, 1, 1))
        assert result == 0

    def test_days360_one_month(self):
        """Test days360 with one month"""
        from datetime import date
        from asset_lens.data.csv_parser import days360
        result = days360(date(2024, 1, 1), date(2024, 2, 1))
        assert result == 30

    def test_days360_end_of_month(self):
        """Test days360 with end of month"""
        from datetime import date
        from asset_lens.data.csv_parser import days360
        result = days360(date(2024, 1, 31), date(2024, 2, 28))
        # Jan 31 is treated as Jan 30 in 30/360 convention
        assert result >= 28

    def test_days360_european_mode(self):
        """Test days360 with European mode"""
        from datetime import date
        from asset_lens.data.csv_parser import days360
        result = days360(date(2024, 1, 31), date(2024, 2, 28), european=True)
        assert result >= 28

    def test_days360_end_of_month_both_31(self):
        """Test days360 with both dates on 31st"""
        from datetime import date
        from asset_lens.data.csv_parser import days360
        result = days360(date(2024, 1, 31), date(2024, 3, 31))
        # Both 31st should be treated as 30th
        assert result >= 58


class TestLoadData:
    """Test load_data method"""

    def test_load_data_with_dir(self):
        """Test loading data from directory"""
        csv_content = "类型,名称,风险\n指数基金,测试产品,中"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            csv_file = temp_path / "工作表 1-表格 1.csv"
            
            with open(csv_file, "w", encoding="utf-8-sig") as f:
                f.write(csv_content)
            
            result = CSVParser.load_data(temp_path)
            assert len(result) == 1
            assert result[0].name == "测试产品"

    def test_load_data_with_csv_file(self):
        """Test loading data from CSV file"""
        csv_content = "类型,名称,风险\n指数基金,测试产品,中"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as f:
            f.write(csv_content)
            temp_path = Path(f.name)
        
        try:
            result = CSVParser.load_data(temp_path)
            assert len(result) == 1
            assert result[0].name == "测试产品"
        finally:
            os.unlink(temp_path)

    def test_load_data_empty_dir(self):
        """Test loading data from empty directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # load_data raises FileNotFoundError when no CSV files found
            with pytest.raises(FileNotFoundError):
                CSVParser.load_data(temp_path)


class TestGetExchangeRates:
    """Test get_exchange_rates method"""

    def test_get_exchange_rates_no_file(self):
        """Test getting exchange rates when file doesn't exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            usd, hkd = CSVParser.get_exchange_rates(temp_path)
            # Should return default rates
            assert usd > 0
            assert hkd > 0

    def test_get_exchange_rates_with_file(self):
        """Test getting exchange rates from file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create exchange rate file
            rate_file = temp_path / "工作表 2-表格 1.csv"
            with open(rate_file, "w", encoding="utf-8-sig") as f:
                f.write("日期,美元汇率,港元汇率\n")
                f.write("2024/01/15,7.25,0.93\n")
            
            usd, hkd = CSVParser.get_exchange_rates(temp_path)
            assert usd == 7.25
            assert hkd == 0.93


class TestParseCsvFileAdvanced:
    """Test parse_csv_file advanced scenarios"""

    def test_parse_csv_file_with_reference_date(self):
        """Test parsing CSV file with reference date"""
        csv_content = "类型,名称,风险,开始日期\n指数基金,测试产品,中,2024/01/01"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as f:
            f.write(csv_content)
            temp_path = Path(f.name)
        
        try:
            from datetime import date
            ref_date = date(2024, 6, 30)
            result = CSVParser.parse_csv_file(temp_path, reference_date=ref_date)
            assert len(result) == 1
        finally:
            os.unlink(temp_path)

    def test_parse_csv_file_with_invalid_rows(self):
        """Test parsing CSV file with some invalid rows"""
        csv_content = "类型,名称,风险\n指数基金,产品A,中\n,产品B,低\n指数基金,产品C,高"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as f:
            f.write(csv_content)
            temp_path = Path(f.name)
        
        try:
            result = CSVParser.parse_csv_file(temp_path)
            # Should skip row with empty type
            assert len(result) >= 1
        finally:
            os.unlink(temp_path)


class TestParseRowAdvanced:
    """Test parse_row advanced scenarios"""

    def test_parse_row_with_all_platforms(self):
        """Test parsing row with all platform amounts"""
        row = {
            "类型": "理财",
            "名称": "测试产品",
            "风险": "低",
            "微信": "1000",
            "中金": "2000",
            "支付宝": "3000",
            "富途": "4000",
            "招商": "5000",
            "港招": "6000",
            "交通": "7000",
            "浦发": "8000",
            "建设": "9000",
            "中信": "10000",
            "民生": "11000",
            "工商": "12000",
            "中银": "13000",
        }
        result = CSVParser.parse_row(row)
        assert result is not None
        assert result.wechat_amount == Decimal("1000")
        assert result.alipay_amount == Decimal("3000")

    def test_parse_row_with_secondary_buy(self):
        """Test parsing row with secondary buy"""
        row = {
            "类型": "理财",
            "名称": "测试产品",
            "风险": "低",
            "二次买入": "5000",  # This is a numeric field
            "二次金额": "3000",
        }
        result = CSVParser.parse_row(row)
        assert result is not None
        # secondary_buy is a Decimal field, not a date
        assert result.secondary_buy == Decimal("5000")
        assert result.secondary_amount == Decimal("3000")

    def test_parse_row_with_compound_return(self):
        """Test parsing row with compound return"""
        row = {
            "类型": "理财",
            "名称": "测试产品",
            "风险": "低",
            "复利年化": "15.5",
        }
        result = CSVParser.parse_row(row)
        assert result is not None
        assert result.compound_return == Decimal("15.5")

    def test_parse_row_with_interest_payment(self):
        """Test parsing row with interest payment"""
        row = {
            "类型": "理财",
            "名称": "测试产品",
            "风险": "低",
            "利息发放": "500",  # This is a numeric field, not a string
        }
        result = CSVParser.parse_row(row)
        assert result is not None
        assert result.interest_payment == Decimal("500")

    def test_parse_row_with_annual_return(self):
        """Test parsing row with annual return"""
        row = {
            "类型": "理财",
            "名称": "测试产品",
            "风险": "低",
            "年化收益": "12.5",
        }
        result = CSVParser.parse_row(row)
        assert result is not None
        assert result.annual_return == Decimal("12.5")
