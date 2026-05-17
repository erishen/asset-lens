"""
CLI Utilities.
CLI 工具函数

包含 CLI 命令中常用的公共函数：
- 错误处理装饰器
- 数据加载工具
- 格式化输出工具
- 配置管理工具
"""

import functools
import json
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import click

from asset_lens.config import config


def handle_errors(func: Callable) -> Callable:
    """
    错误处理装饰器

    自动捕获异常并显示友好的错误消息

    Usage:
        @handle_errors
        def my_command():
            ...
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            click.echo(f"❌ 操作失败: {e}", err=True)
            return None

    return wrapper


def load_portfolio_data(data_mode: str = "sample") -> tuple[dict | None, str | None]:
    """
    加载投资组合数据

    Args:
        data_mode: 数据模式 (sample/real)

    Returns:
        (数据字典, 错误消息) 元组
    """
    from decimal import Decimal

    from asset_lens.data.csv_parser import CSVParser
    from asset_lens.data.models import Portfolio

    config.set_data_mode(data_mode)

    try:
        products = CSVParser.load_data()
        portfolio = Portfolio(
            products,
            usd_rate=Decimal(str(config.default_usd_rate)),
            hkd_rate=Decimal(str(config.default_hkd_rate)),
        )
        return {"portfolio": portfolio, "products": products}, None
    except Exception as e:
        return None, f"加载数据失败: {e}"


def format_currency(amount: float, currency: str = "¥") -> str:
    """
    格式化货币显示

    Args:
        amount: 金额
        currency: 货币符号

    Returns:
        格式化后的字符串
    """
    return f"{currency}{amount:,.2f}"


def format_percent(value: float, decimal: int = 2) -> str:
    """
    格式化百分比显示

    Args:
        value: 百分比值
        decimal: 小数位数

    Returns:
        格式化后的字符串
    """
    return f"{value:.{decimal}f}%"


def format_change(value: float) -> str:
    """
    格式化涨跌幅显示

    Args:
        value: 涨跌幅值

    Returns:
        格式化后的字符串（带正负号）
    """
    if value > 0:
        return f"📈 +{value:.2f}%"
    elif value < 0:
        return f"📉 {value:.2f}%"
    else:
        return f"➡️ {value:.2f}%"


def print_section_header(title: str, width: int = 60) -> None:
    """
    打印章节标题

    Args:
        title: 标题文本
        width: 分隔线宽度
    """
    click.echo("")
    click.echo("=" * width)
    click.echo(title)
    click.echo("=" * width)


def print_sub_header(title: str, width: int = 60) -> None:
    """
    打印子标题

    Args:
        title: 标题文本
        width: 分隔线宽度
    """
    click.echo("")
    click.echo("-" * width)
    click.echo(title)
    click.echo("-" * width)


def print_key_value(key: str, value: Any, indent: int = 0) -> None:
    """
    打印键值对

    Args:
        key: 键名
        value: 值
        indent: 缩进空格数
    """
    prefix = " " * indent
    click.echo(f"{prefix}{key}: {value}")


def print_success(message: str) -> None:
    """
    打印成功消息

    Args:
        message: 消息内容
    """
    click.echo(f"✅ {message}")


def print_error(message: str) -> None:
    """
    打印错误消息

    Args:
        message: 消息内容
    """
    click.echo(f"❌ {message}", err=True)


def print_warning(message: str) -> None:
    """
    打印警告消息

    Args:
        message: 消息内容
    """
    click.echo(f"⚠️ {message}")


def print_info(message: str) -> None:
    """
    打印信息消息

    Args:
        message: 消息内容
    """
    click.echo(f"ℹ️ {message}")


def check_data_freshness(
    file_path: Path, max_age_hours: int = 1, time_key: str = "update_time"
) -> tuple[bool, str | None]:
    """
    检查数据文件的新鲜度

    Args:
        file_path: 数据文件路径
        max_age_hours: 最大允许的小时数
        time_key: 时间字段名

    Returns:
        (是否需要更新, 更新时间字符串) 元组
    """
    if not file_path.exists():
        return True, None

    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
            update_time_str = data.get(time_key, "")
            if update_time_str:
                update_time = datetime.strptime(update_time_str, "%Y-%m-%d %H:%M:%S")
                now = datetime.now()
                age = now - update_time
                if age > timedelta(hours=max_age_hours):
                    return True, update_time_str
                return False, update_time_str
    except Exception:
        pass

    return True, None


def ensure_data_dir() -> None:
    """
    确保数据目录存在
    """
    config.data_path.mkdir(parents=True, exist_ok=True)
    config.cache_path.mkdir(parents=True, exist_ok=True)
    config.output_path.mkdir(parents=True, exist_ok=True)


def get_data_dir(data_mode: str) -> Path | None:
    """
    获取数据目录路径

    Args:
        data_mode: 数据模式 (sample/real)

    Returns:
        数据目录路径
    """
    if data_mode == "sample":
        return config.data_path / "sample"
    else:
        return config.data_path / "real"


def confirm_action(message: str, default: bool = False) -> bool:
    """
    确认操作

    Args:
        message: 确认消息
        default: 默认值

    Returns:
        用户是否确认
    """
    return click.confirm(message, default=default)


def prompt_input(message: str, default: str | None = None) -> str | None:
    """
    提示用户输入

    Args:
        message: 提示消息
        default: 默认值

    Returns:
        用户输入的值
    """
    result = click.prompt(message, default=default)
    return str(result) if result is not None else None


def calculate_profit_metrics(principal: float, current: float, days: int = 365) -> dict[str, float]:
    """
    计算收益指标

    Args:
        principal: 本金
        current: 当前金额
        days: 持有天数

    Returns:
        收益指标字典
    """
    profit = current - principal
    profit_rate = (profit / principal * 100) if principal > 0 else 0
    annual_return = (profit_rate * 365 / days) if days > 0 else 0

    return {
        "profit": profit,
        "profit_rate": profit_rate,
        "annual_return": annual_return,
        "principal": principal,
        "current": current,
    }


def print_profit_summary(metrics: dict[str, float]) -> None:
    """
    打印收益摘要

    Args:
        metrics: 收益指标字典
    """
    print_key_value("本金", format_currency(metrics["principal"]))
    print_key_value("当前", format_currency(metrics["current"]))
    print_key_value("收益", format_currency(metrics["profit"]))
    print_key_value("收益率", format_percent(metrics["profit_rate"]))
    print_key_value("年化收益率", format_percent(metrics["annual_return"]))


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    安全除法

    Args:
        numerator: 分子
        denominator: 分母
        default: 默认值（分母为0时）

    Returns:
        除法结果
    """
    return numerator / denominator if denominator != 0 else default


def format_amount_with_currency(
    amount: float,
    investment_type: str | None = None,
    usd_rate: float | None = None,
    hkd_rate: float | None = None,
) -> str:
    """
    根据投资类型格式化金额显示

    Args:
        amount: 金额（原始货币）
        investment_type: 投资类型
        usd_rate: 美元汇率（可选）
        hkd_rate: 港币汇率（可选）

    Returns:
        格式化后的金额字符串
    """
    if amount == 0:
        return "¥0"

    from pathlib import Path

    from asset_lens.config import config
    from asset_lens.data.csv_parser import CSVParser

    if usd_rate is None or hkd_rate is None:
        try:
            data_dir = Path(config.real_data_path) if config.data_mode == "real" else Path(config.sample_data_path)
            usd_rate, hkd_rate = CSVParser.get_exchange_rates(data_dir)
        except Exception:
            usd_rate = float(config.default_usd_rate)
            hkd_rate = float(config.default_hkd_rate)

    if investment_type in ["美股", "美元基金", "美元基金（美元）"]:
        cny_amount = amount * usd_rate
        return f"${amount:,.0f} (¥{cny_amount:,.0f})"
    elif investment_type in ["港股", "现金（港元）", "股息基金（港元）"]:
        cny_amount = amount * hkd_rate
        return f"HK${amount:,.0f} (¥{cny_amount:,.0f})"

    return f"¥{amount:,.0f}"
