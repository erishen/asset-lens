"""
Investment time grouping analysis for asset-lens.
按投资时间分组分析模块
"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List

from ..data.models import InvestmentProduct


@dataclass
class TimeGroupStats:
    """时间分组统计"""

    group_name: str  # 分组名称
    group_description: str  # 分组描述
    products_count: int  # 产品数量
    total_amount: Decimal  # 总金额
    total_initial: Decimal  # 总初始投资
    total_profit: Decimal  # 总收益
    avg_return_rate: Decimal  # 平均收益率
    avg_holding_days: float  # 平均持有天数
    products: List[str]  # 产品名称列表

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "分组名称": self.group_name,
            "分组描述": self.group_description,
            "产品数量": self.products_count,
            "总金额": str(self.total_amount),
            "总初始投资": str(self.total_initial),
            "总收益": str(self.total_profit),
            "平均收益率": f"{self.avg_return_rate:.2f}%",
            "平均持有天数": f"{self.avg_holding_days:.1f}天",
            "产品列表": self.products,
        }


class TimeGroupAnalyzer:
    """时间分组分析器"""

    def analyze_by_holding_period(
        self,
        products: List[InvestmentProduct],
        short_term_days: int = 90,  # 短期：3个月以内
        mid_term_days: int = 365,  # 中期：3个月到1年
    ) -> Dict[str, Any]:
        """
        按持有时间分组分析

        Args:
            products: 产品列表
            short_term_days: 短期天数阈值
            mid_term_days: 中期天数阈值

        Returns:
            按持有时间分组的结果
        """
        today = date.today()

        # 初始化分组
        groups: Dict[str, Dict[str, Any]] = {
            "short_term": {
                "name": "短期投资",
                "description": f"{short_term_days}天以内",
                "products": [],
                "total_amount": Decimal("0"),
                "total_initial": Decimal("0"),
                "total_profit": Decimal("0"),
                "total_days": 0,
            },
            "mid_term": {
                "name": "中期投资",
                "description": f"{short_term_days}天到{mid_term_days}天",
                "products": [],
                "total_amount": Decimal("0"),
                "total_initial": Decimal("0"),
                "total_profit": Decimal("0"),
                "total_days": 0,
            },
            "long_term": {
                "name": "长期投资",
                "description": f"{mid_term_days}天以上",
                "products": [],
                "total_amount": Decimal("0"),
                "total_initial": Decimal("0"),
                "total_profit": Decimal("0"),
                "total_days": 0,
            },
            "unknown": {
                "name": "未知期限",
                "description": "无开始日期",
                "products": [],
                "total_amount": Decimal("0"),
                "total_initial": Decimal("0"),
                "total_profit": Decimal("0"),
                "total_days": 0,
            },
        }

        # 分组统计
        for product in products:
            if not product.current_amount or product.current_amount == 0:
                continue

            # 计算持有天数
            holding_days = 0
            if product.start_date:
                holding_days = (today - product.start_date).days

            # 确定分组
            if holding_days == 0:
                group_key = "unknown"
            elif holding_days <= short_term_days:
                group_key = "short_term"
            elif holding_days <= mid_term_days:
                group_key = "mid_term"
            else:
                group_key = "long_term"

            # 更新分组统计
            groups[group_key]["products"].append(product.name)
            groups[group_key]["total_amount"] += product.current_amount
            groups[group_key]["total_initial"] += product.initial_amount or Decimal("0")
            groups[group_key]["total_profit"] += product.profit_amount or Decimal("0")
            groups[group_key]["total_days"] += holding_days

        # 计算平均收益率和平均持有天数
        result_groups = []
        for group_key, group_data in groups.items():
            if group_data["products"]:
                avg_return_rate = Decimal("0")
                if group_data["total_initial"] > 0:
                    avg_return_rate = (
                        group_data["total_profit"] / group_data["total_initial"] * Decimal("100")
                    )

                avg_holding_days = group_data["total_days"] / len(group_data["products"])

                stats = TimeGroupStats(
                    group_name=group_data["name"],
                    group_description=group_data["description"],
                    products_count=len(group_data["products"]),
                    total_amount=group_data["total_amount"],
                    total_initial=group_data["total_initial"],
                    total_profit=group_data["total_profit"],
                    avg_return_rate=avg_return_rate,
                    avg_holding_days=avg_holding_days,
                    products=group_data["products"],
                )
                result_groups.append(stats)

        # 按总金额排序
        result_groups.sort(key=lambda x: x.total_amount, reverse=True)

        # 计算总体统计
        total_amount = sum(g.total_amount for g in result_groups)
        total_initial = sum(g.total_initial for g in result_groups)
        total_profit = sum(g.total_profit for g in result_groups)
        total_return_rate = (
            (Decimal(str(total_profit)) / Decimal(str(total_initial)) * Decimal("100"))
            if total_initial > 0
            else Decimal("0")
        )

        return {
            "groups": result_groups,
            "total_amount": total_amount,
            "total_initial": total_initial,
            "total_profit": total_profit,
            "total_return_rate": total_return_rate,
            "total_products": sum(g.products_count for g in result_groups),
        }

    def analyze_by_start_year(
        self,
        products: List[InvestmentProduct],
    ) -> Dict[str, Any]:
        """
        按投资起始年份分组分析

        Args:
            products: 产品列表

        Returns:
            按投资起始年份分组的结果
        """
        year_groups: Dict[int, Dict[str, Any]] = {}

        for product in products:
            if not product.current_amount or product.current_amount == 0:
                continue

            # 获取投资年份
            year = product.start_date.year if product.start_date else 0

            if year not in year_groups:
                year_groups[year] = {
                    "year": year,
                    "year_name": str(year) if year > 0 else "未知年份",
                    "products": [],
                    "total_amount": Decimal("0"),
                    "total_initial": Decimal("0"),
                    "total_profit": Decimal("0"),
                    "total_days": 0,
                }

            year_groups[year]["products"].append(product.name)
            year_groups[year]["total_amount"] += product.current_amount
            year_groups[year]["total_initial"] += product.initial_amount or Decimal("0")
            year_groups[year]["total_profit"] += product.profit_amount or Decimal("0")
            year_groups[year]["total_days"] += (
                (date.today() - product.start_date).days if product.start_date else 0
            )

        # 计算平均收益率
        result_groups = []
        for year, group_data in year_groups.items():
            avg_return_rate = Decimal("0")
            if group_data["total_initial"] > 0:
                avg_return_rate = (
                    group_data["total_profit"] / group_data["total_initial"] * Decimal("100")
                )

            avg_holding_days = (
                group_data["total_days"] / len(group_data["products"])
                if group_data["products"]
                else 0
            )

            stats = TimeGroupStats(
                group_name=group_data["year_name"],
                group_description=f"{group_data['year_name']}年开始投资",
                products_count=len(group_data["products"]),
                total_amount=group_data["total_amount"],
                total_initial=group_data["total_initial"],
                total_profit=group_data["total_profit"],
                avg_return_rate=avg_return_rate,
                avg_holding_days=avg_holding_days,
                products=group_data["products"],
            )
            result_groups.append(stats)

        # 按年份排序
        result_groups.sort(key=lambda x: x.group_name, reverse=True)

        return {
            "year_groups": result_groups,
            "total_years": len(result_groups),
        }
