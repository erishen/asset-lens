"""
Report CLI commands for asset-lens.
报告命令模块 - 包含 report, show-asset-summary, show-exchange-rate-history, show-sell-records, export-asset-summary, risk-summary, position-advice, stop-loss
"""

from pathlib import Path

import click


def _get_data_dir(data_mode: str) -> Path | None:
    """获取数据目录"""
    from asset_lens.config import config

    if data_mode == "real":
        result = config.get_latest_data_dir()
        return result if result else None
    else:
        return config.project_root / "data" / "sample_data"


def register_report_commands(cli: click.Group) -> None:
    """注册报告命令到 CLI 组"""

    @cli.command()
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="当前数据模式")
    def show_asset_summary(data_mode: str | None):
        """显示资产汇总（资产汇总-表格 1.csv）"""
        from asset_lens.config import config
        from asset_lens.data.asset_summary_parser import AssetSummaryParser

        actual_mode = data_mode or config.data_mode
        data_dir = _get_data_dir(actual_mode)
        if not data_dir:
            click.echo("❌ 数据目录不存在")
            return

        csv_file = data_dir / "资产汇总-表格 1.csv"
        if not csv_file.exists():
            csv_file = data_dir / "备份-表格 1.csv"

        if not csv_file.exists():
            click.echo(f"❌ 资产汇总文件不存在: {csv_file}")
            return

        try:
            summaries = AssetSummaryParser.parse_csv_file(csv_file)
            click.echo(f"\n📊 资产汇总记录（共 {len(summaries)} 条）")
            click.echo("=" * 80)

            for summary in summaries[-10:]:
                click.echo(f"日期: {summary.summary_date.strftime('%Y-%m-%d')}")
                click.echo(f"  总金额: ¥{summary.total_amount:,.2f}")
                click.echo(f"  信用卡: ¥{summary.credit_card_amount:,.2f}")
                if summary.return_rate is not None:
                    click.echo(f"  收益率: {summary.return_rate:.2f}%")

            if len(summaries) > 10:
                click.echo(f"\n... 还有 {len(summaries) - 10} 条记录未显示")

            click.echo("=" * 80)

        except Exception as e:
            click.echo(f"❌ 读取资产汇总失败: {e}", err=True)

    @cli.command()
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="当前数据模式")
    def show_exchange_rate_history(data_mode: str | None):
        """显示汇率历史（资产汇总-表格 1.csv）"""
        from asset_lens.config import config
        from asset_lens.data.exchange_rate_parser import ExchangeRateParser

        actual_mode = data_mode or config.data_mode
        data_dir = _get_data_dir(actual_mode)
        if not data_dir:
            click.echo("❌ 数据目录不存在")
            return

        csv_file = data_dir / "资产汇总-表格 1.csv"
        if not csv_file.exists():
            csv_file = data_dir / "备份-表格 1.csv"

        if not csv_file.exists():
            click.echo(f"❌ 汇率历史文件不存在: {csv_file}")
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

    @cli.command()
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="当前数据模式")
    def show_sell_records(data_mode: str | None):
        """显示卖出记录（卖出记录-表格 1.csv）"""
        from asset_lens.config import config
        from asset_lens.data.sell_record_parser import SellRecordParser

        actual_mode = data_mode or config.data_mode
        data_dir = _get_data_dir(actual_mode)
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

            for record in records[-20:]:
                click.echo(f"日期: {record.sell_date.strftime('%Y-%m-%d')}")
                click.echo(f"  名称: {record.name}")
                click.echo(f"  初始金额: ¥{record.initial_amount:,.2f}")
                click.echo(f"  收益金额: ¥{record.profit_amount:,.2f}")
                click.echo(f"  收益率: {record.return_rate:.2f}%")

            if len(records) > 20:
                click.echo(f"\n... 还有 {len(records) - 20} 条记录未显示")

            click.echo("=" * 80)

        except Exception as e:
            click.echo(f"❌ 读取卖出记录失败: {e}", err=True)

    @cli.command()
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="当前数据模式")
    @click.option("--output-format", type=click.Choice(["console", "csv", "json"]), default="console", help="输出格式")
    def export_asset_summary(data_mode: str | None, output_format: str):
        """导出资产汇总数据"""
        from asset_lens.config import config
        from asset_lens.data.asset_summary_parser import AssetSummaryParser

        actual_mode = data_mode or config.data_mode
        data_dir = _get_data_dir(actual_mode)
        if not data_dir:
            click.echo("❌ 数据目录不存在")
            return

        csv_file = data_dir / "资产汇总-表格 1.csv"
        if not csv_file.exists():
            csv_file = data_dir / "备份-表格 1.csv"

        try:
            summaries = AssetSummaryParser.parse_csv_file(csv_file)

            if output_format == "console":
                click.echo(f"\n📊 资产汇总数据（共 {len(summaries)} 条）")
                click.echo("=" * 80)

                for summary in summaries:
                    click.echo(f"日期: {summary.summary_date.strftime('%Y-%m-%d')}")
                    click.echo(f"  总金额: ¥{summary.total_amount:,.2f}")
                    click.echo(f"  收益率: {summary.return_rate:.2f}%")

                click.echo("=" * 80)

            elif output_format == "csv":
                output_file = config.output_path / "asset_summary.csv"
                import csv
                with open(output_file, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["日期", "总金额", "总投资价值", "收益率"])
                    for summary in summaries:
                        writer.writerow([
                            summary.summary_date.strftime("%Y-%m-%d"),
                            summary.total_amount,
                            summary.total_investment_value,
                            summary.return_rate,
                        ])
                click.echo(f"✅ 数据已导出到: {output_file}")

            elif output_format == "json":
                import json
                output_file = config.output_path / "asset_summary.json"
                data = [{
                    "date": s.summary_date.strftime("%Y-%m-%d"),
                    "total_amount": s.total_amount,
                    "total_investment_value": s.total_investment_value,
                    "return_rate": s.return_rate,
                } for s in summaries]
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                click.echo(f"✅ 数据已导出到: {output_file}")

        except Exception as e:
            click.echo(f"❌ 导出失败: {e}", err=True)

    @cli.command()
    def report():
        """生成投资报告"""
        from asset_lens.report.investment_report import investment_report_generator

        click.echo("\n📝 生成投资报告")
        click.echo("=" * 60)

        try:
            report_path = investment_report_generator.generate_pool_report()
            click.echo(f"\n✅ 报告已生成: {report_path}")
        except Exception as e:
            click.echo(f"❌ 生成报告失败: {e}", err=True)

    @cli.command()
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    def risk_summary(data_mode: str | None):
        """显示风险摘要"""
        from asset_lens.config import config
        from asset_lens.data.csv_parser import CSVParser

        if data_mode:
            config.data_mode = data_mode

        click.echo("\n📊 风险摘要")
        click.echo("=" * 60)

        try:
            products = CSVParser.load_data()
            click.echo(f"✅ 成功加载 {len(products)} 个投资产品")

            total_value = sum(p.current_amount or 0 for p in products)
            risk_distribution = {}
            for p in products:
                risk = p.risk_level or "未知"
                risk_distribution[risk] = risk_distribution.get(risk, 0) + (p.current_amount or 0)

            click.echo("\n📈 风险统计:")
            click.echo(f"  总资产: ¥{total_value:,.2f}")
            click.echo("  风险等级分布:")
            for level, amount in risk_distribution.items():
                click.echo(f"    {level}: ¥{amount:,.2f}")

            click.echo("\n✅ 风险分析完成！")

        except Exception as e:
            click.echo(f"❌ 分析失败: {e}", err=True)

    @cli.command()
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    def position_advice(data_mode: str | None):
        """显示仓位建议"""
        from asset_lens.config import config
        from asset_lens.data.csv_parser import CSVParser

        if data_mode:
            config.data_mode = data_mode

        click.echo("\n📊 仓位建议")
        click.echo("=" * 60)

        try:
            products = CSVParser.load_data()
            click.echo(f"✅ 成功加载 {len(products)} 个投资产品")

            click.echo("\n📈 仓位建议:")
            for product in products[:10]:
                advice = "持有"
                if product.annual_return is not None:
                    if product.annual_return > 20:
                        advice = "考虑止盈"
                    elif product.annual_return < -10:
                        advice = "考虑止损"
                click.echo(f"  {product.name}: {advice}")

            click.echo("\n✅ 分析完成！")

        except Exception as e:
            click.echo(f"❌ 分析失败: {e}", err=True)

    @cli.command()
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    def stop_loss(data_mode: str | None):
        """计算止损止盈位"""
        from asset_lens.config import config
        from asset_lens.data.csv_parser import CSVParser

        if data_mode:
            config.data_mode = data_mode

        click.echo("\n📊 止损止盈计算")
        click.echo("=" * 60)

        try:
            products = CSVParser.load_data()
            click.echo(f"✅ 成功加载 {len(products)} 个投资产品")

            for product in products[:10]:
                if product.current_amount and product.initial_amount:
                    entry_price = float(product.initial_amount)
                    current_price = float(product.current_amount)
                    stop_loss_price = entry_price * 0.9
                    take_profit_price = entry_price * 1.2

                    click.echo(f"\n{product.name}:")
                    click.echo(f"  止损位: ¥{stop_loss_price:.2f} (-10%)")
                    click.echo(f"  止盈位: ¥{take_profit_price:.2f} (+20%)")

            click.echo("\n✅ 计算完成！")

        except Exception as e:
            click.echo(f"❌ 计算失败: {e}", err=True)
