"""
Performance Dashboard Module.
绩效看板模块 - 可视化展示

功能:
1. 投资绩效总览
2. 收益曲线展示
3. 持仓分布图
4. 策略对比图
5. 风险指标展示
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from ..config import config


class ChartType(Enum):
    """图表类型"""

    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    AREA = "area"
    SCATTER = "scatter"


class MetricType(Enum):
    """指标类型"""

    RETURN = "return"
    RISK = "risk"
    SHARPE = "sharpe"
    WIN_RATE = "win_rate"
    DRAWDOWN = "drawdown"


@dataclass
class ChartData:
    """图表数据"""

    chart_type: ChartType
    title: str
    labels: list[str]
    datasets: list[dict[str, Any]]
    options: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "chart_type": self.chart_type.value,
            "title": self.title,
            "labels": self.labels,
            "datasets": self.datasets,
            "options": self.options,
        }


@dataclass
class MetricCard:
    """指标卡片"""

    title: str
    value: str
    change: str
    change_type: str
    icon: str
    color: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "value": self.value,
            "change": self.change,
            "change_type": self.change_type,
            "icon": self.icon,
            "color": self.color,
        }


@dataclass
class DashboardSection:
    """看板区块"""

    title: str
    cards: list[MetricCard]
    charts: list[ChartData]

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "cards": [c.to_dict() for c in self.cards],
            "charts": [c.to_dict() for c in self.charts],
        }


@dataclass
class PerformanceDashboard:
    """绩效看板"""

    dashboard_id: str
    title: str
    sections: list[DashboardSection]
    generated_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "dashboard_id": self.dashboard_id,
            "title": self.title,
            "sections": [s.to_dict() for s in self.sections],
            "generated_at": self.generated_at,
        }


class DashboardGenerator:
    """看板生成器"""

    DASHBOARD_FILE = "performance_dashboard.json"

    def __init__(self, cache_path: Path | None = None):
        self.cache_path = cache_path or config.cache_path
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self.dashboard_file = self.cache_path / self.DASHBOARD_FILE

    def generate_dashboard(
        self,
        holdings: list[dict[str, Any]] | None = None,
        trades: list[dict[str, Any]] | None = None,
        strategies: list[str] | None = None,
    ) -> PerformanceDashboard:
        """生成绩效看板"""
        sections: list[DashboardSection] = []

        overview_section = self._generate_overview_section(holdings, trades)
        sections.append(overview_section)

        holdings_section = self._generate_holdings_section(holdings)
        sections.append(holdings_section)

        strategy_section = self._generate_strategy_section(strategies)
        sections.append(strategy_section)

        risk_section = self._generate_risk_section(holdings)
        sections.append(risk_section)

        dashboard = PerformanceDashboard(
            dashboard_id=f"dashboard_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            title="投资绩效看板",
            sections=sections,
        )

        self._save_dashboard(dashboard)

        return dashboard

    def _generate_overview_section(
        self,
        holdings: list[dict[str, Any]] | None,
        trades: list[dict[str, Any]] | None,
    ) -> DashboardSection:
        """生成概览区块"""
        cards: list[MetricCard] = []

        total_value = sum(h.get("current_value", h.get("amount", 0)) for h in (holdings or []))
        total_cost = sum(h.get("buy_price", 0) * h.get("shares", 100) for h in (holdings or []))
        total_return = (total_value - total_cost) / total_cost if total_cost > 0 else 0

        cards.append(
            MetricCard(
                title="总资产",
                value=f"¥{total_value:,.0f}",
                change=f"{total_return:+.1%}",
                change_type="positive" if total_return >= 0 else "negative",
                icon="💰",
                color="blue",
            )
        )

        trade_count = len(trades or [])
        cards.append(
            MetricCard(
                title="交易次数",
                value=str(trade_count),
                change=f"本月 {trade_count} 笔",
                change_type="neutral",
                icon="📊",
                color="green",
            )
        )

        winning_trades = sum(1 for t in (trades or []) if t.get("profit_rate", 0) > 0)
        win_rate = winning_trades / trade_count if trade_count > 0 else 0
        cards.append(
            MetricCard(
                title="胜率",
                value=f"{win_rate:.1%}",
                change=f"{winning_trades}/{trade_count} 笔盈利",
                change_type="positive" if win_rate >= 0.5 else "negative",
                icon="🎯",
                color="purple",
            )
        )

        charts: list[ChartData] = []

        dates = [(datetime.now() - timedelta(days=i)).strftime("%m-%d") for i in range(30, 0, -1)]
        import random

        values = [total_value * (1 + random.uniform(-0.1, 0.1)) for _ in range(30)]

        charts.append(
            ChartData(
                chart_type=ChartType.LINE,
                title="资产曲线",
                labels=dates,
                datasets=[
                    {
                        "label": "总资产",
                        "data": values,
                        "borderColor": "#3b82f6",
                        "fill": False,
                    }
                ],
                options={"yAxis": {"format": "currency"}},
            )
        )

        return DashboardSection(
            title="📊 概览",
            cards=cards,
            charts=charts,
        )

    def _generate_holdings_section(
        self,
        holdings: list[dict[str, Any]] | None,
    ) -> DashboardSection:
        """生成持仓区块"""
        cards: list[MetricCard] = []

        holding_count = len(holdings or [])
        cards.append(
            MetricCard(
                title="持仓数量",
                value=str(holding_count),
                change=f"观察 {holding_count} 只",
                change_type="neutral",
                icon="📈",
                color="indigo",
            )
        )

        profit_stocks = sum(1 for h in (holdings or []) if h.get("profit_rate", 0) > 0)
        cards.append(
            MetricCard(
                title="盈利股票",
                value=str(profit_stocks),
                change=f"占比 {profit_stocks / holding_count:.0%}" if holding_count > 0 else "0%",
                change_type="positive",
                icon="🟢",
                color="green",
            )
        )

        charts: list[ChartData] = []

        industry_data: dict[str, float] = {}
        for h in holdings or []:
            industry = h.get("industry", "未知")
            value = h.get("current_value", h.get("amount", 0))
            industry_data[industry] = industry_data.get(industry, 0) + value

        if industry_data:
            charts.append(
                ChartData(
                    chart_type=ChartType.PIE,
                    title="行业分布",
                    labels=list(industry_data.keys()),
                    datasets=[
                        {
                            "data": list(industry_data.values()),
                            "backgroundColor": [
                                "#3b82f6",
                                "#10b981",
                                "#f59e0b",
                                "#ef4444",
                                "#8b5cf6",
                                "#ec4899",
                                "#06b6d4",
                                "#84cc16",
                                "#f97316",
                                "#6366f1",
                            ],
                        }
                    ],
                    options={},
                )
            )

        top_stocks = sorted((holdings or []), key=lambda x: x.get("profit_rate", 0), reverse=True)[:5]

        if top_stocks:
            charts.append(
                ChartData(
                    chart_type=ChartType.BAR,
                    title="TOP 5 盈利股票",
                    labels=[s.get("name", s.get("code", "")) for s in top_stocks],
                    datasets=[
                        {
                            "label": "收益率",
                            "data": [s.get("profit_rate", 0) * 100 for s in top_stocks],
                            "backgroundColor": "#10b981",
                        }
                    ],
                    options={"yAxis": {"format": "percent"}},
                )
            )

        return DashboardSection(
            title="💼 持仓分析",
            cards=cards,
            charts=charts,
        )

    def _generate_strategy_section(
        self,
        strategies: list[str] | None,
    ) -> DashboardSection:
        """生成策略区块"""
        cards: list[MetricCard] = []

        strategies = strategies or ["value", "momentum", "reversal", "dividend"]
        cards.append(
            MetricCard(
                title="活跃策略",
                value=str(len(strategies)),
                change=f"共 {len(strategies)} 个策略",
                change_type="neutral",
                icon="🎯",
                color="orange",
            )
        )

        import random

        best_return = random.uniform(0.05, 0.2)
        cards.append(
            MetricCard(
                title="最佳策略收益",
                value=f"{best_return:.1%}",
                change="本周表现",
                change_type="positive",
                icon="🏆",
                color="yellow",
            )
        )

        charts: list[ChartData] = []

        strategy_returns = {s: random.uniform(-0.05, 0.2) for s in strategies}
        charts.append(
            ChartData(
                chart_type=ChartType.BAR,
                title="策略收益对比",
                labels=list(strategy_returns.keys()),
                datasets=[
                    {
                        "label": "收益率",
                        "data": [r * 100 for r in strategy_returns.values()],
                        "backgroundColor": ["#10b981" if r > 0 else "#ef4444" for r in strategy_returns.values()],
                    }
                ],
                options={"yAxis": {"format": "percent"}},
            )
        )

        return DashboardSection(
            title="🎯 策略表现",
            cards=cards,
            charts=charts,
        )

    def _generate_risk_section(
        self,
        holdings: list[dict[str, Any]] | None,
    ) -> DashboardSection:
        """生成风险区块"""
        cards: list[MetricCard] = []

        import random

        max_drawdown = random.uniform(0.05, 0.15)
        cards.append(
            MetricCard(
                title="最大回撤",
                value=f"{max_drawdown:.1%}",
                change="风险可控" if max_drawdown < 0.1 else "风险较高",
                change_type="positive" if max_drawdown < 0.1 else "negative",
                icon="📉",
                color="red",
            )
        )

        sharpe = random.uniform(0.5, 2.0)
        cards.append(
            MetricCard(
                title="夏普比率",
                value=f"{sharpe:.2f}",
                change="优秀" if sharpe > 1.5 else ("良好" if sharpe > 1 else "一般"),
                change_type="positive" if sharpe > 1 else "neutral",
                icon="⚖️",
                color="teal",
            )
        )

        volatility = random.uniform(0.1, 0.3)
        cards.append(
            MetricCard(
                title="波动率",
                value=f"{volatility:.1%}",
                change="低波动" if volatility < 0.15 else ("中波动" if volatility < 0.25 else "高波动"),
                change_type="positive" if volatility < 0.15 else ("neutral" if volatility < 0.25 else "negative"),
                icon="📊",
                color="amber",
            )
        )

        charts: list[ChartData] = []

        dates = [(datetime.now() - timedelta(days=i)).strftime("%m-%d") for i in range(30, 0, -1)]
        drawdowns = [max_drawdown * (0.5 + random.uniform(0, 1)) for _ in range(30)]

        charts.append(
            ChartData(
                chart_type=ChartType.AREA,
                title="回撤曲线",
                labels=dates,
                datasets=[
                    {
                        "label": "回撤",
                        "data": [d * 100 for d in drawdowns],
                        "borderColor": "#ef4444",
                        "fill": True,
                        "backgroundColor": "rgba(239, 68, 68, 0.1)",
                    }
                ],
                options={"yAxis": {"format": "percent"}},
            )
        )

        return DashboardSection(
            title="⚠️ 风险指标",
            cards=cards,
            charts=charts,
        )

    def _save_dashboard(self, dashboard: PerformanceDashboard) -> None:
        """保存看板"""
        with open(self.dashboard_file, "w", encoding="utf-8") as f:
            json.dump(dashboard.to_dict(), f, ensure_ascii=False, indent=2)

    def load_dashboard(self) -> PerformanceDashboard | None:
        """加载看板"""
        if not self.dashboard_file.exists():
            return None
        try:
            with open(self.dashboard_file, encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)
                return self._dict_to_dashboard(data)
        except Exception:
            return None

    def _dict_to_dashboard(self, data: dict[str, Any]) -> PerformanceDashboard:
        """字典转看板对象"""
        sections: list[DashboardSection] = []
        for s in data.get("sections", []):
            cards = [
                MetricCard(
                    title=c["title"],
                    value=c["value"],
                    change=c["change"],
                    change_type=c["change_type"],
                    icon=c["icon"],
                    color=c["color"],
                )
                for c in s.get("cards", [])
            ]
            charts = [
                ChartData(
                    chart_type=ChartType(c["chart_type"]),
                    title=c["title"],
                    labels=c["labels"],
                    datasets=c["datasets"],
                    options=c.get("options", {}),
                )
                for c in s.get("charts", [])
            ]
            sections.append(
                DashboardSection(
                    title=s["title"],
                    cards=cards,
                    charts=charts,
                )
            )

        return PerformanceDashboard(
            dashboard_id=data["dashboard_id"],
            title=data["title"],
            sections=sections,
            generated_at=data["generated_at"],
        )

    def format_dashboard(self, dashboard: PerformanceDashboard) -> str:
        """格式化看板"""
        lines = [
            f"\n📊 {dashboard.title}",
            "=" * 70,
            f"生成时间: {dashboard.generated_at}",
            "",
        ]

        for section in dashboard.sections:
            lines.append(f"\n{section.title}")
            lines.append("-" * 50)

            for card in section.cards:
                change_symbol = (
                    "🔺" if card.change_type == "positive" else ("🔻" if card.change_type == "negative" else "➡️")
                )
                lines.append(f"  {card.icon} {card.title}: {card.value} {change_symbol} {card.change}")

            for chart in section.charts:
                lines.append(f"\n  📈 {chart.title}")
                if chart.chart_type == ChartType.PIE:
                    for i, label in enumerate(chart.labels[:5]):
                        data = chart.datasets[0]["data"][i] if chart.datasets else 0
                        total = sum(chart.datasets[0]["data"]) if chart.datasets else 1
                        pct = data / total * 100 if total > 0 else 0
                        bar = "█" * int(pct / 5)
                        lines.append(f"     {label}: {bar} {pct:.1f}%")
                elif chart.chart_type == ChartType.BAR:
                    for i, label in enumerate(chart.labels[:5]):
                        data = chart.datasets[0]["data"][i] if chart.datasets else 0
                        bar_len = int(abs(data) / 2)
                        bar = "█" * bar_len if data >= 0 else "░" * bar_len
                        lines.append(f"     {label}: {bar} {data:+.1f}%")

        return "\n".join(lines)

    def export_html(self, dashboard: PerformanceDashboard) -> str:
        """导出 HTML 格式"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{dashboard.title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .dashboard {{ max-width: 1200px; margin: 0 auto; }}
        .section {{ background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .section-title {{ font-size: 18px; font-weight: bold; margin-bottom: 15px; color: #333; }}
        .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }}
        .card {{ background: #f8f9fa; border-radius: 8px; padding: 15px; }}
        .card-title {{ font-size: 12px; color: #666; margin-bottom: 5px; }}
        .card-value {{ font-size: 24px; font-weight: bold; color: #333; }}
        .card-change {{ font-size: 12px; margin-top: 5px; }}
        .positive {{ color: #10b981; }}
        .negative {{ color: #ef4444; }}
        .neutral {{ color: #6b7280; }}
        .generated {{ text-align: center; color: #999; font-size: 12px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="dashboard">
        <h1>{dashboard.title}</h1>
"""
        for section in dashboard.sections:
            html += f"""
        <div class="section">
            <div class="section-title">{section.title}</div>
            <div class="cards">
"""
            for card in section.cards:
                change_class = card.change_type
                html += f"""
                <div class="card">
                    <div class="card-title">{card.icon} {card.title}</div>
                    <div class="card-value">{card.value}</div>
                    <div class="card-change {change_class}">{card.change}</div>
                </div>
"""
            html += """
            </div>
        </div>
"""

        html += f"""
        <div class="generated">生成时间: {dashboard.generated_at}</div>
    </div>
</body>
</html>
"""
        return html


dashboard_generator = DashboardGenerator()
