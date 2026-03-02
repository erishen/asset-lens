"""
Sold investment analysis for asset-lens.
已卖出投资分析模块
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List

from ..data.models import SellRecord
from ..data.parser_utils import calculate_return_rate


@dataclass
class SoldInvestmentStats:
    """已卖出投资统计"""

    total_records: int  # 总记录数
    total_initial: Decimal  # 总初始投资
    total_profit: Decimal  # 总收益
    total_return_rate: Decimal  # 总收益率
    positive_count: int  # 正收益数量
    negative_count: int  # 负收益数量
    avg_holding_days: float  # 平均持有天数
    avg_return_rate: Decimal  # 平均收益率

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "总记录数": self.total_records,
            "总初始投资": str(self.total_initial),
            "总收益": str(self.total_profit),
            "总收益率": f"{self.total_return_rate:.2f}%",
            "正收益数量": self.positive_count,
            "负收益数量": self.negative_count,
            "平均持有天数": f"{self.avg_holding_days:.1f}天",
            "平均收益率": f"{self.avg_return_rate:.2f}%",
        }


@dataclass
class SoldInvestmentDetail:
    """已卖出投资明细"""

    name: str  # 产品名称
    sell_date: date  # 卖出日期
    initial_amount: Decimal  # 初始金额
    profit_amount: Decimal  # 收益金额
    return_rate: Decimal  # 收益率
    holding_days: int  # 持有天数
    annualized_return: Decimal  # 年化收益率
    risk_level: str  # 风险等级

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "名称": self.name,
            "卖出日期": self.sell_date.isoformat(),
            "初始金额": str(self.initial_amount),
            "收益金额": str(self.profit_amount),
            "收益率": f"{self.return_rate:.2f}%",
            "持有天数": self.holding_days,
            "年化收益率": f"{self.annualized_return:.2f}%",
            "风险等级": self.risk_level,
        }


class SoldInvestmentAnalyzer:
    """已卖出投资分析器"""

    def analyze_sold_investments(
        self,
        sell_records: List[SellRecord],
    ) -> Dict[str, Any]:
        """
        分析已卖出投资

        Args:
            sell_records: 卖出记录列表

        Returns:
            已卖出投资分析结果
        """
        if not sell_records:
            return {
                "stats": SoldInvestmentStats(
                    total_records=0,
                    total_initial=Decimal("0"),
                    total_profit=Decimal("0"),
                    total_return_rate=Decimal("0"),
                    positive_count=0,
                    negative_count=0,
                    avg_holding_days=0.0,
                    avg_return_rate=Decimal("0"),
                ),
                "details": [],
                "by_type": {},
            }

        # 计算统计数据
        total_initial = Decimal("0")
        total_profit = Decimal("0")
        positive_count = 0
        negative_count = 0
        total_holding_days = 0
        weighted_annualized = Decimal("0")

        details = []

        for record in sell_records:
            initial_amount = record.initial_amount or Decimal("0")
            profit_amount = record.profit_amount or Decimal("0")
            return_rate = record.return_rate or Decimal("0")
            holding_days = record.investment_days or 0

            # 使用CSV中的年化收益率（优先使用复利年化，其次年化收益）
            annualized_return = record.compound_return or record.annual_return or Decimal("0")

            detail = SoldInvestmentDetail(
                name=record.name,
                sell_date=record.sell_date,
                initial_amount=initial_amount,
                profit_amount=profit_amount,
                return_rate=return_rate,
                holding_days=holding_days,
                annualized_return=annualized_return,
                risk_level=record.risk_level.value if record.risk_level else "中",
            )
            details.append(detail)

            # 统计
            total_initial += initial_amount
            total_profit += profit_amount
            total_holding_days += holding_days
            # 加权年化收益率（使用初始金额作为权重）
            weighted_annualized += annualized_return * initial_amount

            if profit_amount > 0:
                positive_count += 1
            elif profit_amount < 0:
                negative_count += 1

        # 计算总体收益率
        total_return_rate_pct = (
            (total_profit / total_initial * Decimal("100")) if total_initial > 0 else Decimal("0")
        )

        # 计算平均值
        avg_holding_days = total_holding_days / len(sell_records) if sell_records else 0.0
        # 加权平均年化收益率
        avg_return_rate = (
            (weighted_annualized / total_initial) if total_initial > 0 else Decimal("0")
        )

        stats = SoldInvestmentStats(
            total_records=len(sell_records),
            total_initial=total_initial,
            total_profit=total_profit,
            total_return_rate=total_return_rate_pct,
            positive_count=positive_count,
            negative_count=negative_count,
            avg_holding_days=avg_holding_days,
            avg_return_rate=avg_return_rate,
        )

        # 按收益率排序
        details.sort(key=lambda x: x.return_rate, reverse=True)

        # 按类型分组统计
        by_type = self._analyze_by_type(details)

        return {
            "stats": stats,
            "details": details,
            "by_type": by_type,
        }

    def _analyze_by_type(
        self,
        details: List[SoldInvestmentDetail],
    ) -> Dict[str, Any]:
        """
        按风险等级分组统计

        Args:
            details: 已卖出投资明细列表

        Returns:
            按风险等级统计的结果
        """
        risk_stats: Dict[str, Dict[str, Any]] = {}

        for detail in details:
            risk_key = detail.risk_level

            if risk_key not in risk_stats:
                risk_stats[risk_key] = {
                    "risk_level": risk_key,
                    "count": 0,
                    "total_initial": Decimal("0"),
                    "total_profit": Decimal("0"),
                    "avg_return_rate": Decimal("0"),
                }

            risk_stats[risk_key]["count"] += 1
            risk_stats[risk_key]["total_initial"] += detail.initial_amount
            risk_stats[risk_key]["total_profit"] += detail.profit_amount

        # 计算平均收益率
        for risk_key, stats in risk_stats.items():
            stats["return_rate"] = calculate_return_rate(stats)

        # 按总初始投资排序
        sorted_stats = sorted(risk_stats.values(), key=lambda x: x["total_initial"], reverse=True)

        return {
            "risk_stats": sorted_stats,
            "total_risk_levels": len(sorted_stats),
        }

    def _analyze_by_holding_period(
        self,
        details: List[SoldInvestmentDetail],
    ) -> Dict[str, Any]:
        """
        按持有时间分组分析

        Args:
            details: 已卖出投资明细列表

        Returns:
            按持有时间分组的结果
        """
        short_term = [d for d in details if d.holding_days < 180]  # 短期 < 6个月
        medium_term = [d for d in details if 180 <= d.holding_days <= 720]  # 中期 6个月-2年
        long_term = [d for d in details if d.holding_days > 720]  # 长期 > 2年

        def calculate_group_stats(group: List[SoldInvestmentDetail]) -> Dict[str, Any]:
            """计算分组统计"""
            if not group:
                return {
                    "count": 0,
                    "total_initial": Decimal("0"),
                    "total_profit": Decimal("0"),
                    "avg_return_rate": Decimal("0"),
                    "avg_holding_days": 0.0,
                }

            total_initial = sum(d.initial_amount for d in group)
            total_profit = sum(d.profit_amount for d in group)
            avg_return_rate = (
                (Decimal(str(total_profit)) / Decimal(str(total_initial)) * Decimal("100"))
                if total_initial > 0
                else Decimal("0")
            )
            avg_holding_days = sum(d.holding_days for d in group) / len(group)

            return {
                "count": len(group),
                "total_initial": total_initial,
                "total_profit": total_profit,
                "avg_return_rate": avg_return_rate,
                "avg_holding_days": avg_holding_days,
            }

        return {
            "短期投资（< 6个月）": calculate_group_stats(short_term),
            "中期投资（6个月-2年）": calculate_group_stats(medium_term),
            "长期投资（> 2年）": calculate_group_stats(long_term),
        }

    def get_top_performers(
        self, details: List[SoldInvestmentDetail], top_n: int = 3
    ) -> List[SoldInvestmentDetail]:
        """
        获取表现最好的产品

        Args:
            details: 已卖出投资明细列表
            top_n: 返回数量

        Returns:
            表现最好的产品列表
        """
        positive = [d for d in details if d.return_rate > 0]
        return sorted(positive, key=lambda x: x.return_rate, reverse=True)[:top_n]

    def get_worst_performers(
        self, details: List[SoldInvestmentDetail], top_n: int = 3
    ) -> List[SoldInvestmentDetail]:
        """
        获取表现最差的产品

        Args:
            details: 已卖出投资明细列表
            top_n: 返回数量

        Returns:
            表现最差的产品列表
        """
        negative = [d for d in details if d.return_rate < 0]
        return sorted(negative, key=lambda x: x.return_rate)[:top_n]
