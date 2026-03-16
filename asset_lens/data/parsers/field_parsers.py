"""
Field Parsers - 字段解析器
"""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

from ..models import InvestmentType, RiskLevel


def parse_decimal(value: Optional[str]) -> Optional[Decimal]:
    """解析 Decimal 值"""
    if not value or value.strip() in ("", "-", "N/A", "无"):
        return None
    try:
        clean_value = value.strip().replace(",", "").replace("%", "").replace("￥", "")
        return Decimal(clean_value)
    except (InvalidOperation, ValueError):
        return None


def parse_date(value: Optional[str]) -> Optional[datetime]:
    """解析日期值"""
    if not value or value.strip() in ("", "-", "N/A"):
        return None
    value = value.strip()
    date_formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y.%m.%d",
        "%Y年%m月%d日",
        "%m/%d/%Y",
        "%d/%m/%Y",
    ]
    for fmt in date_formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def parse_boolean(value: Optional[str]) -> bool:
    """解析布尔值"""
    if not value:
        return False
    return value.strip().lower() in ("是", "yes", "true", "1", "y", "√")


def parse_investment_type(value: Optional[str]) -> InvestmentType:
    """解析投资类型"""
    if not value:
        return InvestmentType.OTHER
    type_mapping = {
        "货币": InvestmentType.MONETARY,
        "货币基金": InvestmentType.MONETARY,
        "现金": InvestmentType.CASH,
        "指数基金": InvestmentType.INDEX_FUND,
        "债券基金": InvestmentType.BOND_FUND,
        "混合基金": InvestmentType.MIXED_FUND,
        "股票": InvestmentType.STOCK,
        "美股": InvestmentType.US_STOCK,
        "港股": InvestmentType.HK_STOCK,
        "现金（港元）": InvestmentType.HK_CASH,
        "股息基金（港元）": InvestmentType.HK_DIVIDEND_FUND,
        "QDII": InvestmentType.QDII,
        "理财": InvestmentType.WEALTH,
        "理财产品": InvestmentType.WEALTH,
        "高端理财": InvestmentType.HIGH_END_WEALTH,
        "券商理财": InvestmentType.BROKER_WEALTH,
        "公募固收": InvestmentType.PUBLIC_FIXED_INCOME,
        "定期存款": InvestmentType.FIXED_DEPOSIT,
        "债券": InvestmentType.BOND,
        "特别国债": InvestmentType.SPECIAL_TREASURY_BOND,
        "REITs": InvestmentType.REITS,
        "黄金": InvestmentType.GOLD,
        "基金": InvestmentType.FUND,
        "定投基金": InvestmentType.DCA_FUND,
        "个人养老金": InvestmentType.PENSION,
        "ETF": InvestmentType.ETF,
        "美元基金（美元）": InvestmentType.USD_FUND,
        "其他": InvestmentType.OTHER,
    }
    stripped_value = value.strip()
    return type_mapping.get(stripped_value, InvestmentType.OTHER)


def parse_risk_level(value: Optional[str]) -> RiskLevel:
    """解析风险等级"""
    if not value:
        return RiskLevel.MEDIUM
    risk_mapping = {
        "低": RiskLevel.LOW,
        "中低": RiskLevel.MEDIUM_LOW,
        "中": RiskLevel.MEDIUM,
        "中高": RiskLevel.MEDIUM_HIGH,
        "高": RiskLevel.HIGH,
    }
    return risk_mapping.get(value.strip(), RiskLevel.MEDIUM)


def parse_investment_days(value: Optional[str]) -> Optional[int]:
    """解析投资天数"""
    if not value or value.strip() in ("", "-", "N/A"):
        return None
    try:
        return int(value.strip())
    except ValueError:
        return None


field_parsers = {
    "decimal": parse_decimal,
    "date": parse_date,
    "boolean": parse_boolean,
    "investment_type": parse_investment_type,
    "risk_level": parse_risk_level,
    "investment_days": parse_investment_days,
}
