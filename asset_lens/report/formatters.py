"""
Report formatting functions.
报告格式化函数 - 提取公共格式化逻辑
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any


def format_currency(
    value: float | Decimal | str | None,
    currency: str = "¥",
    decimal_places: int = 2,
    show_sign: bool = False,
) -> str:
    """格式化货币金额"""
    if value is None:
        return f"{currency}0.00"

    try:
        if isinstance(value, str):
            value = value.replace(currency, "").replace(",", "").strip()
            value = float(value)
        elif isinstance(value, Decimal):
            value = float(value)

        formatted = f"{value:,.{decimal_places}f}"
        if show_sign and value > 0:
            return f"+{currency}{formatted}"
        return f"{currency}{formatted}"
    except (ValueError, TypeError):
        return f"{currency}0.00"


def format_percentage(
    value: float | Decimal | str | None,
    decimal_places: int = 2,
    show_sign: bool = True,
) -> str:
    """格式化百分比"""
    if value is None:
        return "N/A"

    try:
        if isinstance(value, str):
            value = value.replace("%", "").strip()
            value = float(value)
        elif isinstance(value, Decimal):
            value = float(value)

        formatted = f"{value:.{decimal_places}f}%"
        if show_sign and value > 0:
            return f"+{formatted}"
        return formatted
    except (ValueError, TypeError):
        return "N/A"


def format_date(
    value: datetime | date | str | None,
    fmt: str = "%Y-%m-%d",
) -> str:
    """格式化日期"""
    if value is None:
        return "N/A"
    if isinstance(value, str):
        try:
            parsed = datetime.strptime(value, "%Y-%m-%d")
            return parsed.strftime(fmt)
        except ValueError:
            return str(value)
    if isinstance(value, date) and not isinstance(value, datetime):
        return value.strftime(fmt)
    return value.strftime(fmt)


def format_number(
    value: float | Decimal | str | None,
    decimal_places: int = 2,
    thousand_separator: bool = True,
) -> str:
    """格式化数字"""
    if value is None:
        return "N/A"

    try:
        if isinstance(value, str):
            value = value.replace(",", "").strip()
            value = float(value)
        elif isinstance(value, Decimal):
            value = float(value)

        if thousand_separator:
            return f"{value:,.{decimal_places}f}"
        return f"{value:.{decimal_places}f}"
    except (ValueError, TypeError):
        return "N/A"


def format_money_value(value: str) -> str:
    """格式化金额值（带货币符号）"""
    try:
        amount = float(value.replace("¥", "").replace(",", "").strip())
        if amount >= 10000:
            return f"¥{amount/10000:.2f}万"
        return f"¥{amount:,.2f}"
    except (ValueError, AttributeError):
        return value


def format_money(value: str) -> str:
    """格式化金额（简化版）"""
    try:
        amount = float(str(value).replace("¥", "").replace(",", "").strip())
        return f"¥{amount:,.2f}"
    except (ValueError, AttributeError):
        return str(value)


def format_days(days: int | None) -> str:
    """格式化天数"""
    if days is None:
        return "N/A"
    if days >= 365:
        years = days / 365
        return f"{years:.1f}年"
    return f"{days}天"


def format_return_rate(rate: float | Decimal | None) -> str:
    """格式化收益率"""
    if rate is None:
        return "N/A"
    rate_float = float(rate)
    if rate_float > 0:
        return f"+{rate_float:.2f}%"
    return f"{rate_float:.2f}%"


def format_product_summary(product: dict[str, Any]) -> str:
    """格式化产品摘要"""
    name = product.get("name", "未知")
    return_rate = product.get("return_rate", 0)
    amount = product.get("current_amount", 0)

    return f"{name}: {format_return_rate(return_rate)} ({format_currency(amount)})"


def format_risk_level(level: str | None) -> str:
    """格式化风险等级"""
    if not level:
        return "中"

    level_map = {
        "low": "低",
        "medium": "中",
        "high": "高",
    }
    return level_map.get(str(level).lower(), str(level))


def format_investment_type(itype: str | None) -> str:
    """格式化投资类型"""
    if not itype:
        return "其他"

    type_map = {
        "fund": "基金",
        "stock": "股票",
        "bond": "债券",
        "deposit": "存款",
        "insurance": "保险",
        "other": "其他",
    }
    return type_map.get(str(itype).lower(), str(itype))


def format_table_row(columns: list[str], widths: list[int]) -> str:
    """格式化表格行"""
    formatted_cols = []
    for col, width in zip(columns, widths):
        formatted_cols.append(str(col).ljust(width))
    return " | ".join(formatted_cols)


def format_section_header(title: str, width: int = 60) -> str:
    """格式化章节标题"""
    return f"\n{'=' * width}\n{title.center(width)}\n{'=' * width}"


def format_subsection_header(title: str, width: int = 40) -> str:
    """格式化子章节标题"""
    return f"\n--- {title} ---"


def truncate_string(s: str, max_length: int = 20) -> str:
    """截断字符串"""
    if len(s) <= max_length:
        return s
    return s[:max_length - 3] + "..."


def safe_str(value: Any, default: str = "N/A") -> str:
    """安全转换为字符串"""
    if value is None:
        return default
    return str(value)


def safe_float(value: Any, default: float = 0.0) -> float:
    """安全转换为浮点数"""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_decimal(value: Any, default: Decimal = Decimal("0")) -> Decimal:
    """安全转换为 Decimal"""
    if value is None:
        return default
    try:
        return Decimal(str(value))
    except Exception:
        return default
