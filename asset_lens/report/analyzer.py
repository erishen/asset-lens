"""
Return analysis report generator for asset-lens.
收益率分析报告生成模块 - 重构后的精简版本
"""

import csv
import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from ..config import config
from ..core.sold_investment import SoldInvestmentAnalyzer
from ..core.time_group import TimeGroupAnalyzer
from ..data.models import Portfolio, SellRecord
from .console_printer import ConsolePrinter
from ..analyzers.portfolio_analyzer import PortfolioAnalyzer
from ..analyzers.risk_analyzer import RiskAnalyzer
from ..analyzers.evaluation_analyzer import EvaluationAnalyzer


class ReportGenerator:
    """报告生成器 - 重构后的精简版本"""

    def __init__(self):
        """初始化报告生成器"""
        self.report_language = config.report_language
        self.sold_analyzer = SoldInvestmentAnalyzer()
        self.time_analyzer = TimeGroupAnalyzer()
        self.portfolio_analyzer = PortfolioAnalyzer()
        self.risk_analyzer = RiskAnalyzer()
        self.evaluation_analyzer = EvaluationAnalyzer()
        self.console_printer = ConsolePrinter()

    def generate_analysis_report(
        self,
        portfolio: Portfolio,
        sell_records: list[SellRecord] | None = None,
    ) -> dict[str, Any]:
        """生成完整的分析报告"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "data_mode": config.data_mode,
            "exchange_rates": self._get_exchange_rates(),
            "portfolio_summary": self.portfolio_analyzer.generate_portfolio_summary(portfolio),
            "top_performers": self.portfolio_analyzer.get_top_performers(portfolio, top_n=10),
            "low_returns": self.portfolio_analyzer.get_low_return_products(
                portfolio, threshold=config.min_return_threshold
            ),
            "short_term_observation": self.portfolio_analyzer.get_short_term_observation_products(portfolio),
            "high_return_reference": self.portfolio_analyzer.get_high_return_reference_products(portfolio),
            "type_distribution": self.portfolio_analyzer.get_type_distribution(portfolio),
            "risk_distribution": self.portfolio_analyzer.get_risk_distribution(portfolio),
            "time_group_analysis": self._generate_time_group_analysis(portfolio),
            "sold_investment_analysis": self._generate_sold_analysis(sell_records),
            "special_bonds": self.portfolio_analyzer.generate_special_bonds_analysis(portfolio),
            "risk_warnings": self.risk_analyzer.generate_risk_warnings(portfolio),
            "optimization_suggestions": self.risk_analyzer.generate_optimization_suggestions(portfolio),
            "investment_advice": self._generate_investment_advice(portfolio),
            "comprehensive_evaluation": self.evaluation_analyzer.generate_comprehensive_evaluation(
                portfolio, sell_records
            ),
            "investment_efficiency": self.evaluation_analyzer.generate_investment_efficiency(portfolio),
        }

        return report

    def _get_exchange_rates(self) -> dict[str, Any]:
        from ..data.csv_parser import CSVParser

        try:
            data_dir = config.data_path
            usd_rate, hkd_rate = CSVParser.get_exchange_rates(data_dir)
            return {"usd_rate": usd_rate, "hkd_rate": hkd_rate, "source": "cache"}
        except Exception:
            return {"usd_rate": 7.2, "hkd_rate": 0.9, "source": "default"}

    def _generate_time_group_analysis(self, portfolio: Portfolio) -> dict[str, Any]:
        """生成时间分组分析"""
        return self.time_analyzer.analyze_by_holding_period(portfolio.products)

    def _generate_sold_analysis(self, sell_records: list[SellRecord] | None) -> dict[str, Any]:
        """生成已卖出投资分析"""
        if not sell_records:
            return {"total_sold": 0, "total_profit": Decimal("0"), "details": []}
        return self.sold_analyzer.analyze_sold_investments(sell_records)

    def _generate_investment_advice(self, portfolio: Portfolio) -> list[str]:
        """生成投资建议"""
        advice = []

        total_value = portfolio.total_value
        if total_value > Decimal("0"):
            advice.append("建议定期审视投资组合，保持资产配置的合理性")

        type_dist = portfolio.get_type_distribution()
        if len(type_dist) < 3:
            advice.append("建议增加投资类型的多样性，分散风险")

        return advice

    # 向后兼容的代理方法
    def get_exchange_rates(self) -> dict[str, Any]:
        """获取汇率（向后兼容）"""
        return self._get_exchange_rates()

    def generate_portfolio_summary(self, portfolio: Portfolio) -> dict[str, Any]:
        """生成投资组合摘要（向后兼容）"""
        return self.portfolio_analyzer.generate_portfolio_summary(portfolio)

    def get_top_performers(self, portfolio: Portfolio, top_n: int = 10) -> list[dict[str, Any]]:
        """获取最高收益产品（向后兼容）"""
        return self.portfolio_analyzer.get_top_performers(portfolio, top_n)

    def get_low_return_products(self, portfolio: Portfolio, threshold: float = 2.0) -> list[dict[str, Any]]:
        """获取低收益产品（向后兼容）"""
        return self.portfolio_analyzer.get_low_return_products(portfolio, threshold)

    def get_type_distribution(self, portfolio: Portfolio) -> dict[str, Any]:
        """获取类型分布（向后兼容）"""
        return self.portfolio_analyzer.get_type_distribution(portfolio)

    def get_risk_distribution(self, portfolio: Portfolio) -> dict[str, Any]:
        """获取风险分布（向后兼容）"""
        return self.portfolio_analyzer.get_risk_distribution(portfolio)

    def generate_risk_warnings(self, portfolio: Portfolio) -> list[dict[str, Any]]:
        """生成风险警告（向后兼容）"""
        return self.risk_analyzer.generate_risk_warnings(portfolio)

    def generate_investment_advice(self, portfolio: Portfolio) -> list[str]:
        """生成投资建议（向后兼容）"""
        return self.risk_analyzer.generate_investment_advice(portfolio)

    def generate_comprehensive_evaluation(self, portfolio: Portfolio, sell_records: list[SellRecord] | None = None) -> dict[str, Any]:
        """生成综合评估（向后兼容）"""
        return self.evaluation_analyzer.generate_comprehensive_evaluation(portfolio, sell_records)

    def generate_investment_efficiency(self, portfolio: Portfolio) -> dict[str, Any]:
        """生成投资效率（向后兼容）"""
        return self.evaluation_analyzer.generate_investment_efficiency(portfolio)

    def get_short_term_observation_products(self, portfolio: Portfolio) -> list[dict[str, Any]]:
        """获取短期观察产品（向后兼容）"""
        return self.portfolio_analyzer.get_short_term_observation_products(portfolio)

    def get_high_return_reference_products(self, portfolio: Portfolio) -> list[dict[str, Any]]:
        """获取高收益参考产品（向后兼容）"""
        return self.portfolio_analyzer.get_high_return_reference_products(portfolio)

    def generate_time_group_analysis(self, portfolio: Portfolio) -> dict[str, Any]:
        """生成时间分组分析（向后兼容）"""
        return self._generate_time_group_analysis(portfolio)

    def generate_special_bonds_analysis(self, portfolio: Portfolio) -> list[dict[str, Any]]:
        """生成特别国债分析（向后兼容）"""
        return self.portfolio_analyzer.generate_special_bonds_analysis(portfolio)

    def print_console_report(self, report: dict[str, Any]) -> None:
        """打印控制台报告"""
        self.console_printer.print_report(report)

    def save_csv_report(self, report: dict[str, Any], output_path: Path | None = None) -> Path:
        """保存 CSV 报告"""
        if output_path is None:
            output_path = config.project_root / "output" / "report.csv"
        elif output_path.is_dir():
            output_path = output_path / "report.csv"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["指标", "值"])
            writer.writerow(["生成时间", report.get("generated_at", "")])
            writer.writerow(["数据模式", report.get("data_mode", "")])

            summary = report.get("portfolio_summary", {})
            if summary:
                writer.writerow(["总产品数", summary.get("total_products", 0)])
                writer.writerow(["总金额", summary.get("total_value", "0")])
                writer.writerow(["总收益", summary.get("total_profit", "0")])
                writer.writerow(["收益率", summary.get("return_rate", "0%")])

        return output_path

    def save_json_report(self, report: dict[str, Any], output_path: Path | None = None) -> Path:
        """保存 JSON 报告"""
        if output_path is None:
            output_path = config.project_root / "output" / "report.json"
        elif output_path.is_dir():
            output_path = output_path / "report.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        def decimal_default(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            if isinstance(obj, Path):
                return str(obj)
            if hasattr(obj, "isoformat"):
                return obj.isoformat()
            if hasattr(obj, "__dict__"):
                return obj.__dict__
            return str(obj)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=decimal_default)

        return output_path


report_generator = ReportGenerator()
