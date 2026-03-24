"""
Evaluation analyzer for asset-lens.
评估分析器 - 包含评估和效率分析方法
"""

from decimal import Decimal
from typing import Any

from ..data.models import Portfolio, SellRecord


class EvaluationAnalyzer:
    """评估分析器"""

    def generate_comprehensive_evaluation(
        self, portfolio: Portfolio, sell_records: list[SellRecord] | None = None
    ) -> dict[str, Any]:
        """生成综合评估"""
        total_value = portfolio.total_value
        total_profit = portfolio.total_profit
        return_rate = portfolio.overall_return_rate or Decimal("0")

        time_weighted_return = self._calculate_time_weighted_return(portfolio)

        evaluation_text = self._get_evaluation_text(return_rate, time_weighted_return)

        return {
            "total_value": str(total_value),
            "total_profit": str(total_profit),
            "return_rate": f"{return_rate:.2f}%",
            "time_weighted_return": f"{time_weighted_return:.2f}%",
            "evaluation": evaluation_text,
            "risk_level": self._get_risk_level(portfolio),
            "diversification_score": self._calculate_diversification_score(portfolio),
        }

    def _calculate_time_weighted_return(self, portfolio: Portfolio) -> Decimal:
        """计算时间加权收益率"""
        if not portfolio.products:
            return Decimal("0")

        total_days = 0
        weighted_return = Decimal("0")

        for product in portfolio.products:
            if product.investment_days and product.annual_return:
                weight = Decimal(str(product.investment_days))
                weighted_return += product.annual_return * weight
                total_days += int(product.investment_days)

        if total_days == 0:
            return Decimal("0")

        return weighted_return / Decimal(str(total_days))

    def _get_evaluation_text(self, return_rate: Decimal | None, time_weighted: Decimal) -> str:
        """获取评估文本"""
        avg_return = ((return_rate or Decimal("0")) + time_weighted) / 2

        if avg_return >= Decimal("10"):
            return "优秀 - 投资组合表现优异，收益远超市场平均水平"
        elif avg_return >= Decimal("5"):
            return "良好 - 投资组合表现良好，收益高于市场平均水平"
        elif avg_return >= Decimal("2"):
            return "一般 - 投资组合表现一般，收益接近市场平均水平"
        elif avg_return >= Decimal("0"):
            return "较差 - 投资组合表现较差，收益低于市场平均水平"
        else:
            return "亏损 - 投资组合处于亏损状态，需要调整策略"

    def _get_risk_level(self, portfolio: Portfolio) -> str:
        """获取风险等级"""
        risk_dist = portfolio.get_risk_distribution()

        high_risk_value = Decimal("0")
        total_value = portfolio.total_value

        if "高" in risk_dist:
            high_risk_value = risk_dist["高"].get("total_value", Decimal("0"))

        if total_value > Decimal("0"):
            high_risk_ratio = high_risk_value / total_value
            if high_risk_ratio > Decimal("0.5"):
                return "高风险"
            elif high_risk_ratio > Decimal("0.3"):
                return "中高风险"
            elif high_risk_ratio > Decimal("0.1"):
                return "中等风险"
            else:
                return "低风险"

        return "未知"

    def _calculate_diversification_score(self, portfolio: Portfolio) -> float:
        """计算分散化评分"""
        type_dist = portfolio.get_type_distribution()

        if not type_dist:
            return 0.0

        num_types = len(type_dist)
        max_score = 100

        if num_types >= 8:
            return max_score
        elif num_types >= 6:
            return max_score * 0.8
        elif num_types >= 4:
            return max_score * 0.6
        elif num_types >= 2:
            return max_score * 0.4
        else:
            return max_score * 0.2

    def generate_investment_efficiency(self, portfolio: Portfolio) -> dict[str, Any]:
        """生成投资效率分析"""
        if not portfolio.products:
            return {
                "average_holding_days": 0,
                "average_return_per_day": "0.00%",
                "efficiency_rating": "无数据",
            }

        total_days = 0
        total_return = Decimal("0")
        product_count = 0

        for product in portfolio.products:
            if product.investment_days and product.return_rate:
                total_days += product.investment_days
                total_return += product.return_rate
                product_count += 1

        if product_count == 0:
            return {
                "average_holding_days": 0,
                "average_return_per_day": "0.00%",
                "efficiency_rating": "无数据",
            }

        avg_days = total_days / product_count
        avg_return = total_return / product_count
        return_per_day = avg_return / Decimal(str(avg_days)) if avg_days > 0 else Decimal("0")

        if return_per_day > Decimal("0.05"):
            rating = "高效"
        elif return_per_day > Decimal("0.02"):
            rating = "中等"
        else:
            rating = "低效"

        return {
            "average_holding_days": round(avg_days),
            "average_return_per_day": f"{return_per_day:.4f}%",
            "efficiency_rating": rating,
        }
