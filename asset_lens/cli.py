"""
CLI (Command Line Interface) for asset-lens.
命令行接口模块
"""

import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

import click

from .config import config
from .core.dca_parser import dca_parser
from .core.irr_calculator import irr_calculator
from .data.asset_summary_parser import AssetSummaryParser
from .data.parser_utils import SELL_RECORD_EXPORT_FIELDS
from .data.csv_parser import CSVParser
from .data.exchange_rate_parser import ExchangeRateParser
from .data.models import Portfolio
from .data.sell_record_parser import SellRecordParser
from .report.analyzer import report_generator
from .utils.currency_converter import currency_converter


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
    # 确保所有必要的目录存在
    config.ensure_directories()


@cli.command()
@click.option(
    "--data-mode",
    type=click.Choice(["sample", "real"]),
    help="数据模式 (sample=示例数据, real=真实数据)",
)
@click.option(
    "--output-format",
    type=click.Choice(["console", "csv", "json", "all"]),
    default="console",
    help="输出格式",
)
@click.option("--data-path", type=click.Path(exists=True), help="自定义数据路径")
def analyze(data_mode, output_format, data_path):
    """分析投资组合并生成报告"""
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

    portfolio = Portfolio(
        products=products,
        usd_rate=Decimal(str(config.default_usd_rate)),
        hkd_rate=Decimal(str(config.default_hkd_rate)),
    )

    print("\n🔢 正在计算收益率...")
    reference_date = datetime.now()

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

    sell_records = []
    try:
        from .data.sell_record_parser import SellRecordParser

        sell_records = SellRecordParser.load_sell_records()
        if sell_records:
            print(f"✅ 成功加载 {len(sell_records)} 条卖出记录")
    except Exception as e:
        print(f"⚠️  加载卖出记录失败: {e}")

    print("\n📝 正在生成分析报告...")
    report_data = report_generator.generate_analysis_report(portfolio, sell_records)

    report_data["products"] = [
        p.to_dict() for p in portfolio.products if p.annual_return is not None
    ]

    if output_format in ["console", "all"]:
        report_generator.print_console_report(report_data)

    if output_format in ["csv", "all"]:
        csv_file = report_generator.save_csv_report(report_data, config.output_path)

    if output_format in ["json", "all"]:
        json_file = report_generator.save_json_report(report_data, config.output_path)

    print("\n✅ 分析完成!")


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

    portfolio = Portfolio(
        products=products,
        usd_rate=Decimal(str(config.default_usd_rate)),
        hkd_rate=Decimal(str(config.default_hkd_rate)),
    )

    print("\n🔢 正在计算收益率...")
    reference_date = datetime.now()

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
    report = calculate_report_generator.generate_calculate_report(portfolio)
    calculate_report_generator.print_calculate_report(report)

    print("\n✅ 计算完成!")


@cli.command()
@click.option("--data-mode", type=click.Choice(["sample", "real"]), help="当前数据模式")
@click.option("--target-mode", type=click.Choice(["sample", "real"]), required=True, help="目标数据模式")
def switch_mode(data_mode, target_mode):
    """切换数据模式（sample <-> real）"""
    # 更新 .env 文件
    env_file = config.project_root / ".env"

    if env_file.exists():
        with open(env_file, "r") as f:
            lines = f.readlines()

        # 更新 DATA_MODE
        with open(env_file, "w") as f:
            for line in lines:
                if line.startswith("DATA_MODE="):
                    f.write(f"DATA_MODE={target_mode}\n")
                else:
                    f.write(line)

        click.echo(f"✅ 数据模式已切换为: {target_mode}")
    else:
        # 创建新的 .env 文件
        with open(env_file, "w") as f:
            f.write(f"DATA_MODE={target_mode}\n")

        click.echo(f"✅ 创建 .env 文件并设置数据模式为: {target_mode}")


@cli.command()
def show_config():
    """显示当前配置"""
    click.echo("\n📋 当前配置")
    click.echo("=" * 50)
    click.echo(f"数据模式: {config.data_mode}")
    click.echo(f"数据路径: {config.data_path}")
    click.echo(f"输出路径: {config.output_path}")
    click.echo(f"缓存路径: {config.cache_path}")
    click.echo(f"默认美元汇率: {config.default_usd_rate}")
    click.echo(f"默认港元汇率: {config.default_hkd_rate}")
    click.echo(f"最低收益率阈值: {config.min_return_threshold}%")
    click.echo(f"工作日占比: {config.workday_ratio}")
    click.echo(f"输出格式: {', '.join(config.output_format)}")
    click.echo(f"报告语言: {config.report_language}")
    click.echo("=" * 50)


@cli.command()
@click.option("--currency", type=click.Choice(["USD", "HKD"]), required=True, help="货币类型")
@click.option("--rate", type=float, required=True, help="汇率（1外币 = X CNY）")
def set_rate(currency, rate):
    """设置货币汇率"""
    from decimal import Decimal

    from .data.models import Currency

    currency_enum = Currency[currency.upper()]
    currency_converter.set_rate(currency_enum, Decimal(str(rate)))
    currency_converter.save_cached_rates()

    click.echo(f"✅ 已更新 {currency} 汇率: {rate}")


@cli.command()
@click.option("--data-mode", type=click.Choice(["sample", "real"]), help="当前数据模式")
def show_asset_summary(data_mode):
    """显示资产汇总（资产汇总-表格 1.csv）"""
    from .data.asset_summary_parser import AssetSummaryParser

    data_dir = _get_data_dir(data_mode)
    if not data_dir:
        click.echo("❌ 数据目录不存在")
        return

    csv_file = data_dir / "资产汇总-表格 1.csv"

    if not csv_file.exists():
        # 兼容旧文件名
        csv_file = data_dir / "备份-表格 1.csv"

    if not csv_file.exists():
        click.echo(f"❌ 资产汇总文件不存在: {csv_file}")
        click.echo(f"💡 提示: 请确保数据目录中有相应的数据文件")
        return

    try:
        summaries = AssetSummaryParser.parse_csv_file(csv_file)
        click.echo(f"\n📊 资产汇总记录（共 {len(summaries)} 条）")
        click.echo("=" * 80)

        for summary in summaries[-10:]:  # 显示最近10条
            click.echo(f"日期: {summary.summary_date.strftime('%Y-%m-%d')}")
            click.echo(f"  总金额: ¥{summary.total_amount:,.2f}")

            # 动态显示平台金额
            from asset_lens.core.platform_loader import PlatformLoader

            PlatformLoader.reset()
            PlatformLoader.load(data_mode=config.data_mode)
            for platform in PlatformLoader.get_all_platforms():
                amount = summary.get_amount(platform.id)
                if amount > 0:
                    click.echo(f"  {platform.name}: ¥{amount:,.2f}")

            click.echo(f"  信用卡: ¥{summary.credit_card_amount:,.2f}")
            click.echo(f"  京东白条: ¥{summary.jingdong_white_amount:,.2f}")
            click.echo(f"  抖音月付: ¥{summary.douyin_monthly_amount:,.2f}")
            click.echo(f"  多多后付: ¥{summary.duoduo_later_amount:,.2f}")
            click.echo(f"  黄金: ¥{summary.gold_amount:,.2f}")
            if summary.return_rate is not None:
                click.echo(f"  收益率: {summary.return_rate:.2f}%")

        if len(summaries) > 10:
            click.echo(f"\n... 还有 {len(summaries) - 10} 条记录未显示")

        click.echo("=" * 80)
        click.echo(f"💡 提示: 使用 'asset-lens export-asset-summary --output-format csv' 导出完整数据")

    except Exception as e:
        click.echo(f"❌ 读取资产汇总失败: {e}", err=True)


@cli.command()
@click.option("--data-mode", type=click.Choice(["sample", "real"]), help="当前数据模式")
def show_exchange_rate_history(data_mode):
    """显示汇率历史（资产汇总-表格 1.csv）"""
    from .data.exchange_rate_parser import ExchangeRateParser

    data_dir = _get_data_dir(data_mode)
    if not data_dir:
        click.echo("❌ 数据目录不存在")
        return

    csv_file = data_dir / "资产汇总-表格 1.csv"

    if not csv_file.exists():
        # 兼容旧文件名
        csv_file = data_dir / "备份-表格 1.csv"

    if not csv_file.exists():
        click.echo(f"❌ 汇率历史文件不存在: {csv_file}")
        click.echo(f"💡 提示: 请确保数据目录中有相应的数据文件")
        return

    try:
        rates = ExchangeRateParser.parse_csv_file(csv_file)
        click.echo(f"\n📊 汇率历史记录（共 {len(rates)} 条）")
        click.echo("=" * 80)

        for rate in rates[-20:]:  # 显示最近20条
            click.echo(f"日期: {rate.rate_date.strftime('%Y-%m-%d')}")
            click.echo(f"  美元汇率: {rate.usd_rate:.4f}")
            click.echo(f"  港元汇率: {rate.hkd_rate:.4f}")

        if len(rates) > 20:
            click.echo(f"\n... 还有 {len(rates) - 20} 条记录未显示")

        click.echo("=" * 80)

    except Exception as e:
        click.echo(f"❌ 读取汇率历史失败: {e}", err=True)


@cli.command()
@click.option("--data-mode", type=click.Choice(["sample", "real"]), help="当前数据模式")
def show_sell_records(data_mode):
    """显示卖出记录（卖出记录-表格 1.csv）"""
    from .data.sell_record_parser import SellRecordParser

    data_dir = _get_data_dir(data_mode)
    if not data_dir:
        click.echo("❌ 数据目录不存在")
        return

    csv_file = data_dir / "卖出记录-表格 1.csv"

    if not csv_file.exists():
        click.echo(f"❌ 卖出记录文件不存在: {csv_file}")
        click.echo(f"💡 提示: 请确保数据目录中有相应的数据文件")
        return

    try:
        records = SellRecordParser.parse_csv_file(csv_file)
        click.echo(f"\n📊 卖出记录（共 {len(records)} 条）")
        click.echo("=" * 80)

        for record in records[-20:]:  # 显示最近20条
            click.echo(f"日期: {record.sell_date.strftime('%Y-%m-%d')}")
            click.echo(f"  名称: {record.name}")
            click.echo(f"  风险: {record.risk_level}")
            click.echo(f"  初始金额: ¥{record.initial_amount:,.2f}")
            click.echo(f"  收益金额: ¥{record.profit_amount:,.2f}")
            click.echo(f"  收益率: {record.return_rate:.2f}%")
            if record.investment_days:
                click.echo(f"  投资天数: {record.investment_days} 天")

        if len(records) > 20:
            click.echo(f"\n... 还有 {len(records) - 20} 条记录未显示")

        click.echo("=" * 80)

    except Exception as e:
        click.echo(f"❌ 读取卖出记录失败: {e}", err=True)


@cli.command()
@click.option("--data-mode", type=click.Choice(["sample", "real"]), help="当前数据模式")
@click.option(
    "--output-format", type=click.Choice(["console", "csv", "json"]), default="console", help="输出格式"
)
def export_asset_summary(data_mode, output_format):
    """导出资产汇总数据"""
    from .data.asset_summary_parser import AssetSummaryParser

    data_dir = _get_data_dir(data_mode)
    if not data_dir:
        click.echo("❌ 数据目录不存在")
        return

    csv_file = data_dir / "资产汇总-表格 1.csv"

    if not csv_file.exists():
        # 兼容旧文件名
        csv_file = data_dir / "备份-表格 1.csv"

    try:
        summaries = AssetSummaryParser.parse_csv_file(csv_file)

        if output_format == "console":
            click.echo(f"\n📊 资产汇总数据（共 {len(summaries)} 条）")
            click.echo("=" * 80)

            for summary in summaries:
                click.echo(f"日期: {summary.summary_date.strftime('%Y-%m-%d')}")
                click.echo(f"  总金额: ¥{summary.total_amount:,.2f}")
                click.echo(f"  总投资价值: ¥{summary.total_investment_value:,.2f}")
                click.echo(f"  收益率: {summary.return_rate:.2f}%")

            click.echo("=" * 80)

        elif output_format == "csv":
            output_file = config.output_path / "asset_summary.csv"
            import csv

            from asset_lens.core.platform_loader import PlatformLoader

            # 重置并加载正确的平台配置
            PlatformLoader.reset()
            PlatformLoader.load(data_mode=config.data_mode)

            # 动态生成字段名
            platform_fields = [f"{p.name}金额" for p in PlatformLoader.get_all_platforms()]
            base_fields = (
                ["汇总日期"]
                + platform_fields
                + [
                    "信用卡金额",
                    "京东白条金额",
                    "抖音月付金额",
                    "多多后付金额",
                    "总金额",
                    "美元汇率",
                    "港元汇率",
                    "黄金金额",
                    "兑换美元金额",
                    "兑换港元金额",
                    "兑换黄金金额",
                    "上证指数",
                    "沪深300",
                    "中证500",
                    "纳指100",
                    "标普500",
                    "恐慌VXX",
                    "美联基利率",
                    "房产总价",
                    "收益率",
                ]
            )

            with open(output_file, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=base_fields)
                writer.writeheader()

                for summary in summaries:
                    row = {
                        "汇总日期": summary.summary_date.strftime("%Y-%m-%d"),
                        "信用卡金额": str(summary.credit_card_amount),
                        "京东白条金额": str(summary.jingdong_white_amount),
                        "抖音月付金额": str(summary.douyin_monthly_amount),
                        "多多后付金额": str(summary.duoduo_later_amount),
                        "总金额": str(summary.total_amount),
                        "美元汇率": str(summary.usd_rate),
                        "港元汇率": str(summary.hkd_rate),
                        "黄金金额": str(summary.gold_amount),
                        "兑换美元金额": str(summary.exchange_usd_amount),
                        "兑换港元金额": str(summary.exchange_hkd_amount),
                        "兑换黄金金额": str(summary.exchange_gold_amount),
                        "上证指数": str(summary.shanghai_index),
                        "沪深300": str(summary.csi300_index),
                        "中证500": str(summary.csi500_index),
                        "纳指100": str(summary.nasdaq100_index),
                        "标普500": str(summary.sp500_index),
                        "恐慌VXX": str(summary.vix_index),
                        "美联基利率": str(summary.us_treasury_rate),
                        "房产总价": str(summary.property_value),
                        "收益率": f"{summary.return_rate:.2f}%" if summary.return_rate else None,
                    }
                    # 添加平台金额
                    for platform in PlatformLoader.get_all_platforms():
                        row[f"{platform.name}金额"] = str(summary.get_amount(platform.id))

                    writer.writerow(row)

            click.echo(f"✅ 资产汇总已导出到: {output_file}")

        elif output_format == "json":
            output_file = config.output_path / "asset_summary.json"
            import json

            from asset_lens.core.platform_loader import PlatformLoader

            data = []
            for summary in summaries:
                row = {
                    "汇总日期": summary.summary_date.strftime("%Y-%m-%d"),
                    "信用卡金额": str(summary.credit_card_amount),
                    "京东白条金额": str(summary.jingdong_white_amount),
                    "抖音月付金额": str(summary.douyin_monthly_amount),
                    "多多后付金额": str(summary.duoduo_later_amount),
                    "总金额": str(summary.total_amount),
                    "美元汇率": str(summary.usd_rate),
                    "港元汇率": str(summary.hkd_rate),
                    "黄金金额": str(summary.gold_amount),
                    "兑换美元金额": str(summary.exchange_usd_amount),
                    "兑换港元金额": str(summary.exchange_hkd_amount),
                    "兑换黄金金额": str(summary.exchange_gold_amount),
                    "上证指数": str(summary.shanghai_index),
                    "沪深300": str(summary.csi300_index),
                    "中证500": str(summary.csi500_index),
                    "纳指100": str(summary.nasdaq100_index),
                    "标普500": str(summary.sp500_index),
                    "恐慌VXX": str(summary.vix_index),
                    "美联基利率": str(summary.us_treasury_rate),
                    "房产总价": str(summary.property_value),
                    "收益率": f"{summary.return_rate:.2f}%" if summary.return_rate else None,
                }
                # 添加平台金额
                for platform in PlatformLoader.get_all_platforms():
                    row[f"{platform.name}金额"] = str(summary.get_amount(platform.id))

                data.append(row)

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            click.echo(f"✅ 资产汇总已导出到: {output_file}")

    except Exception as e:
        click.echo(f"❌ 导出资产汇总失败: {e}", err=True)


@cli.command()
@click.option("--data-mode", type=click.Choice(["sample", "real"]), help="当前数据模式")
@click.option(
    "--output-format", type=click.Choice(["console", "csv", "json"]), default="console", help="输出格式"
)
def export_sell_records(data_mode, output_format):
    """导出卖出记录数据"""
    from .data.sell_record_parser import SellRecordParser

    data_dir = _get_data_dir(data_mode)
    if not data_dir:
        click.echo("❌ 数据目录不存在")
        return

    csv_file = data_dir / "卖出记录-表格 1.csv"

    if not csv_file.exists():
        click.echo(f"❌ 卖出记录文件不存在: {csv_file}")
        click.echo(f"💡 提示: 请确保数据目录中有相应的数据文件")
        return

    try:
        records = SellRecordParser.parse_csv_file(csv_file)

        if output_format == "console":
            click.echo(f"\n📊 卖出记录数据（共 {len(records)} 条）")
            click.echo("=" * 80)

            for record in records:
                click.echo(f"日期: {record.sell_date.strftime('%Y-%m-%d')}")
                click.echo(f"  名称: {record.name}")
                click.echo(f"  风险: {record.risk_level}")
                click.echo(f"  初始金额: ¥{record.initial_amount:,.2f}")
                click.echo(f"  收益金额: ¥{record.profit_amount:,.2f}")
                click.echo(f"  收益率: {record.return_rate:.2f}%")
                if record.investment_days:
                    click.echo(f"  投资天数: {record.investment_days} 天")

            click.echo("=" * 80)

        elif output_format == "csv":
            output_file = config.output_path / "sell_records.csv"
            import csv

            with open(output_file, "w", encoding="utf-8-sig", newline="") as f:
                fieldnames = SELL_RECORD_EXPORT_FIELDS

                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for record in records:
                    writer.writerow(
                        {
                            "卖出日期": record.sell_date.strftime("%Y-%m-%d"),
                            "名称": record.name,
                            "风险等级": record.risk_level,
                            "到期时间": record.maturity_date.strftime("%Y-%m-%d")
                            if record.maturity_date
                            else None,
                            "是否滚动": record.is_rolling,
                            "开始日期": record.start_date.strftime("%Y-%m-%d")
                            if record.start_date
                            else None,
                            "初始金额": str(record.initial_amount),
                            "收益金额": str(record.profit_amount),
                            "收益率": f"{record.return_rate:.2f}%" if record.return_rate else None,
                            "结束日期": record.end_date.strftime("%Y-%m-%d")
                            if record.end_date
                            else None,
                            "到账日期": record.to_account_date.strftime("%Y-%m-%d")
                            if record.to_account_date
                            else None,
                            "结束到账间隔": record.end_to_account_interval,
                            "投资天数": record.investment_days,
                            "年化收益": f"{record.annual_return:.2f}%"
                            if record.annual_return
                            else None,
                            "复利年化": f"{record.compound_return:.2f}%"
                            if record.compound_return
                            else None,
                            "利息发放": str(record.interest_payment)
                            if record.interest_payment
                            else None,
                            "交易记录": record.transaction_records,
                            "默认顺序": record.default_order,
                        }
                    )

            click.echo(f"✅ 卖出记录已导出到: {output_file}")

        elif output_format == "json":
            output_file = config.output_path / "sell_records.json"
            import json

            data = [
                {
                    "卖出日期": record.sell_date.strftime("%Y-%m-%d"),
                    "名称": record.name,
                    "风险等级": record.risk_level,
                    "到期时间": record.maturity_date.strftime("%Y-%m-%d")
                    if record.maturity_date
                    else None,
                    "是否滚动": record.is_rolling,
                    "开始日期": record.start_date.strftime("%Y-%m-%d") if record.start_date else None,
                    "初始金额": str(record.initial_amount),
                    "收益金额": str(record.profit_amount),
                    "收益率": f"{record.return_rate:.2f}%" if record.return_rate else None,
                    "结束日期": record.end_date.strftime("%Y-%m-%d") if record.end_date else None,
                    "到账日期": record.to_account_date.strftime("%Y-%m-%d")
                    if record.to_account_date
                    else None,
                    "结束到账间隔": record.end_to_account_interval,
                    "投资天数": record.investment_days,
                    "年化收益": f"{record.annual_return:.2f}%" if record.annual_return else None,
                    "复利年化": f"{record.compound_return:.2f}%" if record.compound_return else None,
                    "利息发放": str(record.interest_payment) if record.interest_payment else None,
                    "交易记录": record.transaction_records,
                    "默认顺序": record.default_order,
                }
                for record in records
            ]

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            click.echo(f"✅ 卖出记录已导出到: {output_file}")

    except Exception as e:
        click.echo(f"❌ 导出卖出记录失败: {e}", err=True)


@cli.command()
@click.option("--data-mode", type=click.Choice(["sample", "real"]), help="当前数据模式")
@click.option(
    "--output-format", type=click.Choice(["console", "csv", "json"]), default="console", help="输出格式"
)
def export_exchange_rate_history(data_mode, output_format):
    """导出汇率历史数据"""
    from .data.exchange_rate_parser import ExchangeRateParser

    data_dir = _get_data_dir(data_mode)
    if not data_dir:
        click.echo("❌ 数据目录不存在")
        return

    csv_file = data_dir / "资产汇总-表格 1.csv"

    if not csv_file.exists():
        # 兼容旧文件名
        csv_file = data_dir / "备份-表格 1.csv"

    try:
        rates = ExchangeRateParser.parse_csv_file(csv_file)

        if output_format == "console":
            click.echo(f"\n📊 汇率历史数据（共 {len(rates)} 条）")
            click.echo("=" * 80)

            for rate in rates:
                click.echo(f"日期: {rate.rate_date.strftime('%Y-%m-%d')}")
                click.echo(f"  美元汇率: {rate.usd_rate:.4f}")
                click.echo(f"  港元汇率: {rate.hkd_rate:.4f}")

            click.echo("=" * 80)

        elif output_format == "csv":
            output_file = config.output_path / "exchange_rate_history.csv"
            import csv

            with open(output_file, "w", encoding="utf-8-sig", newline="") as f:
                fieldnames = ["汇率日期", "美元汇率", "港元汇率"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for rate in rates:
                    writer.writerow(
                        {
                            "汇率日期": rate.rate_date.strftime("%Y-%m-%d"),
                            "美元汇率": str(rate.usd_rate),
                            "港元汇率": str(rate.hkd_rate),
                        }
                    )

            click.echo(f"✅ 汇率历史已导出到: {output_file}")

        elif output_format == "json":
            output_file = config.output_path / "exchange_rate_history.json"
            import json

            data = [
                {
                    "汇率日期": rate.rate_date.strftime("%Y-%m-%d"),
                    "美元汇率": str(rate.usd_rate),
                    "港元汇率": str(rate.hkd_rate),
                }
                for rate in rates
            ]

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            click.echo(f"✅ 汇率历史已导出到: {output_file}")

    except Exception as e:
        click.echo(f"❌ 导出汇率历史失败: {e}", err=True)


@cli.command()
def init():
    """初始化项目（创建必要的目录和配置文件）"""
    import shutil

    # 创建目录
    config.ensure_directories()

    # 复制 .env.example 到 .env（如果不存在）
    env_file = config.project_root / ".env"
    env_example = config.project_root / ".env.example"

    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        click.echo("✅ 已创建 .env 配置文件")

    # 复制配置示例文件
    config_dir = config.project_root / "config"
    config_examples = [
        ("platforms.json.example", "platforms.json"),
        ("investment_types.json.example", "investment_types.json"),
    ]

    for example_name, target_name in config_examples:
        example_file = config_dir / example_name
        target_file = config_dir / target_name

        if not target_file.exists() and example_file.exists():
            shutil.copy(example_file, target_file)
            click.echo(f"✅ 已创建 config/{target_name}")

    click.echo("\n✅ 项目初始化完成！")
    click.echo("📝 下一步:")
    click.echo("   1. 编辑 .env 文件配置数据模式和API密钥")
    click.echo("   2. 编辑 config/platforms.json 配置投资平台（可选）")
    click.echo("   3. 运行 'asset-lens init-sample' 创建示例数据")
    click.echo("   4. 运行 'asset-lens analyze' 开始分析")


@cli.command()
def init_sample():
    """初始化示例数据"""
    sample_data_path = config.project_root / "data" / "sample_data"
    if not sample_data_path.exists():
        click.echo(f"❌ 示例数据目录不存在: {sample_data_path}", err=True)
        raise click.Abort()

    click.echo(f"✅ 示例数据目录已存在: {sample_data_path}")
    click.echo("💡 运行 'asset-lens analyze --data-mode sample' 开始分析")


@cli.command()
@click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
@click.option("--weekly", is_flag=True, help="周预估模式")
def pnl(data_mode, weekly):
    """估算实时盈亏（基于市场指数）"""
    from rich.console import Console
    from rich.table import Table

    from .core.realtime_pnl import RealtimePnlEstimator

    if data_mode:
        config.data_mode = data_mode

    click.echo(f"\n{'📊 周盈亏估算' if weekly else '📊 日盈亏估算'}")
    click.echo("=" * 60)

    try:
        # 加载投资产品数据
        products = CSVParser.load_data()
        click.echo(f"✅ 成功加载 {len(products)} 个投资产品")

        # 创建估算器
        estimator = RealtimePnlEstimator()

        # 估算盈亏
        result = estimator.estimate_portfolio_pnl(products, is_weekly=weekly)

        if "error" in result:
            click.echo(f"❌ {result['error']}", err=True)
            click.echo("💡 提示: 请先更新市场指数数据缓存")
            return

        # 显示结果
        console = Console()

        # 显示总体盈亏
        click.echo(f"\n💰 总盈亏: ¥{result['total']:,.2f}")
        click.echo(f"📈 估算产品收益率: {result['total_return_rate']:.2f}%")
        click.echo(f"💵 估算产品金额: ¥{result['total_amount']:,.2f}")
        if "total_amount_all" in result:
            total_amount_all = Decimal(str(result['total_amount_all']))
            total_pnl = Decimal(str(result['total']))
            total_return_rate_all = float((total_pnl / total_amount_all * 100) if total_amount_all > 0 else Decimal(0))
            click.echo(f"💵 所有产品金额: ¥{total_amount_all:,.2f}")
            click.echo(f"📊 总资产收益率: {float(total_return_rate_all):.4f}%")

        # 显示指数涨跌幅
        click.echo(f"\n📊 市场指数涨跌幅:")
        for index_key, move in result["moves"].items():
            click.echo(f"  {index_key}: {move:+.2f}%")

        # 显示明细表格
        if result["details"]:
            table = Table(title="\n产品盈亏明细", show_lines=False, expand=True)
            table.add_column("产品名称", style="cyan", no_wrap=True, overflow="ellipsis", min_width=20)
            table.add_column("类型", style="green", no_wrap=True, overflow="ellipsis", min_width=10)
            table.add_column("金额", justify="right", style="yellow", min_width=10)
            table.add_column("盈亏", justify="right", min_width=8)
            table.add_column("收益率", justify="right", min_width=7)
            table.add_column("指数", style="blue", no_wrap=True, min_width=6)

            for detail in result["details"][:20]:
                table.add_row(
                    detail["name"],
                    detail["type"],
                    f"¥{detail['amount']:,.0f}",
                    f"¥{detail['pnl']:,.0f}",
                    f"{detail['return_rate']:.2f}%",
                    detail["index_key"],
                )

            console.print(table)

        click.echo(f"\n✅ 估算完成！")

    except Exception as e:
        click.echo(f"❌ 估算失败: {e}", err=True)


@cli.command()
@click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
@click.option("--weekly", is_flag=True, help="周预估模式")
def estimate(data_mode, weekly):
    """全产品收益估算（基于预期年化收益率）"""
    from rich.console import Console
    from rich.table import Table

    from .core.daily_estimate import estimate_all_products
    from .core.realtime_pnl import RealtimePnlEstimator

    if data_mode:
        config.data_mode = data_mode

    period_text = "周" if weekly else "日"
    click.echo(f"\n📊 全产品{period_text}收益估算")
    click.echo("=" * 60)

    try:
        products = CSVParser.load_data()
        click.echo(f"✅ 成功加载 {len(products)} 个投资产品")

        estimator = RealtimePnlEstimator()
        market_change = Decimal("0")
        
        try:
            moves = estimator.read_index_moves_from_cache(is_weekly=weekly)
            if moves:
                total_change = Decimal("0")
                count = 0
                for key, value in moves.items():
                    total_change += Decimal(str(value))
                    count += 1
                if count > 0:
                    market_change = total_change / count / Decimal("100")
        except Exception:
            pass

        results = estimate_all_products(products, market_change, is_weekly=weekly)

        if not results:
            click.echo("❌ 没有可估算的产品", err=True)
            return

        up_results = [r for r in results if r.estimated_daily_return >= 0]
        down_results = [r for r in results if r.estimated_daily_return < 0]

        up_results.sort(key=lambda x: x.estimated_daily_return, reverse=True)
        down_results.sort(key=lambda x: x.estimated_daily_return)

        console = Console()

        if up_results:
            click.echo(f"\n🟢 上涨产品 ({len(up_results)} 个):")
            table = Table(show_header=True, header_style="bold blue", expand=True)
            table.add_column("产品名称", style="cyan", no_wrap=True, min_width=20)
            table.add_column("类型", min_width=6)
            table.add_column("风险", min_width=4)
            table.add_column("市值", justify="right", min_width=10)
            table.add_column("预估收益", justify="right", min_width=8)
            table.add_column("收益率", justify="right", min_width=7)
            table.add_column("年化", justify="right", min_width=5)

            for result in up_results[:30]:
                table.add_row(
                    result.product_name,
                    result.product_type[:6],
                    (result.risk_level or "未知")[:4],
                    f"¥{result.current_value:,.0f}",
                    f"¥{result.estimated_daily_return:,.0f}",
                    f"{result.estimated_daily_return_rate * 100:.2f}%",
                    f"{result.expected_annual_return * 100:.1f}%",
                )

            console.print(table)

        if down_results:
            click.echo(f"\n🔴 下跌产品 ({len(down_results)} 个):")
            table = Table(show_header=True, header_style="bold blue", expand=True)
            table.add_column("产品名称", style="cyan", no_wrap=True, min_width=20)
            table.add_column("类型", min_width=6)
            table.add_column("风险", min_width=4)
            table.add_column("市值", justify="right", min_width=10)
            table.add_column("预估收益", justify="right", min_width=8)
            table.add_column("收益率", justify="right", min_width=7)
            table.add_column("年化", justify="right", min_width=5)

            for result in down_results[:30]:
                table.add_row(
                    result.product_name,
                    result.product_type[:6],
                    (result.risk_level or "未知")[:4],
                    f"¥{result.current_value:,.0f}",
                    f"¥{result.estimated_daily_return:,.0f}",
                    f"{result.estimated_daily_return_rate * 100:.2f}%",
                    f"{result.expected_annual_return * 100:.1f}%",
                )

            console.print(table)

        total_return = sum(r.estimated_daily_return for r in results)
        total_value = sum(r.current_value for r in results)
        avg_return_rate = total_return / total_value * 100 if total_value > 0 else 0

        click.echo(f"\n📊 汇总:")
        click.echo(f"  总预估收益: ¥{total_return:,.2f}")
        click.echo(f"  总市值: ¥{total_value:,.2f}")
        click.echo(f"  平均收益率: {avg_return_rate:.4f}%")
        click.echo(f"\n✅ 估算完成！")

    except Exception as e:
        click.echo(f"❌ 估算失败: {e}", err=True)


@cli.command()
@click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
def analyze_sold(data_mode):
    """分析已卖出投资"""
    from rich.console import Console
    from rich.table import Table

    from .core.sold_investment import SoldInvestmentAnalyzer

    if data_mode:
        config.data_mode = data_mode

    click.echo("\n📊 已卖出投资分析")
    click.echo("=" * 60)

    try:
        # 加载卖出记录
        data_dir = _get_data_dir(config.data_mode)
        if not data_dir:
            click.echo("❌ 数据目录不存在", err=True)
            return

        csv_file = data_dir / "卖出记录-表格 1.csv"

        if not csv_file.exists():
            click.echo(f"❌ 卖出记录文件不存在: {csv_file}", err=True)
            return

        sell_records = SellRecordParser.parse_csv_file(csv_file)
        click.echo(f"✅ 成功加载 {len(sell_records)} 条卖出记录")

        # 创建分析器
        analyzer = SoldInvestmentAnalyzer()

        # 分析已卖出投资
        result = analyzer.analyze_sold_investments(sell_records)

        # 显示统计结果
        stats = result["stats"]
        click.echo(f"\n📈 总体统计:")
        click.echo(f"  总记录数: {stats.total_records}")
        click.echo(f"  总初始投资: ¥{stats.total_initial:,.2f}")
        click.echo(f"  总收益: ¥{stats.total_profit:,.2f}")
        click.echo(f"  总收益率: {stats.total_return_rate:.2f}%")
        click.echo(f"  正收益数量: {stats.positive_count}")
        click.echo(f"  负收益数量: {stats.negative_count}")
        click.echo(f"  平均持有天数: {stats.avg_holding_days:.1f}天")
        click.echo(f"  平均收益率: {stats.avg_return_rate:.2f}%")

        # 显示明细（使用列表格式，更适合窄终端）
        if result["details"]:
            console = Console(force_terminal=True)
            console.print("\n[bold cyan]📋 已卖出投资明细（前20条）：[/bold cyan]")
            console.print("[dim]─" * 50 + "[/dim]")
            for detail in result["details"][:20]:
                profit_color = "green" if detail.profit_amount >= 0 else "red"
                profit_sign = "+" if detail.profit_amount >= 0 else ""
                console.print(f"[bold white]• {detail.name}[/bold white]")
                console.print(f"  [dim]日期:[/dim] [yellow]{detail.sell_date.strftime('%Y-%m-%d')}[/yellow] | [dim]收益:[/dim] [{profit_color}]¥{detail.profit_amount:,.0f} ({profit_sign}{detail.return_rate:.1f}%)[/{profit_color}] | [dim]年化:[/dim] [blue]{detail.annualized_return:.1f}%[/blue]")
            if len(result["details"]) > 20:
                console.print(f"\n[dim]... 还有 {len(result['details']) - 20} 条记录未显示[/dim]")

        click.echo(f"\n✅ 分析完成！")

    except Exception as e:
        click.echo(f"❌ 分析失败: {e}", err=True)


@cli.command()
@click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
def analyze_by_time(data_mode):
    """按投资时间分组分析"""
    from rich.console import Console
    from rich.table import Table

    from .core.time_group import TimeGroupAnalyzer

    if data_mode:
        config.data_mode = data_mode

    click.echo("\n📊 按投资时间分组分析")
    click.echo("=" * 60)

    try:
        # 加载投资产品数据
        products = CSVParser.load_data()
        click.echo(f"✅ 成功加载 {len(products)} 个投资产品")

        # 创建分析器
        analyzer = TimeGroupAnalyzer()

        # 按持有时间分组分析
        result = analyzer.analyze_by_holding_period(products)

        # 显示总体统计
        click.echo(f"\n📈 总体统计:")
        click.echo(f"  总产品数: {result['total_products']}")
        click.echo(f"  总金额: ¥{result['total_amount']:,.2f}")
        click.echo(f"  总初始投资: ¥{result['total_initial']:,.2f}")
        click.echo(f"  总收益: ¥{result['total_profit']:,.2f}")
        click.echo(f"  总收益率: {result['total_return_rate']:.2f}%")

        # 显示分组表格
        if result["groups"]:
            console = Console()
            table = Table(title="\n投资时间分组统计")
            table.add_column("分组", style="cyan", no_wrap=True)
            table.add_column("描述", style="green", no_wrap=True)
            table.add_column("产品数", justify="right")
            table.add_column("总金额", justify="right", style="yellow")
            table.add_column("总收益", justify="right")
            table.add_column("平均收益率", justify="right")
            table.add_column("平均持有天数", justify="right")

            for group in result["groups"]:
                profit_color = "green" if group.total_profit >= 0 else "red"
                return_color = "green" if group.avg_return_rate >= 0 else "red"

                table.add_row(
                    group.group_name,
                    group.group_description,
                    str(group.products_count),
                    f"¥{group.total_amount:,.0f}",
                    f"¥{group.total_profit:,.2f}",
                    f"{group.avg_return_rate:.2f}%",
                    f"{group.avg_holding_days:.1f}天",
                )

            console.print(table)

        click.echo(f"\n✅ 分析完成！")

    except Exception as e:
        click.echo(f"❌ 分析失败: {e}", err=True)


@cli.command()
@click.option(
    "--api",
    type=click.Choice(["finnhub", "alphavantage"]),
    default="alphavantage",
    help="选择海外市场数据 API (alphavantage: 完整历史数据, finnhub: 仅实时数据)",
)
@click.option("--async", "use_async", is_flag=True, help="使用异步并发获取数据")
def update_market_data(api, use_async):
    """更新市场指数数据

    API 选择说明：
    - alphavantage: 获取完整历史数据（最近一周OHLCV、周期表现、技术状态），免费版25次/天
    - finnhub: 仅获取实时报价数据，免费版60次/分钟

    推荐使用 alphavantage 以获得与 ts-demo 一致的数据格式
    """

    click.echo("\n📊 更新市场指数数据")
    click.echo("=" * 60)

    if use_async:
        import asyncio

        from .data.async_market_data_fetcher import AsyncMarketDataFetcher

        click.echo("🚀 使用异步并发模式")

        try:
            fetcher = AsyncMarketDataFetcher(max_concurrent=5, request_delay=0.3)

            if api == "finnhub":
                result: Dict[str, Any] = asyncio.run(fetcher.fetch_all_foreign_indexes_async())
                success = bool(result.get("data"))
            else:
                domestic_success, foreign_success = asyncio.run(fetcher.update_all_caches_async())
                success = bool(domestic_success) and bool(foreign_success)

            if success:
                click.echo("\n✅ 市场指数数据更新成功！")
            else:
                click.echo("\n❌ 市场指数数据更新失败！", err=True)

        except ImportError:
            click.echo("❌ 需要安装 aiohttp: pip install aiohttp", err=True)
        except Exception as e:
            click.echo(f"❌ 更新失败: {e}", err=True)
    else:
        from .data.market_data_fetcher import MarketDataFetcher

        if api == "alphavantage":
            click.echo("📌 使用 Alpha Vantage API（获取完整历史数据）")
            click.echo("   - 包含：历史走势、周期表现、技术状态")
            click.echo("   - 限制：25次/天，每次请求间隔12秒")
        else:
            click.echo("📌 使用 Finnhub API（仅获取实时数据）")
            click.echo("   - 包含：实时报价、涨跌幅")
            click.echo("   - 限制：60次/分钟")

        click.echo("")

        try:
            sync_fetcher: Any = MarketDataFetcher()
            domestic_result: Dict[str, Any] = sync_fetcher.fetch_all_domestic_indexes()  # type: ignore
            foreign_result: Dict[str, Any] = sync_fetcher.fetch_all_foreign_indexes()  # type: ignore
            success = bool(domestic_result.get("data")) and bool(foreign_result.get("data"))

            if success:
                click.echo("\n✅ 市场指数数据更新成功！")
                click.echo("💡 运行 'make estimate-pnl' 开始估算实时盈亏")
            else:
                click.echo("\n❌ 市场指数数据更新失败！", err=True)
                click.echo("💡 请检查网络连接或稍后重试")

        except Exception as e:
            click.echo(f"❌ 更新失败: {e}", err=True)


@cli.command("ai-analyze")
@click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
@click.option(
    "--risk-preference",
    type=click.Choice(["conservative", "balanced", "aggressive"]),
    default="balanced",
    help="风险偏好",
)
def ai_analyze(data_mode, risk_preference):
    """AI 分析投资组合（需要配置 OPENAI_API_KEY）"""
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    from .core.ai_analyzer import ai_analyzer

    if data_mode:
        config.data_mode = data_mode

    click.echo("\n🤖 AI 投资组合分析")
    click.echo("=" * 60)

    try:
        # 加载数据
        products = CSVParser.load_data()
        portfolio = Portfolio(
            products,
            usd_rate=Decimal(str(config.default_usd_rate)),
            hkd_rate=Decimal(str(config.default_hkd_rate)),
        )
        click.echo(f"✅ 成功加载 {len(products)} 个投资产品")

        # 准备分析数据
        portfolio_data: Dict[str, Any] = {
            "total_value": float(portfolio.total_value),
            "total_profit": float(portfolio.total_profit),
            "overall_return_rate": float(portfolio.overall_return_rate)
            if portfolio.overall_return_rate
            else 0,
            "total_products": len(portfolio.products),
            "risk_distribution": {},
            "type_distribution": {},
            "products": [],
            "low_returns": [],
        }

        # 计算风险分布
        for p in portfolio.products:
            risk_name = p.risk_level.value if p.risk_level else "未知"
            if risk_name not in portfolio_data["risk_distribution"]:
                portfolio_data["risk_distribution"][risk_name] = {"total_value": 0, "percentage": 0}
            portfolio_data["risk_distribution"][risk_name]["total_value"] += float(
                p.current_amount or 0
            )

        for risk_name in portfolio_data["risk_distribution"]:
            portfolio_data["risk_distribution"][risk_name]["percentage"] = (
                portfolio_data["risk_distribution"][risk_name]["total_value"]
                / portfolio_data["total_value"]
                * 100
            )

        # 计算类型分布
        for p in portfolio.products:
            type_name = p.investment_type.value
            if type_name not in portfolio_data["type_distribution"]:
                portfolio_data["type_distribution"][type_name] = {"total_value": 0, "percentage": 0}
            portfolio_data["type_distribution"][type_name]["total_value"] += float(
                p.current_amount or 0
            )

        for type_name in portfolio_data["type_distribution"]:
            portfolio_data["type_distribution"][type_name]["percentage"] = (
                portfolio_data["type_distribution"][type_name]["total_value"]
                / portfolio_data["total_value"]
                * 100
            )

        # 添加产品列表
        for p in portfolio.products[:20]:
            portfolio_data["products"].append(
                {
                    "name": p.name,
                    "current_amount": float(p.current_amount or 0),
                    "profit_amount": float(p.profit_amount or 0),
                    "return_rate": float(p.return_rate or 0),
                    "annual_return": float(p.annual_return or 0),
                    "investment_days": p.investment_days or 0,
                }
            )

        # 添加低收益产品
        for p in portfolio.products:
            if p.annual_return is not None and p.annual_return < 2:
                portfolio_data["low_returns"].append(
                    {
                        "name": p.name,
                        "annual_return": float(p.annual_return),
                    }
                )

        # 执行 AI 分析
        click.echo(f"\n📊 AI 客户端状态: {'已连接' if ai_analyzer.client else '未连接（使用规则分析）'}")

        result = ai_analyzer.generate_investment_advice(portfolio_data, risk_preference)

        # 显示结果
        console = Console()

        # 投资摘要
        console.print(Panel(result["summary"], title="📋 投资摘要", border_style="blue"))

        # 风险评估
        console.print(Panel(result["risk_assessment"], title="⚠️ 风险评估", border_style="yellow"))

        # 综合评分
        score_color = (
            "green" if result["score"] >= 60 else "yellow" if result["score"] >= 40 else "red"
        )
        console.print(
            Panel(
                f"综合评分: {result['score']} 分 ({result['score_level']})",
                title="📊 综合评分",
                border_style=score_color,
            )
        )

        # 投资建议
        if result["suggestions"]:
            console.print("\n💡 投资建议:")
            for i, suggestion in enumerate(result["suggestions"], 1):
                console.print(f"  {i}. {suggestion}")

        # 风险警告
        if result["warnings"]:
            console.print("\n⚠️ 风险警告:")
            for warning in result["warnings"]:
                console.print(f"  - {warning}")

        # 推荐配置
        if result.get("recommended_allocation"):
            table = Table(title="\n📊 推荐资产配置")
            table.add_column("资产类型", style="cyan", no_wrap=True)
            table.add_column("推荐比例", justify="right", style="green")

            for asset_type, ratio in result["recommended_allocation"].items():
                table.add_row(asset_type, f"{ratio}%")

            console.print(table)

        click.echo(f"\n✅ AI 分析完成！")
        click.echo(f"💡 AI 模式: {'已启用' if result.get('ai_enabled') else '规则分析'}")

    except Exception as e:
        click.echo(f"❌ AI 分析失败: {e}", err=True)


@cli.command("portfolio-metrics")
@click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
def portfolio_metrics_cmd(data_mode):
    """计算投资组合专业指标（夏普比率、最大回撤等）"""
    import math
    import random

    from rich.console import Console
    from rich.table import Table

    from .core.portfolio_analytics import portfolio_analytics

    if data_mode:
        config.data_mode = data_mode

    click.echo("\n📊 投资组合专业指标分析")
    click.echo("=" * 60)

    try:
        # 加载数据
        products = CSVParser.load_data()
        portfolio = Portfolio(
            products,
            usd_rate=Decimal(str(config.default_usd_rate)),
            hkd_rate=Decimal(str(config.default_hkd_rate)),
        )
        click.echo(f"✅ 成功加载 {len(products)} 个投资产品")

        # 显示投资组合基本信息
        total_value = float(portfolio.total_value)
        total_profit = float(portfolio.total_profit)
        total_return_rate = (total_profit / total_value * 100) if total_value > 0 else 0

        click.echo(f"\n📈 投资组合概况:")
        click.echo(f"  总市值: ¥{total_value:,.2f}")
        click.echo(f"  总收益: ¥{total_profit:,.2f}")
        click.echo(f"  总收益率: {total_return_rate:.2f}%")

        # 生成模拟的日收益率序列
        # 基于整体收益率和平均投资天数计算
        avg_investment_days = sum(
            p.investment_days or 0 for p in portfolio.products if p.investment_days
        ) / max(1, len([p for p in portfolio.products if p.investment_days]))
        trading_days = min(int(avg_investment_days), 252)

        if trading_days < 10:
            click.echo("❌ 投资天数不足，无法计算指标", err=True)
            return

        # 计算日收益率（使累积收益率等于总收益率）
        # 使用复利公式: (1 + r_daily)^n = 1 + r_total
        # r_daily = (1 + r_total)^(1/n) - 1
        daily_return = (1 + total_return_rate / 100) ** (1 / trading_days) - 1

        # 生成带有波动的日收益率序列
        returns = []
        cumulative = 1.0
        for i in range(trading_days):
            # 添加随机波动（标准差约为日均收益率的2倍）
            noise = random.gauss(0, abs(daily_return) * 2 + 0.003)
            daily_with_noise = daily_return + noise
            returns.append(daily_with_noise)
            cumulative *= 1 + daily_with_noise

        # 调整最后一天的收益率，使累积收益率等于总收益率
        if len(returns) > 0:
            target_cumulative = 1 + total_return_rate / 100
            current_cumulative = 1.0
            for r in returns[:-1]:
                current_cumulative *= 1 + r
            # 计算最后一天需要的收益率
            last_return = (target_cumulative / current_cumulative) - 1
            returns[-1] = last_return

        # 计算指标
        metrics = portfolio_analytics.calculate_metrics(returns)
        risk_metrics = portfolio_analytics.calculate_risk_metrics(returns)

        # 显示业绩指标
        console = Console()

        table1 = Table(title="\n📈 业绩指标")
        table1.add_column("指标", style="cyan")
        table1.add_column("值", justify="right", style="green")

        table1.add_row("总收益率", f"{metrics.total_return:.2f}%")
        table1.add_row("年化收益率", f"{metrics.annualized_return:.2f}%")
        table1.add_row("波动率（年化）", f"{metrics.volatility:.2f}%")
        table1.add_row("夏普比率", f"{metrics.sharpe_ratio:.2f}")
        table1.add_row("最大回撤", f"{metrics.max_drawdown:.2f}%")
        table1.add_row("胜率", f"{metrics.win_rate:.1f}%")
        table1.add_row("盈亏比", f"{metrics.profit_loss_ratio:.2f}")
        table1.add_row("卡玛比率", f"{metrics.calmar_ratio:.2f}")
        table1.add_row("索提诺比率", f"{metrics.sortino_ratio:.2f}")

        console.print(table1)

        # 显示风险指标
        table2 = Table(title="⚠️ 风险指标")
        table2.add_column("指标", style="cyan")
        table2.add_column("值", justify="right", style="yellow")

        table2.add_row("VaR (95%)", f"{risk_metrics.value_at_risk_95:.2f}%")
        table2.add_row("VaR (99%)", f"{risk_metrics.value_at_risk_99:.2f}%")
        table2.add_row("预期亏损 (CVaR)", f"{risk_metrics.expected_shortfall:.2f}%")
        table2.add_row("Beta", f"{risk_metrics.beta:.2f}")
        table2.add_row("跟踪误差", f"{risk_metrics.tracking_error:.2f}%")
        table2.add_row("信息比率", f"{risk_metrics.information_ratio:.2f}")

        console.print(table2)

        # 生成报告
        report = portfolio_analytics.generate_report(returns)
        console.print(f"\n📝 综合评价: {report['evaluation']}")

        click.echo(f"\n💡 提示: 以上指标基于模拟日收益率序列计算，仅供参考")
        click.echo(f"   实际指标应使用历史净值数据计算")

        click.echo(f"\n✅ 指标计算完成！")

    except Exception as e:
        click.echo(f"❌ 计算失败: {e}", err=True)


@cli.command("compare")
@click.option("--before", type=str, help="对比开始日期 (YYYYMMDD)")
@click.option("--after", type=str, help="对比结束日期 (YYYYMMDD)")
@click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
def compare_cmd(before, after, data_mode):
    """对比不同时期的投资收益变化"""
    from datetime import date, timedelta

    from rich.console import Console
    from rich.table import Table

    from .core.comparison import ComparisonAnalyzer

    if data_mode:
        config.data_mode = data_mode

    console = Console()

    click.echo("\n📊 投资收益对比分析")
    click.echo("=" * 60)

    try:
        # 解析日期
        if not before or not after:
            today = date.today()
            after_date = today.strftime("%Y%m%d")
            before_date = (today - timedelta(days=7)).strftime("%Y%m%d")
        else:
            before_date = before
            after_date = after

        # 查找数据目录
        data_root = config.project_root / "data"
        if config.data_mode == "real":
            data_root = data_root / "real"

        # 查找最接近的数据目录
        before_dir = _find_closest_data_dir(data_root, before_date)
        after_dir = _find_closest_data_dir(data_root, after_date)

        if not before_dir:
            click.echo(f"❌ 找不到 {before_date} 附近的数据目录", err=True)
            return

        if not after_dir:
            click.echo(f"❌ 找不到 {after_date} 附近的数据目录", err=True)
            return

        click.echo(f"\n📅 对比数据: {before_dir.name} → {after_dir.name}")

        # 加载数据
        before_products = CSVParser.load_data_from_dir(before_dir)
        after_products = CSVParser.load_data_from_dir(after_dir)

        click.echo(f"  之前产品数: {len(before_products)}")
        click.echo(f"  之后产品数: {len(after_products)}")

        # 创建对比分析器
        analyzer = ComparisonAnalyzer()

        # 生成对比报告
        result = analyzer.compare_periods(before_products, after_products, "周度对比")

        # 显示趋势分析
        trend = result.get("trend")
        if trend:
            console.print(f"\n📈 总体趋势:")
            console.print(f"  之前总金额: ¥{float(trend.total_amount_before):,.2f}")
            console.print(f"  之后总金额: ¥{float(trend.total_amount_after):,.2f}")
            console.print(f"  总变化: ¥{float(trend.total_change):,.2f}")
            console.print(f"  总收益率: {float(trend.total_return_rate):.2f}%")
            console.print(f"  正收益产品: {trend.positive_count} 个")
            console.print(f"  负收益产品: {trend.negative_count} 个")

        # 显示产品对比结果
        details = result.get("details", [])
        if details:
            # 按收益率排序
            sorted_details = sorted(details, key=lambda x: x.return_rate, reverse=True)

            console.print(f"\n📊 收益率变化前10名:")

            table = Table(show_header=True, header_style="bold white on blue")
            table.add_column("名称", style="cyan", no_wrap=True)
            table.add_column("之前金额", justify="right")
            table.add_column("之后金额", justify="right")
            table.add_column("变化", justify="right")
            table.add_column("收益率", justify="right")

            for item in sorted_details[:10]:
                table.add_row(
                    item.name,
                    f"¥{float(item.amount_before):,.2f}",
                    f"¥{float(item.amount_after):,.2f}",
                    f"¥{float(item.amount_change):,.2f}",
                    f"{float(item.return_rate):.2f}%",
                )

            console.print(table)

        click.echo(f"\n✅ 对比分析完成！")

    except Exception as e:
        click.echo(f"❌ 对比分析失败: {e}", err=True)


def _find_closest_data_dir(data_root: Path, target_date: str) -> Optional[Path]:
    """查找最接近目标日期的数据目录"""
    if not data_root.exists():
        return None

    # 获取所有 money_csv_* 目录
    data_dirs = sorted(
        [d for d in data_root.iterdir() if d.is_dir() and d.name.startswith("money_csv_")],
        key=lambda x: x.name,
    )

    if not data_dirs:
        return None

    # 查找最接近的目录
    target = target_date
    for d in reversed(data_dirs):
        dir_date = d.name.replace("money_csv_", "")
        if dir_date <= target:
            return d

    # 如果没有找到，返回最新的目录
    return data_dirs[-1] if data_dirs else None


@cli.command()
@click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
@click.option("--output-dir", type=click.Path(), help="输出目录")
def generate_charts(data_mode, output_dir):
    """生成投资分析图表"""
    from pathlib import Path

    from rich.console import Console

    from .report.charts import ChartGenerator

    if data_mode:
        config.data_mode = data_mode

    console = Console()

    click.echo("\n📊 生成投资分析图表")
    click.echo("=" * 60)

    try:
        products = CSVParser.load_data()
        portfolio = Portfolio(
            products,
            usd_rate=Decimal(str(config.default_usd_rate)),
            hkd_rate=Decimal(str(config.default_hkd_rate)),
        )
        click.echo(f"✅ 成功加载 {len(products)} 个投资产品")

        output_path = Path(output_dir) if output_dir else None
        chart_gen = ChartGenerator(output_path)

        portfolio_data: Dict[str, Any] = {
            "type_distribution": {},
            "risk_distribution": {},
            "top_products": [],
        }

        for p in portfolio.products:
            type_name = p.investment_type.value if p.investment_type else "未知"
            if type_name not in portfolio_data["type_distribution"]:
                portfolio_data["type_distribution"][type_name] = {"total_value": 0}
            portfolio_data["type_distribution"][type_name]["total_value"] += float(
                p.current_amount or 0
            )

        for p in portfolio.products:
            risk_name = p.risk_level.value if p.risk_level else "未知"
            if risk_name not in portfolio_data["risk_distribution"]:
                portfolio_data["risk_distribution"][risk_name] = {"total_value": 0}
            portfolio_data["risk_distribution"][risk_name]["total_value"] += float(
                p.current_amount or 0
            )

        sorted_products = sorted(
            portfolio.products, key=lambda x: float(x.current_amount or 0), reverse=True
        )
        portfolio_data["top_products"] = [
            {"name": p.name, "current_amount": float(p.current_amount or 0)}
            for p in sorted_products[:10]
        ]

        charts = chart_gen.generate_all_charts(portfolio_data)

        click.echo(f"\n✅ 已生成 {len(charts)} 个图表:")
        for name, path in charts.items():
            click.echo(f"  - {name}: {path}")

    except Exception as e:
        click.echo(f"❌ 生成图表失败: {e}", err=True)


@cli.command()
@click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
@click.option("--output-dir", type=click.Path(), help="输出目录")
@click.option("--include-ai", is_flag=True, help="包含 AI 分析")
def generate_report(data_mode, output_dir, include_ai):
    """生成投资分析报告（PDF）"""
    from pathlib import Path

    from .report.charts import ChartGenerator
    from .report.pdf_report import PDFReportGenerator

    if data_mode:
        config.data_mode = data_mode

    click.echo("\n📊 生成投资分析报告")
    click.echo("=" * 60)

    try:
        products = CSVParser.load_data()
        portfolio = Portfolio(
            products,
            usd_rate=Decimal(str(config.default_usd_rate)),
            hkd_rate=Decimal(str(config.default_hkd_rate)),
        )
        click.echo(f"✅ 成功加载 {len(products)} 个投资产品")

        output_path = Path(output_dir) if output_dir else None

        portfolio_data: Dict[str, Any] = {
            "total_value": float(portfolio.total_value),
            "total_profit": float(portfolio.total_profit),
            "overall_return_rate": float(portfolio.overall_return_rate)
            if portfolio.overall_return_rate
            else 0,
            "total_products": len(portfolio.products),
            "type_distribution": {},
            "risk_distribution": {},
        }

        for p in portfolio.products:
            type_name = p.investment_type.value if p.investment_type else "未知"
            if type_name not in portfolio_data["type_distribution"]:
                portfolio_data["type_distribution"][type_name] = {"total_value": 0}
            portfolio_data["type_distribution"][type_name]["total_value"] += float(
                p.current_amount or 0
            )

        for p in portfolio.products:
            risk_name = p.risk_level.value if p.risk_level else "未知"
            if risk_name not in portfolio_data["risk_distribution"]:
                portfolio_data["risk_distribution"][risk_name] = {"total_value": 0}
            portfolio_data["risk_distribution"][risk_name]["total_value"] += float(
                p.current_amount or 0
            )

        chart_gen = ChartGenerator(output_path)
        charts = chart_gen.generate_all_charts(portfolio_data)
        click.echo(f"✅ 已生成 {len(charts)} 个图表")

        analysis_result = None
        if include_ai:
            from .core.ai_analyzer import ai_analyzer

            click.echo("🤖 正在进行 AI 分析...")
            ai_result = ai_analyzer.analyze_portfolio(portfolio_data)
            analysis_result = {
                "summary": ai_result.summary,
                "risk_assessment": ai_result.risk_assessment,
                "suggestions": ai_result.suggestions,
                "warnings": ai_result.warnings,
                "score": ai_result.score,
            }

        pdf_gen = PDFReportGenerator(output_path)
        report_path = pdf_gen.generate_investment_report(
            portfolio_data, analysis_result, charts
        )

        click.echo(f"\n✅ 报告已生成: {report_path}")

    except Exception as e:
        click.echo(f"❌ 生成报告失败: {e}", err=True)


@cli.command()
@click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
@click.option("--output-dir", type=click.Path(), help="输出目录")
@click.option("--include-ai", is_flag=True, help="包含 AI 分析")
def generate_html_report(data_mode, output_dir, include_ai):
    """生成投资分析报告（HTML）"""
    from pathlib import Path

    from .report.charts import ChartGenerator
    from .report.html_report import HTMLReportGenerator

    if data_mode:
        config.data_mode = data_mode

    click.echo("\n📊 生成投资分析报告（HTML）")
    click.echo("=" * 60)

    try:
        products = CSVParser.load_data()
        portfolio = Portfolio(
            products,
            usd_rate=Decimal(str(config.default_usd_rate)),
            hkd_rate=Decimal(str(config.default_hkd_rate)),
        )
        click.echo(f"✅ 成功加载 {len(products)} 个投资产品")

        output_path = Path(output_dir) if output_dir else None

        portfolio_data: Dict[str, Any] = {
            "total_value": float(portfolio.total_value),
            "total_profit": float(portfolio.total_profit),
            "overall_return_rate": float(portfolio.overall_return_rate)
            if portfolio.overall_return_rate
            else 0,
            "total_products": len(portfolio.products),
            "type_distribution": {},
            "risk_distribution": {},
        }

        for p in portfolio.products:
            type_name = p.investment_type.value if p.investment_type else "未知"
            if type_name not in portfolio_data["type_distribution"]:
                portfolio_data["type_distribution"][type_name] = {"total_value": 0}
            portfolio_data["type_distribution"][type_name]["total_value"] += float(
                p.current_amount or 0
            )

        for p in portfolio.products:
            risk_name = p.risk_level.value if p.risk_level else "未知"
            if risk_name not in portfolio_data["risk_distribution"]:
                portfolio_data["risk_distribution"][risk_name] = {"total_value": 0}
            portfolio_data["risk_distribution"][risk_name]["total_value"] += float(
                p.current_amount or 0
            )

        chart_gen = ChartGenerator(output_path)
        charts = chart_gen.generate_all_charts(portfolio_data)
        click.echo(f"✅ 已生成 {len(charts)} 个图表")

        analysis_result = None
        if include_ai:
            from .core.ai_analyzer import ai_analyzer

            click.echo("🤖 正在进行 AI 分析...")
            ai_result = ai_analyzer.analyze_portfolio(portfolio_data)
            analysis_result = {
                "summary": ai_result.summary,
                "risk_assessment": ai_result.risk_assessment,
                "suggestions": ai_result.suggestions,
                "warnings": ai_result.warnings,
                "score": ai_result.score,
            }

        html_gen = HTMLReportGenerator(output_path)
        report_path = html_gen.generate_investment_report(
            portfolio_data, analysis_result, charts
        )

        click.echo(f"\n✅ 报告已生成: {report_path}")

    except Exception as e:
        click.echo(f"❌ 生成报告失败: {e}", err=True)


@cli.command()
@click.argument("codes", nargs=-1, required=True)
def fetch_stock(codes):
    """获取股票实时行情

    示例:
        asset-lens fetch-stock sh600519 sz000001
        asset-lens fetch-stock hk00700
        asset-lens fetch-stock AAPL TSLA
    """
    from .data.stock_fetcher import stock_fetcher

    click.echo("\n📊 获取股票实时行情")
    click.echo("=" * 60)

    result = stock_fetcher.fetch_multiple_stocks(list(codes))

    if result.get("data"):
        click.echo(f"\n✅ 成功获取 {len(result['data'])} 只股票行情")
        click.echo(f"📁 数据已缓存到: {stock_fetcher.stock_cache_file}")
    else:
        click.echo("\n❌ 未能获取任何股票行情", err=True)


@cli.command()
@click.argument("codes", nargs=-1, required=True)
def fetch_fund(codes):
    """获取基金净值

    示例:
        asset-lens fetch-fund 000001 110022
        asset-lens fetch-fund 519778
    """
    from .data.fund_fetcher import fund_fetcher

    click.echo("\n📊 获取基金净值")
    click.echo("=" * 60)

    result = fund_fetcher.fetch_multiple_funds(list(codes))

    if result.get("data"):
        click.echo(f"\n✅ 成功获取 {len(result['data'])} 只基金净值")
        click.echo(f"📁 数据已缓存到: {fund_fetcher.fund_cache_file}")
    else:
        click.echo("\n❌ 未能获取任何基金净值", err=True)


@cli.command()
@click.argument("keyword")
def search_fund(keyword):
    """搜索基金

    示例:
        asset-lens search-fund 沪深300
        asset-lens search-fund 易方达
    """
    from .data.fund_fetcher import fund_fetcher

    click.echo(f"\n🔍 搜索基金: {keyword}")
    click.echo("=" * 60)

    results = fund_fetcher.search_fund(keyword)

    if results:
        click.echo(f"\n找到 {len(results)} 只基金:\n")
        for fund in results[:20]:
            click.echo(f"  {fund['code']} - {fund['name']} ({fund['type']})")
    else:
        click.echo("\n❌ 未找到相关基金", err=True)


@cli.command("fetch-portfolio-funds")
@click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
def fetch_portfolio_funds(data_mode):
    """自动获取投资组合中所有基金的净值

    自动匹配基金代码并获取净值
    """
    from .data.fund_fetcher import fetch_portfolio_fund_quotes

    if data_mode:
        config.data_mode = data_mode

    click.echo("\n📊 自动获取投资组合基金净值")
    click.echo("=" * 60)

    result = fetch_portfolio_fund_quotes()

    if result.get("data"):
        click.echo(f"\n✅ 成功获取 {len(result['data'])} 只基金净值")
        click.echo(f"📁 数据已缓存到: cache/fund_quotes.json")
    else:
        click.echo("\n❌ 未能获取任何基金净值", err=True)


@cli.command("update-all-data")
@click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
def update_all_data(data_mode):
    """更新所有数据（市场指数、基金净值、股票行情）

    一键更新所有需要的数据
    """
    import asyncio

    from .data.async_market_data_fetcher import AsyncMarketDataFetcher
    from .data.fund_fetcher import fetch_portfolio_fund_quotes
    from .data.stock_fetcher import stock_fetcher

    if data_mode:
        config.data_mode = data_mode

    click.echo("\n📊 更新所有数据")
    click.echo("=" * 60)

    click.echo("\n1️⃣ 更新市场指数数据...")
    try:
        fetcher = AsyncMarketDataFetcher(max_concurrent=5, request_delay=0.3)
        domestic_success, foreign_success = asyncio.run(fetcher.update_all_caches_async())
        if domestic_success and foreign_success:
            click.echo("   ✅ 市场指数数据更新成功")
        else:
            click.echo("   ⚠️  市场指数数据部分更新失败")
    except Exception as e:
        click.echo(f"   ❌ 市场指数数据更新失败: {e}")

    click.echo("\n2️⃣ 更新基金净值数据...")
    try:
        result = fetch_portfolio_fund_quotes()
        if result.get("data"):
            click.echo(f"   ✅ 成功获取 {len(result['data'])} 只基金净值")
        else:
            click.echo("   ⚠️  未能获取基金净值数据")
    except Exception as e:
        click.echo(f"   ❌ 基金净值数据更新失败: {e}")

    click.echo("\n3️⃣ 更新股票行情数据...")
    try:
        stock_codes_map = stock_fetcher._load_stock_codes_config()
        stock_codes = list(set(stock_codes_map.values()))
        if stock_codes:
            result = stock_fetcher.fetch_multiple_stocks(stock_codes)
            if result.get("data"):
                click.echo(f"   ✅ 成功获取 {len(result['data'])} 只股票行情")
            else:
                click.echo("   ⚠️  未能获取股票行情数据")
        else:
            click.echo("   ℹ️  没有配置股票代码，跳过")
    except Exception as e:
        click.echo(f"   ❌ 股票行情数据更新失败: {e}")

    click.echo("\n✅ 所有数据更新完成！")
    click.echo("💡 运行 'make pnl' 查看更准确的盈亏估算")


@cli.command("filter-stocks")
@click.option("--config-file", type=click.Path(), help="筛选配置文件路径")
@click.option("--stocks-file", type=click.Path(), help="股票数据文件路径")
@click.option("--fetch-market", is_flag=True, help="从市场获取股票列表（而不是自己投资的股票）")
@click.option("--max-pages", type=int, default=5, help="获取市场股票的最大页数")
def filter_stocks_command(config_file, stocks_file, fetch_market, max_pages):
    """筛选股票

    根据配置文件中的筛选条件筛选股票
    
    默认筛选自己投资的股票，使用 --fetch-market 从市场获取股票列表
    """
    from pathlib import Path

    from .data.stock_filter import StockFilter

    click.echo("\n📊 股票筛选")
    click.echo("=" * 60)

    config_path = Path(config_file) if config_file else None
    stock_filter = StockFilter(config_path)

    click.echo(stock_filter.get_filter_summary())
    click.echo("")

    if fetch_market:
        from .data.market_stock_fetcher import market_stock_fetcher

        click.echo("📡 正在从市场获取股票列表...")
        stocks = market_stock_fetcher.fetch_all_cn_stocks(max_pages=max_pages)

        if stocks:
            market_stock_fetcher.save_market_stocks(stocks)
    elif stocks_file:
        import json

        stocks_path = Path(stocks_file)
        if stocks_path.exists():
            with open(stocks_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                stocks_data = data.get("data", {})
                if isinstance(stocks_data, dict):
                    stocks = list(stocks_data.values())
                else:
                    stocks = stocks_data
        else:
            click.echo(f"❌ 股票数据文件不存在: {stocks_file}", err=True)
            return
    else:
        from .data.stock_fetcher import stock_fetcher

        cached = stock_fetcher.get_cached_stocks()
        stocks_data = cached.get("data", {})
        if isinstance(stocks_data, dict):
            stocks = list(stocks_data.values())
        else:
            stocks = stocks_data

    if not stocks:
        click.echo("❌ 没有股票数据可供筛选", err=True)
        click.echo("💡 请先运行 'make fetch-stock' 获取股票数据")
        click.echo("💡 或使用 'make filter-stocks -- --fetch-market' 从市场获取股票列表")
        return

    click.echo(f"📋 原始股票数量: {len(stocks)}")

    filtered = stock_filter.filter_stocks(stocks)

    click.echo(f"✅ 筛选后股票数量: {len(filtered)}")
    click.echo("")

    if filtered:
        click.echo("筛选结果:")
        click.echo("-" * 100)
        click.echo(
            f"{'代码':<12} {'名称':<20} {'价格':>10} {'涨跌幅':>10} {'换手率':>10} {'市值(亿)':>12}"
        )
        click.echo("-" * 100)

        for stock in filtered[:20]:
            code = stock.get("code", "")
            name = stock.get("name", "")[:18]
            price = stock.get("current_price", 0)
            change = stock.get("change_percent", 0)
            turnover = stock.get("turnover_rate", 0)
            market_cap = stock.get("market_cap", 0)

            change_str = f"{change:+.2f}%"
            turnover_str = f"{turnover:.2f}%" if turnover > 0 else "-"
            cap_str = f"{market_cap:.1f}" if market_cap > 0 else "-"

            click.echo(f"{code:<12} {name:<20} {price:>10.2f} {change_str:>10} {turnover_str:>10} {cap_str:>12}")

        if len(filtered) > 20:
            click.echo(f"\n... 还有 {len(filtered) - 20} 只股票未显示")


@cli.command("volume-breakout")
@click.option("--update-history", is_flag=True, help="更新历史数据")
@click.option("--fetch-market", is_flag=True, help="先获取市场数据")
@click.option("--use-api", is_flag=True, default=True, help="使用API获取历史数据（默认开启）")
@click.option("--days", default=60, help="历史数据天数（默认60天）")
def volume_breakout_command(update_history, fetch_market, use_api, days):
    """放量突破股票筛选

    筛选条件:
    - 今日换手率 > 60日均值 × 3
    - 成交额放大 > 60日均值 × 2
    - 市值在指定区间内
    - 可选：行业属于热点
    """
    from .data.volume_breakout_filter import volume_breakout_filter
    from .data.market_stock_fetcher import market_stock_fetcher

    click.echo("\n📊 放量突破股票筛选")
    click.echo("=" * 60)

    config = volume_breakout_filter.filter_config
    click.echo(f"\n筛选条件:")
    click.echo(f"  - 换手率倍数: {config.turnover_ratio}x (今日 > {days}日均值 × {config.turnover_ratio})")
    click.echo(f"  - 成交额倍数: {config.amount_ratio}x (今日 > {days}日均值 × {config.amount_ratio})")
    click.echo(f"  - 市值范围: {config.market_cap_min} - {config.market_cap_max or '无上限'} 亿元")
    click.echo(f"  - 价格范围: {config.price_min} - {config.price_max} 元")
    click.echo(f"  - 热门行业要求: {'是' if config.require_hot_industry else '否'}")
    click.echo(f"  - 历史数据来源: {'API实时获取' if use_api else '本地缓存'}")

    stocks = None

    if fetch_market:
        click.echo("\n📡 正在获取市场数据...")
        stocks = market_stock_fetcher.fetch_all_cn_stocks(max_pages=5)
        if stocks:
            market_stock_fetcher.save_market_stocks(stocks)
            click.echo(f"✅ 获取 {len(stocks)} 只股票")
        else:
            click.echo("❌ 获取市场数据失败", err=True)
            return

    if use_api:
        click.echo(f"\n📡 正在通过API获取 {days} 日历史数据...")
        if stocks is None:
            stocks = volume_breakout_filter._load_market_stocks()
        if not stocks:
            click.echo("❌ 没有股票数据", err=True)
            return
        results = volume_breakout_filter.filter_with_api_history(stocks, days)
    elif update_history:
        click.echo("\n📡 正在更新历史数据...")
        if stocks is None:
            stocks = volume_breakout_filter._load_market_stocks()
        if stocks:
            volume_breakout_filter.update_history(stocks)
            click.echo(f"✅ 更新 {len(stocks)} 只股票的历史数据")
        else:
            click.echo("❌ 没有股票数据可更新", err=True)
            return
        results = volume_breakout_filter.filter(stocks)
    else:
        results = volume_breakout_filter.filter(stocks)

    if not results:
        click.echo("\n❌ 没有符合条件的股票")
        click.echo("\n💡 提示:")
        click.echo("  - 首次使用请运行: make volume-breakout-update")
        click.echo("  - 需要积累历史数据才能准确判断放量突破")
        click.echo("  - 建议每日运行更新历史数据")
        return

    click.echo(f"\n✅ 找到 {len(results)} 只放量突破股票")
    click.echo("-" * 120)
    click.echo(f"{'代码':<10} {'名称':<16} {'价格':>8} {'涨跌':>8} {'换手率':>8} {'换手倍数':>8} {'成交额倍数':>8} {'市值(亿)':>10} {'行业':<8} {'类型':<8}")
    click.echo("-" * 120)

    for stock in results:
        code = stock.get("code", "")
        name = stock.get("name", "")[:14]
        price = stock.get("current_price", 0)
        change = stock.get("change_percent", 0)
        turnover = stock.get("turnover_rate", 0)
        turnover_ratio = stock.get("turnover_ratio", 0)
        amount_ratio = stock.get("amount_ratio", 0)
        market_cap = stock.get("market_cap", 0)
        industry = stock.get("industry", "-") or "-"
        breakout_type = stock.get("breakout_type", "-")

        change_str = f"{change:+.2f}%"
        turnover_str = f"{turnover:.2f}%"
        cap_str = f"{market_cap:.1f}"

        hot_flag = "🔥" if stock.get("is_hot_industry") else ""

        click.echo(
            f"{code:<10} {name:<16} {price:>8.2f} {change_str:>8} {turnover_str:>8} "
            f"{turnover_ratio:>8.1f}x {amount_ratio:>8.1f}x {cap_str:>10} {industry:<8} {breakout_type:<8} {hot_flag}"
        )

    click.echo("\n" + "=" * 60)
    click.echo("⚠️  免责声明: 以上筛选结果仅供参考，不构成投资建议")


@cli.command("screen-stocks")
@click.option("--type", "-t", type=click.Choice(["fundamental", "technical", "comprehensive"]), default="comprehensive", help="筛选类型")
@click.option("--pe-max", type=float, default=30, help="最大市盈率")
@click.option("--pe-min", type=float, default=0, help="最小市盈率")
@click.option("--market-cap-min", type=float, default=20, help="最小市值(亿元)")
@click.option("--market-cap-max", type=float, default=500, help="最大市值(亿元)")
@click.option("--turnover-min", type=float, default=1, help="最小换手率(%)")
@click.option("--turnover-max", type=float, default=15, help="最大换手率(%)")
@click.option("--change-min", type=float, default=-10, help="最小涨跌幅(%)")
@click.option("--change-max", type=float, default=10, help="最大涨跌幅(%)")
@click.option("--min-score", type=float, default=60, help="最低综合得分")
@click.option("--max-results", type=int, default=20, help="最大返回结果数")
@click.option("--fetch-market", is_flag=True, help="先获取市场数据")
def screen_stocks_command(
    type, pe_max, pe_min, market_cap_min, market_cap_max,
    turnover_min, turnover_max, change_min, change_max,
    min_score, max_results, fetch_market
):
    """股票综合筛选

    多维度筛选最佳股票:
    - fundamental: 基本面筛选 (PE/市值等)
    - technical: 技术面筛选 (均线/趋势等)
    - comprehensive: 综合筛选 (默认)

    示例:
        make screen-stocks
        python -m asset_lens screen-stocks --type fundamental
        python -m asset_lens screen-stocks --pe-max 20 --market-cap-min 50
    """
    from .data.stock_screener import stock_screener
    from .data.market_stock_fetcher import market_stock_fetcher

    click.echo("\n📊 股票综合筛选")
    click.echo("=" * 60)

    click.echo(f"\n筛选条件:")
    click.echo(f"  - 筛选类型: {type}")
    click.echo(f"  - 市盈率: {pe_min} - {pe_max}")
    click.echo(f"  - 市值: {market_cap_min} - {market_cap_max} 亿元")
    click.echo(f"  - 换手率: {turnover_min}% - {turnover_max}%")
    click.echo(f"  - 涨跌幅: {change_min}% - {change_max}%")
    click.echo(f"  - 最低得分: {min_score}")

    stocks = None

    if fetch_market:
        click.echo("\n📡 正在获取市场数据...")
        stocks = market_stock_fetcher.fetch_all_cn_stocks()
        if stocks:
            market_stock_fetcher.save_market_stocks(stocks)
            click.echo(f"✅ 获取 {len(stocks)} 只股票")
        else:
            click.echo("❌ 获取市场数据失败", err=True)
            return

    strategy = {
        "pe_max": pe_max,
        "pe_min": pe_min,
        "market_cap_min": market_cap_min,
        "market_cap_max": market_cap_max,
        "turnover_min": turnover_min,
        "turnover_max": turnover_max,
        "change_min": change_min,
        "change_max": change_max,
        "min_match_rate": 0.6,
        "max_results": max_results,
    }

    stock_screener.screener_config.min_score = min_score
    stock_screener.screener_config.max_results = max_results

    click.echo("\n🔍 正在筛选...")
    results = stock_screener.screen(stocks, filter_type=type)

    if not results:
        click.echo("\n❌ 没有找到符合条件的股票")
        return

    click.echo(f"\n✅ 找到 {len(results)} 只符合条件的股票:\n")
    click.echo("=" * 100)
    click.echo(f"{'排名':<4} {'代码':<10} {'名称':<10} {'现价':>8} {'涨跌%':>8} {'市值(亿)':>10} {'换手%':>8} {'综合分':>8}")
    click.echo("-" * 100)

    for i, stock in enumerate(results, 1):
        code = stock.get("code", "")
        name = stock.get("name", "")
        price = stock.get("current_price", 0)
        change = stock.get("change_percent", 0)
        market_cap = stock.get("market_cap", 0)
        turnover = stock.get("turnover_rate", 0)
        total_score = stock.get("total_score", 0)

        change_str = f"{change:+.2f}%"
        click.echo(f"{i:<4} {code:<10} {name:<10} {price:>8.2f} {change_str:>8} {market_cap:>10.1f} {turnover:>8.2f} {total_score:>8.1f}")

    click.echo("=" * 100)

    click.echo("\n📈 评分明细:")
    for i, stock in enumerate(results[:5], 1):
        name = stock.get("name", "")
        click.echo(f"\n{i}. {name}")
        click.echo(f"   基本面: {stock.get('fundamental_score', 0):.1f}分")
        click.echo(f"   技术面: {stock.get('technical_score', 0):.1f}分")
        click.echo(f"   资金面: {stock.get('capital_score', 0):.1f}分")
        click.echo(f"   行业热度: {stock.get('industry_score', 0):.1f}分")

    click.echo("\n" + "=" * 60)
    click.echo("⚠️  免责声明: 以上筛选结果仅供参考，不构成投资建议")


@cli.command("predict-etf")
@click.option("--force-update", is_flag=True, help="强制更新市场数据")
@click.option("--analyze-portfolio", is_flag=True, help="分析投资组合中的ETF相关产品")
def predict_etf_command(force_update, analyze_portfolio):
    """根据股票活跃度预测ETF表现

    分析市场股票活跃度，预测各类ETF的表现
    
    使用 --analyze-portfolio 可以分析您的投资产品与ETF的关联
    """
    from .data.stock_activity_analyzer import stock_activity_analyzer

    market_stock_file = stock_activity_analyzer.market_stock_cache_file

    click.echo("\n📊 ETF预测分析")
    click.echo("=" * 60)

    if analyze_portfolio:
        from .data.csv_parser import CSVParser
        from .data.models import Portfolio
        from decimal import Decimal

        click.echo("\n📋 分析投资组合中的ETF相关产品")
        click.echo("-" * 60)

        try:
            products = CSVParser.load_data()
            portfolio = Portfolio(
                products,
                usd_rate=Decimal(str(config.default_usd_rate)),
                hkd_rate=Decimal(str(config.default_hkd_rate)),
            )

            etf_related: Dict[str, Any] = {}
            for p in portfolio.products:
                name = p.name
                inv_type = p.investment_type.value if p.investment_type else ""
                amount = float(p.current_amount or 0)

                # 检查是否是指数基金（优先级最高）
                index_keywords = {
                    "沪深300": ["沪深300", "沪深"],
                    "中证500": ["中证500"],
                    "创业板": ["创业板"],
                    "科创50": ["科创50", "科创板50"],
                    "上证50": ["上证50"],
                }

                matched_index = None
                for index_name, keywords in index_keywords.items():
                    for keyword in keywords:
                        if keyword in name:
                            matched_index = index_name
                            break
                    if matched_index:
                        break

                if matched_index:
                    if matched_index not in etf_related:
                        etf_related[matched_index] = {
                            "products": [],
                            "total_amount": 0.0,
                            "type": "index",
                        }
                    products_list = etf_related[matched_index]["products"]
                    products_list.append({
                        "name": name,
                        "type": inv_type,
                        "amount": amount,
                    })
                    etf_related[matched_index]["total_amount"] += amount
                    continue

                # 检查是否是行业ETF
                for etf_name, etf_info in stock_activity_analyzer.ETF_MAPPING.items():
                    keywords = [etf_name]
                    if "新能源" in etf_name:
                        keywords.extend(["新能源", "锂电", "光伏", "风电", "储能"])
                    elif "半导体" in etf_name or "芯片" in etf_name:
                        keywords.extend(["半导体", "芯片", "集成电路"])
                    elif "医药" in etf_name:
                        keywords.extend(["医药", "生物", "医疗", "制药"])
                    elif "消费" in etf_name:
                        keywords.extend(["消费", "食品", "饮料", "家电", "零售"])
                    elif "军工" in etf_name:
                        keywords.extend(["军工", "航空", "航天", "兵器"])

                    for keyword in keywords:
                        if keyword in name:
                            if etf_name not in etf_related:
                                etf_related[etf_name] = {
                                    "products": [],
                                    "total_amount": 0.0,
                                    "type": "industry",
                                }
                            industry_products_list = etf_related[etf_name]["products"]
                            industry_products_list.append({
                                "name": name,
                                "type": inv_type,
                                "amount": amount,
                            })
                            etf_related[etf_name]["total_amount"] += amount
                            break

            if etf_related:
                click.echo(f"\n找到 {len(etf_related)} 个ETF相关投资:\n")
                sorted_etf_related = sorted(etf_related.items(), key=lambda x: float(x[1]["total_amount"]), reverse=True)
                for etf_name, data in sorted_etf_related:
                    click.echo(f"📈 {etf_name}")
                    click.echo(f"   投资金额: ¥{data['total_amount']:,.2f}")
                    click.echo(f"   相关产品:")
                    products_data = data["products"]
                    for p in products_data:  # type: ignore
                        click.echo(f"     - {p.get('name', '')} ({p.get('type', '')}): ¥{p.get('amount', 0):,.2f}")  # type: ignore
                    click.echo()
            else:
                click.echo("未找到与ETF相关的投资产品")

        except Exception as e:
            click.echo(f"❌ 分析投资组合失败: {e}", err=True)
            return

        # 检查并获取市场数据
        market_index_file = stock_activity_analyzer.cache_path / "market_index_domestic.json"
        need_update_stock = False
        need_update_index = False
        
        # 检查市场股票数据
        if not market_stock_file.exists():
            click.echo("\n📡 没有市场股票数据，正在获取...")
            need_update_stock = True
        else:
            try:
                with open(market_stock_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    update_time_str = data.get("update_time", "")
                    if update_time_str:
                        from datetime import datetime, timedelta
                        update_time = datetime.strptime(update_time_str, "%Y-%m-%d %H:%M:%S")
                        now = datetime.now()
                        age = now - update_time
                        if age > timedelta(hours=1):
                            click.echo(f"\n⚠️  市场股票数据已过期（更新于 {update_time_str}）")
                            need_update_stock = True
            except Exception:
                need_update_stock = True
        
        # 检查指数市场数据
        if not market_index_file.exists():
            click.echo("\n📡 没有指数市场数据，正在获取...")
            need_update_index = True
        else:
            try:
                with open(market_index_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    update_time_str = data.get("更新时间", "")
                    if update_time_str:
                        from datetime import datetime, timedelta
                        update_time = datetime.strptime(update_time_str, "%Y-%m-%d %H:%M:%S")
                        now = datetime.now()
                        age = now - update_time
                        if age > timedelta(hours=1):
                            click.echo(f"\n⚠️  指数市场数据已过期（更新于 {update_time_str}）")
                            need_update_index = True
            except Exception:
                need_update_index = True
        
        # 更新市场股票数据
        if need_update_stock:
            from .data.market_stock_fetcher import market_stock_fetcher
            stocks = market_stock_fetcher.fetch_all_cn_stocks(max_pages=5)
            if stocks:
                market_stock_fetcher.save_market_stocks(stocks)
                click.echo("✅ 市场股票数据更新完成\n")
            else:
                click.echo("❌ 市场股票数据更新失败", err=True)
        
        # 更新指数市场数据
        if need_update_index:
            import asyncio
            from .data.async_market_data_fetcher import AsyncMarketDataFetcher
            fetcher = AsyncMarketDataFetcher(max_concurrent=5, request_delay=0.3)
            domestic_success, _ = asyncio.run(fetcher.update_all_caches_async())
            if domestic_success:
                click.echo("✅ 指数市场数据更新完成\n")
            else:
                click.echo("❌ 指数市场数据更新失败", err=True)

        click.echo("=" * 60)
        click.echo("📊 您投资的ETF预测结果")
        click.echo("=" * 60)

        stocks = stock_activity_analyzer.load_market_stocks()
        
        # 先显示指数基金（使用指数市场数据）
        index_funds = {k: v for k, v in etf_related.items() if k in stock_activity_analyzer.INDEX_FUND_MAPPING}
        industry_etfs = {k: v for k, v in etf_related.items() if k in stock_activity_analyzer.ETF_MAPPING}
        
        if index_funds:
            click.echo("\n📈 指数基金（使用指数市场数据）")
            click.echo("-" * 60)
            for etf_name in sorted(index_funds.keys(), key=lambda x: index_funds[x]["total_amount"], reverse=True):
                prediction = stock_activity_analyzer.predict_index_fund(etf_name)
                if prediction:
                    direction = "📈" if prediction.predicted_change > 0 else "📉" if prediction.predicted_change < 0 else "➡️"
                    click.echo(f"\n{direction} {prediction.etf_name} ({prediction.etf_code})")
                    click.echo(f"   预测涨跌: {prediction.predicted_change:+.2f}%")
                    click.echo(f"   置信度: {prediction.confidence:.0f}%")
                    if prediction.confidence >= 99:
                        click.echo(f"   数据来源: 指数市场数据（实时）")
                    elif prediction.confidence >= 90:
                        click.echo(f"   数据来源: 指数市场数据（今日）")
                    else:
                        click.echo(f"   数据来源: 指数市场数据（历史）")
        
        # 再显示行业ETF（使用股票活跃度分析）
        if industry_etfs and stocks:
            click.echo("\n📊 行业ETF（使用股票活跃度分析）")
            click.echo("-" * 60)
            for etf_name in sorted(industry_etfs.keys(), key=lambda x: industry_etfs[x]["total_amount"], reverse=True):
                prediction = stock_activity_analyzer.predict_etf(etf_name, stocks)
                if prediction:
                    direction = "📈" if prediction.predicted_change > 0 else "📉" if prediction.predicted_change < 0 else "➡️"
                    click.echo(f"\n{direction} {prediction.etf_name} ({prediction.etf_code})")
                    click.echo(f"   预测涨跌: {prediction.predicted_change:+.2f}%")
                    click.echo(f"   置信度: {prediction.confidence:.1f}%")
                    click.echo(f"   活跃度: {prediction.activity_score:.1f}/100")
                    click.echo(f"   相关股票: {prediction.related_stocks} 只")
                    click.echo(f"   上涨比例: {prediction.up_ratio*100:.1f}%")
                    click.echo(f"   下跌比例: {prediction.down_ratio*100:.1f}%")

                    if prediction.top_gainers:
                        click.echo(f"   领涨股票:")
                        for stock in prediction.top_gainers[:3]:
                            click.echo(f"     - {stock['name']} ({stock['code']}): {stock['change']:+.2f}%")

                    if prediction.top_losers:
                        click.echo(f"   领跌股票:")
                        for stock in prediction.top_losers[:3]:
                            click.echo(f"     - {stock['name']} ({stock['code']}): {stock['change']:+.2f}%")

        # 添加市场热点行业分析
        click.echo("\n" + "=" * 60)
        click.echo("🔥 市场热点行业分析")
        click.echo("=" * 60)

        invested_etfs = list(etf_related.keys())
        suggestions = stock_activity_analyzer.get_investment_suggestions(invested_etfs)

        if suggestions.get("hot_industries"):
            click.echo("\n📈 热门行业（未投资）")
            click.echo("-" * 60)
            for industry in suggestions["hot_industries"]:
                direction = "📈" if industry["predicted_change"] > 0 else "📉"
                click.echo(f"\n{direction} {industry['name']} ({industry['code']})")
                click.echo(f"   预测涨跌: {industry['predicted_change']:+.2f}%")
                click.echo(f"   活跃度: {industry['activity_score']:.1f}/100")
                click.echo(f"   相关股票: {industry['stock_count']} 只")
                click.echo(f"   平均换手率: {industry['avg_turnover']:.2f}%")
                click.echo(f"   上涨比例: {industry['up_ratio']*100:.1f}%")
                click.echo(f"   下跌比例: {industry['down_ratio']*100:.1f}%")
                
                # 获取该行业的股票详情
                if stocks:
                    etf_info = stock_activity_analyzer.ETF_MAPPING.get(industry['name'], {})
                    if etf_info:
                        filter_func = etf_info.get('stocks_filter', lambda s: False)
                        related_stocks = [s for s in stocks if filter_func(s)]
                        sorted_stocks = sorted(related_stocks, key=lambda x: x.get("change_percent", 0), reverse=True)
                        up_stocks = [s for s in sorted_stocks if s.get("change_percent", 0) > 0]
                        down_stocks = [s for s in sorted_stocks if s.get("change_percent", 0) < 0]
                        top_gainers = up_stocks[:3]
                        top_losers = down_stocks[:3]
                        
                        if top_gainers:
                            click.echo(f"   领涨股票:")
                            for stock in top_gainers:
                                click.echo(f"     - {stock.get('name', '')} ({stock.get('code', '')}): {stock.get('change_percent', 0):+.2f}%")
                        
                        if top_losers:
                            click.echo(f"   领跌股票:")
                            for stock in top_losers:
                                click.echo(f"     - {stock.get('name', '')} ({stock.get('code', '')}): {stock.get('change_percent', 0):+.2f}%")

        if suggestions.get("suggestions"):
            click.echo("\n💡 投资建议")
            click.echo("-" * 60)
            for suggestion in suggestions["suggestions"]:
                click.echo(f"  {suggestion}")

        click.echo("\n" + "=" * 60)
        click.echo("⚠️  免责声明: 以上预测仅供参考，不构成投资建议")
        return

    need_update = force_update

    if not need_update and market_stock_file.exists():
        try:
            with open(market_stock_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                update_time_str = data.get("update_time", "")

                if update_time_str:
                    update_time = datetime.strptime(update_time_str, "%Y-%m-%d %H:%M:%S")
                    now = datetime.now()
                    age = now - update_time

                    if age > timedelta(hours=1):
                        click.echo(f"⚠️  市场数据已过期（更新于 {update_time_str}，距今 {int(age.total_seconds() / 3600)} 小时）")
                        need_update = True
                    else:
                        click.echo(f"✅ 市场数据有效（更新于 {update_time_str}）")
        except Exception as e:
            click.echo(f"⚠️  无法读取市场数据更新时间: {e}")
            need_update = True
    elif not market_stock_file.exists():
        click.echo("❌ 没有市场股票数据")
        need_update = True

    if need_update:
        click.echo("\n📡 正在更新市场数据...")
        from .data.market_stock_fetcher import market_stock_fetcher

        stocks = market_stock_fetcher.fetch_all_cn_stocks(max_pages=5)

        if stocks:
            market_stock_fetcher.save_market_stocks(stocks)
            click.echo("✅ 市场数据更新完成\n")
        else:
            click.echo("❌ 市场数据更新失败", err=True)
            return

    overview = stock_activity_analyzer.get_market_overview()

    if not overview:
        click.echo("❌ 没有市场股票数据", err=True)
        click.echo("💡 请先运行 'make filter-market-stocks' 获取市场股票数据")
        return

    click.echo("\n📈 市场概览")
    click.echo("-" * 60)
    click.echo(f"  总股票数: {overview['total_stocks']}")
    click.echo(f"  上涨: {overview['up_count']} ({overview['up_count']/overview['total_stocks']*100:.1f}%)")
    click.echo(f"  下跌: {overview['down_count']} ({overview['down_count']/overview['total_stocks']*100:.1f}%)")
    click.echo(f"  平盘: {overview['flat_count']}")
    click.echo(f"  平均涨跌幅: {overview['avg_change']:+.2f}%")
    click.echo(f"  平均换手率: {overview['avg_turnover']:.2f}%")
    click.echo(f"  市场活跃度: {overview['activity_score']:.1f}/100")
    click.echo(f"  涨停: {overview['limit_up_count']} 只")
    click.echo(f"  跌停: {overview['limit_down_count']} 只")

    click.echo("\n📊 ETF预测结果")
    click.echo("-" * 60)

    predictions = stock_activity_analyzer.predict_all_etfs()

    if not predictions:
        click.echo("❌ 没有ETF预测结果")
        return

    for pred in predictions:
        direction = "📈" if pred.predicted_change > 0 else "📉" if pred.predicted_change < 0 else "➡️"
        click.echo(f"\n{direction} {pred.etf_name} ({pred.etf_code})")
        click.echo(f"   预测涨跌: {pred.predicted_change:+.2f}%")
        click.echo(f"   置信度: {pred.confidence:.1f}%")
        click.echo(f"   活跃度: {pred.activity_score:.1f}/100")
        click.echo(f"   相关股票: {pred.related_stocks} 只")
        click.echo(f"   上涨比例: {pred.up_ratio*100:.1f}%")
        click.echo(f"   下跌比例: {pred.down_ratio*100:.1f}%")

        if pred.top_gainers:
            click.echo(f"   领涨股票:")
            for stock in pred.top_gainers[:3]:
                click.echo(f"     - {stock['name']} ({stock['code']}): {stock['change']:+.2f}%")

        if pred.top_losers:
            click.echo(f"   领跌股票:")
            for stock in pred.top_losers[:3]:
                click.echo(f"     - {stock['name']} ({stock['code']}): {stock['change']:+.2f}%")

    click.echo("\n" + "=" * 60)
    click.echo("⚠️  免责声明: 以上预测仅供参考，不构成投资建议")


@cli.command("stock-pool")
@click.argument("action", type=click.Choice(["list", "add", "remove", "buy", "sell", "status"]))
@click.option("--code", help="股票代码")
@click.option("--name", help="股票名称")
@click.option("--price", type=float, help="价格")
@click.option("--shares", type=int, default=100, help="股数")
@click.option("--status-filter", type=click.Choice(["watching", "holding", "sold"]), help="状态筛选")
@click.option("--pool-name", default="default", help="股票池名称")
def stock_pool_command(action, code, name, price, shares, status_filter, pool_name):
    """股票池管理

    动作:
    - list: 列出股票池中的股票
    - add: 添加股票到股票池
    - remove: 从股票池移除股票
    - buy: 模拟买入
    - sell: 模拟卖出
    - status: 查看股票池状态

    示例:
        asset-lens stock-pool list
        asset-lens stock-pool add --code sh600519 --name 贵州茅台 --price 1800
        asset-lens stock-pool buy --code sh600519 --price 1800 --shares 100
        asset-lens stock-pool sell --code sh600519 --price 1900
    """
    from .data.stock_pool import StockPool

    pool = StockPool(pool_name)

    if action == "list":
        stocks = pool.list_stocks(status_filter)
        if not stocks:
            click.echo("股票池为空")
            return

        click.echo(f"\n📊 股票池列表 ({pool_name})")
        click.echo("=" * 100)
        click.echo(f"{'代码':<12} {'名称':<12} {'状态':<8} {'买入价':>10} {'现价':>10} {'盈亏':>10} {'收益率':>8}")
        click.echo("-" * 100)

        for stock in stocks:
            profit_str = f"{stock['profit']:+.2f}" if stock['profit'] != 0 else "-"
            rate_str = f"{stock['profit_rate']:+.2f}%" if stock['profit_rate'] != 0 else "-"
            click.echo(
                f"{stock['code']:<12} {stock['name']:<12} {stock['status']:<8} "
                f"{stock['buy_price']:>10.2f} {stock['current_price']:>10.2f} "
                f"{profit_str:>10} {rate_str:>8}"
            )

        click.echo("=" * 100)

    elif action == "add":
        if not code or not name or price is None:
            click.echo("❌ 请提供 --code, --name 和 --price 参数", err=True)
            return
        pool.add_stock(code, name, price, "watching")

    elif action == "remove":
        if not code:
            click.echo("❌ 请提供 --code 参数", err=True)
            return
        pool.remove_stock(code)

    elif action == "buy":
        if not code or price is None:
            click.echo("❌ 请提供 --code 和 --price 参数", err=True)
            return
        pool.buy_stock(code, price, shares)

    elif action == "sell":
        if not code or price is None:
            click.echo("❌ 请提供 --code 和 --price 参数", err=True)
            return
        pool.sell_stock(code, price)

    elif action == "status":
        performance = pool.get_performance()
        click.echo(f"\n📊 股票池状态 ({pool_name})")
        click.echo("=" * 60)
        click.echo(f"总股票数: {performance['total_stocks']}")
        click.echo(f"观察中: {performance['watching_count']}")
        click.echo(f"持有中: {performance['holding_count']}")
        click.echo(f"已卖出: {performance['sold_count']}")
        click.echo(f"总盈亏: {performance['total_profit']:+.2f} 元")
        click.echo(f"收益率: {performance['profit_rate']:+.2f}%")
        click.echo(f"胜率: {performance['win_rate']:.1f}%")
        click.echo("=" * 60)


@cli.command("strategy")
@click.argument("action", type=click.Choice(["list", "show", "set", "screen"]))
@click.option("--name", help="策略名称")
@click.option("--min-score", type=float, default=60, help="最低得分")
@click.option("--max-results", type=int, default=20, help="最大结果数")
@click.option("--fetch-market", is_flag=True, help="先获取市场数据")
def strategy_command(action, name, min_score, max_results, fetch_market):
    """策略管理

    动作:
    - list: 列出所有策略
    - show: 显示策略详情
    - set: 设置当前策略
    - screen: 使用策略筛选股票

    示例:
        asset-lens strategy list
        asset-lens strategy show --name value
        asset-lens strategy set --name momentum
        asset-lens strategy screen --name value --min-score 70
    """
    from .data.strategy_engine import strategy_engine
    from .data.investment_system import investment_system

    if action == "list":
        strategies = strategy_engine.list_strategies()
        click.echo("\n📊 可用策略列表")
        click.echo("=" * 80)
        click.echo(f"{'名称':<15} {'描述':<30} {'买入条件':>8} {'卖出条件':>8} {'仓位':>8}")
        click.echo("-" * 80)

        for s in strategies:
            click.echo(
                f"{s['name']:<15} {s['description'][:28]:<30} "
                f"{s['buy_conditions']:>8} {s['sell_conditions']:>8} "
                f"{s['position_size']*100:>7.0f}%"
            )

        click.echo("=" * 80)

    elif action == "show":
        if not name:
            click.echo("❌ 请提供 --name 参数", err=True)
            return

        strategy = strategy_engine.get_strategy(name)
        if not strategy:
            click.echo(f"❌ 策略 {name} 不存在", err=True)
            return

        click.echo(f"\n📊 策略详情: {strategy.name}")
        click.echo("=" * 60)
        click.echo(f"描述: {strategy.description}")
        click.echo(f"单只仓位: {strategy.position_size*100:.0f}%")
        click.echo(f"最大持仓: {strategy.max_positions} 只")
        click.echo(f"止损: {strategy.stop_loss*100:.0f}%")
        click.echo(f"止盈: {strategy.take_profit*100:.0f}%")

        click.echo("\n买入条件:")
        for c in strategy.buy_conditions:
            click.echo(f"  - {c.name}: {c.field} {c.operator} {c.value} (权重: {c.weight})")

        click.echo("\n卖出条件:")
        for c in strategy.sell_conditions:
            click.echo(f"  - {c.name}: {c.field} {c.operator} {c.value} (权重: {c.weight})")

        click.echo("=" * 60)

    elif action == "set":
        if not name:
            click.echo("❌ 请提供 --name 参数", err=True)
            return
        investment_system.set_strategy(name)

    elif action == "screen":
        if not name:
            click.echo("❌ 请提供 --name 参数", err=True)
            return

        stocks = None
        if fetch_market:
            from .data.market_stock_fetcher import market_stock_fetcher

            click.echo("📡 正在获取市场数据...")
            stocks = market_stock_fetcher.fetch_all_cn_stocks()
            if stocks:
                market_stock_fetcher.save_market_stocks(stocks)
                click.echo(f"✅ 获取 {len(stocks)} 只股票")
            else:
                click.echo("❌ 获取市场数据失败", err=True)
                return
        else:
            from .data.stock_fetcher import stock_fetcher

            cached = stock_fetcher.get_cached_stocks()
            stocks_data = cached.get("data", {})
            if isinstance(stocks_data, dict):
                stocks = list(stocks_data.values())
            else:
                stocks = stocks_data

        if not stocks:
            click.echo("❌ 没有股票数据", err=True)
            return

        click.echo(f"\n🔍 使用策略 {name} 筛选股票...")
        results = strategy_engine.screen_stocks(stocks, name, min_score)

        if not results:
            click.echo("❌ 没有找到符合条件的股票")
            return

        click.echo(f"\n✅ 找到 {len(results)} 只符合条件的股票:\n")
        click.echo("=" * 100)
        click.echo(f"{'排名':<4} {'代码':<10} {'名称':<12} {'现价':>8} {'策略分':>8} {'匹配条件':>8}")
        click.echo("-" * 100)

        for i, stock in enumerate(results[:max_results], 1):
            code = stock.get("code", "")
            sname = stock.get("name", "")
            price = stock.get("current_price", 0)
            score = stock.get("strategy_score", 0)
            matched = stock.get("matched_conditions", 0)

            click.echo(f"{i:<4} {code:<10} {sname:<12} {price:>8.2f} {score:>8.1f} {matched:>8}")

        click.echo("=" * 100)


@cli.command("backtest")
@click.option("--strategy", "-s", required=True, help="策略名称")
@click.option("--start-date", help="开始日期 (YYYY-MM-DD)")
@click.option("--end-date", help="结束日期 (YYYY-MM-DD)")
@click.option("--capital", type=float, default=100000, help="初始资金")
@click.option("--days", type=int, default=60, help="历史数据天数")
def backtest_command(strategy, start_date, end_date, capital, days):
    """策略回测

    使用历史数据回测策略表现

    示例:
        asset-lens backtest --strategy value --days 60
        asset-lens backtest --strategy momentum --start-date 2024-01-01 --end-date 2024-03-01
    """
    from datetime import datetime, timedelta
    from .data.backtester import backtester
    from .data.stock_history_fetcher import stock_history_fetcher
    from .data.market_stock_fetcher import market_stock_fetcher

    click.echo(f"\n📊 策略回测: {strategy}")
    click.echo("=" * 60)

    click.echo("📡 正在获取历史数据...")

    end = datetime.now() if not end_date else datetime.strptime(end_date, "%Y-%m-%d")
    start = end - timedelta(days=days) if not start_date else datetime.strptime(start_date, "%Y-%m-%d")

    stocks = market_stock_fetcher.get_cached_market_stocks()
    if not stocks:
        click.echo("❌ 没有市场数据，请先运行 'make update-all-data'", err=True)
        return

    stock_codes = [s.get("code", "") for s in stocks[:100] if s.get("code")]

    historical_data: Dict[str, List[Dict[str, Any]]] = {}
    for code in stock_codes[:20]:
        try:
            history = stock_history_fetcher.fetch_history(code, days=days)
            if history:
                klines: List[Dict[str, Any]] = history.get("klines", [])
                if klines:
                    historical_data[code] = klines
        except Exception:
            pass

    if not historical_data:
        click.echo("❌ 无法获取历史数据", err=True)
        return

    click.echo(f"✅ 获取 {len(historical_data)} 只股票的历史数据")

    click.echo(f"\n🔍 正在回测...")
    try:
        result = backtester.run_backtest(
            strategy_name=strategy,
            historical_data=historical_data,
            initial_capital=capital,
            start_date=start.strftime("%Y-%m-%d"),
            end_date=end.strftime("%Y-%m-%d"),
        )

        click.echo(f"\n📈 回测结果")
        click.echo("=" * 60)
        click.echo(f"策略: {result.strategy_name}")
        click.echo(f"回测区间: {result.start_date} ~ {result.end_date}")
        click.echo(f"初始资金: ¥{result.initial_capital:,.2f}")
        click.echo(f"最终资金: ¥{result.final_capital:,.2f}")
        click.echo(f"总收益率: {result.total_return*100:+.2f}%")
        click.echo(f"年化收益: {result.annual_return*100:+.2f}%")
        click.echo(f"最大回撤: {result.max_drawdown*100:.2f}%")
        click.echo(f"夏普比率: {result.sharpe_ratio:.2f}")
        click.echo(f"胜率: {result.win_rate:.1f}%")
        click.echo(f"盈亏比: {result.profit_factor:.2f}")
        click.echo(f"总交易: {result.total_trades} 次")
        click.echo(f"盈利: {result.win_trades} 次, 亏损: {result.lose_trades} 次")

        if result.trades:
            click.echo(f"\n📋 交易记录 (最近10条)")
            click.echo("-" * 80)
            for trade in result.trades[-10:]:
                action = "买入" if trade.action == "buy" else "卖出"
                profit_str = f"盈亏: {trade.profit:+.2f}" if trade.action == "sell" else ""
                click.echo(
                    f"  {trade.date} {action} {trade.name}({trade.code}) "
                    f"价格: {trade.price:.2f} 股数: {trade.shares} {profit_str}"
                )

        click.echo("=" * 60)

    except Exception as e:
        click.echo(f"❌ 回测失败: {e}", err=True)


@cli.command("investment-status")
@click.option("--pool-name", default="default", help="股票池名称")
def investment_status_command(pool_name):
    """查看投资系统状态

    显示当前投资策略系统的整体状态
    """
    from .data.investment_system import InvestmentSystem

    system = InvestmentSystem(pool_name)
    report = system.generate_report()
    click.echo(report)


@cli.command("investment-report")
@click.option("--pool-name", default="default", help="股票池名称")
@click.option("--output", type=click.Path(), help="输出文件路径")
def investment_report_command(pool_name, output):
    """生成投资报告

    导出投资系统数据到文件
    """
    from pathlib import Path
    from .data.investment_system import InvestmentSystem

    system = InvestmentSystem(pool_name)

    output_path = Path(output) if output else None
    filepath = system.export_data(output_path)

    click.echo(f"\n✅ 报告已生成: {filepath}")


@cli.command("optimize-strategy")
@click.option("--strategies", help="策略列表（逗号分隔）")
@click.option("--days", type=int, default=60, help="历史数据天数")
@click.option("--metric", type=click.Choice(["sharpe_ratio", "total_return", "win_rate"]), default="sharpe_ratio", help="优化指标")
def optimize_strategy_command(strategies, days, metric):
    """策略优化

    比较多个策略，找出最佳策略

    示例:
        asset-lens optimize-strategy --strategies value,momentum,dividend
        asset-lens optimize-strategy --metric win_rate --days 90
    """
    from datetime import datetime, timedelta
    from .data.investment_system import investment_system
    from .data.stock_history_fetcher import stock_history_fetcher
    from .data.market_stock_fetcher import market_stock_fetcher

    click.echo("\n📊 策略优化")
    click.echo("=" * 60)

    strategy_list = strategies.split(",") if strategies else None

    click.echo("📡 正在获取历史数据...")

    end = datetime.now()
    start = end - timedelta(days=days)

    stocks = market_stock_fetcher.get_cached_market_stocks()
    if not stocks:
        click.echo("❌ 没有市场数据，请先运行 'make fetch-market-stocks'", err=True)
        return

    stock_codes = [s.get("code", "") for s in stocks[:100] if s.get("code")]

    historical_data: Dict[str, List[Dict[str, Any]]] = {}
    for code in stock_codes[:20]:
        try:
            history = stock_history_fetcher.fetch_history(code, days=days)
            if history:
                klines: List[Dict[str, Any]] = history.get("klines", [])
                if klines:
                    historical_data[code] = klines
        except Exception:
            pass

    if not historical_data:
        click.echo("❌ 无法获取历史数据", err=True)
        return

    click.echo(f"✅ 获取 {len(historical_data)} 只股票的历史数据")

    click.echo(f"\n🔍 正在优化策略（指标: {metric}）...")
    try:
        best_name, best_result = investment_system.optimize_strategy(
            historical_data=historical_data,
            strategies=strategy_list,
            metric=metric,
        )

        click.echo(f"\n🏆 最佳策略: {best_name}")
        click.echo("-" * 60)
        click.echo(f"总收益率: {best_result.total_return*100:+.2f}%")
        click.echo(f"年化收益: {best_result.annual_return*100:+.2f}%")
        click.echo(f"最大回撤: {best_result.max_drawdown*100:.2f}%")
        click.echo(f"夏普比率: {best_result.sharpe_ratio:.2f}")
        click.echo(f"胜率: {best_result.win_rate:.1f}%")
        click.echo("=" * 60)

    except Exception as e:
        click.echo(f"❌ 优化失败: {e}", err=True)


@cli.command("track-stocks")
@click.argument("action", type=click.Choice(["record", "detect", "report"]))
@click.option("--pool-name", default="default", help="股票池名称")
@click.option("--fetch-market", is_flag=True, help="先获取市场数据")
def track_stocks_command(action, pool_name, fetch_market):
    """股票跟踪监控

    动作:
    - record: 记录股票池中股票的每日数据
    - detect: 检测妖股信号
    - report: 生成跟踪报告

    示例:
        asset-lens track-stocks record --fetch-market
        asset-lens track-stocks detect
        asset-lens track-stocks report
    """
    from .data.stock_tracker import StockTracker
    from .data.market_stock_fetcher import market_stock_fetcher

    tracker = StockTracker(pool_name)

    if action == "record":
        if fetch_market:
            click.echo("📡 正在获取市场数据...")
            stocks = market_stock_fetcher.fetch_all_cn_stocks()
            if stocks:
                market_stock_fetcher.save_market_stocks(stocks)
            else:
                click.echo("❌ 获取市场数据失败", err=True)
                return
        else:
            stocks = market_stock_fetcher.get_cached_market_stocks()

        if not stocks:
            click.echo("❌ 没有市场数据", err=True)
            return

        count = tracker.record_batch(stocks)
        click.echo(f"✅ 记录了 {count} 只股票的每日数据")

    elif action == "detect":
        click.echo("🔍 正在检测妖股信号...")
        signals = tracker.detect_monster_stocks()

        if not signals:
            click.echo("❌ 没有检测到妖股信号")
            return

        click.echo(f"\n🔥 检测到 {len(signals)} 个妖股信号:\n")
        click.echo("=" * 80)
        click.echo(f"{'代码':<10} {'名称':<12} {'信号类型':<30} {'得分':>8}")
        click.echo("-" * 80)

        for s in signals:
            click.echo(f"{s.code:<10} {s.name:<12} {s.signal_type:<30} {s.score:>8.0f}")

        click.echo("=" * 80)

    elif action == "report":
        tracker.print_tracking_report()


@cli.command("momentum-screen")
@click.option("--min-score", type=float, default=60, help="最低策略得分")
@click.option("--max-results", type=int, default=20, help="最大结果数")
@click.option("--add-to-pool", is_flag=True, help="自动添加到股票池")
@click.option("--pool-name", default="momentum", help="股票池名称")
@click.option("--use-cache", is_flag=True, default=True, help="使用缓存数据")
def momentum_screen_command(min_score, max_results, add_to_pool, pool_name, use_cache):
    """动量策略选股

    使用 momentum 策略筛选股票，可选自动添加到股票池

    示例:
        asset-lens momentum-screen
        asset-lens momentum-screen --add-to-pool
        asset-lens momentum-screen --min-score 70 --max-results 10
    """
    from .data.strategy_engine import strategy_engine
    from .data.stock_pool import StockPool
    from .data.market_stock_fetcher import market_stock_fetcher

    click.echo("\n📊 动量策略选股")
    click.echo("=" * 60)

    stocks = None
    if use_cache:
        stocks = market_stock_fetcher.get_cached_market_stocks()
        if stocks:
            click.echo(f"✅ 使用缓存数据: {len(stocks)} 只股票")
    
    if not stocks:
        click.echo("📡 正在获取市场数据...")
        stocks = market_stock_fetcher.fetch_all_cn_stocks()
        if stocks:
            market_stock_fetcher.save_market_stocks(stocks)
            click.echo(f"✅ 获取 {len(stocks)} 只股票")
        else:
            click.echo("❌ 获取市场数据失败", err=True)
            return

    click.echo(f"\n🔍 使用 momentum 策略筛选...")
    results = strategy_engine.screen_stocks(stocks, "momentum", min_score)

    if not results:
        click.echo("❌ 没有找到符合条件的股票")
        return

    click.echo(f"\n✅ 找到 {len(results)} 只符合条件的股票:\n")
    click.echo("=" * 120)
    click.echo(f"{'排名':<4} {'代码':<10} {'名称':<12} {'现价':>8} {'涨跌%':>8} {'换手%':>8} {'策略分':>8} {'匹配条件':>8}")
    click.echo("-" * 120)

    for i, stock in enumerate(results[:max_results], 1):
        code = stock.get("code", "")
        name = stock.get("name", "")
        price = stock.get("current_price", 0)
        change = stock.get("change_percent", 0)
        turnover = stock.get("turnover_rate", 0)
        score = stock.get("strategy_score", 0)
        matched = stock.get("matched_conditions", 0)

        change_str = f"{change:+.2f}%"
        click.echo(f"{i:<4} {code:<10} {name:<12} {price:>8.2f} {change_str:>8} {turnover:>8.2f} {score:>8.1f} {matched:>8}")

    click.echo("=" * 120)

    if add_to_pool:
        pool = StockPool(pool_name)
        pool.config.strategy_name = "momentum"
        added = 0

        for stock in results[:max_results]:
            code = stock.get("code", "")
            name = stock.get("name", "")
            price = stock.get("current_price", 0)
            score = stock.get("strategy_score", 0)

            if pool.add_stock(code, name, price, "watching", f"策略得分: {score:.1f}", strategy_score=score):
                added += 1

        click.echo(f"\n✅ 已添加 {added} 只股票到股票池 '{pool_name}'")


@cli.command("market-environment")
@click.option("--analyze", is_flag=True, help="分析当前市场环境")
@click.option("--adapt", help="适配策略参数（指定策略名称）")
def market_environment_command(analyze, adapt):
    """市场环境分析

    分析当前市场环境，推荐适合的策略

    示例:
        asset-lens market-environment --analyze
        asset-lens market-environment --adapt momentum
    """
    from .data.market_environment import market_environment_analyzer
    from .data.market_stock_fetcher import market_stock_fetcher

    if analyze:
        click.echo("\n📊 分析市场环境...")
        click.echo("=" * 60)

        stocks = market_stock_fetcher.get_cached_market_stocks()

        index_data = {}
        if stocks:
            changes = [s.get("change_percent", 0) for s in stocks]
            index_data["change_5d"] = sum(changes[:5]) / 5 if len(changes) >= 5 else 0
            index_data["change_20d"] = sum(changes[:20]) / 20 if len(changes) >= 20 else 0
            index_data["change_60d"] = sum(changes[:60]) / 60 if len(changes) >= 60 else 0
            index_data["volatility"] = (max(changes) - min(changes)) / 2 if changes else 0

        environment = market_environment_analyzer.analyze_environment(index_data, stocks)
        report = market_environment_analyzer.get_environment_report()
        click.echo(report)

    elif adapt:
        click.echo(f"\n📊 适配策略: {adapt}")
        click.echo("=" * 60)

        stocks = market_stock_fetcher.get_cached_market_stocks()
        index_data = {}
        if stocks:
            changes = [s.get("change_percent", 0) for s in stocks]
            index_data["change_5d"] = sum(changes[:5]) / 5 if len(changes) >= 5 else 0
            index_data["change_20d"] = sum(changes[:20]) / 20 if len(changes) >= 20 else 0
            index_data["change_60d"] = sum(changes[:60]) / 60 if len(changes) >= 60 else 0
            index_data["volatility"] = (max(changes) - min(changes)) / 2 if changes else 0

        environment = market_environment_analyzer.analyze_environment(index_data, stocks)
        adaptation = market_environment_analyzer.adapt_strategy(adapt, environment)

        click.echo(f"\n策略: {adaptation.strategy_name}")
        click.echo(f"预期表现: {adaptation.expected_performance}")
        click.echo(f"调整原因: {adaptation.reason}")
        click.echo(f"\n原始参数:")
        for key, value in adaptation.original_params.items():
            click.echo(f"  {key}: {value}")
        click.echo(f"\n适配参数:")
        for key, value in adaptation.adapted_params.items():
            original = adaptation.original_params.get(key, value)
            if value != original:
                click.echo(f"  {key}: {value} (原: {original})")
            else:
                click.echo(f"  {key}: {value}")

    else:
        report = market_environment_analyzer.get_environment_report()
        click.echo(report)


@cli.command("personal-data")
@click.argument("action", type=click.Choice(["load", "summary", "history"]))
@click.option("--index", help="指数名称")
@click.option("--etf", help="ETF名称")
@click.option("--days", type=int, default=30, help="历史天数")
def personal_data_command(action, index, etf, days):
    """个人数据管理

    整合您每周记录的指数、汇率等数据

    动作:
    - load: 加载每周数据
    - summary: 显示市场概况
    - history: 查看历史数据

    示例:
        asset-lens personal-data load
        asset-lens personal-data summary
        asset-lens personal-data history --index 上证指数 --days 60
    """
    from .data.personal_data_integrator import personal_data_integrator

    if action == "load":
        click.echo("\n📊 加载个人每周数据...")
        count = personal_data_integrator.load_weekly_data()
        click.echo(f"✅ 加载了 {count} 条记录")

    elif action == "summary":
        personal_data_integrator.print_market_summary()

    elif action == "history":
        if index:
            click.echo(f"\n📊 {index} 历史数据 ({days}天):")
            history = personal_data_integrator.get_index_history(index, days)
            if history:
                click.echo("-" * 40)
                for date, value in history[-10:]:
                    click.echo(f"  {date}: {value:.2f}")
            else:
                click.echo("❌ 没有找到数据")

        elif etf:
            click.echo(f"\n📊 {etf} 历史数据 ({days}天):")
            history = personal_data_integrator.get_etf_history(etf, days)
            if history:
                click.echo("-" * 40)
                for date, value in history[-10:]:
                    click.echo(f"  {date}: {value:.2f}")
            else:
                click.echo("❌ 没有找到数据")

        else:
            click.echo("❌ 请指定 --index 或 --etf 参数")


@cli.command("run-daily-tasks")
@click.option("--run-now", is_flag=True, help="立即执行一次")
def run_daily_tasks_command(run_now):
    """运行每日任务

    自动执行: 数据更新、策略选股、股票跟踪、妖股检测

    示例:
        asset-lens run-daily-tasks --run-now
    """
    from .data.scheduler import task_scheduler

    if run_now:
        results = task_scheduler.run_daily_tasks()
        click.echo("\n📋 任务执行结果:")
        for r in results:
            status = "✅" if r.get("status") == "completed" else "❌"
            click.echo(f"  {status} {r.get('task', 'unknown')}: {r.get('status', 'unknown')}")
    else:
        click.echo("\n🚀 启动定时任务调度器...")
        click.echo("   每日执行时间: 09:30")
        click.echo("   按 Ctrl+C 停止")
        task_scheduler.start_scheduler(daily_time="09:30", run_on_start=False)


@cli.command("task-status")
def task_status_command():
    """查看任务状态"""
    from .data.scheduler import task_scheduler

    status = task_scheduler.get_task_status()

    click.echo("\n📋 任务状态")
    click.echo("=" * 60)
    click.echo(f"当前时间: {status['current_time']}")

    if status["tasks"]:
        click.echo("\n任务执行记录:")
        for task_name, task_info in status["tasks"].items():
            status_icon = "✅" if task_info.get("status") == "success" else "❌"
            click.echo(f"  {status_icon} {task_name}")
            click.echo(f"     最后执行: {task_info.get('last_run', 'N/A')}")
            click.echo(f"     状态: {task_info.get('status', 'N/A')}")
            if task_info.get("message"):
                click.echo(f"     信息: {task_info.get('message')}")
    else:
        click.echo("\n暂无任务执行记录")

    click.echo("=" * 60)


@cli.command("report")
@click.argument("report_type", type=click.Choice(["strategy", "pool", "comparison", "risk"]))
@click.option("--strategy", default="momentum", help="策略名称（用于策略报告）")
@click.option("--pool-name", default="momentum", help="股票池名称")
def report_command(report_type, strategy, pool_name):
    """生成投资报告

    报告类型:
    - strategy: 策略报告
    - pool: 股票池报告
    - comparison: 策略对比报告
    - risk: 风险评估报告

    示例:
        asset-lens report strategy --strategy momentum
        asset-lens report pool --pool-name momentum
        asset-lens report comparison
        asset-lens report risk --pool-name momentum
    """
    from .data.report_generator import investment_report_generator

    if report_type == "strategy":
        report = investment_report_generator.generate_strategy_report(strategy, pool_name)
    elif report_type == "pool":
        report = investment_report_generator.generate_pool_report(pool_name)
    elif report_type == "comparison":
        report = investment_report_generator.generate_comparison_report()
    elif report_type == "risk":
        report = investment_report_generator.generate_risk_report(pool_name)

    investment_report_generator.print_report(report)


@cli.command("risk-summary")
@click.option("--pool-name", default="momentum", help="股票池名称")
def risk_summary_command(pool_name):
    """查看风险摘要"""
    from .data.risk_manager import risk_manager

    risk_manager.print_risk_summary(pool_name)


@cli.command("position-advice")
@click.option("--pool-name", default="momentum", help="股票池名称")
@click.option("--capital", type=float, default=100000, help="总资金")
def position_advice_command(pool_name, capital):
    """获取仓位建议"""
    from .data.risk_manager import risk_manager

    advices = risk_manager.calculate_position_advice(pool_name, capital)

    click.echo("\n📊 仓位建议")
    click.echo("=" * 60)
    click.echo(f"股票池: {pool_name}")
    click.echo(f"总资金: {capital:,.0f}")
    click.echo("")

    if not advices:
        click.echo("无持仓")
        return

    click.echo(f"{'代码':<10} {'名称':<12} {'当前仓位':>10} {'建议仓位':>10} {'操作':>8} {'原因':<20}")
    click.echo("-" * 80)

    for advice in advices:
        action_icon = "📈" if advice.action == "increase" else "📉" if advice.action == "decrease" else "➡️"
        click.echo(
            f"{advice.code:<10} {advice.name:<12} "
            f"{advice.current_position:>10.1%} {advice.suggested_position:>10.1%} "
            f"{action_icon} {advice.action:<6} {advice.reason:<20}"
        )

    click.echo("=" * 60)


@cli.command("stop-loss")
@click.argument("code")
@click.option("--buy-price", type=float, required=True, help="买入价格")
@click.option("--strategy", help="策略名称")
def stop_loss_command(code, buy_price, strategy):
    """计算止损止盈位"""
    from .data.risk_manager import risk_manager

    result = risk_manager.calculate_stop_loss_take_profit(code, buy_price, strategy_name=strategy)

    click.echo("\n📊 止损止盈建议")
    click.echo("=" * 60)
    click.echo(f"股票代码: {code}")
    click.echo(f"买入价格: {buy_price:.2f}")
    click.echo(f"计算方法: {result['method']}")
    click.echo("")
    click.echo(f"止损位: {result['stop_loss_price']:.2f} ({result['stop_loss']:.2%})")
    click.echo(f"止盈位: {result['take_profit_price']:.2f} ({result['take_profit']:.2%})")
    click.echo(f"风险收益比: {result['risk_reward_ratio']:.2f}")
    click.echo("=" * 60)


if __name__ == "__main__":
    cli()
