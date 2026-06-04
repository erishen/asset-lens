import csv
import json
import logging
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..config import config

logger = logging.getLogger(__name__)


class ReportFormatMixin:
    def print_console_report(self, report: dict[str, Any]) -> None:
        console = Console(force_terminal=True)

        console.print("")
        title = Panel(
            f"[bold]理财收益综合评估报告[/bold]\n"
            f"数据模式: {report['data_mode'].upper()}\n"
            f"生成时间: {report['generated_at']}",
            border_style="blue",
        )
        console.print(title)

        exchange_rates = report.get("exchange_rates", {})
        console.print("\n[bold]💵 汇率信息:[/bold]")
        console.print(f"   美元汇率: [cyan]{exchange_rates.get('usd_rate', '-')}[/cyan] CNY/USD")
        console.print(f"   港元汇率: [cyan]{exchange_rates.get('hkd_rate', '-')}[/cyan] CNY/HKD")

        sold_analysis = report.get("sold_investment_analysis")
        if sold_analysis:
            console.print("\n[bold green]📊 已实现收益分析[/bold green]")

            sold_table = Table(show_header=False, box=None)
            sold_table.add_column("指标", style="bold", no_wrap=True)
            sold_table.add_column("值", style="cyan", no_wrap=True)
            sold_table.add_row("总投入", f"{self._format_money(sold_analysis['total_initial'])}元")
            sold_table.add_row("已实现收益", f"[green]+{self._format_money(sold_analysis['total_profit'])}元[/green]")
            sold_table.add_row("实现收益率", f"[green]{sold_analysis['total_return_rate']}[/green]")
            sold_table.add_row("平均年化收益率", f"[yellow]{sold_analysis['avg_return_rate']}[/yellow]")
            console.print(sold_table)

            console.print("\n[dim]📊 收益率说明：")
            console.print("[dim]• 已实现收益率：卖出记录中的收益率，包含所有卖出部分的总收益")
            console.print("[dim]• 年化收益率：直接从CSV读取预计算的年化数据（包含年化收益和复利年化）")
            console.print("[dim]  注意：卖出记录的年化收益率为CSV中预先计算的数据，未使用IRR计算")
            console.print("[dim]  对于有多次交易记录的产品，当前年化收益可能与实际IRR存在差异[/dim]")

            if sold_analysis.get("top_performers"):
                console.print("\n[bold green]表现最好的已卖出产品:[/bold green]")
                for i, p in enumerate(sold_analysis["top_performers"][:3], 1):
                    console.print(f"  [green]{i}. {p['name']}: {p['return_rate']} ({p['holding_days']}天)[/green]")

            if sold_analysis.get("worst_performers"):
                console.print("\n[bold red]亏损产品:[/bold red]")
                for i, p in enumerate(sold_analysis["worst_performers"][:10], 1):
                    console.print(f"  [red]{i}. {p['name']}: {p['return_rate']} ({p['holding_days']}天)[/red]")

        time_analysis = report.get("time_group_analysis", {})
        if time_analysis.get("groups"):
            console.print("\n[bold blue]📅 按投资时间分组分析:[/bold blue]")

            time_table = Table(show_header=True, header_style="bold blue", box=None)
            time_table.add_column("分组", style="cyan", no_wrap=True)
            time_table.add_column("数量", justify="right")
            time_table.add_column("投资金额", justify="right")
            time_table.add_column("实现收益", justify="right")
            time_table.add_column("平均年化", justify="right")

            for group in time_analysis["groups"]:
                time_table.add_row(
                    group["name"],
                    str(group["count"]),
                    f"{self._format_money(group['total_amount'])}元",
                    f"[green]+{self._format_money(group['total_profit'])}元[/green]",
                    group["avg_return_rate"],
                )
            console.print(time_table)

            console.print("\n[dim]🎯 时间分组总结:")
            console.print("[dim]• 短期投资偏好快速获利，但收益可能不够稳定")
            console.print("[dim]• 中期投资平衡了收益和风险，是较好的投资周期")
            console.print("[dim]• 长期投资收益偏低，建议: 优化投资策略[/dim]")

        console.print("\n[bold blue]💼 当前持有投资分析[/bold blue]")
        summary = report["portfolio_summary"]

        portfolio_table = Table(show_header=False, box=None)
        portfolio_table.add_column("指标", style="bold")
        portfolio_table.add_column("值", style="cyan")
        portfolio_table.add_row("当前总资产", f"{self._format_money(summary['total_value'])}元")
        portfolio_table.add_row("总投入资金", f"{self._format_money(summary['total_initial'])}元")
        portfolio_table.add_row("  其中有效投资", f"{self._format_money(summary['valid_initial'])}元")
        portfolio_table.add_row("未实现收益", f"[green]+{self._format_money(summary['total_profit'])}元[/green]")
        portfolio_table.add_row("整体收益率", f"[green]{summary['overall_return_rate']}[/green]")
        portfolio_table.add_row("有效投资收益率", f"[green]{summary['valid_return_rate']}[/green]")
        portfolio_table.add_row(
            "正收益产品平均年化收益率", f"[yellow]{summary.get('positive_avg_return', 'N/A')}[/yellow]"
        )
        console.print(portfolio_table)

        console.print("\n[bold]投资类型分布:[/bold]")
        type_table = Table(show_header=True, header_style="bold cyan", box=None)
        type_table.add_column("类型", style="cyan")
        type_table.add_column("占比", justify="right")
        type_table.add_column("金额", justify="right")
        for type_name, stats in report["type_distribution"].items():
            type_table.add_row(type_name, stats["percentage"], f"{self._format_money(stats['total_value'])}元")
        console.print(type_table)

        special_bonds = report.get("special_bonds", [])
        if special_bonds:
            console.print("\n[bold yellow]📄 特别国债计算明细[/bold yellow]")
            for i, bond in enumerate(special_bonds, 1):
                console.print(f"  [yellow]{i}. {bond['name']}[/yellow]")
                console.print(f"     当前持仓: {self._format_money(bond['current_amount'])}元")
                console.print(f"     未实现收益: [green]{self._format_money(bond['profit_amount'])}元[/green]")
                console.print(f"     年化: {bond['annual_return']} ({bond['investment_days']}天)")

        console.print("\n[bold]🎯 风险等级分布[/bold]")
        risk_table = Table(show_header=True, header_style="bold magenta", box=None)
        risk_table.add_column("风险等级", style="magenta")
        risk_table.add_column("占比", justify="right")
        risk_table.add_column("金额", justify="right")
        for risk_name, stats in report["risk_distribution"].items():
            risk_table.add_row(risk_name, stats["percentage"], f"{self._format_money(stats['total_value'])}元")
        console.print(risk_table)

        risk_warnings = report.get("risk_warnings", [])
        if risk_warnings:
            console.print("\n[bold red]⚠️  风险提示[/bold red]")
            for warning in risk_warnings:
                console.print(f"[red]• {warning['message']}[/red]")
                if warning.get("products"):
                    for p in warning["products"][:5]:
                        if isinstance(p, dict):
                            name = p.get("name", "未知")
                            if "return_rate" in p:
                                value = p.get("return_rate", "-")
                                console.print(f"  [red]- {name}: {value}[/red]")
                            elif "loss" in p:
                                loss = p.get("loss", "-")
                                return_rate = p.get("return_rate", "-")
                                console.print(f"  [red]- {name}: 亏损 {loss}元, 收益率 {return_rate}[/red]")
                            elif "return" in p:
                                ret = p.get("return", "-")
                                days = p.get("days", "-")
                                console.print(f"  [red]- {name}: {ret} (投资 {days} 天)[/red]")
                            elif "annual_return" in p:
                                annual_ret = p.get("annual_return", "-")
                                current_amt = p.get("current_amount", "-")
                                status = p.get("status", "-")
                                console.print(
                                    f"  [red]- {name}: 年化 {annual_ret}, 金额 {current_amt}元, {status}[/red]"
                                )
                            else:
                                console.print(f"  [red]- {name}[/red]")

        suggestions = report.get("optimization_suggestions", [])
        if suggestions:
            console.print("\n[bold green]💡 优化建议[/bold green]")
            for idx, suggestion in enumerate(suggestions, 1):
                console.print(f"\n[bold cyan]{idx}. {suggestion['title']}:[/bold cyan]")
                for detail in suggestion["details"]:
                    if detail == "":
                        console.print("")
                    elif detail.startswith("  "):
                        console.print(f"   {detail}")
                    elif detail.startswith("\n"):
                        console.print(f"   {detail.strip()}")
                    elif detail.startswith("•"):
                        console.print(f"   {detail}")
                    else:
                        console.print(f"   • {detail}")

        evaluation = report.get("comprehensive_evaluation", {})
        if evaluation:
            console.print("\n[bold magenta]🎉 综合评价[/bold magenta]")

            eval_table = Table(show_header=False, box=None)
            eval_table.add_column("指标", style="bold")
            eval_table.add_column("值", style="cyan")
            eval_table.add_row("总当前金额", f"{self._format_money(evaluation['total_current_amount'])}元")
            eval_table.add_row("总投入本金", f"{self._format_money(evaluation['total_investment'])}元")
            eval_table.add_row("已实现收益", f"[green]+{self._format_money(evaluation['realized_profit'])}元[/green]")
            eval_table.add_row("未实现收益", f"[green]+{self._format_money(evaluation['unrealized_profit'])}元[/green]")
            eval_table.add_row("整体收益率", f"[green]+{evaluation['overall_return_rate']}[/green] (累计总收益率)")
            eval_table.add_row(
                "加权年化收益率", f"[green]+{evaluation['weighted_annual_return']}[/green] (按投资金额加权)"
            )
            eval_table.add_row(
                "时间加权年化收益率",
                f"[green]+{evaluation['time_weighted_return']}[/green] (按平均投资时间{evaluation['avg_investment_days']}天)",
            )
            console.print(eval_table)

            expected = evaluation.get("expected_annual_return", "0")
            rate = evaluation.get("current_annualized_rate", "2.0")
            console.print(
                f"\n[bold]💰 基于当前表现预期年收益:[/bold] {self._format_money(expected)}元 (按{rate}%年化收益率)"
            )
            console.print(f"\n[cyan]{evaluation['evaluation']}[/cyan]")

        efficiency = report.get("investment_efficiency", {})
        if efficiency:
            console.print("\n[bold blue]📈 投资效率分析:[/bold blue]")
            console.print(f"• 当前资金增值效率: [cyan]{efficiency['capital_efficiency']}[/cyan]")
            console.print(f"• 年化资金增长率: [cyan]{efficiency['annual_growth_rate']}[/cyan]")

        logger.info("" + "=" * 60)

    def _format_money_value(self, value: str) -> str:
        try:
            amount = float(value)
            return f"{amount / 10000:.2f}万"
        except (ValueError, TypeError):
            return value

    def _format_money(self, value: str) -> str:
        try:
            amount = float(value)
            if amount >= 10000:
                return f"{amount / 10000:.2f}万"
            else:
                return f"{amount:,.0f}"
        except (ValueError, TypeError):
            return value

    def save_csv_report(self, report: dict[str, Any], output_path: Path | None) -> Path | None:
        if output_path is None:
            output_path = config.output_path
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"投资收益率分析_{timestamp}.csv"
        file_path = output_path / filename

        products = report.get("products", [])
        if not products:
            return file_path

        with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=products[0].keys())
            writer.writeheader()
            writer.writerows(products)

        logger.info(f" CSV 报告已保存: {file_path}")
        return file_path

    def save_json_report(self, report: dict[str, Any], output_path: Path | None = None) -> Path:
        if output_path is None:
            output_path = config.output_path
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"投资收益率分析_{timestamp}.json"
        file_path = output_path / filename

        def decimal_default(obj):
            if isinstance(obj, Decimal):
                return str(obj)
            raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=decimal_default)

        logger.info(f" JSON 报告已保存: {file_path}")
        return file_path
