from decimal import Decimal
from typing import Any

from ..config import config
from ..data.models import Portfolio


class AnalysisWarningsMixin:
    def generate_risk_warnings(self, portfolio: Portfolio) -> list[dict[str, Any]]:
        warnings = []

        low_returns = self.get_low_return_products(portfolio, threshold=config.min_return_threshold)  # type: ignore[attr-defined]
        if low_returns:
            warnings.append(
                {
                    "level": "warning",
                    "type": "low_return",
                    "message": f"发现 {len(low_returns)} 个收益率低于 {config.min_return_threshold}% 的产品（低于银行定期）",
                    "products": low_returns[:5],
                }
            )

        loss_products = [p for p in portfolio.products if p.profit_amount and p.profit_amount < Decimal("0")]
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
            high_risk_ratio = high_risk_stats.get("total_value", Decimal("0")) / portfolio.total_value
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
                            "return": f"{p.annual_return:.2f}%" if p.annual_return is not None else "-",
                        }
                        for p in long_term_low_return[:3]
                    ],
                }
            )

        return warnings

    def generate_optimization_suggestions(self, portfolio: Portfolio) -> list[dict[str, Any]]:
        suggestions = []

        portfolio.get_type_distribution()
        total_value = portfolio.total_value

        low_returns = self.get_low_return_products(portfolio, threshold=2.0)  # type: ignore[attr-defined]
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
                        f"• 可转移的低效资金: {transferable_amount / 10000:.1f}万元",
                        f"• 理论增加年收益: {potential_gain / 10000:.1f}万元",
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
            observe_products = self.get_short_term_observation_products(portfolio)[:7]  # type: ignore[attr-defined]

            details = [f"• 建议赎回的低效产品 ({len(redeem_products)}个):"]
            for i, p in enumerate(redeem_products, 1):
                amount_str = self._format_money_value(p["current_amount"])  # type: ignore[attr-defined]
                name = p["name"][:20] + "..." if len(p["name"]) > 20 else p["name"]
                details.append(f"  {i}. {name} ({amount_str}) - {p['annual_return']}")

            if observe_products:
                details.append(f"\n• 短期观察产品 ({len(observe_products)}个，建议等待至3个月):")
                for i, p in enumerate(observe_products, 1):
                    amount_str = self._format_money_value(p["current_amount"])  # type: ignore[attr-defined]
                    name = p["name"][:20] + "..." if len(p["name"]) > 20 else p["name"]
                    details.append(f"  {i}. ⏳ {name} ({amount_str}) - {p['annual_return']}")

            details.append("")
            details.append("• 将资金转投收益率2.5%以上的产品（如优质债基、混合基金）")

            high_return_ref = self.get_high_return_reference_products(portfolio)  # type: ignore[attr-defined]
            if high_return_ref:
                details.append(f"• 可参考的高收益产品 ({len(high_return_ref)}个):")
                for i, p in enumerate(high_return_ref[:5], 1):
                    amount_str = self._format_money_value(p["current_amount"])  # type: ignore[attr-defined]
                    self._format_money(p["profit_amount"])  # type: ignore[attr-defined]
                    name = p["name"][:20] + "..." if len(p["name"]) > 20 else p["name"]
                    details.append(f"  {i}. {name} ({amount_str}) - {p['annual_return']}")

            suggestions.append(
                {
                    "type": "low_efficiency",
                    "title": "📉 低效产品处理",
                    "details": details,
                }
            )

        short_term_loss = len(self.get_short_term_observation_products(portfolio))  # type: ignore[attr-defined]
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

    def generate_investment_advice(self, portfolio: Portfolio) -> list[str]:
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
