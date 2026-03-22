"""
Product Parser - 产品解析器
"""

from datetime import date
from decimal import Decimal

from ..models import InvestmentProduct
from .field_parsers import (
    parse_boolean,
    parse_date,
    parse_decimal,
    parse_investment_days,
    parse_investment_type,
    parse_risk_level,
)


class ProductParser:
    """投资产品解析器"""

    COLUMN_MAPPING = {
        "类型": "investment_type",
        "名称": "name",
        "风险": "risk_level",
        "平台A": "wechat_amount",
        "平台B": "alipay_amount",
        "到期时间": "maturity_date",
        "滚动": "is_rolling",
        "开始日期": "start_date",
        "初始金额": "initial_amount",
        "二次买入": "secondary_buy",
        "二次金额": "secondary_amount",
        "收益金额": "profit_amount",
        "投资天数": "investment_days",
        "收益率": "return_rate",
        "年化收益": "annual_return",
        "复利年化": "compound_return",
        "利息发放": "interest_payment",
        "交易记录": "transaction_records",
        "默认顺序": "default_order",
        "美元汇率": "usd_rate",
        "港元汇率": "hkd_rate",
    }

    @classmethod
    def parse_row(
        cls, row: dict[str, str], reference_date: date | None = None
    ) -> InvestmentProduct | None:
        """解析单行数据为投资产品"""
        if not row:
            return None

        mapped_row = {}
        for cn_name, en_name in cls.COLUMN_MAPPING.items():
            if cn_name in row:
                mapped_row[en_name] = row[cn_name]

        name = mapped_row.get("name", "").strip()
        if not name:
            return None

        investment_type = parse_investment_type(mapped_row.get("investment_type", "其他"))
        risk_level = parse_risk_level(mapped_row.get("risk_level", "中"))

        platform_amounts = cls._parse_platform_amounts(mapped_row)

        product = InvestmentProduct(
            investment_type=investment_type,
            name=name,
            risk_level=risk_level,
            platform_amounts=platform_amounts,
            maturity_date=cls._parse_maturity_date(mapped_row.get("maturity_date")),
            is_rolling=parse_boolean(mapped_row.get("is_rolling", "")),
            start_date=cls._parse_start_date(mapped_row.get("start_date")),
            initial_amount=parse_decimal(mapped_row.get("initial_amount")),
            secondary_buy=parse_decimal(mapped_row.get("secondary_buy")),
            secondary_amount=parse_decimal(mapped_row.get("secondary_amount")),
            profit_amount=parse_decimal(mapped_row.get("profit_amount")),
            investment_days=parse_investment_days(mapped_row.get("investment_days")),
            return_rate=parse_decimal(mapped_row.get("return_rate")),
            annual_return=parse_decimal(mapped_row.get("annual_return")),
            compound_return=parse_decimal(mapped_row.get("compound_return")),
            interest_payment=parse_decimal(mapped_row.get("interest_payment")),
            transaction_records=mapped_row.get("transaction_records"),
            default_order=cls._parse_int(mapped_row.get("default_order")),
            usd_rate=parse_decimal(mapped_row.get("usd_rate")),
            hkd_rate=parse_decimal(mapped_row.get("hkd_rate")),
        )

        product.current_amount = sum(platform_amounts.values()) or product.initial_amount

        return product

    @staticmethod
    def _parse_platform_amounts(row: dict[str, str]) -> dict[str, Decimal]:
        """解析平台金额"""
        amounts = {}
        platform_fields = {
            "wechat_amount": "wechat",
            "alipay_amount": "alipay",
        }
        for field, platform in platform_fields.items():
            amount = parse_decimal(row.get(field, ""))
            if amount:
                amounts[platform] = amount
        return amounts

    @staticmethod
    def _parse_maturity_date(value: str | None) -> date | None:
        """解析到期日期"""
        if not value:
            return None
        dt = parse_date(value)
        return dt.date() if dt else None

    @staticmethod
    def _parse_start_date(value: str | None) -> date | None:
        """解析开始日期"""
        if not value:
            return None
        dt = parse_date(value)
        return dt.date() if dt else None

    @staticmethod
    def _parse_int(value: str | None) -> int | None:
        """解析整数"""
        if not value:
            return None
        try:
            return int(value.strip())
        except ValueError:
            return None


product_parser = ProductParser()
