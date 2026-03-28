"""
Return analysis report generator for asset-lens.
收益率分析报告生成模块
"""

import csv
import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..config import config
from ..core.sold_investment import SoldInvestmentAnalyzer, SoldInvestmentStats
from ..core.time_group import TimeGroupAnalyzer
from ..data.models import (
    InvestmentProduct,
    InvestmentType,
    Portfolio,
    RiskLevel,
    SellRecord,
)


class ReportGenerator:
    """报告生成器"""

    def __init__(self):
        """初始化报告生成器"""
        self.report_language = config.report_language
        self.sold_analyzer = SoldInvestmentAnalyzer()
        self.time_analyzer = TimeGroupAnalyzer()

    def generate_analysis_report(
        self,
        portfolio: Portfolio,
        sell_records: List[SellRecord] | None = None,
    ) -> Dict[str, Any]:
        """生成完整的分析报告

        Args:
            portfolio: 投资组合对象
            sell_records: 已卖出记录列表

        Returns:
            包含完整分析报告的字典
        """
        report = {
            "generated_at": datetime.now().isoformat(),
            "data_mode": config.data_mode,
            "exchange_rates": self.get_exchange_rates(),
            "portfolio_summary": self.generate_portfolio_summary(portfolio),
            "top_performers": self.get_top_performers(portfolio, top_n=10),
            "low_returns": self.get_low_return_products(
                portfolio, threshold=config.min_return_threshold
            ),
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
            "comprehensive_evaluation": self.generate_comprehensive_evaluation(
                portfolio, sell_records
            ),
            "investment_efficiency": self.generate_investment_efficiency(portfolio),
        }

        return report

    def get_exchange_rates(self) -> Dict[str, Any]:
        """获取汇率信息

        Returns:
            包含美元和港元汇率的字典
        """
        from ..data.csv_parser import CSVParser

        data_dir = config.get_latest_data_dir()
        usd_rate, hkd_rate = CSVParser.get_exchange_rates(data_dir) if data_dir else (config.default_usd_rate, config.default_hkd_rate)

        return {
            "usd_rate": str(usd_rate),
            "hkd_rate": str(hkd_rate),
            "source": "csv_file" if data_dir else "config",
        }

    def generate_portfolio_summary(self, portfolio: Portfolio) -> Dict[str, Any]:
        """生成投资组合摘要

        Args:
            portfolio: 投资组合对象

        Returns:
            包含投资组合摘要信息的字典
        """
        return {
            "total_products": len(portfolio.products),
            "total_value": str(portfolio.total_value),
            "total_initial": str(portfolio.total_initial),
            "total_profit": str(portfolio.total_profit),
            "overall_return_rate": f"{portfolio.overall_return_rate:.2f}%"
            if portfolio.overall_return_rate
            else "N/A",
            "positive_avg_return": self._calculate_positive_avg_return(portfolio),
        }

    def _calculate_positive_avg_return(self, portfolio: Portfolio) -> str:
        """计算正收益产品的平均收益率

        Args:
            portfolio: 投资组合对象

        Returns:
            平均收益率字符串
        """
        positive_products = [
            p for p in portfolio.products if p.annual_return and p.annual_return > Decimal("0")
        ]
        if not positive_products:
            return "N/A"
        avg_return = Decimal(
            str(sum(p.annual_return for p in positive_products if p.annual_return))
        ) / Decimal(str(len(positive_products)))
        return f"{avg_return:.2f}%"

    def get_top_performers(self, portfolio: Portfolio, top_n: int = 10) -> List[Dict[str, Any]]:
        """获取收益率最高的产品

        Args:
            portfolio: 投资组合对象
            top_n: 返回的产品数量

        Returns:
            按收益率排序的产品列表
        """
        products_with_return = [
            p
            for p in portfolio.products
            if p.annual_return is not None or p.return_rate is not None
        ]

        products_with_return.sort(
            key=lambda p: p.annual_return or p.return_rate or Decimal("0"), reverse=True
        )

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

    def get_low_return_products(
        self, portfolio: Portfolio, threshold: float = 2.0
    ) -> List[Dict[str, Any]]:
        """获取低收益产品列表

        Args:
            portfolio: 投资组合对象
            threshold: 收益率阈值，低于此值的产品将被返回

        Returns:
            低收益产品列表
        """
        low_return_products = [
            p
            for p in portfolio.products
            if p.annual_return is not None and p.annual_return < Decimal(str(threshold))
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

    def get_short_term_observation_products(self, portfolio: Portfolio) -> List[Dict[str, Any]]:
        """获取短期需要观察的产品

        Args:
            portfolio: 投资组合对象

        Returns:
            短期投资且收益偏低的产品列表
        """
        short_term_products = [
            p
            for p in portfolio.products
            if p.investment_days
            and p.investment_days < 90
            and p.annual_return
            and p.annual_return < Decimal("3")
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

    def get_high_return_reference_products(self, portfolio: Portfolio) -> List[Dict[str, Any]]:
        """获取高收益参考产品

        Args:
            portfolio: 投资组合对象

        Returns:
            年化收益率超过10%的产品列表
        """
        high_return_products = [
            p for p in portfolio.products if p.annual_return and p.annual_return > Decimal("10")
        ]

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

    def get_type_distribution(self, portfolio: Portfolio) -> Dict[str, Any]:
        """获取投资类型分布

        Args:
            portfolio: 投资组合对象

        Returns:
            按投资类型分组的统计信息
        """
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

    def get_risk_distribution(self, portfolio: Portfolio) -> Dict[str, Any]:
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

    def generate_time_group_analysis(self, portfolio: Portfolio) -> Dict[str, Any]:
        result = self.time_analyzer.analyze_by_holding_period(portfolio.products)

        groups = []
        for group in result.get("groups", []):
            groups.append(
                {
                    "name": group.group_name,
                    "description": group.group_description,
                    "count": group.products_count,
                    "total_amount": str(group.total_amount),
                    "total_initial": str(group.total_initial),
                    "total_profit": str(group.total_profit),
                    "avg_return_rate": f"{group.avg_return_rate:.2f}%"
                    if group.avg_return_rate
                    else "-",
                    "avg_holding_days": group.avg_holding_days,
                    "products": group.products[:5],
                }
            )

        return {
            "groups": groups,
            "total_products": result.get("total_products", 0),
            "total_amount": str(result.get("total_amount", Decimal("0"))),
            "total_initial": str(result.get("total_initial", Decimal("0"))),
            "total_profit": str(result.get("total_profit", Decimal("0"))),
        }

    def generate_sold_analysis(
        self, sell_records: List[SellRecord] | None = None
    ) -> Optional[Dict[str, Any]]:
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

    def generate_special_bonds_analysis(self, portfolio: Portfolio) -> List[Dict[str, Any]]:
        special_bonds = []
        bond_keywords = ["特别国债", "国债"]

        for product in portfolio.products:
            if any(keyword in product.name for keyword in bond_keywords):
                special_bonds.append(
                    {
                        "name": product.name,
                        "current_amount": str(product.current_amount)
                        if product.current_amount
                        else "-",
                        "initial_amount": str(product.initial_amount)
                        if product.initial_amount
                        else "-",
                        "profit_amount": str(product.profit_amount)
                        if product.profit_amount
                        else "-",
                        "return_rate": f"{product.return_rate:.2f}%"
                        if product.return_rate
                        else "-",
                        "annual_return": f"{product.annual_return:.2f}%"
                        if product.annual_return
                        else "-",
                        "investment_days": product.investment_days or "-",
                    }
                )

        return special_bonds

    def generate_risk_warnings(self, portfolio: Portfolio) -> List[Dict[str, Any]]:
        warnings = []

        low_returns = self.get_low_return_products(portfolio, threshold=config.min_return_threshold)
        if low_returns:
            warnings.append(
                {
                    "level": "warning",
                    "type": "low_return",
                    "message": f"发现 {len(low_returns)} 个收益率低于 {config.min_return_threshold}% 的产品（低于银行定期）",
                    "products": low_returns[:5],
                }
            )

        loss_products = [
            p for p in portfolio.products if p.profit_amount and p.profit_amount < Decimal("0")
        ]
        if loss_products:
            loss_products.sort(key=lambda p: p.profit_amount or Decimal("0"))
            warnings.append(
                {
                    "level": "danger",
                    "type": "loss",
                    "message": f"发现 {len(loss_products)} 个严重亏损产品",
                    "products": [
                        {
                            "name": p.name,
                            "loss": str(abs(p.profit_amount)) if p.profit_amount else None,
                            "return_rate": f"{p.return_rate:.2f}%" if p.return_rate else "-",
                        }
                        for p in loss_products[:5]
                    ],
                }
            )

        risk_dist = portfolio.get_risk_distribution()
        high_risk_stats = risk_dist.get("高", {})
        if high_risk_stats and portfolio.total_value > Decimal("0"):
            high_risk_ratio = (
                high_risk_stats.get("total_value", Decimal("0")) / portfolio.total_value
            )
            if high_risk_ratio > Decimal("0.5"):
                warnings.append(
                    {
                        "level": "warning",
                        "type": "high_risk",
                        "message": f"高风险产品占比过高 ({high_risk_ratio * 100:.1f}%)",
                    }
                )

        long_term_low_return = [
            p
            for p in portfolio.products
            if p.investment_days
            and p.investment_days > 365
            and p.annual_return is not None
            and p.annual_return < Decimal("3")
        ]
        if long_term_low_return:
            warnings.append(
                {
                    "level": "info",
                    "type": "long_term_low_return",
                    "message": f"发现 {len(long_term_low_return)} 个长期投资但收益偏低的产品",
                    "products": [
                        {
                            "name": p.name,
                            "days": p.investment_days,
                            "return": f"{p.annual_return:.2f}%"
                            if p.annual_return is not None
                            else "-",
                        }
                        for p in long_term_low_return[:3]
                    ],
                }
            )

        return warnings

    def generate_optimization_suggestions(self, portfolio: Portfolio) -> List[Dict[str, Any]]:
        suggestions = []

        type_dist = portfolio.get_type_distribution()
        total_value = portfolio.total_value

        low_returns = self.get_low_return_products(portfolio, threshold=2.0)
        transferable_amount = sum(
            float(p.get("current_amount", 0)) for p in low_returns if p.get("status") == "收益过低"
        )
        potential_gain = transferable_amount * 0.03

        if total_value > Decimal("0"):
            suggestions.append(
                {
                    "type": "asset_allocation",
                    "title": "🎯 资产配置优化（适应低利率环境）",
                    "details": [
                        f"• 可转移的低效资金: {transferable_amount/10000:.1f}万元",
                        f"• 理论增加年收益: {potential_gain/10000:.1f}万元",
                        "• 建议配置目标：",
                        "  - 理财产品: 25-30% (保留流动性)",
                        "  - 股票基金: 15-20% (提升收益潜力)",
                        "  - 债券基金: 20-25% (平衡风险收益)",
                        "  - 定投基金: 5-10% (分散时间风险)",
                        "  - 特别国债: 10-15% (稳定收益)",
                        "  - 其他投资: 10-15% (多元化配置)",
                        "",
                        "• 考虑增加指数基金定投，分散时间风险",
                        "• 适当配置REITs、可转债等替代投资",
                    ],
                }
            )

        if low_returns:
            redeem_products = [p for p in low_returns if p.get("status") == "收益过低"][:7]
            observe_products = self.get_short_term_observation_products(portfolio)[:7]

            details = [f"• 建议赎回的低效产品 ({len(redeem_products)}个):"]
            for i, p in enumerate(redeem_products, 1):
                amount_str = self._format_money_value(p["current_amount"])
                name = p["name"][:20] + "..." if len(p["name"]) > 20 else p["name"]
                details.append(f"  {i}. {name} ({amount_str}) - {p['annual_return']}")

            if observe_products:
                details.append(f"\n• 短期观察产品 ({len(observe_products)}个，建议等待至3个月):")
                for i, p in enumerate(observe_products, 1):
                    amount_str = self._format_money_value(p["current_amount"])
                    name = p["name"][:20] + "..." if len(p["name"]) > 20 else p["name"]
                    details.append(f"  {i}. ⏳ {name} ({amount_str}) - {p['annual_return']}")

            details.append("")
            details.append("• 将资金转投收益率2.5%以上的产品（如优质债基、混合基金）")

            high_return_ref = self.get_high_return_reference_products(portfolio)
            if high_return_ref:
                details.append(f"• 可参考的高收益产品 ({len(high_return_ref)}个):")
                for i, p in enumerate(high_return_ref[:5], 1):
                    amount_str = self._format_money_value(p["current_amount"])
                    profit_str = self._format_money(p["profit_amount"])
                    name = p["name"][:20] + "..." if len(p["name"]) > 20 else p["name"]
                    details.append(f"  {i}. {name} ({amount_str}) - {p['annual_return']}")

            suggestions.append(
                {
                    "type": "low_efficiency",
                    "title": "📉 低效产品处理",
                    "details": details,
                }
            )

        short_term_loss = len(self.get_short_term_observation_products(portfolio))
        long_term_low = len(
            [
                p
                for p in low_returns
                if p.get("investment_days")
                and str(p.get("investment_days")).isdigit()
                and int(str(p.get("investment_days", "0"))) > 90
            ]
        )

        suggestions.append(
            {
                "type": "strategy",
                "title": "🔄 投资策略调整",
                "details": [
                    f"• 等待观察：短期亏损产品先观察至3个月 ({short_term_loss}个，避免手续费)",
                    f"• 逐步调整：持有超过3个月的低效产品可安全赎回 ({long_term_low}个)",
                    "• 建立定期调仓机制：每季度评估一次",
                ],
            }
        )

        suggestions.append(
            {
                "type": "implementation",
                "title": "📝 具体实施步骤（优先级排序）",
                "details": [
                    "1️⃣ 立即行动：赎回收益率<1%的理财产品",
                    "2️⃣ 短期行动：将赎回资金的50%转入优质混合基金",
                    "3️⃣ 中期行动：建立指数基金定投计划（每月定投）",
                    "4️⃣ 长期行动：逐步减少理财产品占比至30%以下",
                    "5️⃣ 持续监控：每季度评估资产组合表现并调整",
                ],
            }
        )

        suggestions.append(
            {
                "type": "risk_management",
                "title": "📊 风险管理",
                "details": [
                    "• 单一平台资金不超过总资产的30%",
                    "• 高风险投资不超过总资产的20%",
                    "• 保持3-6个月的流动性储备",
                ],
            }
        )

        return suggestions

    def generate_investment_advice(self, portfolio: Portfolio) -> List[str]:
        advice = []

        if portfolio.overall_return_rate:
            if portfolio.overall_return_rate > Decimal("10"):
                advice.append("✅ 整体投资收益表现优秀！")
            elif portfolio.overall_return_rate > Decimal("5"):
                advice.append("✅ 整体投资收益表现良好，跑赢银行定期")
            elif portfolio.overall_return_rate > Decimal("2"):
                advice.append("ℹ️  整体投资表现尚可，跑赢银行定期")
            else:
                advice.append("⚠️  整体投资收益表现较低，建议检视投资策略")

        if not advice:
            advice.append("✅ 投资组合表现良好，继续保持！")

        return advice

    def generate_comprehensive_evaluation(
        self,
        portfolio: Portfolio,
        sell_records: List[SellRecord] | None = None,
    ) -> Dict[str, Any]:
        total_initial = Decimal("0")
        total_profit = Decimal("0")
        total_value = Decimal("0")

        for product in portfolio.products:
            if not product.start_date:
                continue

            # 计算净投入（使用交易记录）
            net_invest = portfolio._calculate_net_invest(product)

            # 确定使用的初始金额
            if net_invest and net_invest > 0:
                initial = net_invest
            elif product.initial_amount:
                initial = product.initial_amount
            else:
                continue

            # 汇率转换
            if product.investment_type:
                from ..data.models import InvestmentType

                if product.investment_type in [InvestmentType.US_STOCK, InvestmentType.USD_FUND]:
                    rate = product.usd_rate or portfolio.usd_rate
                    initial = initial * rate
                elif product.investment_type in [
                    InvestmentType.HK_STOCK,
                    InvestmentType.HK_CASH,
                    InvestmentType.HK_DIVIDEND_FUND,
                ]:
                    rate = product.hkd_rate or portfolio.hkd_rate
                    initial = initial * rate

            total_initial += initial

            # 计算当前总资产
            if product.current_amount:
                current = product.current_amount
                if product.investment_type:
                    from ..data.models import InvestmentType

                    if product.investment_type in [
                        InvestmentType.US_STOCK,
                        InvestmentType.USD_FUND,
                    ]:
                        current = current * (product.usd_rate or portfolio.usd_rate)
                    elif product.investment_type in [
                        InvestmentType.HK_STOCK,
                        InvestmentType.HK_CASH,
                        InvestmentType.HK_DIVIDEND_FUND,
                    ]:
                        current = current * (product.hkd_rate or portfolio.hkd_rate)
                total_value += current

            # 计算未实现收益
            if product.profit_amount:
                total_profit += product.profit_amount

        realized_profit = Decimal("0")
        realized_initial = Decimal("0")
        if sell_records:
            for record in sell_records:
                if record.profit_amount:
                    realized_profit += record.profit_amount
                if record.initial_amount:
                    realized_initial += record.initial_amount

        unrealized_profit = total_profit

        # 总投入本金（与 ts-demo 一致：使用 initialAmount）
        total_investment = total_initial

        # 总当前金额
        total_current_amount = total_value

        if total_investment > Decimal("0"):
            total_profit_all = unrealized_profit + realized_profit
            overall_return_rate = (total_profit_all / total_investment) * 100
        else:
            overall_return_rate = Decimal("0")

        weighted_annual_return = Decimal("0")
        total_weight = Decimal("0")
        for product in portfolio.products:
            if product.annual_return and product.current_amount:
                weight = product.current_amount
                weighted_annual_return += product.annual_return * weight
                total_weight += weight

        if total_weight > Decimal("0"):
            weighted_annual_return = weighted_annual_return / total_weight
        else:
            weighted_annual_return = Decimal("0")

        avg_investment_days = Decimal("0")
        products_with_days = [p for p in portfolio.products if p.investment_days]
        if products_with_days:
            avg_investment_days = Decimal(
                str(
                    sum(p.investment_days or 0 for p in products_with_days)
                    / len(products_with_days)
                )
            )

        # 时间加权年化收益率（使用复利公式，与 ts-demo 一致）
        if avg_investment_days > Decimal("0") and overall_return_rate > Decimal("0"):
            avg_investment_years = avg_investment_days / Decimal("360")
            if avg_investment_years > Decimal("0"):
                time_weighted_return = (
                    (Decimal("1") + overall_return_rate / Decimal("100"))
                    ** (Decimal("1") / avg_investment_years)
                    - Decimal("1")
                ) * Decimal("100")
            else:
                time_weighted_return = Decimal("0")
        else:
            time_weighted_return = Decimal("0")

        # 计算预期年收益：当前总资产 × 当前年化收益率（最低按2%计算）
        current_annualized_rate = max(weighted_annual_return / Decimal("100"), Decimal("0.02"))
        expected_annual_return = total_value * current_annualized_rate

        return {
            "total_investment": str(total_investment),
            "total_current_amount": str(total_current_amount),
            "realized_profit": str(realized_profit),
            "unrealized_profit": str(unrealized_profit),
            "overall_return_rate": f"{overall_return_rate:.2f}%",
            "weighted_annual_return": f"{weighted_annual_return:.2f}%",
            "time_weighted_return": f"{time_weighted_return:.2f}%",
            "avg_investment_days": round(avg_investment_days, 1),
            "expected_annual_return": str(expected_annual_return),
            "current_annualized_rate": f"{float(current_annualized_rate) * 100:.1f}",
            "evaluation": self._get_evaluation_text(overall_return_rate, time_weighted_return),
        }

    def _get_evaluation_text(self, return_rate: Decimal, time_weighted: Decimal) -> str:
        if return_rate > Decimal("10"):
            return "✅ 整体投资表现优秀，跑赢银行定期"
        elif return_rate > Decimal("5"):
            return "✅ 整体投资表现良好，跑赢银行定期"
        elif return_rate > Decimal("2"):
            advice = "✅ 整体投资表现尚可，跑赢银行定期"
            if time_weighted > Decimal("5"):
                advice += f"\n💡 投资时机把握较好（时间加权年化{time_weighted:.1f}%），建议优化资金配置提升整体收益"
            return advice
        else:
            return "⚠️  整体投资表现较低，建议优化投资策略"

    def generate_investment_efficiency(self, portfolio: Portfolio) -> Dict[str, Any]:
        total_value = portfolio.total_value or Decimal("0")
        total_initial = portfolio.total_initial or Decimal("0")

        if total_initial > Decimal("0"):
            capital_efficiency = (total_value / total_initial) * 100
        else:
            capital_efficiency = Decimal("100")

        avg_investment_days = Decimal("0")
        products_with_days = [p for p in portfolio.products if p.investment_days]
        if products_with_days:
            avg_investment_days = Decimal(
                str(
                    sum(p.investment_days or 0 for p in products_with_days)
                    / len(products_with_days)
                )
            )

        if avg_investment_days > Decimal("0") and portfolio.overall_return_rate:
            annual_growth_rate = portfolio.overall_return_rate * (
                Decimal("365") / avg_investment_days
            )
        else:
            annual_growth_rate = Decimal("0")

        return {
            "capital_efficiency": f"{capital_efficiency:.1f}%",
            "annual_growth_rate": f"{annual_growth_rate:.2f}%",
            "avg_investment_years": float(avg_investment_days / Decimal("365"))
            if avg_investment_days
            else 0,
        }

    def print_console_report(self, report: Dict[str, Any]) -> None:
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
        console.print(f"\n[bold]💵 汇率信息:[/bold]")
        console.print(f"   美元汇率: [cyan]{exchange_rates.get('usd_rate', '-')}[/cyan] CNY/USD")
        console.print(f"   港元汇率: [cyan]{exchange_rates.get('hkd_rate', '-')}[/cyan] CNY/HKD")

        sold_analysis = report.get("sold_investment_analysis")
        if sold_analysis:
            console.print(f"\n[bold green]📊 已实现收益分析[/bold green]")

            sold_table = Table(show_header=False, box=None)
            sold_table.add_column("指标", style="bold", no_wrap=True)
            sold_table.add_column("值", style="cyan", no_wrap=True)
            sold_table.add_row("总投入", f"{self._format_money(sold_analysis['total_initial'])}元")
            sold_table.add_row(
                "已实现收益", f"[green]+{self._format_money(sold_analysis['total_profit'])}元[/green]"
            )
            sold_table.add_row("实现收益率", f"[green]{sold_analysis['total_return_rate']}[/green]")
            sold_table.add_row("平均年化收益率", f"[yellow]{sold_analysis['avg_return_rate']}[/yellow]")
            console.print(sold_table)

            console.print(f"\n[dim]📊 收益率说明：")
            console.print("[dim]• 已实现收益率：卖出记录中的收益率，包含所有卖出部分的总收益")
            console.print("[dim]• 年化收益率：直接从CSV读取预计算的年化数据（包含年化收益和复利年化）")
            console.print("[dim]  注意：卖出记录的年化收益率为CSV中预先计算的数据，未使用IRR计算")
            console.print("[dim]  对于有多次交易记录的产品，当前年化收益可能与实际IRR存在差异[/dim]")

            if sold_analysis.get("top_performers"):
                console.print(f"\n[bold green]表现最好的已卖出产品:[/bold green]")
                for i, p in enumerate(sold_analysis["top_performers"][:3], 1):
                    console.print(
                        f"  [green]{i}. {p['name']}: {p['return_rate']} ({p['holding_days']}天)[/green]"
                    )

            if sold_analysis.get("worst_performers"):
                console.print(f"\n[bold red]亏损产品:[/bold red]")
                for i, p in enumerate(sold_analysis["worst_performers"][:10], 1):
                    console.print(
                        f"  [red]{i}. {p['name']}: {p['return_rate']} ({p['holding_days']}天)[/red]"
                    )

        time_analysis = report.get("time_group_analysis", {})
        if time_analysis.get("groups"):
            console.print(f"\n[bold blue]📅 按投资时间分组分析:[/bold blue]")

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

            console.print(f"\n[dim]🎯 时间分组总结:")
            console.print("[dim]• 短期投资偏好快速获利，但收益可能不够稳定")
            console.print("[dim]• 中期投资平衡了收益和风险，是较好的投资周期")
            console.print("[dim]• 长期投资收益偏低，建议: 优化投资策略[/dim]")

        console.print(f"\n[bold blue]💼 当前持有投资分析[/bold blue]")
        summary = report["portfolio_summary"]

        portfolio_table = Table(show_header=False, box=None)
        portfolio_table.add_column("指标", style="bold")
        portfolio_table.add_column("值", style="cyan")
        portfolio_table.add_row("当前总资产", f"{self._format_money(summary['total_value'])}元")
        portfolio_table.add_row("总投入资金", f"{self._format_money(summary['total_initial'])}元")
        portfolio_table.add_row(
            "未实现收益", f"[green]+{self._format_money(summary['total_profit'])}元[/green]"
        )
        portfolio_table.add_row("整体收益率", f"[green]{summary['overall_return_rate']}[/green]")
        portfolio_table.add_row("有效投资收益率", f"[green]{summary['overall_return_rate']}[/green]")
        portfolio_table.add_row(
            "正收益产品平均年化收益率", f"[yellow]{summary.get('positive_avg_return', 'N/A')}[/yellow]"
        )
        console.print(portfolio_table)

        console.print(f"\n[bold]投资类型分布:[/bold]")
        type_table = Table(show_header=True, header_style="bold cyan", box=None)
        type_table.add_column("类型", style="cyan")
        type_table.add_column("占比", justify="right")
        type_table.add_column("金额", justify="right")
        for type_name, stats in report["type_distribution"].items():
            type_table.add_row(
                type_name, stats["percentage"], f"{self._format_money(stats['total_value'])}元"
            )
        console.print(type_table)

        special_bonds = report.get("special_bonds", [])
        if special_bonds:
            console.print(f"\n[bold yellow]📄 特别国债计算明细[/bold yellow]")
            for i, bond in enumerate(special_bonds, 1):
                console.print(f"  [yellow]{i}. {bond['name']}[/yellow]")
                console.print(f"     当前持仓: {self._format_money(bond['current_amount'])}元")
                console.print(
                    f"     未实现收益: [green]{self._format_money(bond['profit_amount'])}元[/green]"
                )
                console.print(f"     年化: {bond['annual_return']} ({bond['investment_days']}天)")

        console.print(f"\n[bold]🎯 风险等级分布[/bold]")
        risk_table = Table(show_header=True, header_style="bold magenta", box=None)
        risk_table.add_column("风险等级", style="magenta")
        risk_table.add_column("占比", justify="right")
        risk_table.add_column("金额", justify="right")
        for risk_name, stats in report["risk_distribution"].items():
            risk_table.add_row(
                risk_name, stats["percentage"], f"{self._format_money(stats['total_value'])}元"
            )
        console.print(risk_table)

        risk_warnings = report.get("risk_warnings", [])
        if risk_warnings:
            console.print(f"\n[bold red]⚠️  风险提示[/bold red]")
            for warning in risk_warnings:
                console.print(f"[red]• {warning['message']}[/red]")
                if warning.get("products"):
                    for p in warning["products"][:5]:
                        if isinstance(p, dict):
                            name = p.get("name", "未知")
                            # 根据不同类型的警告显示不同的信息
                            if "return_rate" in p:
                                value = p.get("return_rate", "-")
                                console.print(f"  [red]- {name}: {value}[/red]")
                            elif "loss" in p:
                                loss = p.get("loss", "-")
                                return_rate = p.get("return_rate", "-")
                                console.print(
                                    f"  [red]- {name}: 亏损 {loss}元, 收益率 {return_rate}[/red]"
                                )
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
            console.print(f"\n[bold green]💡 优化建议[/bold green]")
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
            console.print(f"\n[bold magenta]🎉 综合评价[/bold magenta]")

            eval_table = Table(show_header=False, box=None)
            eval_table.add_column("指标", style="bold")
            eval_table.add_column("值", style="cyan")
            eval_table.add_row(
                "总当前金额", f"{self._format_money(evaluation['total_current_amount'])}元"
            )
            eval_table.add_row("总投入本金", f"{self._format_money(evaluation['total_investment'])}元")
            eval_table.add_row(
                "已实现收益", f"[green]+{self._format_money(evaluation['realized_profit'])}元[/green]"
            )
            eval_table.add_row(
                "未实现收益", f"[green]+{self._format_money(evaluation['unrealized_profit'])}元[/green]"
            )
            eval_table.add_row(
                "整体收益率", f"[green]+{evaluation['overall_return_rate']}[/green] (累计总收益率)"
            )
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
            console.print(f"\n[bold blue]📈 投资效率分析:[/bold blue]")
            console.print(f"• 当前资金增值效率: [cyan]{efficiency['capital_efficiency']}[/cyan]")
            console.print(f"• 年化资金增长率: [cyan]{efficiency['annual_growth_rate']}[/cyan]")

        print("\n" + "=" * 60)

    def _format_money_value(self, value: str) -> str:
        try:
            amount = float(value)
            return f"{amount/10000:.2f}万"
        except:
            return value

    def _format_money(self, value: str) -> str:
        try:
            amount = float(value)
            if amount >= 10000:
                return f"{amount/10000:.2f}万"
            else:
                return f"{amount:,.0f}"
        except:
            return value

    def save_csv_report(self, report: Dict[str, Any], output_path: Path | None) -> Path | None:
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

        print(f"\n✅ CSV 报告已保存: {file_path}")
        return file_path

    def save_json_report(self, report: Dict[str, Any], output_path: Path | None = None) -> Path:
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

        print(f"✅ JSON 报告已保存: {file_path}")
        return file_path


report_generator = ReportGenerator()
