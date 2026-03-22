"""
Comparison analysis for asset-lens.
对比分析模块
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from ..data.models import InvestmentProduct
from ..data.parser_utils import calculate_return_rate


@dataclass
class ComparisonResult:
    """对比结果"""

    name: str  # 产品名称
    type: str  # 产品类型
    amount_before: Decimal  # 之前金额
    amount_after: Decimal  # 之后金额
    amount_change: Decimal  # 金额变化
    return_rate: Decimal  # 收益率
    investment_days: int  # 投资天数
    annualized_return: Decimal  # 年化收益率

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "名称": self.name,
            "类型": self.type,
            "之前金额": str(self.amount_before),
            "之后金额": str(self.amount_after),
            "金额变化": str(self.amount_change),
            "收益率": f"{self.return_rate:.2f}%",
            "投资天数": self.investment_days,
            "年化收益率": f"{self.annualized_return:.2f}%",
        }


@dataclass
class TrendAnalysis:
    """趋势分析"""

    period: str  # 分析周期
    total_amount_before: Decimal  # 之前总金额
    total_amount_after: Decimal  # 之后总金额
    total_change: Decimal  # 总变化
    total_return_rate: Decimal  # 总收益率
    products_count: int  # 产品数量
    positive_count: int  # 正收益产品数
    negative_count: int  # 负收益产品数

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "分析周期": self.period,
            "之前总金额": str(self.total_amount_before),
            "之后总金额": str(self.total_amount_after),
            "总变化": str(self.total_change),
            "总收益率": f"{self.total_return_rate:.2f}%",
            "产品数量": self.products_count,
            "正收益产品数": self.positive_count,
            "负收益产品数": self.negative_count,
        }


class ComparisonAnalyzer:
    """对比分析器"""

    def compare_periods(
        self,
        products_before: list[InvestmentProduct],
        products_after: list[InvestmentProduct],
        period: str = "自定义对比",
    ) -> dict[str, Any]:
        """
        对比两个时期的投资组合

        Args:
            products_before: 之前的产品列表
            products_after: 之后的产品列表
            period: 分析周期描述

        Returns:
            对比分析结果
        """
        # 创建产品名称到产品的映射
        before_map = {p.name: p for p in products_before if p.name}
        after_map = {p.name: p for p in products_after if p.name}

        # 找出所有产品名称
        all_names = set(before_map.keys()) | set(after_map.keys())

        # 计算每个产品的变化
        results = []
        total_amount_before = Decimal("0")
        total_amount_after = Decimal("0")
        positive_count = 0
        negative_count = 0

        for name in all_names:
            product_before = before_map.get(name)
            product_after = after_map.get(name)

            # 获取金额
            amount_before = (
                product_before.current_amount
                if product_before and product_before.current_amount
                else Decimal("0")
            )
            amount_after = (
                product_after.current_amount
                if product_after and product_after.current_amount
                else Decimal("0")
            )

            # 计算变化
            amount_change = amount_after - amount_before
            return_rate = (
                (amount_change / amount_before * Decimal("100"))
                if amount_before != 0
                else Decimal("0")
            )

            # 计算投资天数
            investment_days = 0
            if product_after and product_after.start_date:
                investment_days = (date.today() - product_after.start_date).days
            elif product_before and product_before.start_date:
                investment_days = (date.today() - product_before.start_date).days

            # 计算年化收益率
            annualized_return = Decimal("0")
            if investment_days > 0 and amount_before != 0:
                annualized_return = return_rate * Decimal("365") / Decimal(str(investment_days))

            # 获取产品类型
            product_type = "其他"
            if product_after and product_after.investment_type:
                product_type = product_after.investment_type.value
            elif product_before and product_before.investment_type:
                product_type = product_before.investment_type.value

            result = ComparisonResult(
                name=name,
                type=product_type,
                amount_before=amount_before,
                amount_after=amount_after,
                amount_change=amount_change,
                return_rate=return_rate,
                investment_days=investment_days,
                annualized_return=annualized_return,
            )
            results.append(result)

            # 统计
            total_amount_before += amount_before
            total_amount_after += amount_after
            if amount_change > 0:
                positive_count += 1
            elif amount_change < 0:
                negative_count += 1

        # 按收益率排序
        results.sort(key=lambda x: x.return_rate, reverse=True)

        # 计算总体趋势
        total_change = total_amount_after - total_amount_before
        total_return_rate = (
            (total_change / total_amount_before * Decimal("100"))
            if total_amount_before != 0
            else Decimal("0")
        )

        trend = TrendAnalysis(
            period=period,
            total_amount_before=total_amount_before,
            total_amount_after=total_amount_after,
            total_change=total_change,
            total_return_rate=total_return_rate,
            products_count=len(results),
            positive_count=positive_count,
            negative_count=negative_count,
        )

        return {
            "trend": trend,
            "details": results,
        }

    def analyze_by_type(
        self,
        products: list[InvestmentProduct],
    ) -> dict[str, Any]:
        """
        按投资类型统计分析

        Args:
            products: 产品列表

        Returns:
            按类型统计的结果
        """
        type_stats: dict[str, dict[str, Any]] = {}

        for product in products:
            if not product.current_amount or product.current_amount == 0:
                continue

            type_key = product.investment_type.value if product.investment_type else "其他"

            if type_key not in type_stats:
                type_stats[type_key] = {
                    "type": type_key,
                    "count": 0,
                    "total_amount": Decimal("0"),
                    "total_initial": Decimal("0"),
                    "total_profit": Decimal("0"),
                    "products": [],
                }

            type_stats[type_key]["count"] += 1
            type_stats[type_key]["total_amount"] += product.current_amount
            type_stats[type_key]["total_initial"] += product.initial_amount or Decimal("0")
            type_stats[type_key]["total_profit"] += product.profit_amount or Decimal("0")
            type_stats[type_key]["products"].append(product.name)

        # 计算收益率
        for type_key, stats in type_stats.items():
            stats["return_rate"] = calculate_return_rate(stats)

        # 按总金额排序
        sorted_stats = sorted(type_stats.values(), key=lambda x: x["total_amount"], reverse=True)

        return {
            "type_stats": sorted_stats,
            "total_types": len(sorted_stats),
        }

    def analyze_fund_flow(
        self,
        products: list[InvestmentProduct],
    ) -> dict[str, Any]:
        """
        分析资金流动

        Args:
            products: 产品列表

        Returns:
            资金流动分析结果
        """
        total_amount = Decimal("0")
        total_initial = Decimal("0")
        total_profit = Decimal("0")

        inflow = Decimal("0")  # 流入资金
        outflow = Decimal("0")  # 流出资金

        for product in products:
            if not product.current_amount or product.current_amount == 0:
                continue

            total_amount += product.current_amount
            total_initial += product.initial_amount or Decimal("0")
            total_profit += product.profit_amount or Decimal("0")

            # 判断资金流向
            if product.profit_amount and product.profit_amount > 0:
                inflow += product.profit_amount
            elif product.profit_amount and product.profit_amount < 0:
                outflow += abs(product.profit_amount)

        net_flow = inflow - outflow

        return {
            "total_amount": total_amount,
            "total_initial": total_initial,
            "total_profit": total_profit,
            "inflow": inflow,
            "outflow": outflow,
            "net_flow": net_flow,
            "inflow_rate": (inflow / total_initial * Decimal("100"))
            if total_initial > 0
            else Decimal("0"),
            "outflow_rate": (outflow / total_initial * Decimal("100"))
            if total_initial > 0
            else Decimal("0"),
        }

    def generate_comparison_report(
        self,
        products_before: list[InvestmentProduct],
        products_after: list[InvestmentProduct],
        period: str = "自定义对比",
    ) -> dict[str, Any]:
        """
        生成完整的对比报告

        Args:
            products_before: 之前的产品列表
            products_after: 之后的产品列表
            period: 分析周期描述

        Returns:
            完整的对比分析结果
        """
        # 基础对比
        comparison = self.compare_periods(products_before, products_after, period)

        # 分类统计
        improving = [r for r in comparison["details"] if r.return_rate > Decimal("0.5")]
        deteriorating = [r for r in comparison["details"] if r.return_rate < Decimal("-0.5")]
        stable = [r for r in comparison["details"] if abs(r.return_rate) <= Decimal("0.5")]

        # 新增和卖出产品
        new_products = [r for r in comparison["details"] if r.amount_before == 0]
        sold_products = [r for r in comparison["details"] if r.amount_after == 0]

        # 按类型统计
        type_analysis = self.analyze_by_type(products_after)

        # 资金流动分析
        fund_flow = self.analyze_fund_flow(products_after)

        # 计算上涨和下跌比例
        total_count = len(comparison["details"])
        improving_count = len(improving)
        deteriorating_count = len(deteriorating)

        improving_rate = (
            (Decimal(str(improving_count)) / Decimal(str(total_count)) * Decimal("100"))
            if total_count > 0
            else Decimal("0")
        )
        deteriorating_rate = (
            (Decimal(str(deteriorating_count)) / Decimal(str(total_count)) * Decimal("100"))
            if total_count > 0
            else Decimal("0")
        )

        return {
            "comparison": comparison,
            "improving": improving,
            "deteriorating": deteriorating,
            "stable": stable,
            "new_products": new_products,
            "sold_products": sold_products,
            "type_analysis": type_analysis,
            "fund_flow": fund_flow,
            "improving_rate": improving_rate,
            "deteriorating_rate": deteriorating_rate,
        }

    def generate_trend_chart(self, value: Decimal, max_value: Decimal, width: int = 20) -> str:
        """
        生成ASCII趋势图表

        Args:
            value: 当前值
            max_value: 最大值
            width: 图表宽度

        Returns:
            ASCII图表字符串
        """
        if max_value == 0:
            return ""

        bars = int((abs(value) / max_value) * width)
        bar_char = "█" if value >= 0 else "░"
        direction = "→" if value >= 0 else "←"
        return f"{direction} {bar_char * bars}"
