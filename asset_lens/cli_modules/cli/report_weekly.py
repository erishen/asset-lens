"""
Weekly report CLI command.
周报生成命令
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import cast

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

logger = logging.getLogger(__name__)


def register_weekly_command(cli: click.Group) -> None:
    @cli.command("weekly")
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    @click.option("--output", type=str, default="output/weekly_report.md", help="输出文件")
    @click.option("--skip-ml", is_flag=True, help="跳过ML预测")
    @click.option("--skip-north-flow", is_flag=True, help="跳过北向资金分析")
    def weekly(data_mode: str | None, output: str, skip_ml: bool, skip_north_flow: bool):
        from asset_lens.cli_modules.cli.helpers import load_products, setup_data_mode
        from asset_lens.cli_modules.cli.report import _format_amount, _get_cny_amount, _get_profit_cny_amount
        from asset_lens.cli_modules.cli.report_helpers import (
            _check_risks,
            _evaluate_fund,
            _generate_suggestions,
            _get_ml_predictions,
            _get_north_flow,
            _get_platform_products,
        )

        setup_data_mode(data_mode)
        console = Console()

        console.print("\n" + "=" * 60)
        console.print(Panel("📊 周度投资报告", style="bold blue"))
        console.print("=" * 60)

        try:
            products = load_products()
            console.print(f"✅ 成功加载 {len(products)} 个投资产品")

            # 计算收益率（关键：必须调用，否则年化收益率会是原始值）
            from asset_lens.data.parsers.investment_calculator import InvestmentCalculator

            reference_date = datetime.now()
            for product in products:
                InvestmentCalculator.calculate_product_returns(product, reference_date)
            console.print("✅ 收益率计算完成")

            output_path = Path(output)
            report_lines = []

            report_lines.extend(
                [
                    "# 📊 周度投资报告",
                    "",
                    f"**报告日期**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    "",
                    "---",
                    "",
                ]
            )

            total_amount = sum(_get_cny_amount(p) for p in products)
            total_profit = sum(_get_profit_cny_amount(p) for p in products)
            profit_rate = (total_profit / total_amount * 100) if total_amount > 0 else 0

            console.print("\n[bold]📈 投资组合概览[/bold]")
            overview_table = Table(show_header=True, header_style="bold cyan")
            overview_table.add_column("指标", style="dim")
            overview_table.add_column("数值", justify="right")
            overview_table.add_row("总产品数", f"{len(products)}")
            overview_table.add_row("总资产", f"¥{total_amount:,.2f}")
            overview_table.add_row("总收益", f"¥{total_profit:,.2f}")
            overview_table.add_row("实际收益率", f"{profit_rate:+.2f}%")
            console.print(overview_table)

            report_lines.extend(
                [
                    "## 📈 投资组合概览",
                    "",
                    "| 指标 | 数值 |",
                    "|------|------|",
                    f"| 总产品数 | {len(products)} |",
                    f"| 总资产 | ¥{total_amount:,.2f} |",
                    f"| 总收益 | ¥{total_profit:,.2f} |",
                    f"| 实际收益率 | {profit_rate:+.2f}% |",
                    "",
                ]
            )

            sorted_by_return = sorted(
                [p for p in products if p.return_rate is not None],
                key=lambda p: float(p.return_rate or 0),
                reverse=True,
            )

            console.print("\n[bold]📊 本周表现[/bold]")
            gain_table = Table(title="🔴 涨幅前10", show_header=True, header_style="bold red")
            gain_table.add_column("产品名称", style="dim")
            gain_table.add_column("实际收益率", justify="right", style="red")
            gain_table.add_column("金额", justify="right")
            for p in sorted_by_return[:10]:
                gain_table.add_row(p.name[:20], f"{float(p.return_rate or 0):+.2f}%", _format_amount(p))
            console.print(gain_table)

            loss_products = [p for p in sorted_by_return if float(p.return_rate or 0) < 0]
            if loss_products:
                loss_table = Table(title="🟢 跌幅前10", show_header=True, header_style="bold green")
                loss_table.add_column("产品名称", style="dim")
                loss_table.add_column("实际收益率", justify="right", style="green")
                loss_table.add_column("金额", justify="right")
                for p in loss_products[:10]:
                    loss_table.add_row(p.name[:20], f"{float(p.return_rate or 0):.2f}%", _format_amount(p))
                console.print(loss_table)

            report_lines.extend(
                [
                    "",
                    "## 📊 本周表现",
                    "",
                    "### 🔴 涨幅前10",
                    "",
                    "| 产品名称 | 收益率 | 金额 |",
                    "|----------|--------|------|",
                ]
            )
            report_lines.extend(
                f"| {p.name} | {float(p.return_rate or 0):+.2f}% | {_format_amount(p)} |" for p in sorted_by_return[:10]
            )

            if loss_products:
                report_lines.extend(
                    [
                        "",
                        "### 🔴 跌幅前10",
                        "",
                        "| 产品名称 | 收益率 | 金额 |",
                        "|----------|--------|------|",
                    ]
                )
                report_lines.extend(
                    f"| {p.name} | {float(p.return_rate or 0):.2f}% | {_format_amount(p)} |" for p in loss_products[:10]
                )

            funds = [p for p in products if p.investment_type and "基金" in p.investment_type.value]
            large_funds = [f for f in funds if _get_cny_amount(f) >= 10000]

            if large_funds:
                console.print("\n[bold]💰 基金持仓分析（1万以上）[/bold]")
                report_lines.extend(
                    [
                        "",
                        "## 💰 基金持仓分析（1万以上）",
                        "",
                    ]
                )

                north_flow = _get_north_flow()
                north_trend = (
                    "bullish"
                    if north_flow.get("total_flow", 0) > 100
                    else ("bearish" if north_flow.get("total_flow", 0) < -100 else "neutral")
                )

                platform_funds = _get_platform_products(funds)

                for platform_name, platform_data in sorted(
                    platform_funds.items(), key=lambda x: x[1]["amount"], reverse=True
                ):
                    platform_fund_list = cast(list, platform_data["products"])
                    if not platform_fund_list:
                        continue

                    console.print(f"\n[cyan]📱 {platform_name}[/cyan] (¥{platform_data['amount']:,.0f})")

                    fund_table = Table(show_header=True, header_style="bold cyan")
                    fund_table.add_column("基金名称", style="dim")
                    fund_table.add_column("类型", width=8)
                    fund_table.add_column("金额", justify="right", width=12)
                    fund_table.add_column("年化收益率", justify="right", width=10)
                    fund_table.add_column("评分", justify="right", width=6)
                    fund_table.add_column("建议", width=12)
                    fund_evals = []
                    for f in platform_fund_list:
                        eval_result = _evaluate_fund(f, north_trend)
                        fund_evals.append((f, eval_result))

                    fund_evals.sort(key=lambda x: x[1]["score"], reverse=True)

                    for f, eval_result in fund_evals[:8]:
                        annual_return = float(f.annual_return or 0)
                        suggestion = f"{eval_result['emoji']} {eval_result['suggestion']}"
                        fund_table.add_row(
                            f.name,
                            eval_result["fund_type"],
                            _format_amount(f),
                            f"{annual_return:.1f}%",
                            str(eval_result["score"]),
                            suggestion,
                        )
                    console.print(fund_table)

                    report_lines.extend(
                        [
                            f"### 📱 {platform_name} (¥{platform_data['amount']:,.0f})",
                            "",
                            "| 基金名称 | 类型 | 持有金额 | 年化收益 | 评分 | 建议 | 理由 |",
                            "|----------|------|----------|----------|------|------|------|",
                        ]
                    )

                    for f, eval_result in fund_evals:
                        annual_return = float(f.annual_return or 0)
                        suggestion = f"{eval_result['emoji']} {eval_result['suggestion']}"
                        reasons_str = "; ".join(eval_result["reasons"][:2])
                        report_lines.append(
                            f"| {f.name} | {eval_result['fund_type']} | {_format_amount(f)} | {annual_return:.2f}% | {eval_result['score']} | {suggestion} | {reasons_str} |"
                        )

            if not skip_ml:
                console.print("\n[bold]🔮 ML预测分析[/bold]")
                try:
                    ml_results = _get_ml_predictions()
                    if ml_results:
                        bullish = ml_results.get("bullish", [])[:5]
                        bearish = ml_results.get("bearish", [])[:5]

                        if bullish:
                            ml_table = Table(show_header=True, header_style="bold cyan", title="🔴 看涨股票")
                            ml_table.add_column("代码", style="dim")
                            ml_table.add_column("名称", style="red")
                            ml_table.add_column("上涨概率", justify="right", style="red")
                            for r in bullish:
                                ml_table.add_row(r["code"], r["name"], f"{r['prob']:.1f}%")
                            console.print(ml_table)

                        if bearish:
                            ml_down_table = Table(show_header=True, header_style="bold cyan", title="🟢 看跌股票")
                            ml_down_table.add_column("代码", style="dim")
                            ml_down_table.add_column("名称", style="green")
                            ml_down_table.add_column("下跌概率", justify="right", style="green")
                            for r in bearish:
                                ml_down_table.add_row(r["code"], r["name"], f"{r['prob']:.1f}%")
                            console.print(ml_down_table)

                        report_lines.extend(
                            [
                                "",
                                "## 🔮 ML预测分析",
                                "",
                                "### 🔴 看涨股票（高置信度）",
                                "",
                                "| 代码 | 名称 | 上涨概率 | 预测 |",
                                "|------|------|----------|------|",
                            ]
                        )
                        report_lines.extend(
                            f"| {r['code']} | {r['name']} | {r['prob']:.1f}% | ↑ |"
                            for r in ml_results.get("bullish", [])[:10]
                        )

                        report_lines.extend(
                            [
                                "",
                                "### 🟢 看跌股票（高置信度）",
                                "",
                                "| 代码 | 名称 | 下跌概率 | 预测 |",
                                "|------|------|----------|------|",
                            ]
                        )
                        report_lines.extend(
                            f"| {r['code']} | {r['name']} | {r['prob']:.1f}% | ↓ |"
                            for r in ml_results.get("bearish", [])[:10]
                        )
                except Exception as e:
                    console.print(f"[yellow]⚠️ ML预测失败: {e}[/yellow]")

            if not skip_north_flow:
                console.print("\n[bold]📈 北向资金分析[/bold]")
                try:
                    north_flow = _get_north_flow()
                    if north_flow:
                        total_flow = north_flow.get("total_flow", 0)
                        trend_emoji = "🔴" if total_flow > 0 else "🟢"
                        console.print(f"本周净流入: {trend_emoji} {total_flow:+.2f} 亿")

                        nf_table = Table(show_header=True, header_style="bold cyan")
                        nf_table.add_column("日期", style="dim")
                        nf_table.add_column("净流入(亿)", justify="right")
                        nf_table.add_column("趋势", justify="center")
                        for flow in north_flow.get("flows", [])[:7]:
                            trend = "🔴" if flow["flow"] > 0 else "🟢"
                            nf_table.add_row(flow["date"], f"{flow['flow']:+.2f}", trend)
                        console.print(nf_table)

                        report_lines.extend(
                            [
                                "",
                                "## 📈 北向资金分析",
                                "",
                                f"**本周净流入**: {total_flow:+.2f} 亿",
                                "",
                                f"**整体趋势**: {'🔴 净流入' if total_flow > 0 else '🟢 净流出'}",
                                "",
                                "### 本周流向",
                                "",
                                "| 日期 | 净流入(亿) | 趋势 |",
                                "|------|------------|------|",
                            ]
                        )
                        for flow in north_flow.get("flows", [])[:7]:
                            trend = "🔴 流入" if flow["flow"] >= 0 else "🟢 流出"
                            report_lines.append(f"| {flow['date']} | {flow['flow']:+.2f} | {trend} |")
                except Exception as e:
                    console.print(f"[yellow]⚠️ 北向资金分析失败: {e}[/yellow]")

            risk_warnings = _check_risks(products)
            if risk_warnings:
                console.print("\n[bold red]⚠️ 风险预警[/bold red]")
                for warning in risk_warnings:
                    console.print(f"  {warning}")
                report_lines.extend(
                    [
                        "",
                        "## ⚠️ 风险预警",
                        "",
                    ]
                )
                report_lines.extend(f"- {warning}" for warning in risk_warnings)

            console.print("\n[bold green]💡 下周投资建议[/bold green]")
            suggestions = _generate_suggestions(products, funds)
            for suggestion in suggestions:
                console.print(f"  {suggestion}")
            report_lines.extend(
                [
                    "",
                    "## 💡 下周投资建议",
                    "",
                ]
            )
            report_lines.extend(f"- {suggestion}" for suggestion in suggestions)

            report_lines.extend(
                [
                    "",
                    "---",
                    "",
                    f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
                ]
            )

            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text("\n".join(report_lines), encoding="utf-8")

            console.print(f"\n✅ 周报已生成: [cyan]{output_path}[/cyan]")

        except Exception as e:
            console.print(f"[red]❌ 周报生成失败: {e}[/red]")
            raise
