
from asset_lens.data.models import InvestmentType, RiskLevel
from asset_lens.data.parsers.field_parsers import (
    field_parsers,
    parse_boolean,
    parse_date,
    parse_decimal,
    parse_investment_days,
    parse_investment_type,
    parse_risk_level,
)


class TestParseDecimal:
    def test_basic(self):
        result = parse_decimal("123.45")
        assert result is not None
        assert float(result) == 123.45

    def test_with_comma(self):
        result = parse_decimal("1,234.56")
        assert result is not None
        assert float(result) == 1234.56

    def test_with_percent(self):
        result = parse_decimal("5.5%")
        assert result is not None
        assert float(result) == 5.5

    def test_with_yen(self):
        result = parse_decimal("￥1000")
        assert result is not None
        assert float(result) == 1000

    def test_none(self):
        assert parse_decimal(None) is None

    def test_empty(self):
        assert parse_decimal("") is None

    def test_dash(self):
        assert parse_decimal("-") is None

    def test_na(self):
        assert parse_decimal("N/A") is None

    def test_chinese_na(self):
        assert parse_decimal("无") is None

    def test_invalid(self):
        assert parse_decimal("abc") is None

    def test_whitespace(self):
        result = parse_decimal("  100  ")
        assert result is not None
        assert float(result) == 100


class TestParseDate:
    def test_iso_format(self):
        result = parse_date("2024-01-15")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_slash_format(self):
        result = parse_date("2024/01/15")
        assert result is not None
        assert result.year == 2024

    def test_dot_format(self):
        result = parse_date("2024.01.15")
        assert result is not None
        assert result.year == 2024

    def test_chinese_format(self):
        result = parse_date("2024年01月15日")
        assert result is not None
        assert result.year == 2024

    def test_compact_format(self):
        result = parse_date("20240115")
        assert result is not None
        assert result.year == 2024

    def test_datetime_format(self):
        result = parse_date("2024-01-15 10:30:00")
        assert result is not None
        assert result.hour == 10

    def test_none(self):
        assert parse_date(None) is None

    def test_empty(self):
        assert parse_date("") is None

    def test_invalid(self):
        assert parse_date("not-a-date") is None


class TestParseBoolean:
    def test_chinese_yes(self):
        assert parse_boolean("是") is True

    def test_yes(self):
        assert parse_boolean("yes") is True

    def test_true(self):
        assert parse_boolean("true") is True

    def test_one(self):
        assert parse_boolean("1") is True

    def test_y(self):
        assert parse_boolean("y") is True

    def test_checkmark(self):
        assert parse_boolean("√") is True

    def test_no(self):
        assert parse_boolean("no") is False

    def test_false(self):
        assert parse_boolean("false") is False

    def test_zero(self):
        assert parse_boolean("0") is False

    def test_none(self):
        assert parse_boolean(None) is False

    def test_empty(self):
        assert parse_boolean("") is False

    def test_case_insensitive(self):
        assert parse_boolean("YES") is True
        assert parse_boolean("True") is True


class TestParseInvestmentType:
    def test_stock(self):
        assert parse_investment_type("股票") == InvestmentType.STOCK

    def test_fund(self):
        assert parse_investment_type("基金") == InvestmentType.FUND

    def test_bond(self):
        assert parse_investment_type("债券") == InvestmentType.BOND

    def test_dca_fund(self):
        assert parse_investment_type("定投基金") == InvestmentType.DCA_FUND

    def test_etf(self):
        assert parse_investment_type("ETF") == InvestmentType.ETF

    def test_gold(self):
        assert parse_investment_type("黄金") == InvestmentType.GOLD

    def test_monetary(self):
        assert parse_investment_type("货币基金") == InvestmentType.MONETARY

    def test_none(self):
        assert parse_investment_type(None) == InvestmentType.OTHER

    def test_unknown(self):
        assert parse_investment_type("未知类型") == InvestmentType.OTHER

    def test_whitespace(self):
        assert parse_investment_type("  股票  ") == InvestmentType.STOCK


class TestParseRiskLevel:
    def test_low(self):
        assert parse_risk_level("低") == RiskLevel.LOW

    def test_medium_low(self):
        assert parse_risk_level("中低") == RiskLevel.MEDIUM_LOW

    def test_medium(self):
        assert parse_risk_level("中") == RiskLevel.MEDIUM

    def test_medium_high(self):
        assert parse_risk_level("中高") == RiskLevel.MEDIUM_HIGH

    def test_high(self):
        assert parse_risk_level("高") == RiskLevel.HIGH

    def test_none(self):
        assert parse_risk_level(None) == RiskLevel.MEDIUM

    def test_unknown(self):
        assert parse_risk_level("未知") == RiskLevel.MEDIUM


class TestParseInvestmentDays:
    def test_basic(self):
        assert parse_investment_days("365") == 365

    def test_none(self):
        assert parse_investment_days(None) is None

    def test_empty(self):
        assert parse_investment_days("") is None

    def test_na(self):
        assert parse_investment_days("N/A") is None

    def test_invalid(self):
        assert parse_investment_days("abc") is None


class TestFieldParsersRegistry:
    def test_all_parsers_registered(self):
        assert "decimal" in field_parsers
        assert "date" in field_parsers
        assert "boolean" in field_parsers
        assert "investment_type" in field_parsers
        assert "risk_level" in field_parsers
        assert "investment_days" in field_parsers

    def test_parsers_are_callable(self):
        for parser in field_parsers.values():
            assert callable(parser)
