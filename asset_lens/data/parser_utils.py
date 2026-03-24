"""
Common parser utilities for asset-lens.
通用解析工具模块，避免代码重复
"""

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation


def parse_date(value: str | None) -> datetime | None:
    """解析日期字符串"""
    if not value:
        return None

    value = str(value).strip()
    if not value:
        return None

    date_formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y.%m.%d",
        "%Y%m%d",
    ]

    for fmt in date_formats:
        try:
            return datetime.strptime(value, fmt)
        except (ValueError, TypeError):
            continue

    if " " in value:
        date_part = value.split(" ")[0]
        time_match = re.search(r"(\d{1,2}):(\d{1,2}):?(\d{1,2})?", value)

        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_part, fmt)
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2))
                    second = int(time_match.group(3)) if time_match.group(3) else 0
                    return dt.replace(hour=hour, minute=minute, second=second)
                return dt
            except (ValueError, TypeError):
                continue

    return None


def parse_decimal(value: str | None) -> Decimal | None:
    """解析数字字符串"""
    if not value:
        return None

    value_str = str(value).replace(",", "").replace("¥", "").strip()
    if not value_str:
        return None

    try:
        return Decimal(value_str)
    except (InvalidOperation, ValueError, TypeError):
        return None


SELL_RECORD_FIELDS: list[str] = [
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

SELL_RECORD_EXPORT_FIELDS: list[str] = [
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


def calculate_return_rate(stats: dict[str, Decimal]) -> Decimal:
    """计算收益率"""
    if stats.get("total_initial", Decimal("0")) > 0:
        return stats["total_profit"] / stats["total_initial"] * Decimal("100")
    return Decimal("0")
