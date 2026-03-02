"""
Common parser utilities for asset-lens.
通用解析工具模块，避免代码重复
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional


def parse_decimal(value: str) -> Optional[Decimal]:
    """解析 Decimal 值"""
    if not value or value.strip() == "":
        return None
    try:
        cleaned = value.replace(",", "").strip()
        return Decimal(cleaned)
    except Exception:
        return None


def parse_date(value: str) -> Optional[datetime]:
    """解析日期值"""
    if not value or value.strip() == "":
        return None

    date_formats = [
        "%Y/%m/%d",
        "%Y-%m-%d",
        "%Y.%m.%d",
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y.%m.%d %H:%M:%S",
        "%Y%m%d",
    ]

    for fmt in date_formats:
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue

    return None


def parse_boolean(value: str) -> bool:
    """解析布尔值"""
    if not value or value.strip() == "":
        return False
    return value.strip().lower() in ["true", "yes", "1", "是", "可赎"]


SELL_RECORD_FIELDS: List[str] = [
    "类型",
    "名称",
    "风险",
    "平台A",
    "平台C",
    "平台B",
    "券商A",
    "银行A",
    "银行I",
    "银行B",
    "银行C",
    "银行D",
    "银行E",
    "银行F",
    "银行G",
    "银行H",
    "到期时间",
    "滚动",
    "开始日期",
    "初始金额",
    "收益金额",
    "收益率",
    "结束日期",
    "到账日期",
    "结束到账间隔",
    "投资天数",
    "年化收益",
    "复利年化",
    "利息发放",
    "交易记录",
    "默认顺序",
]

SELL_RECORD_EXPORT_FIELDS: List[str] = [
    "卖出日期",
    "名称",
    "风险等级",
    "到期时间",
    "是否滚动",
    "开始日期",
    "初始金额",
    "收益金额",
    "收益率",
    "结束日期",
    "到账日期",
    "结束到账间隔",
    "投资天数",
    "年化收益",
    "复利年化",
    "利息发放",
    "交易记录",
    "默认顺序",
]


def calculate_return_rate(stats: Dict[str, Decimal]) -> Decimal:
    """计算收益率"""
    if stats.get("total_initial", Decimal("0")) > 0:
        return stats["total_profit"] / stats["total_initial"] * Decimal("100")
    return Decimal("0")
