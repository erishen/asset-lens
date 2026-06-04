"""
Monthly report CLI command.
月报生成命令
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

logger = logging.getLogger(__name__)


def register_monthly_command(cli: click.Group) -> None:
    @cli.command("monthly")
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    @click.option("--output", type=str, default="output/monthly_report.md", help="输出文件")
    @click.option("--skip-ml", is_flag=True, help="跳过ML预测")
    @click.option("--skip-north-flow", is_flag=True, help="跳过北向资金分析")
    def monthly(data_mode: str | None, output: str, skip_ml: bool, skip_north_flow: bool):
        from asset_lens.cli_modules.cli.helpers import load_products, setup_data_mode
        from asset_lens.cli_modules.cli.report import _format_amount, _get_cny_amount, _get_profit_cny_amount
        from asset_lens.cli_modules.cli.report_helpers import (  # type: ignore[attr-defined]
            _check_risks,
            _evaluate_fund_with_peers,
            _get_fund_type_threshold,
            _get_ml_predictions_monthly,
            _get_platform_products,
        )

        setup_data_mode(data_mode)
        console = Console()

        console.print("\n" + "=" * 60)
        console.print(Panel("📅 月度投资报告", style="bold green"))
        console.print("=" * 60)

        try:
            products = load_products()
            console.print(f"✅ 成功加载 {len(products)} 个投资产品")

            output_path = Path(output)
            report_lines = []

            current_month = datetime.now().strftime("%Y年%m月")

            report_lines.extend(
                [
                    "# 📅 月度投资报告",
                    "",
                    f"**报告月份**: {current_month}",
                    f"**报告日期**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    "",
                    "---",
                    "",
                ]
            )

            total_amount = sum(_get_cny_amount(p) for p in products)
            total_profit = sum(_get_profit_cny_amount(p) for p in products)
            profit_rate = (total_profit / total_amount * 100) if total_amount > 0 else 0

            console.print("\n[bold]📈 月度投资组合概览[/bold]")
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
                    "## 📈 月度投资组合概览",
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

            console.print("\n[bold]📊 本月表现[/bold]")
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
                    "## 📊 本月表现",
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

                platform_funds = _get_platform_products(large_funds)

                for platform_name, platform_data in sorted(
                    platform_funds.items(), key=lambda x: x[1]["amount"], reverse=True
                ):
                    platform_fund_list = cast(list, platform_data["products"])
                    if not platform_fund_list:
                        continue

                    console.print(f"\n[cyan]📱 {platform_name}[/cyan] (¥{platform_data['amount']:,.0f})")

                    fund_table = Table(show_header=True, header_style="bold cyan")
                    fund_table.add_column("基金名称", style="dim")
                    fund_table.add_column("类型", justify="center")
                    fund_table.add_column("金额", justify="right")
                    fund_table.add_column("年化收益率", justify="right")
                    fund_table.add_column("评分", justify="right")
                    fund_table.add_column("建议", justify="center")

                    fund_evaluations = []
                    for fund in platform_fund_list:
                        eval_result = _evaluate_fund_with_peers(fund, platform_fund_list, "neutral")
                        fund_evaluations.append((fund, eval_result))

                    fund_evaluations.sort(key=lambda x: x[1]["score"], reverse=True)

                    for fund, eval_result in fund_evaluations:
                        fund_type = _get_fund_type_threshold(fund).get("type", "其他")
                        annual_return = float(fund.annual_return or 0)
                        score = eval_result["score"]
                        suggestion = eval_result["suggestion"]
                        fund_table.add_row(
                            fund.name, fund_type, _format_amount(fund), f"{annual_return:.1f}%", str(score), suggestion
                        )
                    console.print(fund_table)

                    report_lines.extend(
                        [
                            f"### 📱 {platform_name} (¥{platform_data['amount']:,.0f})",
                            "",
                            "| 基金名称 | 类型 | 金额 | 年化 | 评分 | 建议 |",
                            "|----------|------|------|------|------|------|",
                        ]
                    )
                    for fund, eval_result in fund_evaluations:
                        fund_type = _get_fund_type_threshold(fund).get("type", "其他")
                        annual_return = float(fund.annual_return or 0)
                        score = eval_result["score"]
                        suggestion = eval_result["suggestion"]
                        report_lines.append(
                            f"| {fund.name} | {fund_type} | {_format_amount(fund)} | {annual_return:.1f}% | {score} | {suggestion} |"
                        )

            north_flow_trend = "neutral"
            if not skip_north_flow:
                console.print("\n[bold]🌊 北向资金分析[/bold]")
                try:
                    from asset_lens.data.fundamental_fetcher import MoneyFlowFetcher

                    fetcher = MoneyFlowFetcher()
                    df = fetcher.get_north_money_flow(days=30)
                    if df is not None and not df.empty:
                        total_inflow = df["north_net_inflow"].sum()
                        avg_inflow = total_inflow / len(df)

                        if total_inflow > 100:
                            north_flow_trend = "bullish"
                            trend_str = "🔴 强势流入"
                        elif total_inflow > 0:
                            north_flow_trend = "neutral"
                            trend_str = "🔴 小幅流入"
                        else:
                            north_flow_trend = "bearish"
                            trend_str = "🟢 净流出"

                        console.print(f"  本月净流入: {trend_str} {total_inflow:.2f} 亿")
                        console.print(f"  日均净流入: {avg_inflow:.2f} 亿")

                        nf_table = Table(show_header=True, header_style="bold cyan")
                        nf_table.add_column("日期", style="dim")
                        nf_table.add_column("净流入(亿)", justify="right")
                        nf_table.add_column("趋势", justify="center")

                        for _, row in df.iterrows():
                            date_val = str(row.get("date", row.get("日期", "")))[:10]
                            flow_val = float(row.get("north_net_inflow", 0))
                            trend = "🔴" if flow_val > 0 else "🟢"
                            nf_table.add_row(date_val, f"{flow_val:+.2f}", trend)

                        console.print(nf_table)

                        report_lines.extend(
                            [
                                "",
                                "## 🌊 北向资金分析",
                                "",
                                f"**本月净流入**: {trend_str} {total_inflow:.2f} 亿",
                                "",
                                f"**日均净流入**: {avg_inflow:.2f} 亿",
                                "",
                                "### 本月流向详情",
                                "",
                                "| 日期 | 净流入(亿) | 趋势 |",
                                "|------|------------|------|",
                            ]
                        )

                        for _, row in df.iterrows():
                            date_val = str(row.get("date", row.get("日期", "")))[:10]
                            flow_val = float(row.get("north_net_inflow", 0))
                            trend = "🔴 流入" if flow_val > 0 else "🟢 流出"
                            report_lines.append(f"| {date_val} | {flow_val:+.2f} | {trend} |")

                except Exception as e:
                    console.print(f"  ⚠️ 北向资金数据获取失败: {e}")

            if not skip_ml:
                console.print("\n[bold]🔮 ML预测分析（下月展望）[/bold]")
                try:
                    ml_results = _get_ml_predictions_monthly()
                    prediction_days = ml_results.get("prediction_days", 20)
                    if ml_results and (ml_results.get("bullish") or ml_results.get("bearish")):
                        bullish = ml_results.get("bullish", [])[:5]
                        bearish = ml_results.get("bearish", [])[:5]

                        console.print(f"  📊 预测时间范围: 未来 {prediction_days} 个交易日")

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
                                "## 🔮 ML预测分析（下月展望）",
                                "",
                                f"**预测时间范围**: 未来 {prediction_days} 个交易日",
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
                    else:
                        console.print("  ⚠️ 暂无有效预测结果")
                except Exception as e:
                    console.print(f"  ⚠️ ML预测失败: {e}")

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

            console.print("\n[bold green]💡 下月投资建议[/bold green]")
            suggestions = []

            platform_products = _get_platform_products(products)
            for platform_name, data in sorted(platform_products.items(), key=lambda x: x[1]["amount"], reverse=True):
                products_list = cast(list, data["products"])
                funds_in_platform: list[Any] = [
                    p for p in products_list if p.investment_type and "基金" in p.investment_type.value
                ]
                if not funds_in_platform:
                    continue

                strong_buy = []
                consider_buy = []
                hold = []
                reduce = []

                for fund in funds_in_platform:
                    eval_result = _evaluate_fund_with_peers(fund, funds_in_platform, north_flow_trend)
                    suggestion = eval_result["suggestion"]
                    reasons = eval_result["reasons"]

                    if "强烈加仓" in suggestion:
                        strong_buy.append({"fund": fund, "reasons": reasons})
                    elif "加仓" in suggestion:
                        consider_buy.append({"fund": fund, "reasons": reasons})
                    elif "持有" in suggestion:
                        hold.append({"fund": fund, "reasons": reasons})
                    elif "减仓" in suggestion or "赎回" in suggestion:
                        reduce.append({"fund": fund, "reasons": reasons})

                if strong_buy or consider_buy or hold or reduce:
                    suggestions.append(
                        f"\n📱 【{platform_name}】 (¥{data['amount']:,.0f}，{len(funds_in_platform)}只基金)"
                    )

                    if strong_buy:
                        suggestions.append(f"  🔴🔴 强烈加仓 ({len(strong_buy)}只):")
                        for item in strong_buy[:4]:
                            name = item["fund"].name[:12]
                            reasons = item["reasons"][0] if item["reasons"] else ""
                            suggestions.append(f"      • {name} ({_format_amount(item['fund'])}): {reasons}")

                    if consider_buy:
                        suggestions.append(f"  🔴 考虑加仓 ({len(consider_buy)}只):")
                        for item in consider_buy[:3]:
                            name = item["fund"].name[:12]
                            reasons = item["reasons"][0] if item["reasons"] else ""
                            suggestions.append(f"      • {name} ({_format_amount(item['fund'])}): {reasons}")

                    if hold:
                        suggestions.append(f"  🟡 继续持有 ({len(hold)}只):")
                        for item in hold[:2]:
                            name = item["fund"].name[:12]
                            suggestions.append(f"      • {name}")

                    if reduce:
                        suggestions.append(f"  🟢 考虑减仓 ({len(reduce)}只):")
                        for item in reduce[:2]:
                            name = item["fund"].name[:12]
                            reasons = item["reasons"][0] if item["reasons"] else ""
                            suggestions.append(f"      • {name}: {reasons}")

            for suggestion in suggestions:
                console.print(suggestion)

            report_lines.extend(
                [
                    "",
                    "## 💡 下月投资建议",
                    "",
                ]
            )
            report_lines.extend(suggestions)

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

            console.print(f"\n✅ 月报已生成: [cyan]{output_path}[/cyan]")

        except Exception as e:
            console.print(f"[red]❌ 月报生成失败: {e}[/red]")
            raise
