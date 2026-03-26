"""
报告生成 CLI 命令
"""

from datetime import datetime

import click
from rich.console import Console
from rich.panel import Panel


def register_report_commands(cli: click.Group) -> None:
    """注册报告命令到 CLI 组"""

    @cli.command("weekly")
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    @click.option("--output", type=str, default="output/weekly_report.md", help="输出文件")
    def weekly(data_mode: str | None, output: str):
        """生成周度投资报告"""
        from pathlib import Path

        from asset_lens.cli.helpers import load_products, setup_data_mode

        setup_data_mode(data_mode)

        click.echo("\n📊 生成周度投资报告")
        click.echo("=" * 60)

        try:
            products = load_products()
            click.echo(f"✅ 成功加载 {len(products)} 个投资产品")

            output_path = Path(output)

            report_lines = [
                "# 周度投资报告",
                "",
                f"**报告日期**: {datetime.now().strftime('%Y-%m-%d')}",
                "",
                "## 投资组合概览",
                "",
                f"- 总产品数: {len(products)}",
                f"- 总金额: ¥{sum(float(p.current_amount or 0) for p in products):,.2f}",
                f"- 总收益: ¥{sum(float(p.current_amount or 0) - float(p.initial_amount or 0) for p in products):,.2f}",
                "",
                "## 本周重点关注",
                "",
                "### 涨幅前5",
                "",
            ]

            sorted_products = sorted(
                products,
                key=lambda p: float(p.return_rate or 0),
                reverse=True
            )[:5]

            for p in sorted_products:
                report_lines.append(f"- {p.name}: {float(p.return_rate or 0):.2f}%")

            report_lines.extend([
                "",
                "### 跌幅前5",
                "",
            ])

            sorted_products_desc = sorted(
                products,
                key=lambda p: float(p.return_rate or 0)
            )[:5]

            for p in sorted_products_desc:
                report_lines.append(f"- {p.name}: {float(p.return_rate or 0):.2f}%")

            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text("\n".join(report_lines), encoding="utf-8")

            click.echo(f"\n✅ 周报已生成: {output_path}")

        except Exception as e:
            click.echo(f"❌ 周报生成失败: {e}", err=True)

    @cli.command("chart")
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    @click.option("--output", type=str, default="output/charts", help="输出目录")
    def chart(data_mode: str | None, output: str):
        """生成投资分析图表"""
        from pathlib import Path

        from asset_lens.cli.helpers import load_products, setup_data_mode
        from asset_lens.data.chart_generator import ChartGenerator

        setup_data_mode(data_mode)

        click.echo("\n📊 生成投资分析图表")
        click.echo("=" * 60)

        try:
            products = load_products()
            click.echo(f"✅ 成功加载 {len(products)} 个投资产品")

            output_dir = Path(output)
            chart_gen = ChartGenerator()

            portfolio_data = {
                "products": [
                    {
                        "name": p.name,
                        "type": p.investment_type.value if p.investment_type else "未知",
                        "amount": float(p.current_amount or 0),
                        "return_rate": float(p.return_rate or 0),
                    }
                    for p in products
                ]
            }

            chart_data = chart_gen.generate_profit_curve(portfolio_data)
            click.echo(f"\n✅ 图表数据已生成")
            chart_gen.print_chart_summary(chart_data)

            click.echo("\n✅ 图表生成完成！")

        except Exception as e:
            click.echo(f"❌ 图表生成失败: {e}", err=True)

    @cli.command("generate-report")
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    @click.option("--output", type=str, default="output/report.pdf", help="输出文件")
    @click.option("--include-ai", is_flag=True, help="包含 AI 分析")
    def generate_report(data_mode: str | None, output: str, include_ai: bool):
        """生成投资分析报告（PDF）"""
        from pathlib import Path

        from asset_lens.cli.helpers import load_products, setup_data_mode
        from asset_lens.report.pdf_report import PDFReportGenerator

        setup_data_mode(data_mode)

        click.echo("\n📊 生成投资分析报告（PDF）")
        click.echo("=" * 60)

        try:
            products = load_products()
            click.echo(f"✅ 成功加载 {len(products)} 个投资产品")

            output_path = Path(output)
            report_gen = PDFReportGenerator(output_path.parent)
            portfolio_data = {"products": [{"name": p.name, "amount": float(p.current_amount or 0)} for p in products]}
            report_path = report_gen.generate_investment_report(portfolio_data, filename=output_path.name)

            click.echo(f"\n✅ 报告已生成: {report_path}")

        except Exception as e:
            click.echo(f"❌ 报告生成失败: {e}", err=True)

    @cli.command("generate-html-report")
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    @click.option("--output", type=str, default="output/report.html", help="输出文件")
    @click.option("--include-ai", is_flag=True, help="包含 AI 分析")
    def generate_html_report(data_mode: str | None, output: str, include_ai: bool):
        """生成投资分析报告（HTML）"""
        from pathlib import Path

        from asset_lens.cli.helpers import load_products, setup_data_mode
        from asset_lens.report.html_report import HTMLReportGenerator

        setup_data_mode(data_mode)

        click.echo("\n📊 生成投资分析报告（HTML）")
        click.echo("=" * 60)

        try:
            products = load_products()
            click.echo(f"✅ 成功加载 {len(products)} 个投资产品")

            output_path = Path(output)
            report_gen = HTMLReportGenerator(output_path.parent)
            portfolio_data = {"products": [{"name": p.name, "amount": float(p.current_amount or 0)} for p in products]}
            report_path = report_gen.generate_investment_report(portfolio_data, filename=output_path.name)

            click.echo(f"\n✅ 报告已生成: {report_path}")

        except Exception as e:
            click.echo(f"❌ 报告生成失败: {e}", err=True)

    @cli.command("ai-analyze")
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    def ai_analyze(data_mode: str | None):
        """使用 AI 分析投资组合"""
        from asset_lens.cli.helpers import load_products, setup_data_mode

        setup_data_mode(data_mode)

        click.echo("\n🤖 AI 投资组合分析")
        click.echo("=" * 60)

        try:
            products = load_products()
            click.echo(f"✅ 成功加载 {len(products)} 个投资产品")

            console = Console()

            total_amount = sum(float(p.current_amount or 0) for p in products)
            total_profit = sum(float(p.current_amount or 0) - float(p.initial_amount or 0) for p in products)
            avg_return = sum(float(p.return_rate or 0) for p in products) / len(products) if products else 0

            analysis = f"""
投资组合概览:
- 总产品数: {len(products)}
- 总金额: ¥{total_amount:,.2f}
- 总收益: ¥{total_profit:,.2f}
- 平均收益率: {avg_return:.2f}%

投资建议:
1. 分散投资: 建议保持不同类型资产的合理配置
2. 定期再平衡: 根据市场变化调整持仓比例
3. 关注风险: 注意高风险产品的仓位控制
"""

            console.print(Panel(analysis, title="AI 分析结果", border_style="blue"))

            click.echo("\n✅ AI 分析完成！")

        except Exception as e:
            click.echo(f"❌ AI 分析失败: {e}", err=True)
