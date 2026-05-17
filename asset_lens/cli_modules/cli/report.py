"""
报告生成 CLI 命令
"""

from datetime import datetime
from pathlib import Path
from typing import Any, cast

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

_global_rates: dict[str, float | bool | None] = {"usd": None, "hkd": None, "loaded": False}


def _get_global_rates(data_dir: Path | None = None) -> tuple[float, float]:
    """获取全局汇率（从数据文件的资产汇总表格加载）"""
    if not _global_rates["loaded"]:
        from asset_lens.config import config
        from asset_lens.data.csv_parser import CSVParser

        if data_dir is None:
            data_dir = Path(config.real_data_path) if config.data_mode == "real" else Path(config.sample_data_path)

        try:
            usd_rate, hkd_rate = CSVParser.get_exchange_rates(data_dir)
            _global_rates["usd"] = usd_rate
            _global_rates["hkd"] = hkd_rate
        except Exception:
            _global_rates["usd"] = float(config.default_usd_rate)
            _global_rates["hkd"] = float(config.default_hkd_rate)

        _global_rates["loaded"] = True

    return _global_rates["usd"] or 7.2, _global_rates["hkd"] or 0.92


def _get_cny_amount(product) -> float:
    """获取产品的人民币金额（考虑汇率转换）"""
    amount = float(product.current_amount or 0)
    if amount == 0:
        return 0

    inv_type = product.investment_type.value if product.investment_type else ""
    global_usd, global_hkd = _get_global_rates()

    if inv_type in ["美股", "美元基金", "美元基金（美元）"]:
        usd_rate = float(product.usd_rate) if product.usd_rate else global_usd
        return amount * usd_rate
    elif inv_type in ["港股", "现金（港元）", "股息基金（港元）"]:
        hkd_rate = float(product.hkd_rate) if product.hkd_rate else global_hkd
        return amount * hkd_rate

    return amount


def _get_initial_cny_amount(product) -> float:
    """获取产品初始金额的人民币值（考虑汇率转换）"""
    amount = float(product.initial_amount or 0)
    if amount == 0:
        return 0

    inv_type = product.investment_type.value if product.investment_type else ""
    global_usd, global_hkd = _get_global_rates()

    if inv_type in ["美股", "美元基金", "美元基金（美元）"]:
        usd_rate = float(product.usd_rate) if product.usd_rate else global_usd
        return amount * usd_rate
    elif inv_type in ["港股", "现金（港元）", "股息基金（港元）"]:
        hkd_rate = float(product.hkd_rate) if product.hkd_rate else global_hkd
        return amount * hkd_rate

    return amount


def _get_profit_cny_amount(product) -> float:
    """获取产品收益的人民币值（考虑汇率转换）

    对于没有初始金额的产品（如货币基金），收益为0
    """
    initial = _get_initial_cny_amount(product)
    if initial == 0:
        return 0
    return _get_cny_amount(product) - initial


def _format_amount(product) -> str:
    """格式化金额显示（美元资产显示美元和人民币）"""
    amount = float(product.current_amount or 0)
    if amount == 0:
        return "¥0"

    inv_type = product.investment_type.value if product.investment_type else ""
    global_usd, global_hkd = _get_global_rates()

    if inv_type in ["美股", "美元基金", "美元基金（美元）"]:
        usd_rate = float(product.usd_rate) if product.usd_rate else global_usd
        cny_amount = amount * usd_rate
        return f"${amount:,.0f} (¥{cny_amount:,.0f})"
    elif inv_type in ["港股", "现金（港元）", "股息基金（港元）"]:
        hkd_rate = float(product.hkd_rate) if product.hkd_rate else global_hkd
        cny_amount = amount * hkd_rate
        return f"HK${amount:,.0f} (¥{cny_amount:,.0f})"

    return f"¥{amount:,.0f}"


def register_report_commands(cli: click.Group) -> None:
    """注册报告命令到 CLI 组"""

    @cli.command("weekly")
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    @click.option("--output", type=str, default="output/weekly_report.md", help="输出文件")
    @click.option("--skip-ml", is_flag=True, help="跳过ML预测")
    @click.option("--skip-north-flow", is_flag=True, help="跳过北向资金分析")
    def weekly(data_mode: str | None, output: str, skip_ml: bool, skip_north_flow: bool):
        """生成周度投资报告（增强版）"""
        from pathlib import Path

        from asset_lens.cli_modules.cli.helpers import load_products, setup_data_mode

        setup_data_mode(data_mode)
        console = Console()

        console.print("\n" + "=" * 60)
        console.print(Panel("📊 周度投资报告", style="bold blue"))
        console.print("=" * 60)

        try:
            products = load_products()
            console.print(f"✅ 成功加载 {len(products)} 个投资产品")

            output_path = Path(output)
            report_lines = []

            # 1. 报告头部
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

            # 2. 投资组合概览
            total_amount = sum(_get_cny_amount(p) for p in products)
            total_profit = sum(_get_profit_cny_amount(p) for p in products)
            profit_rate = (total_profit / total_amount * 100) if total_amount > 0 else 0

            # Console 输出概览
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

            # 3. 涨跌幅排行
            sorted_up = sorted(
                [p for p in products if p.return_rate and float(p.return_rate) > 0],
                key=lambda p: float(p.return_rate or 0),
                reverse=True,
            )[:5]

            sorted_down = sorted(
                [p for p in products if p.return_rate and float(p.return_rate) < 0],
                key=lambda p: float(p.return_rate or 0),
            )[:5]

            # Console 输出涨跌幅
            console.print("\n[bold]📊 本周表现[/bold]")
            perf_table = Table(show_header=True, header_style="bold cyan", title="🔴 涨幅前5")
            perf_table.add_column("产品名称", style="dim")
            perf_table.add_column("实际收益率", justify="right", style="red")
            perf_table.add_column("金额", justify="right")
            for p in sorted_up:
                perf_table.add_row(p.name[:20], f"+{float(p.return_rate or 0):.2f}%", _format_amount(p))
            console.print(perf_table)

            if sorted_down:
                down_table = Table(show_header=True, header_style="bold cyan", title="🟢 跌幅前5")
                down_table.add_column("产品名称", style="dim")
                down_table.add_column("实际收益率", justify="right", style="green")
                down_table.add_column("金额", justify="right")
                for p in sorted_down:
                    down_table.add_row(p.name[:20], f"{float(p.return_rate or 0):.2f}%", _format_amount(p))
                console.print(down_table)

            report_lines.extend(
                [
                    "## 📊 本周表现",
                    "",
                    "### 🔴 涨幅前10",
                    "",
                    "| 产品名称 | 收益率 | 金额 |",
                    "|----------|--------|------|",
                ]
            )

            report_lines.extend(
                f"| {p.name} | +{float(p.return_rate or 0):.2f}% | {_format_amount(p)} |"
                for p in sorted_up
            )

            report_lines.extend(
                [
                    "",
                    "### 🟢 跌幅前10",
                    "",
                    "| 产品名称 | 收益率 | 金额 |",
                    "|----------|--------|------|",
                ]
            )

            report_lines.extend(
                f"| {p.name} | {float(p.return_rate or 0):.2f}% | {_format_amount(p)} |"
                for p in sorted_down
            )

            # 4. 基金持仓分析（1万以上，按平台分组）
            console.print("\n[bold]💰 基金持仓分析（1万以上）[/bold]")
            report_lines.extend(
                [
                    "",
                    "## 💰 基金持仓分析（1万以上）",
                    "",
                ]
            )

            fund_types = ["指数基金", "债券基金", "混合基金", "QDII", "ETF", "定投基金", "基金"]
            funds = [
                p
                for p in products
                if p.investment_type
                and p.investment_type.value in fund_types
                and p.current_amount
                and _get_cny_amount(p) >= 10000
            ]

            north_flow = _get_north_flow()
            north_trend = (
                "bullish"
                if north_flow.get("total_flow", 0) > 100
                else ("bearish" if north_flow.get("total_flow", 0) < -100 else "neutral")
            )

            # 按平台分组
            platform_funds = _get_platform_products(funds)

            for platform_name, platform_data in sorted(platform_funds.items(), key=lambda x: x[1]["amount"], reverse=True):
                platform_fund_list = cast(list, platform_data["products"])
                if not platform_fund_list:
                    continue

                console.print(f"\n[cyan]📱 {platform_name}[/cyan] (¥{platform_data['amount']:,.0f})")

                fund_evals = []
                for f in platform_fund_list:
                    eval_result = _evaluate_fund(f, north_trend)
                    fund_evals.append((f, eval_result))

                fund_evals.sort(key=lambda x: x[1]["score"], reverse=True)

                # Console 输出基金分析
                fund_table = Table(show_header=True, header_style="bold cyan")
                fund_table.add_column("基金名称", style="dim")
                fund_table.add_column("类型", width=8)
                fund_table.add_column("金额", justify="right", width=12)
                fund_table.add_column("年化收益率", justify="right", width=10)
                fund_table.add_column("评分", justify="right", width=6)
                fund_table.add_column("建议", width=12)
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

            # 5. ML预测分析
            if not skip_ml:
                console.print("\n[bold]🔮 ML预测分析[/bold]")
                try:
                    ml_results = _get_ml_predictions()
                    if ml_results:
                        bullish = ml_results.get("bullish", [])[:5]
                        bearish = ml_results.get("bearish", [])[:5]

                        # Console 输出ML预测
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

            # 6. 北向资金分析
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

            # 7. 风险预警
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

            # 8. 投资建议
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

            # 9. 总结
            report_lines.extend(
                [
                    "",
                    "---",
                    "",
                    f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
                ]
            )

            # 写入文件
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text("\n".join(report_lines), encoding="utf-8")

            console.print(f"\n✅ 周报已生成: [cyan]{output_path}[/cyan]")

        except Exception as e:
            console.print(f"[red]❌ 周报生成失败: {e}[/red]")
            raise

    @cli.command("monthly")
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    @click.option("--output", type=str, default="output/monthly_report.md", help="输出文件")
    @click.option("--skip-ml", is_flag=True, help="跳过ML预测")
    @click.option("--skip-north-flow", is_flag=True, help="跳过北向资金分析")
    def monthly(data_mode: str | None, output: str, skip_ml: bool, skip_north_flow: bool):
        """生成月度投资报告"""
        from pathlib import Path

        from asset_lens.cli_modules.cli.helpers import load_products, setup_data_mode

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
                f"| {p.name} | {float(p.return_rate or 0):+.2f}% | {_format_amount(p)} |"
                for p in sorted_by_return[:10]
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
                    f"| {p.name} | {float(p.return_rate or 0):.2f}% | {_format_amount(p)} |"
                    for p in loss_products[:10]
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

                # 按平台分组
                platform_funds = _get_platform_products(large_funds)

                for platform_name, platform_data in sorted(platform_funds.items(), key=lambda x: x[1]["amount"], reverse=True):
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

                        # 显示本月流向表格
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
                funds_in_platform: list[Any] = [p for p in products_list if p.investment_type and "基金" in p.investment_type.value]
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
                        f"\n📱 【{platform_name}】 (¥{data['amount']:,.0f}，{len(platform_funds)}只基金)"
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

    @cli.command("daily-report")
    def daily_report():
        """生成日度报告（快速摘要）"""
        from datetime import datetime

        from rich.console import Console
        from rich.panel import Panel

        from asset_lens.cli_modules.cli.helpers import load_products

        console = Console()
        console.print("\n📝 日度报告")
        console.print("=" * 60)

        try:
            console.print(f"\n📅 日期: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

            console.print("\n💰 投资组合概览:")
            try:
                products = load_products()

                if products:
                    total_amount = sum(_get_cny_amount(p) for p in products)
                    total_profit = sum(_get_profit_cny_amount(p) for p in products)
                    profit_rate = (total_profit / total_amount * 100) if total_amount > 0 else 0

                    summary = f"""
总资产: ¥{total_amount:,.2f}
总收益: ¥{total_profit:,.2f}
收益率: {profit_rate:+.2f}%
产品数: {len(products)}
"""
                    console.print(Panel(summary, title="投资组合", border_style="blue"))
                else:
                    console.print("[yellow]⚠️ 无投资组合数据[/yellow]")
            except Exception:
                console.print("[yellow]⚠️ 无法加载投资组合[/yellow]")

            console.print("\n✅ 日度报告生成完成！")

        except Exception as e:
            console.print(f"[red]❌ 报告生成失败: {e}[/red]")


def _train_model_if_needed(model_path, prediction_days: int, max_age_days: int = 7) -> bool:
    """如果模型不存在或过期则自动训练

    Args:
        model_path: 模型文件路径
        prediction_days: 预测天数
        max_age_days: 模型最大有效期（天），默认7天
    """
    from datetime import datetime, timedelta
    from pathlib import Path

    model_path = Path(model_path)

    if model_path.exists():
        file_mtime = datetime.fromtimestamp(model_path.stat().st_mtime)
        age = datetime.now() - file_mtime

        if age > timedelta(days=max_age_days):
            print(f"⚠️ 模型已过期 (训练于 {age.days} 天前)，正在重新训练...")
        else:
            print(f"✅ 模型有效 (训练于 {age.days} 天前)")
            return True
    else:
        print(f"⚠️ 模型不存在，正在自动训练 (prediction_days={prediction_days})...")

    try:
        import numpy as np
        import pandas as pd

        from asset_lens.data.market_stock_fetcher import MarketStockFetcher
        from asset_lens.ml.trainer import ModelTrainer, TrainingConfig

        fetcher = MarketStockFetcher()
        stocks_data = fetcher.get_cached_market_stocks()

        if not stocks_data:
            print("⚠️ 无缓存数据，正在自动获取市场股票数据...")
            try:
                stocks_data = fetcher.fetch_all_cn_stocks(max_pages=3)
                if stocks_data:
                    fetcher.save_market_stocks(stocks_data)
                    print(f"✅ 已获取 {len(stocks_data)} 只股票数据")
                else:
                    print("❌ 获取市场数据失败")
                    return False
            except Exception as fetch_error:
                print(f"❌ 获取市场数据失败: {fetch_error}")
                return False

        print(f"✅ 加载 {len(stocks_data)} 只股票数据")

        # 根据预测天数动态调整阈值
        # 短期(5天): 2%, 中期(20天): 5%, 长期(60天): 10%
        threshold_pct = max(0.02, prediction_days * 0.0025)

        config = TrainingConfig(
            prediction_days=prediction_days,
            positive_threshold=threshold_pct,
            negative_threshold=-threshold_pct,
        )
        trainer = ModelTrainer(model_type="lightgbm", config=config)

        from asset_lens.data.stock_history_fetcher import StockHistoryFetcher

        history_fetcher = StockHistoryFetcher()

        stocks_price_data = {}
        success_count = 0

        for stock in stocks_data[:100]:
            code = stock.get("code", "")
            if not code:
                continue

            try:
                history = history_fetcher.fetch_history(code, days=120)
                if history and history.get("klines"):
                    df = pd.DataFrame(history["klines"])
                    if len(df) >= 60:
                        df["open"] = pd.to_numeric(df["open"], errors="coerce")
                        df["high"] = pd.to_numeric(df["high"], errors="coerce")
                        df["low"] = pd.to_numeric(df["low"], errors="coerce")
                        df["close"] = pd.to_numeric(df["close"], errors="coerce")
                        df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
                        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
                        df = df.dropna()

                        if len(df) >= 60:
                            stocks_price_data[code] = df
                            success_count += 1
            except Exception:
                continue

        if success_count < 10:
            print(f"⚠️ 真实数据不足({success_count}只)，使用模拟数据补充...")
            np.random.seed(42)
            for stock in stocks_data[:200]:
                code = stock.get("code", "")
                current_price = stock.get("current_price", 10)

                if code in stocks_price_data or not code or current_price <= 0:
                    continue

                n_days = 100
                returns = np.random.randn(n_days) * 0.02
                prices = current_price * np.exp(np.cumsum(returns))

                df = pd.DataFrame(
                    {
                        "open": prices * (1 + np.random.randn(n_days) * 0.01),
                        "high": prices * (1 + np.abs(np.random.randn(n_days) * 0.02)),
                        "low": prices * (1 - np.abs(np.random.randn(n_days) * 0.02)),
                        "close": prices,
                        "volume": np.random.randint(100000, 1000000, n_days),
                        "amount": prices * np.random.randint(100000, 1000000, n_days),
                    }
                )

                stocks_price_data[code] = df

        print(f"✅ 使用 {len(stocks_price_data)} 只股票数据训练")

        X, y = trainer.prepare_multi_stock_data(stocks_price_data)
        trainer.train(X, y)
        trainer.save_model(model_path)

        print(f"✅ 模型训练完成: {model_path}")
        return True
    except Exception as e:
        print(f"❌ 自动训练失败: {e}")
        return False


def _get_ml_predictions() -> dict:
    """获取ML预测结果（短期5天）"""
    return _get_ml_predictions_for_model(
        model_path="cache/ml/model.pkl", prediction_days=5, label="短期", bullish_threshold=0.7, bearish_threshold=0.3
    )


def _get_ml_predictions_monthly() -> dict:
    """获取ML预测结果（中期20天，约一个月）"""
    return _get_ml_predictions_for_model(
        model_path="cache/ml/model_monthly.pkl",
        prediction_days=20,
        label="中期",
        bullish_threshold=0.6,
        bearish_threshold=0.4,
    )


def _get_ml_predictions_for_model(
    model_path: str, prediction_days: int, label: str, bullish_threshold: float = 0.7, bearish_threshold: float = 0.3
) -> dict:
    """获取ML预测结果（通用函数）"""
    from pathlib import Path

    from asset_lens.data.stock_history_fetcher import StockHistoryFetcher
    from asset_lens.ml.predictor import StockPredictor
    from asset_lens.trading.stock_pool import StockPool

    model_path_obj = Path(model_path)

    if not model_path_obj.exists() and not _train_model_if_needed(model_path_obj, prediction_days=prediction_days):
        return {"bullish": [], "bearish": [], "prediction_days": prediction_days, "label": label}

    try:
        predictor = StockPredictor(model_path=model_path_obj)
    except Exception as exc:
        print(f"ML模型加载失败: {exc}")
        return {"bullish": [], "bearish": [], "prediction_days": prediction_days, "label": label}

    pool = StockPool()
    stocks = pool.list_stocks()[:20]
    fetcher = StockHistoryFetcher()

    bullish = []
    bearish = []

    for stock_info in stocks:
        try:
            code = stock_info.get("code", "") if isinstance(stock_info, dict) else stock_info
            name = stock_info.get("name", code) if isinstance(stock_info, dict) else code

            history = fetcher.fetch_history(code, days=120)
            history_data = None
            if history and history.get("klines"):
                history_data = []
                for kline in history["klines"]:
                    history_data.append(
                        {
                            "open": float(kline.get("open", 0)),
                            "high": float(kline.get("high", 0)),
                            "low": float(kline.get("low", 0)),
                            "close": float(kline.get("close", 0)),
                            "volume": float(kline.get("volume", 0)),
                            "amount": float(kline.get("amount", 0)),
                            "amplitude": float(kline.get("amplitude", 0)),
                            "change_amount": float(kline.get("change_amount", 0)),
                            "change_percent": float(kline.get("change_percent", 0)),
                            "turnover_rate": float(kline.get("turnover_rate", 0)),
                        }
                    )

            result = predictor.predict_single(code=code, name=name, history_data=history_data)
            if result:
                prob = result.up_prob
                if prob >= bullish_threshold:
                    bullish.append({"code": code, "name": name, "prob": prob * 100})
                elif prob <= bearish_threshold:
                    bearish.append({"code": code, "name": name, "prob": (1 - prob) * 100})
        except Exception:
            continue

    bullish.sort(key=lambda x: x["prob"], reverse=True)
    bearish.sort(key=lambda x: x["prob"], reverse=True)

    return {"bullish": bullish, "bearish": bearish, "prediction_days": prediction_days, "label": label}


def _get_north_flow() -> dict:
    """获取北向资金数据"""
    from asset_lens.data.fundamental_fetcher import MoneyFlowFetcher

    fetcher = MoneyFlowFetcher()
    df = fetcher.get_north_money_flow(days=7)

    if df is None or df.empty:
        return {"total_flow": 0, "flows": []}

    flows: list[dict[str, float | str]] = []
    for _, row in df.iterrows():
        date_val = row.get("date", row.get("日期", ""))
        flow_val = row.get("north_net_inflow", row.get("净流入", row.get("north_inflow", 0)))
        flows.append({"date": str(date_val)[:10], "flow": float(flow_val) if flow_val else 0})

    total_flow = sum(f["flow"] for f in flows if isinstance(f["flow"], (int, float)))
    return {"total_flow": total_flow, "flows": flows}


def _check_risks(products: list) -> list:
    """检查风险"""
    warnings = []

    # 检查亏损产品
    loss_products = [p for p in products if p.return_rate and float(p.return_rate) < -10]
    if loss_products:
        warnings.append(f"🔴 {len(loss_products)} 只产品亏损超过10%，建议检查止损")

    # 检查高风险产品集中度
    high_risk_amount = sum(
        _get_cny_amount(p) for p in products if p.risk_level and p.risk_level.value in ["高", "中高"]
    )
    total_amount = sum(_get_cny_amount(p) for p in products)
    if total_amount > 0 and high_risk_amount / total_amount > 0.5:
        warnings.append(f"⚠️ 高风险产品占比 {high_risk_amount / total_amount * 100:.1f}%，建议分散风险")

    # 检查单一产品集中度
    for p in products:
        cny_amount = _get_cny_amount(p)
        if cny_amount > 0 and total_amount > 0 and cny_amount / total_amount > 0.2:
            warnings.append(f"⚠️ {p.name} 占比 {cny_amount / total_amount * 100:.1f}%，集中度较高")

    return warnings


def _get_fund_type_threshold(fund) -> dict:
    """根据基金类型返回不同的判断阈值"""
    inv_type = fund.investment_type.value if fund.investment_type else ""
    name = fund.name.lower() if fund.name else ""

    if "债券" in inv_type or "债" in name:
        return {"excellent": 6, "good": 4, "normal": 2, "type": "债券型"}
    elif "货币" in inv_type or "货币" in name or "钱宝" in name or "朝朝宝" in name:
        return {"excellent": 3, "good": 2, "normal": 1.5, "type": "货币型"}
    elif "qdii" in inv_type.lower() or "qdii" in name or "纳斯达克" in name or "标普" in name:
        return {"excellent": 15, "good": 10, "normal": 5, "type": "QDII"}
    elif "黄金" in name or "gold" in name:
        return {"excellent": 12, "good": 8, "normal": 4, "type": "黄金"}
    elif "指数" in inv_type or "沪深300" in name or "中证500" in name or "增强" in name:
        return {"excellent": 12, "good": 8, "normal": 4, "type": "指数型"}
    elif "混合" in inv_type or "混合" in name:
        return {"excellent": 15, "good": 10, "normal": 5, "type": "混合型"}
    elif "股票" in inv_type or "股票" in name:
        return {"excellent": 18, "good": 12, "normal": 6, "type": "股票型"}
    else:
        return {"excellent": 15, "good": 10, "normal": 5, "type": "其他"}


def _evaluate_fund(fund, north_flow_trend: str = "neutral") -> dict:
    """综合评估基金"""
    annual_return = float(fund.annual_return or 0)
    threshold = _get_fund_type_threshold(fund)

    score = 0
    reasons = []

    if annual_return >= threshold["excellent"]:
        score += 40
        reasons.append(f"年化{annual_return:.1f}%超{threshold['type']}优秀线{threshold['excellent']}%")
    elif annual_return >= threshold["good"]:
        score += 25
        reasons.append(f"年化{annual_return:.1f}%达{threshold['type']}良好线{threshold['good']}%")
    elif annual_return >= threshold["normal"]:
        score += 10
        reasons.append(f"年化{annual_return:.1f}%达{threshold['type']}正常线{threshold['normal']}%")
    elif annual_return > 0:
        score += 5
        reasons.append(f"年化{annual_return:.1f}%偏低")
    else:
        score -= 20
        reasons.append(f"年化{annual_return:.1f}%亏损")

    amount = _get_cny_amount(fund)
    if amount < 10000:
        score += 5
        reasons.append("小仓位可加仓")
    elif amount < 30000:
        score += 0
    else:
        score -= 5
        reasons.append("仓位较重")

    if north_flow_trend == "bullish":
        if threshold["type"] in ["股票型", "混合型", "指数型"]:
            score += 10
            reasons.append("北向资金流入利好")
    elif north_flow_trend == "bearish" and threshold["type"] in ["股票型", "混合型", "指数型"]:
        score -= 10
        reasons.append("北向资金流出不利")

    return_rate = float(fund.return_rate or 0)
    if return_rate < -10:
        score -= 20
        reasons.append(f"累计亏损{abs(return_rate):.1f}%")
    elif return_rate < -5:
        score -= 10
        reasons.append(f"累计亏损{abs(return_rate):.1f}%")

    if score >= 50:
        suggestion = "强烈加仓"
        emoji = "🔴🔴"
    elif score >= 30:
        suggestion = "考虑加仓"
        emoji = "🔴"
    elif score >= 10:
        suggestion = "继续持有"
        emoji = "🟡"
    elif score >= 0:
        suggestion = "观察"
        emoji = "🟡"
    elif score >= -20:
        suggestion = "考虑减仓"
        emoji = "🟢"
    else:
        suggestion = "建议赎回"
        emoji = "🟢🟢"

    return {
        "score": score,
        "suggestion": suggestion,
        "emoji": emoji,
        "reasons": reasons,
        "fund_type": threshold["type"],
    }


def _get_fund_category(fund) -> str:
    """获取基金类别（用于同类比较）"""
    name = fund.name.lower() if fund.name else ""

    if "沪深300" in name or "300etf" in name:
        return "沪深300"
    elif "中证500" in name or "500etf" in name:
        return "中证500"
    elif "中证1000" in name or "1000etf" in name:
        return "中证1000"
    elif "创业板" in name:
        return "创业板"
    elif "科创50" in name or "科创板" in name:
        return "科创50"
    elif "纳斯达克" in name or "纳指" in name:
        return "纳斯达克"
    elif "标普" in name:
        return "标普500"
    elif "黄金" in name or "gold" in name:
        return "黄金"
    elif "港股" in name or "恒生" in name:
        return "港股"
    elif "债券" in name or "债" in name:
        return "债券"
    elif "军工" in name:
        return "军工"
    elif "医药" in name:
        return "医药"
    elif "消费" in name:
        return "消费"
    elif "新能源" in name:
        return "新能源"
    elif "芯片" in name or "半导体" in name:
        return "芯片"
    elif "油气" in name or "能源" in name:
        return "油气"
    else:
        return "其他"


def _evaluate_fund_with_peers(fund, peer_funds: list, north_flow_trend: str = "neutral") -> dict:
    """综合评估基金（含同类比较）"""
    annual_return = float(fund.annual_return or 0)
    threshold = _get_fund_type_threshold(fund)
    inv_type = fund.investment_type.value if fund.investment_type else ""

    score = 0
    reasons = []

    # 特殊处理：美元基金/货币基金
    is_usd_fund = "美元" in inv_type
    is_money_fund = "货币" in fund.name or "货币" in inv_type or "Money" in fund.name

    if is_money_fund and annual_return == 0:
        annual_return = 3.5
        reasons.append("货币基金约3.5%年化")

    # 1. 年化收益绝对值评分（权重降低）
    if annual_return >= threshold["excellent"]:
        score += 30
        if not is_money_fund:
            reasons.append(f"年化{annual_return:.1f}%优秀")
    elif annual_return >= threshold["good"]:
        score += 20
        if not is_money_fund:
            reasons.append(f"年化{annual_return:.1f}%良好")
    elif annual_return >= threshold["normal"]:
        score += 10
        if not is_money_fund:
            reasons.append(f"年化{annual_return:.1f}%正常")
    elif annual_return > 0:
        score += 5
    elif annual_return < 0:
        score -= 10
        reasons.append(f"年化{annual_return:.1f}%亏损")

    # 2. 同类基金相对排名（新增）
    if peer_funds and len(peer_funds) > 1:
        peer_returns = [float(f.annual_return or 0) for f in peer_funds]
        peer_returns.sort(reverse=True)
        rank = peer_returns.index(annual_return) + 1 if annual_return in peer_returns else len(peer_returns)
        percentile = (1 - (rank - 1) / len(peer_returns)) * 100

        if percentile >= 80:
            score += 20
            reasons.append(f"同类排名前{100 - percentile + 1:.0f}%")
        elif percentile >= 50:
            score += 10
        elif percentile < 30:
            score -= 10
            reasons.append(f"同类排名后{percentile:.0f}%")

    # 3. 持仓金额
    amount = _get_cny_amount(fund)
    if amount < 10000:
        score += 5
    elif amount > 50000:
        score -= 5
        reasons.append("仓位较重")

    # 4. 北向资金趋势
    if north_flow_trend == "bullish":
        if threshold["type"] in ["股票型", "混合型", "指数型"]:
            score += 10
            reasons.append("北向资金流入利好")
    elif north_flow_trend == "bearish" and threshold["type"] in ["股票型", "混合型", "指数型"]:
        score -= 10
        reasons.append("北向资金流出不利")

    # 5. 累计收益
    return_rate = float(fund.return_rate or 0)
    if return_rate < -10:
        score -= 15
        reasons.append(f"累计亏损{abs(return_rate):.1f}%")
    elif return_rate < -5:
        score -= 8
        reasons.append(f"累计亏损{abs(return_rate):.1f}%")

    # 6. 美元基金特殊标记
    if is_usd_fund:
        reasons.append("美元资产")

    # 7. 评级
    if score >= 45:
        suggestion = "强烈加仓"
        emoji = "🔴🔴"
    elif score >= 25:
        suggestion = "考虑加仓"
        emoji = "🔴"
    elif score >= 10:
        suggestion = "继续持有"
        emoji = "🟡"
    elif score >= 0:
        suggestion = "观察"
        emoji = "🟡"
    elif score >= -15:
        suggestion = "考虑减仓"
        emoji = "🟢"
    else:
        suggestion = "建议赎回"
        emoji = "🟢🟢"

    return {
        "score": score,
        "suggestion": suggestion,
        "emoji": emoji,
        "reasons": reasons,
        "fund_type": threshold["type"],
        "category": _get_fund_category(fund),
    }


def _get_platform_products(products: list) -> dict[str, dict[str, list | float | str]]:
    """按平台分组产品"""
    from asset_lens.config import config
    from asset_lens.core.platform_loader import PlatformLoader

    PlatformLoader.load(data_mode=config.data_mode)
    platforms = PlatformLoader.get_all_platforms(data_mode=config.data_mode)

    platform_products: dict[str, dict[str, Any]] = {}
    for platform in platforms:
        platform_products[platform.name] = {
            "products": [],
            "amount": 0.0,
            "type": platform.type,
        }

    platform_products["其他"] = {
        "products": [],
        "amount": 0.0,
        "type": "other",
    }

    for p in products:
        if p.platform_amounts:
            for platform_id, amount in p.platform_amounts.items():
                platform_info = PlatformLoader.get_platform(platform_id)
                if platform_info:
                    platform_name = platform_info.name
                    if platform_name not in platform_products:
                        platform_products[platform_name] = {
                            "products": [],
                            "amount": 0.0,
                            "type": platform_info.type,
                        }
                    platform_products[platform_name]["products"].append(p)
                    # 汇率转换
                    inv_type = p.investment_type.value if p.investment_type else ""
                    global_usd, global_hkd = _get_global_rates()
                    if inv_type in ["美股", "美元基金（美元）"]:
                        usd_rate = float(p.usd_rate) if p.usd_rate else global_usd
                        cny_amount = float(amount) * usd_rate
                    elif inv_type in ["港股", "现金（港元）", "股息基金（港元）"]:
                        hkd_rate = float(p.hkd_rate) if p.hkd_rate else global_hkd
                        cny_amount = float(amount) * hkd_rate
                    else:
                        cny_amount = float(amount)
                    platform_products[platform_name]["amount"] = (
                        float(platform_products[platform_name]["amount"]) + cny_amount
                    )
        else:
            platform_products["其他"]["products"].append(p)
            platform_products["其他"]["amount"] = float(platform_products["其他"]["amount"]) + _get_cny_amount(p)

    return {k: v for k, v in platform_products.items() if float(v["amount"]) > 0}


def _generate_suggestions(products: list, funds: list) -> list:
    """生成投资建议（增强版，按平台分组，含同类比较）"""
    suggestions: list[str] = []

    north_flow = _get_north_flow()
    north_trend = (
        "bullish"
        if north_flow.get("total_flow", 0) > 100
        else ("bearish" if north_flow.get("total_flow", 0) < -100 else "neutral")
    )

    platform_products = _get_platform_products(products)

    # 先按类别分组所有基金（跨平台同类比较）
    all_funds = [
        p
        for p in products
        if p.investment_type and p.investment_type.value in ["基金", "定投基金", "ETF", "QDII"]
    ]

    category_funds_global: dict[str, list] = {}
    for f in all_funds:
        category = _get_fund_category(f)
        if category not in category_funds_global:
            category_funds_global[category] = []
        category_funds_global[category].append(f)

    for platform_name, platform_data in sorted(platform_products.items(), key=lambda x: x[1]["amount"], reverse=True):
        products_list = cast(list, platform_data["products"])
        platform_funds = [
            p
            for p in products_list
            if p.investment_type and p.investment_type.value in ["基金", "定投基金", "ETF", "QDII"]
        ]

        if not platform_funds:
            platform_funds = [p for p in products_list if p.investment_type and "基金" in p.investment_type.value]

        if not platform_funds:
            continue

        fund_evaluations = []
        for f in platform_funds:
            category = _get_fund_category(f)
            peers = category_funds_global.get(category, [])
            eval_result = _evaluate_fund_with_peers(f, peers, north_trend)
            eval_result["fund"] = f
            eval_result["category"] = category
            fund_evaluations.append(eval_result)

        fund_evaluations.sort(key=lambda x: x["score"], reverse=True)

        strong_buy = [e for e in fund_evaluations if e["score"] >= 50]
        consider_buy = [e for e in fund_evaluations if 30 <= e["score"] < 50]
        hold_funds = [e for e in fund_evaluations if 10 <= e["score"] < 30]
        watch_funds = [e for e in fund_evaluations if 0 <= e["score"] < 10]
        reduce_funds = [e for e in fund_evaluations if -20 <= e["score"] < 0]
        sell_funds = [e for e in fund_evaluations if e["score"] < -20]

        suggestions.append(f"\n📱 【{platform_name}】 (¥{platform_data['amount']:,.0f}，{len(platform_funds)}只基金)")

        if strong_buy:
            suggestions.append(f"  🔴🔴 强烈加仓 ({len(strong_buy)}只):")
            for e in strong_buy[:4]:
                name = e["fund"].name[:12]
                reasons = e["reasons"][0] if e["reasons"] else ""
                suggestions.append(f"      • {name} (¥{e['fund'].current_amount:,.0f}): {reasons}")
        if consider_buy:
            suggestions.append(f"  🔴 考虑加仓 ({len(consider_buy)}只):")
            for e in consider_buy[:3]:
                name = e["fund"].name[:12]
                reasons = e["reasons"][0] if e["reasons"] else ""
                suggestions.append(f"      • {name} ({_format_amount(e['fund'])}): {reasons}")

        if hold_funds:
            suggestions.append(f"  🟡 继续持有 ({len(hold_funds)}只):")
            for e in hold_funds[:3]:
                name = e["fund"].name[:12]
                suggestions.append(f"      • {name} ({_format_amount(e['fund'])})")

        if watch_funds:
            suggestions.append(f"  ⚪ 需要观察 ({len(watch_funds)}只):")
            for e in watch_funds[:2]:
                name = e["fund"].name[:12]
                suggestions.append(f"      • {name}")

        if reduce_funds:
            suggestions.append(f"  🟢 考虑减仓 ({len(reduce_funds)}只):")
            for e in reduce_funds[:2]:
                name = e["fund"].name[:12]
                reasons = e["reasons"][0] if e["reasons"] else ""
                suggestions.append(f"      • {name}: {reasons}")

        if sell_funds:
            suggestions.append(f"  🟢🟢 建议赎回 ({len(sell_funds)}只):")
            for e in sell_funds[:2]:
                name = e["fund"].name[:12]
                reasons = e["reasons"][0] if e["reasons"] else ""
                suggestions.append(f"      • {name}: {reasons}")

        if not any([strong_buy, consider_buy, hold_funds, watch_funds, reduce_funds, sell_funds]):
            suggestions.append("  ⚪ 暂无建议")

    loss_products = [p for p in products if p.return_rate and float(p.return_rate) < 0]
    if loss_products:
        suggestions.append(f"\n📉 {len(loss_products)} 只产品亏损，建议检查止损位")

    if north_trend == "bullish":
        suggestions.append(f"\n📈 北向资金净流入+{north_flow['total_flow']:.0f}亿，利好权益类资产")
    elif north_trend == "bearish":
        suggestions.append(f"\n📉 北向资金净流出{north_flow['total_flow']:.0f}亿，注意风险")

    suggestions.append("\n📊 各平台资金独立管理，建议保持股债平衡配置")

    return suggestions


def _generate_monthly_suggestions(products: list, type_stats: dict, total_amount: float) -> list:
    """生成月度投资建议"""
    suggestions = []

    suggestions.append(f"📅 本月投资组合共 {len(products)} 只产品，总资产 ¥{total_amount:,.0f}")

    sorted_types = sorted(type_stats.items(), key=lambda x: x[1]["amount"], reverse=True)
    if sorted_types:
        top_type, top_stats = sorted_types[0]
        top_pct = top_stats["amount"] / total_amount * 100 if total_amount > 0 else 0
        suggestions.append(f"📊 资产配置: {top_type} 占比最高 ({top_pct:.1f}%)")

    loss_products = [p for p in products if p.return_rate and float(p.return_rate) < -5]
    if loss_products:
        suggestions.append(f"⚠️ {len(loss_products)} 只产品亏损超过5%，建议检查止损策略")

    high_return = [p for p in products if p.annual_return and float(p.annual_return) > 10]
    if high_return:
        suggestions.append(f"🏆 {len(high_return)} 只产品年化收益超过10%，表现优异")

    bond_amount = sum(stats["amount"] for t, stats in type_stats.items() if "债" in t)
    bond_pct = bond_amount / total_amount * 100 if total_amount > 0 else 0
    if bond_pct < 20:
        suggestions.append(f"💡 债券类资产占比 {bond_pct:.1f}%，建议适当增加以降低波动")

    suggestions.append("📋 建议: 每月检查资产配置，保持分散投资，定期再平衡")

    return suggestions
