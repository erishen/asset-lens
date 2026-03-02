"""
CLI (Command Line Interface) for asset-lens.
命令行接口模块
"""

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict

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
def weekly_report():
    """生成周度收益报告"""
    ctx = click.get_current_context()
    ctx.invoke(analyze, output_format="all")


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

    if data_mode == "real":
        csv_file = config.get_latest_data_dir() / "资产汇总-表格 1.csv"
    else:
        data_dir = config.project_root / "data" / "sample_data"
        csv_file = data_dir / "资产汇总-表格 1.csv"

    if not csv_file.exists():
        # 兼容旧文件名
        if data_mode == "real":
            csv_file = config.get_latest_data_dir() / "备份-表格 1.csv"
        else:
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

    if data_mode == "real":
        csv_file = config.get_latest_data_dir() / "资产汇总-表格 1.csv"
    else:
        data_dir = config.project_root / "data" / "sample_data"
        csv_file = data_dir / "资产汇总-表格 1.csv"

    if not csv_file.exists():
        # 兼容旧文件名
        if data_mode == "real":
            csv_file = config.get_latest_data_dir() / "备份-表格 1.csv"
        else:
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

    if data_mode == "real":
        csv_file = config.get_latest_data_dir() / "卖出记录-表格 1.csv"
    else:
        data_dir = config.project_root / "data" / "sample_data"
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

    if data_mode == "real":
        csv_file = config.get_latest_data_dir() / "资产汇总-表格 1.csv"
    else:
        data_dir = config.project_root / "data" / "sample_data"
        csv_file = data_dir / "资产汇总-表格 1.csv"

    if not csv_file.exists():
        # 兼容旧文件名
        if data_mode == "real":
            csv_file = config.get_latest_data_dir() / "备份-表格 1.csv"
        else:
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

    if data_mode == "real":
        csv_file = config.get_latest_data_dir() / "卖出记录-表格 1.csv"
    else:
        data_dir = config.project_root / "data" / "sample_data"
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

    if data_mode == "real":
        csv_file = config.get_latest_data_dir() / "资产汇总-表格 1.csv"
    else:
        data_dir = config.project_root / "data" / "sample_data"
        csv_file = data_dir / "资产汇总-表格 1.csv"

    if not csv_file.exists():
        # 兼容旧文件名
        if data_mode == "real":
            csv_file = config.get_latest_data_dir() / "备份-表格 1.csv"
        else:
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
def estimate_pnl(data_mode, weekly):
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
        click.echo(f"📈 总收益率: {result['total_return_rate']:.2f}%")
        click.echo(f"💵 估算产品金额: ¥{result['total_amount']:,.2f}")
        if "total_amount_all" in result:
            click.echo(f"💵 所有产品金额: ¥{result['total_amount_all']:,.2f}")

        # 显示指数涨跌幅
        click.echo(f"\n📊 市场指数涨跌幅:")
        for index_key, move in result["moves"].items():
            click.echo(f"  {index_key}: {move:+.2f}%")

        # 显示明细表格
        if result["details"]:
            table = Table(title="\n产品盈亏明细")
            table.add_column("产品名称", style="cyan", no_wrap=True)
            table.add_column("类型", style="green", no_wrap=True)
            table.add_column("金额", justify="right", style="yellow")
            table.add_column("盈亏", justify="right")
            table.add_column("收益率", justify="right")
            table.add_column("指数", style="blue", no_wrap=True)

            for detail in result["details"][:20]:  # 只显示前20个
                pnl_color = "green" if detail["pnl"] >= 0 else "red"
                return_color = "green" if detail["return_rate"] >= 0 else "red"

                table.add_row(
                    detail["name"][:20],
                    detail["type"],
                    f"¥{detail['amount']:,.0f}",
                    f"¥{detail['pnl']:,.2f}",
                    f"{detail['return_rate']:.2f}%",
                    detail["index_key"],
                )

            console.print(table)

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
        if config.is_real_mode:
            csv_file = config.get_latest_data_dir() / "卖出记录-表格 1.csv"
        else:
            data_dir = config.project_root / "data" / "sample_data"
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
def update_market_data(api):
    """更新市场指数数据

    API 选择说明：
    - alphavantage: 获取完整历史数据（最近一周OHLCV、周期表现、技术状态），免费版25次/天
    - finnhub: 仅获取实时报价数据，免费版60次/分钟

    推荐使用 alphavantage 以获得与 ts-demo 一致的数据格式
    """
    from .data.market_data_fetcher import MarketDataFetcher

    click.echo("\n📊 更新市场指数数据")
    click.echo("=" * 60)

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
        fetcher = MarketDataFetcher()
        success = fetcher.update_all_cache(api)

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


if __name__ == "__main__":
    cli()
