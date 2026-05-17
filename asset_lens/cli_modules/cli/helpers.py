"""
CLI helper functions for asset-lens.
CLI 辅助函数 - 提取公共逻辑，减少代码重复
"""

from datetime import datetime
from decimal import Decimal
from pathlib import Path

import click


def setup_data_mode(data_mode: str | None) -> None:
    """设置数据模式（统一入口，带验证）"""
    from asset_lens.config import config

    if data_mode:
        config.set_data_mode(data_mode)


def load_products(data_path: str | None = None) -> list:
    """加载投资产品数据"""
    from asset_lens.data.csv_parser import CSVParser

    if data_path:
        return CSVParser.load_data(Path(data_path))
    return CSVParser.load_data()


def calculate_product_returns(products: list, reference_date: datetime | None = None) -> None:
    """计算产品收益率"""
    from asset_lens.core.dca_parser import dca_parser
    from asset_lens.core.irr_calculator import irr_calculator

    if reference_date is None:
        reference_date = datetime.now()

    for product in products:
        if product.transaction_records:
            transactions = dca_parser.parse_transaction_record(
                product.transaction_records,
                reference_date=reference_date,
            )
            product.transactions = transactions

            if transactions and product.current_amount:
                irr = irr_calculator.calculate_annualized_irr(
                    transactions=transactions,
                    current_value=product.current_amount,
                    reference_date=reference_date,
                )
                product.annualized_return_irr = irr
        else:
            if product.initial_amount and product.current_amount and product.investment_days:
                simple_return = irr_calculator.calculate_simple_annual_return(
                    initial_amount=product.initial_amount,
                    current_amount=product.current_amount,
                    days=product.investment_days,
                )
                product.annualized_return_irr = simple_return


def print_command_tips(commands: list[str]) -> None:
    """打印相关命令提示"""
    click.echo("\n💡 相关命令:")
    for cmd in commands:
        click.echo(f"   {cmd}")


def format_percentage(value: float | Decimal | None, decimal_places: int = 2) -> str:
    """格式化百分比"""
    if value is None:
        return "N/A"
    return f"{value:.{decimal_places}%}"


def format_amount(value: float | Decimal | None, currency: str = "¥") -> str:
    """格式化金额"""
    if value is None:
        return "N/A"
    return f"{currency}{value:,.2f}"


def get_usd_rate() -> Decimal:
    """获取美元汇率"""
    from asset_lens.config import config
    from asset_lens.data.csv_parser import CSVParser

    data_dir = config.get_latest_data_dir()
    if data_dir:
        usd_rate, _ = CSVParser.get_exchange_rates(data_dir)
        return Decimal(str(usd_rate))

    return Decimal(str(config.default_usd_rate))


def get_hkd_rate() -> Decimal:
    """获取港币汇率"""
    from asset_lens.config import config
    from asset_lens.data.csv_parser import CSVParser

    data_dir = config.get_latest_data_dir()
    if data_dir:
        _, hkd_rate = CSVParser.get_exchange_rates(data_dir)
        return Decimal(str(hkd_rate))

    return Decimal(str(config.default_hkd_rate))
