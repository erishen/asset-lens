from datetime import datetime
from decimal import Decimal
from typing import Any

from ..config import config
from ..core.sold_investment import SoldInvestmentAnalyzer
from ..core.time_group import TimeGroupAnalyzer
from ..data.models import Portfolio, SellRecord
from .analysis_evaluation import AnalysisEvaluationMixin
from .analysis_warnings import AnalysisWarningsMixin
from .report_format import ReportFormatMixin


class ReportGenerator(AnalysisWarningsMixin, AnalysisEvaluationMixin, ReportFormatMixin):
    def __init__(self):
        self.report_language = config.report_language
        self.sold_analyzer = SoldInvestmentAnalyzer()
        self.time_analyzer = TimeGroupAnalyzer()

    def generate_analysis_report(
        self,
        portfolio: Portfolio,
        sell_records: list[SellRecord] | None = None,
    ) -> dict[str, Any]:
        report = {
            "generated_at": datetime.now().isoformat(),
            "data_mode": config.data_mode,
            "exchange_rates": self.get_exchange_rates(),
            "portfolio_summary": self.generate_portfolio_summary(portfolio),
            "top_performers": self.get_top_performers(portfolio, top_n=10),
            "low_returns": self.get_low_return_products(portfolio, threshold=config.min_return_threshold),
            "short_term_observation": self.get_short_term_observation_products(portfolio),
            "high_return_reference": self.get_high_return_reference_products(portfolio),
            "type_distribution": self.get_type_distribution(portfolio),
            "risk_distribution": self.get_risk_distribution(portfolio),
            "time_group_analysis": self.generate_time_group_analysis(portfolio),
            "sold_investment_analysis": self.generate_sold_analysis(sell_records),
            "special_bonds": self.generate_special_bonds_analysis(portfolio),
            "risk_warnings": self.generate_risk_warnings(portfolio),
            "optimization_suggestions": self.generate_optimization_suggestions(portfolio),
            "investment_advice": self.generate_investment_advice(portfolio),
            "comprehensive_evaluation": self.generate_comprehensive_evaluation(portfolio, sell_records),
            "investment_efficiency": self.generate_investment_efficiency(portfolio, sell_records),
        }

        return report

    def get_exchange_rates(self) -> dict[str, Any]:
        from ..data.csv_parser import CSVParser

        data_dir = config.get_latest_data_dir()
        usd_rate, hkd_rate = (
            CSVParser.get_exchange_rates(data_dir) if data_dir else (config.default_usd_rate, config.default_hkd_rate)
        )

        return {
            "usd_rate": str(usd_rate),
            "hkd_rate": str(hkd_rate),
            "source": "csv_file" if data_dir else "config",
        }

    def generate_portfolio_summary(self, portfolio: Portfolio) -> dict[str, Any]:
        from ..data.models import InvestmentType

        valid_initial = Decimal("0")
        valid_profit = Decimal("0")
        for product in portfolio.products:
            if product.start_date and product.initial_amount:
                amount = product.initial_amount
                if product.investment_type in [InvestmentType.US_STOCK, InvestmentType.USD_FUND]:
                    amount = amount * (product.usd_rate or portfolio.usd_rate)
                elif product.investment_type in [
                    InvestmentType.HK_STOCK,
                    InvestmentType.HK_CASH,
                    InvestmentType.HK_DIVIDEND_FUND,
                ]:
                    amount = amount * (product.hkd_rate or portfolio.hkd_rate)
                valid_initial += amount
                if product.profit_amount:
                    valid_profit += product.profit_amount

        valid_return_rate = (valid_profit / valid_initial * 100) if valid_initial > Decimal("0") else Decimal("0")

        return {
            "total_products": len(portfolio.products),
            "total_value": str(portfolio.total_value),
            "total_initial": str(portfolio.total_initial),
            "valid_initial": str(valid_initial),
            "total_profit": str(portfolio.total_profit),
            "overall_return_rate": f"{portfolio.overall_return_rate:.2f}%" if portfolio.overall_return_rate else "N/A",
            "valid_return_rate": f"{valid_return_rate:.2f}%",
            "positive_avg_return": self._calculate_positive_avg_return(portfolio),
        }

    def _calculate_positive_avg_return(self, portfolio: Portfolio) -> str:
        positive_products = [p for p in portfolio.products if p.annual_return and p.annual_return > Decimal("0")]
        if not positive_products:
            return "N/A"
        avg_return = Decimal(str(sum(p.annual_return for p in positive_products if p.annual_return))) / Decimal(
            str(len(positive_products))
        )
        return f"{avg_return:.2f}%"

    def get_top_performers(self, portfolio: Portfolio, top_n: int = 10) -> list[dict[str, Any]]:
        products_with_return = [
            p for p in portfolio.products if p.annual_return is not None or p.return_rate is not None
        ]

        products_with_return.sort(key=lambda p: p.annual_return or p.return_rate or Decimal("0"), reverse=True)

        top_products = products_with_return[:top_n]

        return [
            {
                "rank": i + 1,
                "name": p.name,
                "type": p.investment_type.value,
                "risk_level": p.risk_level.value if p.risk_level else "-",
                "return_rate": f"{p.return_rate:.2f}%" if p.return_rate else "-",
                "annual_return": f"{p.annual_return:.2f}%" if p.annual_return else "-",
                "current_amount": str(p.current_amount) if p.current_amount else "-",
                "profit_amount": str(p.profit_amount) if p.profit_amount else "-",
                "investment_days": p.investment_days or "-",
            }
            for i, p in enumerate(top_products)
        ]

    def get_low_return_products(self, portfolio: Portfolio, threshold: float = 2.0) -> list[dict[str, Any]]:
        low_return_products = [
            p for p in portfolio.products if p.annual_return is not None and p.annual_return < Decimal(str(threshold))
        ]

        low_return_products.sort(key=lambda p: p.annual_return or Decimal("0"), reverse=True)

        return [
            {
                "name": p.name,
                "type": p.investment_type.value,
                "risk_level": p.risk_level.value if p.risk_level else "-",
                "annual_return": f"{p.annual_return:.2f}%",
                "current_amount": str(p.current_amount) if p.current_amount else "-",
                "investment_days": p.investment_days or "-",
                "profit_amount": str(p.profit_amount) if p.profit_amount else "-",
                "status": "亏损" if p.profit_amount and p.profit_amount < Decimal("0") else "收益过低",
            }
            for p in low_return_products
        ]

    def get_short_term_observation_products(self, portfolio: Portfolio) -> list[dict[str, Any]]:
        short_term_products = [
            p
            for p in portfolio.products
            if p.investment_days and p.investment_days < 90 and p.annual_return and p.annual_return < Decimal("3")
        ]

        return [
            {
                "name": p.name,
                "annual_return": f"{p.annual_return:.2f}%",
                "investment_days": p.investment_days,
                "current_amount": str(p.current_amount) if p.current_amount else "-",
                "status": "短期波动(正常现象)"
                if p.profit_amount and p.profit_amount < Decimal("0")
                else "收益偏低(观察)",
            }
            for p in short_term_products
        ]

    def get_high_return_reference_products(self, portfolio: Portfolio) -> list[dict[str, Any]]:
        high_return_products = [p for p in portfolio.products if p.annual_return and p.annual_return > Decimal("10")]

        high_return_products.sort(key=lambda p: p.annual_return or Decimal("0"), reverse=True)

        return [
            {
                "name": p.name,
                "type": p.investment_type.value,
                "annual_return": f"{p.annual_return:.2f}%",
                "profit_amount": str(p.profit_amount) if p.profit_amount else "-",
                "current_amount": str(p.current_amount) if p.current_amount else "-",
                "level": "超高收益" if p.annual_return and p.annual_return > Decimal("50") else "高收益",
            }
            for p in high_return_products[:10]
        ]

    def get_type_distribution(self, portfolio: Portfolio) -> dict[str, Any]:
        type_stats = portfolio.get_type_distribution()

        return {
            type_name: {
                "count": stats["count"],
                "total_value": str(stats["total_value"]),
                "percentage": f"{stats['percentage']:.2f}%",
                "product_names": [p.name for p in stats["products"]],
            }
            for type_name, stats in type_stats.items()
        }

    def get_risk_distribution(self, portfolio: Portfolio) -> dict[str, Any]:
        risk_stats = portfolio.get_risk_distribution()

        return {
            risk_name: {
                "count": stats["count"],
                "total_value": str(stats["total_value"]),
                "percentage": f"{stats['percentage']:.2f}%",
                "product_names": [p.name for p in stats["products"]],
            }
            for risk_name, stats in risk_stats.items()
        }

    def generate_time_group_analysis(self, portfolio: Portfolio) -> dict[str, Any]:
        result = self.time_analyzer.analyze_by_holding_period(portfolio.products)

        groups = [
            {
                "name": group.group_name,
                "description": group.group_description,
                "count": group.products_count,
                "total_amount": str(group.total_amount),
                "total_initial": str(group.total_initial),
                "total_profit": str(group.total_profit),
                "avg_return_rate": f"{group.avg_return_rate:.2f}%" if group.avg_return_rate else "-",
                "avg_holding_days": group.avg_holding_days,
                "products": group.products[:5],
            }
            for group in result.get("groups", [])
        ]

        return {
            "groups": groups,
            "total_products": result.get("total_products", 0),
            "total_amount": str(result.get("total_amount", Decimal("0"))),
            "total_initial": str(result.get("total_initial", Decimal("0"))),
            "total_profit": str(result.get("total_profit", Decimal("0"))),
        }

    def generate_sold_analysis(self, sell_records: list[SellRecord] | None = None) -> dict[str, Any] | None:
        if not sell_records:
            return None

        result = self.sold_analyzer.analyze_sold_investments(sell_records)
        stats = result["stats"]

        top_performers = self.sold_analyzer.get_top_performers(result["details"], top_n=5)
        worst_performers = self.sold_analyzer.get_worst_performers(result["details"], top_n=10)

        return {
            "total_records": stats.total_records,
            "total_initial": str(stats.total_initial),
            "total_profit": str(stats.total_profit),
            "total_return_rate": f"{stats.total_return_rate:.2f}%",
            "positive_count": stats.positive_count,
            "negative_count": stats.negative_count,
            "avg_holding_days": stats.avg_holding_days,
            "avg_return_rate": f"{stats.avg_return_rate:.2f}%",
            "top_performers": [
                {
                    "name": p.name,
                    "return_rate": f"{p.return_rate:.2f}%",
                    "holding_days": p.holding_days,
                }
                for p in top_performers
            ],
            "worst_performers": [
                {
                    "name": p.name,
                    "return_rate": f"{p.return_rate:.2f}%",
                    "holding_days": p.holding_days,
                }
                for p in worst_performers
            ],
        }

    def generate_special_bonds_analysis(self, portfolio: Portfolio) -> list[dict[str, Any]]:
        bond_keywords = ["特别国债", "国债"]
        special_bonds = [
            {
                "name": product.name,
                "current_amount": str(product.current_amount) if product.current_amount else "-",
                "initial_amount": str(product.initial_amount) if product.initial_amount else "-",
                "profit_amount": str(product.profit_amount) if product.profit_amount else "-",
                "return_rate": f"{product.return_rate:.2f}%" if product.return_rate else "-",
                "annual_return": f"{product.annual_return:.2f}%" if product.annual_return else "-",
                "investment_days": product.investment_days or "-",
            }
            for product in portfolio.products
            if any(keyword in product.name for keyword in bond_keywords)
        ]

        return special_bonds


report_generator = ReportGenerator()
