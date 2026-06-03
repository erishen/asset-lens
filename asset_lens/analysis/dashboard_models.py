from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ChartType(Enum):
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    AREA = "area"
    SCATTER = "scatter"


class MetricType(Enum):
    RETURN = "return"
    RISK = "risk"
    SHARPE = "sharpe"
    WIN_RATE = "win_rate"
    DRAWDOWN = "drawdown"


@dataclass
class ChartData:
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
