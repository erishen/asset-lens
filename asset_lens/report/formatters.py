"""
Report Formatters - 报告格式化工具

提供统一的报告格式化函数。
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Any, Optional, Union


def format_currency(
    value: Union[float, int, Decimal, str],
    currency: str = "¥",
    decimal_places: int = 2,
    show_sign: bool = False,
) -> str:
    """
    格式化货币金额

    Args:
        value: 金额值
        currency: 货币符号
        decimal_places: 小数位数
        show_sign: 是否显示正负号

    Returns:
        格式化后的货币字符串
    """
    try:
        if isinstance(value, str):
            value = value.replace(",", "").replace(currency, "").strip()
        value = float(value)
    except (ValueError, TypeError):
        return f"{currency}0.00"

    if show_sign and value > 0:
        return f"+{currency}{value:,.{decimal_places}f}"
    return f"{currency}{value:,.{decimal_places}f}"


def format_percentage(
    value: Union[float, int, Decimal, str],
    decimal_places: int = 2,
    show_sign: bool = True,
) -> str:
    """
    格式化百分比

    Args:
        value: 百分比值（如 5.5 表示 5.5%）
        decimal_places: 小数位数
        show_sign: 是否显示正负号

    Returns:
        格式化后的百分比字符串
    """
    try:
        if isinstance(value, str):
            value = value.replace("%", "").strip()
        value = float(value)
    except (ValueError, TypeError):
        return "0.00%"

    if show_sign and value > 0:
        return f"+{value:.{decimal_places}f}%"
    return f"{value:.{decimal_places}f}%"


def format_date(
    value: Union[datetime, date, str],
    fmt: str = "%Y-%m-%d",
) -> str:
    """
    格式化日期

    Args:
        value: 日期值
        fmt: 格式化模板

    Returns:
        格式化后的日期字符串
    """
    if isinstance(value, datetime):
        return value.strftime(fmt)
    elif isinstance(value, date):
        return value.strftime(fmt)
    elif isinstance(value, str):
        return value
    return str(value)


def format_number(
    value: Union[float, int, Decimal, str],
    decimal_places: int = 2,
    thousand_separator: bool = True,
) -> str:
    """
    格式化数字

    Args:
        value: 数字值
        decimal_places: 小数位数
        thousand_separator: 是否使用千位分隔符

    Returns:
        格式化后的数字字符串
    """
    try:
        if isinstance(value, str):
            value = value.replace(",", "").strip()
        value = float(value)
    except (ValueError, TypeError):
        return "0.00"

    if thousand_separator:
        return f"{value:,.{decimal_places}f}"
    return f"{value:.{decimal_places}f}"


def format_large_number(value: Union[float, int]) -> str:
    """
    格式化大数字（使用万、亿单位）

    Args:
        value: 数字值

    Returns:
        格式化后的字符串
    """
    if abs(value) >= 100000000:
        return f"{value / 100000000:.2f}亿"
    elif abs(value) >= 10000:
        return f"{value / 10000:.2f}万"
    return f"{value:.2f}"
