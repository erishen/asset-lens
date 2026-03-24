"""
Report printer for asset-lens.
报告打印模块 - 处理报告的控制台输出
"""

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


class ReportPrinter:
    """报告打印器"""

    def __init__(self):
        self.console = Console()

    def print_report(self, report: dict[str, Any]) -> None:
        """打印报告"""
        report_type = report.get("report_type", "unknown")
        title = self._get_report_title(report_type)

        self.console.print(Panel(title, border_style="blue"))

        if report_type == "strategy_report":
            self._print_strategy_report(report)
        elif report_type == "pool_report":
            self._print_pool_report(report)
        elif report_type == "comparison_report":
            self._print_comparison_report(report)
        elif report_type == "risk_report":
            self._print_risk_report(report)
        else:
            self._print_generic_report(report)

    def _get_report_title(self, report_type: str) -> str:
        """获取报告标题"""
        titles = {
            "strategy_report": "📊 策略报告",
            "pool_report": "📈 股票池报告",
            "comparison_report": "📋 对比报告",
            "risk_report": "⚠️ 风险报告",
        }
        return titles.get(report_type, "📄 报告")

    def _print_strategy_report(self, report: dict[str, Any]) -> None:
        """打印策略报告"""
        strategy_info = report.get("strategy_info", {})
        if strategy_info:
            self.console.print(f"\n🎯 策略: {strategy_info.get('name', 'N/A')}")
            self.console.print(f"   描述: {strategy_info.get('description', 'N/A')}")

        performance = report.get("performance", {})
        if performance:
            table = Table(title="表现指标")
            table.add_column("指标", style="cyan")
            table.add_column("值", justify="right")
            for key, value in performance.items():
                table.add_row(key, str(value))
            self.console.print(table)

        recommendations = report.get("recommendations", [])
        if recommendations:
            self.console.print("\n💡 建议:")
            for i, rec in enumerate(recommendations, 1):
                self.console.print(f"  {i}. {rec}")

    def _print_pool_report(self, report: dict[str, Any]) -> None:
        """打印股票池报告"""
        pool_name = report.get("pool_name", "default")
        self.console.print(f"\n📦 股票池: {pool_name}")

        stocks = report.get("stocks", [])
        if stocks:
            table = Table(title="持仓股票")
            table.add_column("代码", style="cyan")
            table.add_column("名称", style="green")
            table.add_column("数量", justify="right")
            table.add_column("成本", justify="right")
            table.add_column("现价", justify="right")
            table.add_column("盈亏", justify="right")

            for stock in stocks[:20]:
                table.add_row(
                    stock.get("code", ""),
                    stock.get("name", ""),
                    str(stock.get("quantity", 0)),
                    f"¥{stock.get('cost', 0):.2f}",
                    f"¥{stock.get('current_price', 0):.2f}",
                    f"{stock.get('profit_pct', 0):.2f}%",
                )
            self.console.print(table)

    def _print_comparison_report(self, report: dict[str, Any]) -> None:
        """打印对比报告"""
        strategies = report.get("strategies", [])
        if strategies:
            table = Table(title="策略对比")
            table.add_column("策略", style="cyan")
            table.add_column("收益率", justify="right")
            table.add_column("胜率", justify="right")
            table.add_column("最大回撤", justify="right")

            for s in strategies:
                table.add_row(
                    s.get("name", ""),
                    f"{s.get('return_rate', 0):.2f}%",
                    f"{s.get('win_rate', 0):.1f}%",
                    f"{s.get('max_drawdown', 0):.2f}%",
                )
            self.console.print(table)

    def _print_risk_report(self, report: dict[str, Any]) -> None:
        """打印风险报告"""
        risk_level = report.get("risk_level", "未知")
        self.console.print(f"\n⚠️ 风险等级: {risk_level}")

        warnings = report.get("warnings", [])
        if warnings:
            self.console.print("\n🚨 警告:")
            for warning in warnings:
                self.console.print(f"  • {warning}")

        recommendations = report.get("recommendations", [])
        if recommendations:
            self.console.print("\n💡 建议:")
            for rec in recommendations:
                self.console.print(f"  • {rec.get('message', '')}")

    def _print_generic_report(self, report: dict[str, Any]) -> None:
        """打印通用报告"""
        for key, value in report.items():
            if key not in ["report_type", "generate_time"]:
                self.console.print(f"{key}: {value}")
