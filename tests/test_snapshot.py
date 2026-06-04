import json

import pytest

from asset_lens.data.snapshot import PortfolioSnapshot, SnapshotManager


@pytest.fixture
def tmp_storage(tmp_path):
    return tmp_path / "snapshot_test"


@pytest.fixture
def manager(tmp_storage):
    return SnapshotManager(storage_path=tmp_storage)


class TestPortfolioSnapshot:
    def test_to_dict(self):
        snapshot = PortfolioSnapshot(
            snapshot_id="20260101_120000",
            timestamp="2026-06-01 12:00:00",
            total_assets=100000,
            total_profit=10000,
            return_rate=10.0,
            position_count=5,
            positions=[{"code": "000001", "name": "A"}],
            risk_metrics={"sharpe": 1.5},
            market_regime="bull",
            metadata={"source": "auto"},
        )
        d = snapshot.to_dict()
        assert d["snapshot_id"] == "20260101_120000"
        assert d["total_assets"] == 100000
        assert d["return_rate"] == 10.0
        assert d["position_count"] == 5
        assert len(d["positions"]) == 1
        assert d["risk_metrics"]["sharpe"] == 1.5
        assert d["market_regime"] == "bull"

    def test_default_values(self):
        snapshot = PortfolioSnapshot(
            snapshot_id="id1",
            timestamp="2026-01-01",
            total_assets=0,
            total_profit=0,
            return_rate=0,
            position_count=0,
        )
        assert snapshot.positions == []
        assert snapshot.risk_metrics == {}
        assert snapshot.market_regime == "unknown"
        assert snapshot.metadata == {}


class TestCreateSnapshot:
    def test_create_basic(self, manager):
        snapshot = manager.create_snapshot(
            total_assets=100000,
            total_profit=5000,
            return_rate=5.0,
            position_count=3,
        )
        assert snapshot.total_assets == 100000
        assert snapshot.total_profit == 5000
        assert snapshot.return_rate == 5.0
        assert snapshot.position_count == 3
        assert len(snapshot.snapshot_id) > 0
        assert snapshot.positions == []
        assert snapshot.risk_metrics == {}

    def test_create_with_positions(self, manager):
        positions = [{"code": "000001", "name": "A"}, {"code": "000002", "name": "B"}]
        risk_metrics = {"var": 2000}
        snapshot = manager.create_snapshot(
            total_assets=80000,
            total_profit=-2000,
            return_rate=-2.5,
            position_count=2,
            positions=positions,
            risk_metrics=risk_metrics,
            market_regime="bear",
            metadata={"note": "test"},
        )
        assert len(snapshot.positions) == 2
        assert snapshot.risk_metrics["var"] == 2000
        assert snapshot.market_regime == "bear"
        assert snapshot.metadata["note"] == "test"


class TestGetSnapshot:
    def test_get_existing(self, manager):
        manager.create_snapshot(total_assets=100000, total_profit=0, return_rate=0, position_count=0)
        today_str = __import__("datetime").datetime.now().strftime("%Y-%m-%d")
        snapshot = manager.get_snapshot(today_str)
        assert snapshot is not None
        assert snapshot.total_assets == 100000

    def test_get_nonexistent(self, manager):
        snapshot = manager.get_snapshot("2099-01-01")
        assert snapshot is None

    def test_corrupted_file(self, manager, tmp_storage):
        date_str = "2026-06-01"
        filename = manager._get_snapshot_filename(date_str)
        file_path = tmp_storage / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text("corrupted json content")
        snapshot = manager.get_snapshot(date_str)
        assert snapshot is None

    def test_empty_snapshots_file(self, manager, tmp_storage):
        date_str = "2026-06-02"
        filename = manager._get_snapshot_filename(date_str)
        file_path = tmp_storage / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(json.dumps({"items": []}))
        snapshot = manager.get_snapshot(date_str)
        assert snapshot is None


class TestGetSnapshotsByDateRange:
    def test_range_with_snapshots(self, manager):
        manager.create_snapshot(total_assets=100000, total_profit=0, return_rate=0, position_count=0)
        snapshots = manager.get_snapshots_by_date_range(
            start_date=__import__("datetime").datetime.now().strftime("%Y-%m-%d"),
            end_date=__import__("datetime").datetime.now().strftime("%Y-%m-%d"),
        )
        assert len(snapshots) >= 1

    def test_invalid_date_format(self, manager):
        snapshots = manager.get_snapshots_by_date_range(start_date="invalid", end_date="invalid")
        assert snapshots == []

    def test_no_snapshots_in_range(self, manager):
        snapshots = manager.get_snapshots_by_date_range(
            start_date="1900-01-01",
            end_date="1900-01-31",
        )
        assert snapshots == []


class TestGetLatestSnapshots:
    def test_returns_snapshots(self, manager):
        manager.create_snapshot(total_assets=100000, total_profit=0, return_rate=0, position_count=0)
        latest = manager.get_latest_snapshots(count=5)
        assert len(latest) >= 1

    def test_respects_count_limit(self, manager):
        for _ in range(3):
            manager.create_snapshot(total_assets=100000, total_profit=0, return_rate=0, position_count=0)
        latest = manager.get_latest_snapshots(count=2)
        assert len(latest) <= 2

    def test_zero_count(self, manager):
        latest = manager.get_latest_snapshots(count=0)
        assert len(latest) == 0


class TestSaveSnapshot:
    def test_multiple_snapshots_same_day(self, manager):
        today_str = __import__("datetime").datetime.now().strftime("%Y-%m-%d")
        manager.create_snapshot(total_assets=100000, total_profit=0, return_rate=0, position_count=0)
        manager.create_snapshot(total_assets=110000, total_profit=1000, return_rate=1.0, position_count=2)
        filename = manager._get_snapshot_filename(today_str)
        file_path = manager.storage_path / filename
        assert file_path.exists()
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        assert len(data.get("items", [])) == 2
