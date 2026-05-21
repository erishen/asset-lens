"""
Console printer for asset-lens.
控制台打印器 - 处理报告的控制台输出
"""

from decimal import Decimal, InvalidOperation
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


class ConsolePrinter:
    """控制台打印器"""

    def print_report(self, report: dict[str, Any]) -> None:
        """打印完整报告"""
        console = Console()

        self._print_header(console, report)
        self._print_exchange_rates(console, report)
        self._print_portfolio_summary(console, report)
        self._print_type_distribution(console, report)
        self._print_risk_distribution(console, report)
        self._print_risk_warnings(console, report)
        self._print_suggestions(console, report)
        self._print_evaluation(console, report)

    def _print_header(self, console: Console, report: dict[str, Any]) -> None:
        """打印报告头部"""
        console.print(
            Panel(
                f"[bold blue]投资组合分析报告[/bold blue]\n"
                f"生成时间: {report.get('generated_at', 'N/A')}\n"
                f"数据模式: {report.get('data_mode', 'N/A')}",
                title="Asset Lens",
                border_style="blue",
            )
        )

    def _print_exchange_rates(self, console: Console, report: dict[str, Any]) -> None:
        """打印汇率信息"""
        rates = report.get("exchange_rates", {})
        if rates:
            console.print(f"\n💵 汇率: USD={rates.get('usd_rate', 'N/A')}, HKD={rates.get('hkd_rate', 'N/A')}")

    def _print_portfolio_summary(self, console: Console, report: dict[str, Any]) -> None:
        """打印投资组合摘要"""
        summary = report.get("portfolio_summary", {})
        if not summary:
            return

        console.print("\n📊 投资组合摘要:")
        console.print(f"  总产品数: {summary.get('total_products', 0)}")
        console.print(f"  总金额: ¥{summary.get('total_value', '0')}")
        console.print(f"  总收益: ¥{summary.get('total_profit', '0')}")
        console.print(f"  收益率: {summary.get('return_rate', '0%')}")

    def _print_type_distribution(self, console: Console, report: dict[str, Any]) -> None:
        """打印类型分布"""
        type_dist = report.get("type_distribution", {})
        if not type_dist:
            return

        table = Table(title="\n📈 投资类型分布")
        table.add_column("类型", style="cyan")
        table.add_column("数量", justify="right")
        table.add_column("金额", justify="right")
        table.add_column("占比", justify="right")

        for type_name, stats in type_dist.items():
            percentage = stats.get("percentage", 0)
            if isinstance(percentage, str):
                percentage = percentage.replace("%", "")
            table.add_row(
                type_name,
                str(stats.get("count", 0)),
                f"¥{stats.get('total_value', 0)}",
                f"{float(percentage):.1f}%",
            )

        console.print(table)

    def _print_risk_distribution(self, console: Console, report: dict[str, Any]) -> None:
        """打印风险分布"""
        risk_dist = report.get("risk_distribution", {})
        if not risk_dist:
            return

        table = Table(title="\n⚠️ 风险分布")
        table.add_column("风险等级", style="cyan")
        table.add_column("数量", justify="right")
        table.add_column("金额", justify="right")
        table.add_column("占比", justify="right")

        for risk_level, stats in risk_dist.items():
            percentage = stats.get("percentage", 0)
            if isinstance(percentage, str):
                percentage = percentage.replace("%", "")
            table.add_row(
                risk_level,
                str(stats.get("count", 0)),
                f"¥{stats.get('total_value', 0)}",
                f"{float(percentage):.1f}%",
            )

        console.print(table)

    def _print_risk_warnings(self, console: Console, report: dict[str, Any]) -> None:
        """打印风险警告"""
        warnings = report.get("risk_warnings", [])
        if not warnings:
            return

        console.print("\n⚠️ 风险警告:")
        for warning in warnings:
            level = warning.get("level", "info")
            message = warning.get("message", "")
            if level == "danger":
                console.print(f"  🔴 {message}")
            elif level == "warning":
                console.print(f"  🟡 {message}")
            else:
                console.print(f"  🔵 {message}")

    def _print_suggestions(self, console: Console, report: dict[str, Any]) -> None:
        """打印优化建议"""
        suggestions = report.get("optimization_suggestions", [])
        if not suggestions:
            return

        console.print("\n💡 优化建议:")
        for i, suggestion in enumerate(suggestions, 1):
            console.print(f"  {i}. {suggestion.get('suggestion', '')}")

    def _print_evaluation(self, console: Console, report: dict[str, Any]) -> None:
        """打印综合评估"""
        evaluation = report.get("comprehensive_evaluation", {})
        if not evaluation:
            return

        console.print("\n📝 综合评估:")
        console.print(f"  {evaluation.get('evaluation', 'N/A')}")
        console.print(f"  风险等级: {evaluation.get('risk_level', 'N/A')}")
        console.print(f"  分散化评分: {evaluation.get('diversification_score', 0):.0f}/100")

    def _format_money(self, value: str) -> str:
        """格式化金额"""
        try:
            amount = Decimal(value.replace("¥", "").replace(",", ""))
            if amount >= Decimal("10000"):
                return f"¥{amount / Decimal('10000'):.1f}万"
            return f"¥{amount:.0f}"
        except (ValueError, TypeError, InvalidOperation):
            return value
