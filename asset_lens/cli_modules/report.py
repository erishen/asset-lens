"""
CLI Report Commands.
CLI 报告命令
"""

import click
from pathlib import Path
from datetime import datetime
from typing import Optional

from ..config import config


def get_data_dir(data_mode: Optional[str] = None) -> Optional[Path]:
    """获取数据目录"""
    if data_mode:
        config.data_mode = data_mode
    return config.data_path


def show_asset_summary(data_mode: Optional[str] = None):
    """显示资产汇总"""
    from ..data.asset_summary_parser import AssetSummaryParser

    data_dir = get_data_dir(data_mode)
    if not data_dir:
        click.echo("❌ 数据目录不存在")
        return

    csv_file = data_dir / "资产汇总-表格 1.csv"

    if not csv_file.exists():
        csv_file = data_dir / "备份-表格 1.csv"

    if not csv_file.exists():
        click.echo(f"❌ 资产汇总文件不存在: {csv_file}")
        click.echo(f"💡 提示: 请确保数据目录中有相应的数据文件")
        return

    try:
        summaries = AssetSummaryParser.parse_csv_file(csv_file)
        click.echo(f"\n📊 资产汇总记录（共 {len(summaries)} 条）")
        click.echo("=" * 80)

        for summary in summaries[-10:]:
            click.echo(f"日期: {summary.summary_date.strftime('%Y-%m-%d')}")
            click.echo(f"  总金额: ¥{summary.total_amount:,.2f}")

            from ..core.platform_loader import PlatformLoader

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


def show_exchange_rate_history(data_mode: Optional[str] = None):
    """显示汇率历史"""
    from ..data.exchange_rate_parser import ExchangeRateParser

    data_dir = get_data_dir(data_mode)
    if not data_dir:
        click.echo("❌ 数据目录不存在")
        return

    csv_file = data_dir / "资产汇总-表格 1.csv"

    if not csv_file.exists():
        csv_file = data_dir / "备份-表格 1.csv"

    if not csv_file.exists():
        click.echo(f"❌ 汇率历史文件不存在: {csv_file}")
        click.echo(f"💡 提示: 请确保数据目录中有相应的数据文件")
        return

    try:
        rates = ExchangeRateParser.parse_csv_file(csv_file)
        click.echo(f"\n📊 汇率历史记录（共 {len(rates)} 条）")
        click.echo("=" * 80)

        for rate in rates[-20:]:
            click.echo(f"日期: {rate.rate_date.strftime('%Y-%m-%d')}")
            click.echo(f"  美元汇率: {rate.usd_rate:.4f}")
            click.echo(f"  港元汇率: {rate.hkd_rate:.4f}")

        if len(rates) > 20:
            click.echo(f"\n... 还有 {len(rates) - 20} 条记录未显示")

        click.echo("=" * 80)

    except Exception as e:
        click.echo(f"❌ 读取汇率历史失败: {e}", err=True)


def show_sell_records(data_mode: Optional[str] = None):
    """显示卖出记录"""
    from ..data.sell_record_parser import SellRecordParser

    data_dir = get_data_dir(data_mode)
    if not data_dir:
        click.echo("❌ 数据目录不存在")
        return

    csv_file = data_dir / "卖出记录-表格 1.csv"

    if not csv_file.exists():
        click.echo(f"❌ 卖出记录文件不存在: {csv_file}")
        return

    try:
        records = SellRecordParser.parse_csv_file(csv_file)
        click.echo(f"\n📊 卖出记录（共 {len(records)} 条）")
        click.echo("=" * 80)

        for record in records[-10:]:
            click.echo(f"产品: {record.name}")
            click.echo(f"  卖出日期: {record.sell_date.strftime('%Y-%m-%d')}")
            click.echo(f"  初始金额: ¥{record.initial_amount:,.2f}")
            click.echo(f"  收益: ¥{record.profit_amount:,.2f}")
            click.echo(f"  收益率: {record.return_rate:.2f}%")

        if len(records) > 10:
            click.echo(f"\n... 还有 {len(records) - 10} 条记录未显示")

        click.echo("=" * 80)

    except Exception as e:
        click.echo(f"❌ 读取卖出记录失败: {e}", err=True)


def export_asset_summary(output_format: str = "csv", data_mode: Optional[str] = None):
    """导出资产汇总"""
    from ..data.asset_summary_parser import AssetSummaryParser

    data_dir = get_data_dir(data_mode)
    if not data_dir:
        click.echo("❌ 数据目录不存在")
        return

    csv_file = data_dir / "资产汇总-表格 1.csv"

    if not csv_file.exists():
        click.echo(f"❌ 资产汇总文件不存在: {csv_file}")
        return

    try:
        summaries = AssetSummaryParser.parse_csv_file(csv_file)
        output_path = config.output_path
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if output_format in ["csv", "all"]:
            output_file = output_path / f"asset_summary_{timestamp}.csv"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("日期,总金额,信用卡,京东白条,抖音月付,多多后付,黄金\n")
                for s in summaries:
                    f.write(
                        f"{s.summary_date.strftime('%Y-%m-%d')},"
                        f"{s.total_amount},"
                        f"{s.credit_card_amount},"
                        f"{s.jingdong_white_amount},"
                        f"{s.douyin_monthly_amount},"
                        f"{s.duoduo_later_amount},"
                        f"{s.gold_amount}\n"
                    )
            click.echo(f"✅ CSV 导出成功: {output_file}")

        if output_format in ["json", "all"]:
            import json

            output_file = output_path / f"asset_summary_{timestamp}.json"
            data = [
                {
                    "date": s.summary_date.strftime("%Y-%m-%d"),
                    "total_amount": float(s.total_amount),
                    "credit_card": float(s.credit_card_amount),
                    "jingdong_white": float(s.jingdong_white_amount),
                    "douyin_monthly": float(s.douyin_monthly_amount),
                    "duoduo_later": float(s.duoduo_later_amount),
                    "gold": float(s.gold_amount),
                }
                for s in summaries
            ]
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            click.echo(f"✅ JSON 导出成功: {output_file}")

    except Exception as e:
        click.echo(f"❌ 导出失败: {e}", err=True)


def export_sell_records(output_format: str = "csv", data_mode: Optional[str] = None):
    """导出卖出记录"""
    from ..data.sell_record_parser import SellRecordParser

    data_dir = get_data_dir(data_mode)
    if not data_dir:
        click.echo("❌ 数据目录不存在")
        return

    csv_file = data_dir / "卖出记录-表格 1.csv"

    if not csv_file.exists():
        click.echo(f"❌ 卖出记录文件不存在: {csv_file}")
        return

    try:
        records = SellRecordParser.parse_csv_file(csv_file)
        output_path = config.output_path
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if output_format in ["csv", "all"]:
            output_file = output_path / f"sell_records_{timestamp}.csv"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("产品名称,卖出日期,初始金额,收益,收益率\n")
                for r in records:
                    f.write(
                        f"{r.name},"
                        f"{r.sell_date.strftime('%Y-%m-%d')},"
                        f"{r.initial_amount},"
                        f"{r.profit_amount},"
                        f"{r.return_rate}\n"
                    )
            click.echo(f"✅ CSV 导出成功: {output_file}")

    except Exception as e:
        click.echo(f"❌ 导出失败: {e}", err=True)
