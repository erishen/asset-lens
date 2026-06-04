from unittest.mock import patch

import pytest

from asset_lens.analysis.dashboard import DashboardGenerator
from asset_lens.analysis.dashboard_models import (
    ChartData,
    ChartType,
    DashboardSection,
    MetricCard,
    MetricType,
    PerformanceDashboard,
)


class TestChartType:
    def test_values(self):
        assert ChartType.LINE.value == "line"
        assert ChartType.BAR.value == "bar"
        assert ChartType.PIE.value == "pie"
        assert ChartType.AREA.value == "area"
        assert ChartType.SCATTER.value == "scatter"


class TestMetricType:
    def test_values(self):
        assert MetricType.RETURN.value == "return"
        assert MetricType.RISK.value == "risk"
        assert MetricType.SHARPE.value == "sharpe"


class TestChartData:
    def test_creation(self):
        chart = ChartData(
            chart_type=ChartType.LINE,
            title="Test",
            labels=["A", "B"],
            datasets=[{"data": [1, 2]}],
        )
        assert chart.chart_type == ChartType.LINE
        assert chart.title == "Test"
        assert chart.options == {}

    def test_to_dict(self):
        chart = ChartData(
            chart_type=ChartType.BAR,
            title="Test",
            labels=["A"],
            datasets=[{"data": [1]}],
            options={"yAxis": {"format": "percent"}},
        )
        d = chart.to_dict()
        assert d["chart_type"] == "bar"
        assert d["title"] == "Test"
        assert d["options"]["yAxis"]["format"] == "percent"


class TestMetricCard:
    def test_creation(self):
        card = MetricCard(
            title="总资产", value="¥100,000", change="+5.0%",
            change_type="positive", icon="💰", color="blue",
        )
        assert card.title == "总资产"
        assert card.change_type == "positive"

    def test_to_dict(self):
        card = MetricCard(
            title="Test", value="100", change="+1%",
            change_type="positive", icon="📊", color="green",
        )
        d = card.to_dict()
        assert d["title"] == "Test"
        assert d["value"] == "100"


class TestDashboardSection:
    def test_creation(self):
        card = MetricCard(title="T", value="V", change="C", change_type="positive", icon="📊", color="blue")
        chart = ChartData(chart_type=ChartType.LINE, title="C", labels=[], datasets=[])
        section = DashboardSection(title="Section", cards=[card], charts=[chart])
        assert section.title == "Section"
        assert len(section.cards) == 1

    def test_to_dict(self):
        card = MetricCard(title="T", value="V", change="C", change_type="positive", icon="📊", color="blue")
        section = DashboardSection(title="S", cards=[card], charts=[])
        d = section.to_dict()
        assert d["title"] == "S"
        assert len(d["cards"]) == 1


class TestPerformanceDashboard:
    def test_creation(self):
        dashboard = PerformanceDashboard(
            dashboard_id="test_1",
            title="Test Dashboard",
            sections=[],
        )
        assert dashboard.dashboard_id == "test_1"
        assert dashboard.generated_at != ""

    def test_to_dict(self):
        dashboard = PerformanceDashboard(
            dashboard_id="test_1",
            title="Test",
            sections=[],
        )
        d = dashboard.to_dict()
        assert d["dashboard_id"] == "test_1"
        assert "generated_at" in d


class TestDashboardGenerator:
    @pytest.fixture
    def generator(self, tmp_path):
        with patch("asset_lens.analysis.dashboard.config") as mock_config:
            mock_config.cache_path = tmp_path
            gen = DashboardGenerator(cache_path=tmp_path)
        return gen

    def test_init(self, generator, tmp_path):
        assert generator.cache_path == tmp_path
        assert tmp_path.exists()

    def test_generate_dashboard(self, generator):
        dashboard = generator.generate_dashboard()
        assert isinstance(dashboard, PerformanceDashboard)
        assert len(dashboard.sections) == 4
        assert dashboard.dashboard_id.startswith("dashboard_")

    def test_generate_dashboard_with_holdings(self, generator):
        holdings = [
            {"code": "600519", "name": "贵州茅台", "current_value": 180000, "buy_price": 1700, "shares": 100, "profit_rate": 0.05, "industry": "白酒"},
        ]
        dashboard = generator.generate_dashboard(holdings=holdings)
        assert isinstance(dashboard, PerformanceDashboard)

    def test_generate_dashboard_with_trades(self, generator):
        trades = [
            {"profit_rate": 0.1},
            {"profit_rate": -0.05},
        ]
        dashboard = generator.generate_dashboard(trades=trades)
        assert isinstance(dashboard, PerformanceDashboard)

    def test_save_and_load(self, generator):
        dashboard = generator.generate_dashboard()
        loaded = generator.load_dashboard()
        assert loaded is not None
        assert loaded.dashboard_id == dashboard.dashboard_id

    def test_load_nonexistent(self, tmp_path):
        with patch("asset_lens.analysis.dashboard.config") as mock_config:
            mock_config.cache_path = tmp_path
            gen = DashboardGenerator(cache_path=tmp_path)
        gen.dashboard_file = tmp_path / "nonexistent.json"
        assert gen.load_dashboard() is None

    def test_load_invalid_json(self, generator):
        generator.dashboard_file.write_text("not json", encoding="utf-8")
        assert generator.load_dashboard() is None

    def test_format_dashboard(self, generator):
        dashboard = generator.generate_dashboard()
        text = generator.format_dashboard(dashboard)
        assert "投资绩效看板" in text
        assert "概览" in text

    def test_export_html(self, generator):
        dashboard = generator.generate_dashboard()
        html = generator.export_html(dashboard)
        assert "<html>" in html
        assert "投资绩效看板" in html
        assert "card" in html

    def test_generate_empty_holdings(self, generator):
        dashboard = generator.generate_dashboard(holdings=[], trades=[])
        assert isinstance(dashboard, PerformanceDashboard)
