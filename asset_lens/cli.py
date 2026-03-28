"""
CLI entry point for asset-lens.
CLI 入口文件 - 包含所有命令
"""

import click
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .config import config
from .data.csv_parser import CSVParser
from .data.models import Portfolio


def _get_data_dir(data_mode: str) -> Optional[Path]:
    """获取数据目录，处理 None 情况"""
    if data_mode == "real":
        return config.get_latest_data_dir()
    else:
        return config.project_root / "data" / "sample_data"


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """asset-lens: Personal Asset Operating System"""
    config.ensure_directories()


@cli.command()
@click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
def calculate(data_mode):
    """计算所有投资产品的收益率（快捷命令）"""
    from .report.calculate_report import calculate_report_generator

    if data_mode:
        config.data_mode = data_mode
        print(f"使用数据模式: {data_mode}")

    print("\n📊 正在加载数据...")
    try:
        products = CSVParser.load_data()
        print(f"✅ 成功加载 {len(products)} 个投资产品")
    except Exception as e:
        click.echo(f"❌ 加载数据失败: {e}", err=True)
        raise click.Abort()

    data_dir = _get_data_dir(config.data_mode)
    usd_rate, hkd_rate = CSVParser.get_exchange_rates(data_dir) if data_dir else (config.default_usd_rate, config.default_hkd_rate)

    portfolio = Portfolio(
        products=products,
        usd_rate=Decimal(str(usd_rate)),
        hkd_rate=Decimal(str(hkd_rate)),
    )

    print("\n🔢 正在计算收益率...")
    reference_date = datetime.now()

    from .core.dca_parser import dca_parser
    from .core.irr_calculator import irr_calculator

    for product in portfolio.products:
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

    print("✅ 收益率计算完成")

    print("\n📝 正在生成计算报告...")
    calculate_report_generator.generate_report(portfolio)

    click.echo("\n✅ 计算完成！")


@cli.command()
@click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
@click.option("--output-format", type=click.Choice(["console", "csv", "json", "html", "all"]), default="console", help="输出格式")
@click.option("--data-path", type=str, help="数据路径")
def analyze(data_mode, output_format, data_path):
    """分析投资组合并生成报告"""
    from .report.analyzer import report_generator
    from .data.models import SellRecord
    from .data.sell_record_parser import SellRecordParser

    if data_mode:
        config.data_mode = data_mode
        print(f"使用数据模式: {data_mode}")

    print("\n📊 正在加载数据...")
    try:
        if data_path:
            products = CSVParser.load_data(Path(data_path))
        else:
            products = CSVParser.load_data()
        print(f"✅ 成功加载 {len(products)} 个投资产品")
    except Exception as e:
        click.echo(f"❌ 加载数据失败: {e}", err=True)
        raise click.Abort()

    data_dir = _get_data_dir(config.data_mode)
    usd_rate, hkd_rate = CSVParser.get_exchange_rates(data_dir) if data_dir else (config.default_usd_rate, config.default_hkd_rate)

    portfolio = Portfolio(
        products=products,
        usd_rate=Decimal(str(usd_rate)),
        hkd_rate=Decimal(str(hkd_rate)),
    )

    print("\n🔢 正在计算收益率...")
    reference_date = datetime.now()

    from .core.dca_parser import dca_parser
    from .core.irr_calculator import irr_calculator

    for product in portfolio.products:
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

    print("✅ 收益率计算完成")

    sell_records: list[SellRecord] = []
    try:
        data_dir = _get_data_dir(config.data_mode)
        if data_dir:
            csv_file = data_dir / "卖出记录-表格 1.csv"
            if csv_file.exists():
                sell_records = SellRecordParser.parse_csv_file(csv_file)
                print(f"✅ 成功加载 {len(sell_records)} 条卖出记录")
    except Exception as e:
        print(f"⚠️ 加载卖出记录失败: {e}")

    print("\n📝 正在生成分析报告...")
    report_data = report_generator.generate_analysis_report(portfolio, sell_records)

    if output_format in ["console", "all"]:
        report_generator.print_console_report(report_data)

    if output_format in ["csv", "all"]:
        csv_file = report_generator.save_csv_report(report_data, config.output_path)
        if csv_file:
            print(f"✅ CSV 报告已保存: {csv_file}")

    if output_format in ["json", "all"]:
        json_file = report_generator.save_json_report(report_data, config.output_path)
        if json_file:
            print(f"✅ JSON 报告已保存: {json_file}")

    click.echo("\n✅ 分析完成！")


@cli.command()
@click.option("--before", type=str, help="对比的前一个数据目录名")
@click.option("--after", type=str, help="对比的后一个数据目录名")
def compare(before, after):
    """对比两个时间点的投资收益变化"""
    from .report.compare_report import compare_report_generator

    click.echo("\n📊 投资收益对比分析")
    click.echo("=" * 60)

    try:
        data_dir = Path("data")
        real_dir = data_dir / "real"

        if real_dir.exists():
            data_dirs = sorted([d for d in real_dir.iterdir() if d.is_dir()], key=lambda x: x.name)
        else:
            data_dirs = sorted([d for d in data_dir.iterdir() if d.is_dir()], key=lambda x: x.name)

        if not data_dirs:
            click.echo("❌ 没有找到数据目录", err=True)
            return

        if len(data_dirs) < 2:
            click.echo("❌ 需要至少两个数据目录进行对比", err=True)
            click.echo(f"💡 当前找到 {len(data_dirs)} 个目录: {[d.name for d in data_dirs]}", err=True)
            return

        before_dir = data_dirs[-2] if not before else next((d for d in data_dirs if before in d.name), data_dirs[-2])
        after_dir = data_dirs[-1] if not after else next((d for d in data_dirs if after in d.name), data_dirs[-1])

        click.echo(f"📁 对比目录: {before_dir.name} vs {after_dir.name}")

        products_before = CSVParser.load_data_from_dir(before_dir)
        products_after = CSVParser.load_data_from_dir(after_dir)

        compare_report_generator.generate_report(products_before, products_after, before_dir.name, after_dir.name)

        click.echo("\n✅ 对比完成！")

    except Exception as e:
        click.echo(f"❌ 对比失败: {e}", err=True)


def create_cli() -> click.Group:
    """创建并配置 CLI 应用"""
    return cli


__all__ = ["cli", "create_cli"]
