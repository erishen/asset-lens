"""Smoke tests for asset_lens.data untested modules."""

from asset_lens.data.feature_builder import EnhancedFeatureBuilder
from asset_lens.data.fundamental_fetcher import FundamentalData
from asset_lens.data.money_flow_fetcher import MoneyFlowData
from asset_lens.data.snapshot import PortfolioSnapshot, SnapshotManager


class TestSnapshot:
    def test_portfolio_snapshot_creation(self):
        snapshot = PortfolioSnapshot(
            snapshot_id="test-001",
            timestamp="2025-01-01 12:00:00",
            total_assets=100000.0,
            total_profit=5000.0,
            return_rate=5.0,
            position_count=10,
        )
        assert snapshot.snapshot_id == "test-001"
        assert snapshot.total_assets == 100000.0
        assert snapshot.position_count == 10

    def test_portfolio_snapshot_to_dict(self):
        snapshot = PortfolioSnapshot(
            snapshot_id="test-002",
            timestamp="2025-01-01",
            total_assets=50000.0,
            total_profit=-1000.0,
            return_rate=-2.0,
            position_count=5,
        )
        d = snapshot.to_dict()
        assert isinstance(d, dict)
        assert d["snapshot_id"] == "test-002"
        assert d["total_assets"] == 50000.0

    def test_snapshot_manager_creation(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SnapshotManager(storage_path=Path(tmpdir) / "snapshots")
            assert manager.storage_path.exists()


class TestMoneyFlowData:
    def test_money_flow_data_creation(self):
        data = MoneyFlowData(code="000001")
        assert data.code == "000001"
        assert data.main_net_inflow == 0.0

    def test_money_flow_data_to_dict(self):
        data = MoneyFlowData(code="000001", main_net_inflow=100.5, date="2025-01-01")
        d = data.to_dict()
        assert d["code"] == "000001"
        assert d["main_net_inflow"] == 100.5


class TestFundamentalData:
    def test_fundamental_data_creation(self):
        data = FundamentalData(code="000001")
        assert data.code == "000001"
        assert data.pe_ratio == 0.0

    def test_fundamental_data_to_dict(self):
        data = FundamentalData(code="000001", pe_ratio=15.5, pb_ratio=2.0, roe=12.0)
        d = data.to_dict()
        assert d["code"] == "000001"
        assert d["pe_ratio"] == 15.5
        assert d["roe"] == 12.0


class TestFeatureBuilder:
    def test_enhanced_feature_builder_creation(self):
        builder = EnhancedFeatureBuilder()
        assert builder is not None
        assert builder.fundamental_fetcher is not None
        assert builder.money_flow_fetcher is not None
