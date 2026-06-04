from asset_lens.core.portfolio_comparator import PortfolioComparator, portfolio_comparator


class TestPortfolioComparator:
    def test_empty_snapshots(self):
        comparator = PortfolioComparator()
        assert comparator.compare_weekly() is None

    def test_single_snapshot(self):
        comparator = PortfolioComparator()
        comparator.add_snapshot({"timestamp": "2026-05-20 10:00:00", "total_assets": 100000})
        assert comparator.compare_weekly() is None

    def test_compare_weekly(self):
        comparator = PortfolioComparator()
        comparator.add_snapshot({"timestamp": "2026-05-13 10:00:00", "total_assets": 100000})
        comparator.add_snapshot({"timestamp": "2026-05-20 10:00:00", "total_assets": 105000})
        result = comparator.compare_weekly()
        assert result is not None
        assert result["before"]["total_assets"] == 100000
        assert result["after"]["total_assets"] == 105000
        assert "change" in result
        assert "return_rate" in result

    def test_compare_weekly_zero_before(self):
        comparator = PortfolioComparator()
        comparator.add_snapshot({"timestamp": "2026-05-13 10:00:00", "total_assets": 0})
        comparator.add_snapshot({"timestamp": "2026-05-20 10:00:00", "total_assets": 1000})
        result = comparator.compare_weekly()
        assert result is not None
        assert result["return_rate"] == "0"

    def test_compare_periods(self):
        comparator = PortfolioComparator()
        comparator.add_snapshot({"timestamp": "2026-05-01 10:00:00", "total_assets": 90000})
        comparator.add_snapshot({"timestamp": "2026-05-15 10:00:00", "total_assets": 95000})
        comparator.add_snapshot({"timestamp": "2026-05-20 10:00:00", "total_assets": 100000})
        result = comparator.compare_periods("2026-05-01", "2026-05-20")
        assert result is not None
        assert result["period1"]["total_assets"] == 90000
        assert result["period2"]["total_assets"] == 100000

    def test_compare_periods_no_match(self):
        comparator = PortfolioComparator()
        comparator.add_snapshot({"timestamp": "2026-05-01 10:00:00", "total_assets": 90000})
        result = comparator.compare_periods("2026-04-01", "2026-04-30")
        assert result is None

    def test_get_trend_up(self):
        comparator = PortfolioComparator()
        comparator.add_snapshot({"timestamp": "2026-05-15 10:00:00", "total_assets": 90000})
        comparator.add_snapshot({"timestamp": "2026-06-01 10:00:00", "total_assets": 100000})
        result = comparator.get_trend_analysis(days=30)
        assert result["trend"] == "up"
        assert result["days"] == 2

    def test_get_trend_down(self):
        comparator = PortfolioComparator()
        comparator.add_snapshot({"timestamp": "2026-05-15 10:00:00", "total_assets": 100000})
        comparator.add_snapshot({"timestamp": "2026-06-01 10:00:00", "total_assets": 90000})
        result = comparator.get_trend_analysis(days=30)
        assert result["trend"] == "down"

    def test_get_trend_stable(self):
        comparator = PortfolioComparator()
        comparator.add_snapshot({"timestamp": "2026-05-15 10:00:00", "total_assets": 100000})
        comparator.add_snapshot({"timestamp": "2026-06-01 10:00:00", "total_assets": 100000})
        result = comparator.get_trend_analysis(days=30)
        assert result["trend"] == "stable"

    def test_get_trend_no_recent(self):
        comparator = PortfolioComparator()
        comparator.add_snapshot({"timestamp": "2020-01-01 10:00:00", "total_assets": 100000})
        result = comparator.get_trend_analysis(days=30)
        assert result["trend"] == "unknown"
        assert result["days"] == 0

    def test_add_snapshot(self):
        comparator = PortfolioComparator()
        snapshot = {"timestamp": "2026-05-20 10:00:00", "total_assets": 100000}
        comparator.add_snapshot(snapshot)
        assert len(comparator._snapshots) == 1

    def test_module_instance(self):
        assert isinstance(portfolio_comparator, PortfolioComparator)
