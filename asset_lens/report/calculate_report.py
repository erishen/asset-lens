"""
收益率计算报告生成器
模仿 ts-demo 的 npm run calculate 输出格式
"""

from decimal import Decimal
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..config import config
from ..data.models import InvestmentProduct, InvestmentType, Portfolio


class CalculateReportGenerator:
    """收益率计算报告生成器"""

    def __init__(self):
        self.console = Console(force_terminal=True)

    def generate_calculate_report(self, portfolio: Portfolio) -> dict[str, Any]:
        products_with_return = self._get_products_with_return(portfolio)
        products_without_return = self._get_products_without_return(portfolio)

        products_with_return.sort(key=lambda p: p.annual_return or Decimal("0"), reverse=True)

        top_performers = products_with_return[:10]
        negative_performers = [
            p for p in products_with_return if p.annual_return and p.annual_return < Decimal("0")
        ]
        low_positive_performers = [
            p
            for p in products_with_return
            if p.annual_return and Decimal("0") <= p.annual_return < Decimal("2")
        ]

        positive_products = [
            p for p in products_with_return if p.annual_return and p.annual_return > Decimal("0")
        ]
        avg_positive_return = Decimal("0")
        if positive_products:
            total = sum(p.annual_return for p in positive_products if p.annual_return)
            avg_positive_return = Decimal(str(total)) / Decimal(str(len(positive_products)))

        # 总投资金额 = 所有有类型且金额>0的记录的当前金额总和（考虑汇率转换，不包含利息）
        usd_rate = Decimal(str(config.default_usd_rate))
        hkd_rate = Decimal(str(config.default_hkd_rate))

        all_products_with_amount = [
            p
            for p in portfolio.products
            if p.investment_type != InvestmentType.OTHER
            and p.current_amount
            and p.current_amount > Decimal("0")
        ]
        # 总投资金额不包含利息（与 ts-demo 保持一致）
        total_investment = sum(
            (p.current_amount or Decimal("0")) * (p.usd_rate or usd_rate)
            if p.investment_type in [InvestmentType.US_STOCK, InvestmentType.USD_FUND]
            else (p.current_amount or Decimal("0")) * (p.hkd_rate or hkd_rate)
            if p.investment_type
            in [InvestmentType.HK_STOCK, InvestmentType.HK_CASH, InvestmentType.HK_DIVIDEND_FUND]
            else p.current_amount or Decimal("0")
            for p in all_products_with_amount
        )

        # 有效投资总额 = 能计算收益率的记录的当前金额总和（包含利息）
        total_value = sum(p.get_converted_amount(usd_rate, hkd_rate) for p in products_with_return)

        # 无收益率数据的投资金额（包含利息，用于显示）
        no_return_value = sum(
            p.get_converted_amount(usd_rate, hkd_rate) for p in products_without_return
        )

        return {
            "total_products": len(portfolio.products),
            "products_with_return": len(products_with_return),
            "products_without_return": len(products_without_return),
            "top_performers": top_performers,
            "negative_performers": negative_performers,
            "low_positive_performers": low_positive_performers,
            "avg_positive_return": avg_positive_return,
            "type_distribution": self._get_type_distribution(products_with_return),
            "no_return_distribution": self._get_type_distribution(products_without_return),
            "total_investment": total_investment,
            "total_value": total_value,
            "no_return_value": no_return_value,
        }

    def _get_products_with_return(self, portfolio: Portfolio) -> list[InvestmentProduct]:
        return [
            p
            for p in portfolio.products
            if p.annual_return is not None and p.start_date is not None
        ]

    def _get_products_without_return(self, portfolio: Portfolio) -> list[InvestmentProduct]:
        return [p for p in portfolio.products if p.annual_return is None or p.start_date is None]

    def _get_type_distribution(
        self, products: list[InvestmentProduct]
    ) -> dict[str, dict[str, Any]]:
        usd_rate = Decimal(str(config.default_usd_rate))
        hkd_rate = Decimal(str(config.default_hkd_rate))
        type_stats: dict[str, dict[str, Any]] = {}

        for product in products:
            type_name = self._get_raw_type(product)

            if type_name not in type_stats:
                type_stats[type_name] = {
                    "count": 0,
                    "total_value": Decimal("0"),
                }

            type_stats[type_name]["count"] += 1
            if product.current_amount:
                type_stats[type_name]["total_value"] += product.get_converted_amount(
                    usd_rate, hkd_rate
                )

        total_value = Decimal(str(sum(s["total_value"] for s in type_stats.values())))

        for type_name in type_stats:
            if total_value > Decimal("0"):
                type_stats[type_name]["percentage"] = (
                    Decimal(str(type_stats[type_name]["total_value"])) / total_value * 100
                )
            else:
                type_stats[type_name]["percentage"] = Decimal("0")

        return type_stats

    def _get_raw_type(self, product: InvestmentProduct) -> str:
        raw_type_mapping = {
            InvestmentType.MONETARY: "货币",
            InvestmentType.CASH: "现金",
            InvestmentType.INDEX_FUND: "指数基金",
            InvestmentType.BOND_FUND: "债券基金",
            InvestmentType.MIXED_FUND: "混合基金",
            InvestmentType.STOCK: "股票",
            InvestmentType.US_STOCK: "美股（美元）",
            InvestmentType.HK_STOCK: "港股（港元）",
            InvestmentType.HK_CASH: "现金（港元）",
            InvestmentType.HK_DIVIDEND_FUND: "股息基金（港元）",
            InvestmentType.QDII: "QDII",
            InvestmentType.WEALTH: "理财",
            InvestmentType.HIGH_END_WEALTH: "高端理财",
            InvestmentType.BROKER_WEALTH: "券商理财",
            InvestmentType.PUBLIC_FIXED_INCOME: "公募固收",
            InvestmentType.FIXED_DEPOSIT: "定期存款",
            InvestmentType.BOND: "债券",
            InvestmentType.SPECIAL_TREASURY_BOND: "特别国债",
            InvestmentType.REITS: "REITs",
            InvestmentType.GOLD: "黄金",
            InvestmentType.FUND: "基金",
            InvestmentType.DCA_FUND: "定投基金",
            InvestmentType.PENSION: "个人养老金",
            InvestmentType.ETF: "ETF",
            InvestmentType.USD_FUND: "美元基金（美元）",
            InvestmentType.OTHER: "其他",
        }
        return raw_type_mapping.get(product.investment_type, "其他")

    def _get_display_type(self, product: InvestmentProduct) -> str:
        type_mapping = {
            InvestmentType.MONETARY: "货币",
            InvestmentType.CASH: "现金",
            InvestmentType.INDEX_FUND: "基金",
            InvestmentType.BOND_FUND: "债券",
            InvestmentType.MIXED_FUND: "基金",
            InvestmentType.STOCK: "股票",
            InvestmentType.US_STOCK: "美股",
            InvestmentType.HK_STOCK: "港股",
            InvestmentType.HK_CASH: "现金（港元）",
            InvestmentType.HK_DIVIDEND_FUND: "股息基金（港元）",
            InvestmentType.QDII: "QDII",
            InvestmentType.WEALTH: "理财",
            InvestmentType.HIGH_END_WEALTH: "高端理财",
            InvestmentType.BROKER_WEALTH: "券商理财",
            InvestmentType.PUBLIC_FIXED_INCOME: "公募固收",
            InvestmentType.FIXED_DEPOSIT: "定期存款",
            InvestmentType.BOND: "债券",
            InvestmentType.SPECIAL_TREASURY_BOND: "特别国债",
            InvestmentType.REITS: "REITs",
            InvestmentType.GOLD: "黄金",
            InvestmentType.FUND: "基金",
            InvestmentType.DCA_FUND: "定投基金",
            InvestmentType.PENSION: "个人养老金",
            InvestmentType.ETF: "ETF",
            InvestmentType.USD_FUND: "美元基金（美元）",
            InvestmentType.OTHER: "其他",
        }
        return type_mapping.get(product.investment_type, "其他")

    def _get_main_platform(self, product: InvestmentProduct) -> str:
        amounts = {}
        for platform in config.platforms:
            amount = product.platform_amounts.get(platform.id, Decimal("0"))
            if amount and amount > Decimal("0"):
                amounts[platform.name] = amount

        if amounts:
            return str(max(amounts, key=lambda k: amounts[k] or Decimal("0")))
        return "未知"

    def _has_transactions(self, product: InvestmentProduct) -> bool:
        if product.transaction_records and product.transaction_records.strip():
            return True
        if product.secondary_buy:
            return True
        return False

    def _is_dca_product(self, product: InvestmentProduct) -> bool:
        """判断是否为定投产品"""
        if not product.transaction_records:
            return False
        records = product.transaction_records.strip()
        buy_count = records.count(":buy:")
        sell_count = records.count(":sell:")
        return buy_count >= 3 and sell_count == 0

    def _is_secondary_buy_product(self, product: InvestmentProduct) -> bool:
        """判断是否为二次买入产品"""
        if product.secondary_buy:
            return True
        if product.transaction_records and product.transaction_records.strip():
            buy_count = product.transaction_records.count(":buy:")
            sell_count = product.transaction_records.count(":sell:")
            return buy_count == 2 and sell_count == 0
        return False

    def _get_transaction_info(self, product: InvestmentProduct) -> str:
        if product.transaction_records and product.transaction_records.strip():
            buy_count = product.transaction_records.count(":buy:")
            sell_count = product.transaction_records.count(":sell:")
            if buy_count > 0 or sell_count > 0:
                return f"{buy_count}次买入{f'，{sell_count}次卖出' if sell_count > 0 else ''}"

        if product.secondary_buy:
            return "二次买入"

        return ""

    def _get_transaction_display_type(self, product: InvestmentProduct) -> str:
        """获取交易记录显示类型"""
        if self._is_dca_product(product):
            return "dca"
        elif self._is_secondary_buy_product(product):
            return "secondary"
        elif self._has_transactions(product):
            return "transaction"
        return "normal"

    def print_calculate_report(self, report: dict[str, Any]) -> None:
        self.console.print("")

        self._print_return_explanation()

        self._print_top_performers(report["top_performers"])

        avg_return = report["avg_positive_return"]
        self.console.print(f"\n[bold blue]正收益产品的平均年化收益率: {avg_return:.2f}%[/bold blue]")

        if report["negative_performers"]:
            self._print_negative_performers(report["negative_performers"])

        if report["low_positive_performers"]:
            self._print_low_positive_performers(report["low_positive_performers"])

        self._print_summary(report)

        if report["products_without_return"] > 0:
            self._print_no_return_products(report)

        self._print_suggestions()

    def _print_return_explanation(self) -> None:
        explanation = Panel(
            "[dim]• 实际收益率：整个投资期间的实际收益比例，直观反映总体盈亏\n"
            "• 年化收益率：基于复利公式计算，假设当前收益率持续一年的理论值\n"
            "  - 无交易记录产品：使用简单年化公式\n"
            "  - 有交易记录产品（中长期）：使用IRR（内部收益率）考虑资金时间价值\n"
            "  - 短期投资（<180天）或债券类：使用简单年化，避免IRR失真\n"
            "• IRR特点：考虑每笔资金流入流出的时间点，更准确反映投资效率\n"
            "  因此相同投资天数的产品，年化收益率可能因资金使用效率不同而有差异[/dim]",
            title="[bold]📊 收益率说明[/bold]",
            border_style="dim",
        )
        self.console.print(explanation)

    def _print_top_performers(self, products: list[InvestmentProduct]) -> None:
        self.console.print("\n[bold green]📈 收益率排名前10的产品：[/bold green]")

        table = Table(
            show_header=True,
            header_style="bold white on red",
            box=None,
            row_styles=["", "dim"],
            expand=True,
        )
        table.add_column("名称", style="cyan", no_wrap=True)
        table.add_column("平台", width=6, no_wrap=True)
        table.add_column("天数", justify="right", width=4)
        table.add_column("年化", justify="right", width=7, style="bold green")
        table.add_column("实际", justify="right", width=6, style="green")

        for product in products:
            name = product.name
            has_trans = self._has_transactions(product)
            if has_trans:
                name = f"[bold]{name} *[/bold]"

            platform = self._get_main_platform(product)
            days = f"{product.investment_days}" if product.investment_days else "-"
            annual = f"{product.annual_return:.2f}%" if product.annual_return else "-"
            actual = f"{product.return_rate:.2f}%" if product.return_rate else "-"

            table.add_row(name, platform, days, annual, actual)

        self.console.print(table)

        self._print_transaction_details(products[:10], "top")

    def _print_negative_performers(self, products: list[InvestmentProduct]) -> None:
        self.console.print("\n[bold red]📉 收益率为负的产品：[/bold red]")

        table = Table(
            show_header=True,
            header_style="bold white on green",
            box=None,
            row_styles=["", "dim"],
            expand=True,
        )
        table.add_column("名称", style="cyan", no_wrap=True)
        table.add_column("平台", width=6, no_wrap=True)
        table.add_column("天数", justify="right", width=4)
        table.add_column("年化", justify="right", width=7, style="bold red")
        table.add_column("实际", justify="right", width=6, style="red")

        for product in products:
            name = product.name
            has_trans = self._has_transactions(product)
            if has_trans:
                name = f"[bold]{name} *[/bold]"

            platform = self._get_main_platform(product)
            days = f"{product.investment_days}" if product.investment_days else "-"
            annual = f"{product.annual_return:.2f}%" if product.annual_return else "-"
            actual = f"{product.return_rate:.2f}%" if product.return_rate else "-"

            table.add_row(name, platform, days, annual, actual)

        self.console.print(table)

        self._print_transaction_details(products, "negative")

    def _print_low_positive_performers(self, products: list[InvestmentProduct]) -> None:
        self.console.print("\n[bold yellow]📊 收益率0-2.0%的产品：[/bold yellow]")

        table = Table(
            show_header=True,
            header_style="bold black on yellow",
            box=None,
            row_styles=["", "dim"],
            expand=True,
        )
        table.add_column("名称", style="cyan", no_wrap=True)
        table.add_column("平台", width=6, no_wrap=True)
        table.add_column("天数", justify="right", width=4)
        table.add_column("年化", justify="right", width=7, style="bold yellow")
        table.add_column("实际", justify="right", width=6, style="yellow")

        for product in products:
            name = product.name
            has_trans = self._has_transactions(product)
            if has_trans:
                name = f"[bold]{name} *[/bold]"

            platform = self._get_main_platform(product)
            days = f"{product.investment_days}" if product.investment_days else "-"
            annual = f"{product.annual_return:.2f}%" if product.annual_return else "-"
            actual = f"{product.return_rate:.2f}%" if product.return_rate else "-"

            table.add_row(name, platform, days, annual, actual)

        self.console.print(table)

        self._print_transaction_details(products, "low")

    def _print_transaction_details(self, products: list[InvestmentProduct], section: str) -> None:
        trans_products = [p for p in products if self._has_transactions(p)]

        if trans_products:
            self.console.print("[dim]（带 * 的为有多次买卖产品）[/dim]")

            for product in trans_products:
                trans_info = self._get_transaction_info(product)
                annual = f"{product.annual_return:.2f}%" if product.annual_return else "-"
                actual = f"{product.return_rate:.2f}%" if product.return_rate else "-"

                if section == "negative":
                    color = "red"
                elif section == "low":
                    color = "yellow"
                else:
                    color = "cyan"

                display_type = self._get_transaction_display_type(product)
                if display_type == "dca":
                    label = "定投产品"
                elif display_type == "secondary":
                    label = "二次买入"
                else:
                    label = "交易记录"

                self.console.print(
                    f"[{color}]{label}：{product.name}，{trans_info}，收益率：{annual} ({actual})[/{color}]"
                )

    def _print_summary(self, report: dict[str, Any]) -> None:
        total_inv = report["total_investment"]
        total_val = report["total_value"]
        no_return_val = report["no_return_value"]
        diff = float(total_inv) - float(total_val)

        summary_lines = [
            f"📊 总投资金额：{float(total_inv)/10000:.2f}万元 ({float(total_inv):,.0f}元)",
            f"💰 有效投资总额：{float(total_val)/10000:.2f}万元 ({float(total_val):,.0f}元)",
        ]

        if abs(diff) > 100:
            summary_lines.append(f"📋 差异说明：{abs(diff)/10000:.2f}万元为无收益率数据的记录（如无开始日期等）")

        summary = Panel(
            "\n".join(summary_lines),
            title="[bold]投资汇总[/bold]",
            border_style="blue",
        )
        self.console.print("\n")
        self.console.print(summary)

        self.console.print("\n[bold]📈 投资类型分布（有效投资）：[/bold]")

        type_table = Table(show_header=True, header_style="bold blue", box=None)
        type_table.add_column("类型", style="cyan", width=18, no_wrap=True)
        type_table.add_column("金额(万)", justify="right", width=10)
        type_table.add_column("占有效(%)", justify="right", width=10)
        type_table.add_column("占总投资(%)", justify="right", width=12)
        type_table.add_column("项目数", justify="right", width=8)

        type_dist = report["type_distribution"]
        sorted_types = sorted(type_dist.items(), key=lambda x: x[1]["total_value"], reverse=True)

        for type_name, stats in sorted_types:
            amount_wan = float(stats["total_value"]) / 10000
            pct_valid = float(stats["percentage"])
            pct_total = float(stats["total_value"]) / float(total_inv) * 100 if total_inv > 0 else 0
            count = stats["count"]
            type_table.add_row(
                type_name, f"{amount_wan:.2f}", f"{pct_valid:.2f}", f"{pct_total:.2f}", str(count)
            )

        self.console.print(type_table)

    def _print_no_return_products(self, report: dict[str, Any]) -> None:
        self.console.print("\n[bold]📋 无收益率数据的投资：[/bold]")

        no_return_table = Table(show_header=True, header_style="bold magenta", box=None)
        no_return_table.add_column("类型", style="cyan", width=18, no_wrap=True)
        no_return_table.add_column("金额(万)", justify="right", width=10)
        no_return_table.add_column("占无效(%)", justify="right", width=10)
        no_return_table.add_column("占总投资(%)", justify="right", width=12)
        no_return_table.add_column("项目数", justify="right", width=8)

        no_return_dist = report["no_return_distribution"]
        total_inv = report["total_investment"]
        no_return_val = report["no_return_value"]

        sorted_no_return = sorted(
            no_return_dist.items(), key=lambda x: x[1]["total_value"], reverse=True
        )

        for type_name, stats in sorted_no_return:
            amount_wan = float(stats["total_value"]) / 10000
            pct_invalid = float(stats["percentage"])
            pct_total = float(stats["total_value"]) / float(total_inv) * 100 if total_inv > 0 else 0
            count = stats["count"]
            no_return_table.add_row(
                type_name, f"{amount_wan:.2f}", f"{pct_invalid:.2f}", f"{pct_total:.2f}", str(count)
            )

        self.console.print(no_return_table)

    def _print_suggestions(self) -> None:
        suggestions = Panel(
            "[bold]1.[/bold] 考虑赎回低收益产品，转投更高收益品种\n"
            "[bold]2.[/bold] 检查产品期限，避免短期产品长期持有\n"
            "[bold]3.[/bold] 分散投资到不同平台和产品类型",
            title="[bold]💡 建议策略[/bold]",
            border_style="green",
        )
        self.console.print("\n")
        self.console.print(suggestions)


calculate_report_generator = CalculateReportGenerator()
