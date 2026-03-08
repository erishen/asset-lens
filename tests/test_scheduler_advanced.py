"""
Additional tests for scheduler.py to improve coverage
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from asset_lens.data.scheduler import TaskScheduler, run_with_timeout, TimeoutError


class TestRunWithTimeoutAdvanced:
    """Advanced tests for run_with_timeout"""

    def test_run_with_timeout_returns_result(self):
        """Test that run_with_timeout returns function result"""
        def return_value():
            return {"data": "test"}
        
        result = run_with_timeout(return_value, 5, "test")
        assert result["data"] == "test"

    def test_run_with_timeout_catches_exception(self):
        """Test that run_with_timeout catches exceptions"""
        def raise_error():
            raise RuntimeError("test error")
        
        result = run_with_timeout(raise_error, 5, "test")
        assert "error" in result
        assert "test error" in result["error"]


class TestTaskSchedulerTasks:
    """Tests for TaskScheduler task methods"""

    @pytest.fixture
    def temp_cache_path(self):
        """临时缓存路径"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def scheduler(self, temp_cache_path):
        """创建测试实例"""
        with patch('asset_lens.data.scheduler.config') as mock_config:
            mock_config.cache_path = temp_cache_path
            scheduler = TaskScheduler()
            yield scheduler

    def test_task_update_all_data_success(self, scheduler):
        """Test task_update_all_data success"""
        mock_fund_result = {"data": {"fund1": {}, "fund2": {}}}
        mock_stock_result = {"data": {"stock1": {}}}

        with patch('asset_lens.data.fund_fetcher.fetch_portfolio_fund_quotes') as mock_fund:
            with patch('asset_lens.data.stock_fetcher.stock_fetcher') as mock_fetcher:
                mock_fund.return_value = mock_fund_result
                mock_fetcher._load_stock_codes_config.return_value = {"name1": "000001"}
                mock_fetcher.fetch_multiple_stocks.return_value = mock_stock_result

                result = scheduler.task_update_all_data()

                assert result["status"] == "completed"
                assert "funds" in result["details"]
                assert "stocks" in result["details"]

    def test_task_update_all_data_exception(self, scheduler):
        """Test task_update_all_data with exception"""
        with patch('asset_lens.data.fund_fetcher.fetch_portfolio_fund_quotes') as mock_fund:
            mock_fund.side_effect = Exception("Network error")

            result = scheduler.task_update_all_data()

            assert result["status"] == "failed"
            assert "error" in result

    def test_task_track_stocks_with_cache(self, scheduler):
        """Test task_track_stocks with cached data"""
        mock_tracker = MagicMock()
        mock_tracker.record_batch.return_value = 10

        cached_stocks = [{"code": "sh600519", "name": "贵州茅台"}]

        with patch('asset_lens.data.stock_tracker.StockTracker') as mock_tracker_class:
            with patch('asset_lens.data.market_stock_fetcher.market_stock_fetcher') as mock_fetcher:
                mock_tracker_class.return_value = mock_tracker
                mock_fetcher.get_cached_market_stocks.return_value = cached_stocks

                result = scheduler.task_track_stocks("test_pool")

                assert result["status"] == "completed"
                assert result["details"]["recorded"] == 10

    def test_task_track_stocks_fetch_new(self, scheduler):
        """Test task_track_stocks fetching new data"""
        mock_tracker = MagicMock()
        mock_tracker.record_batch.return_value = 5

        new_stocks = [{"code": "sh600519", "name": "贵州茅台"}]

        with patch('asset_lens.data.stock_tracker.StockTracker') as mock_tracker_class:
            with patch('asset_lens.data.market_stock_fetcher.market_stock_fetcher') as mock_fetcher:
                mock_tracker_class.return_value = mock_tracker
                mock_fetcher.get_cached_market_stocks.return_value = []
                mock_fetcher.fetch_all_cn_stocks.return_value = new_stocks

                result = scheduler.task_track_stocks("test_pool")

                assert result["status"] == "completed"
                mock_fetcher.save_market_stocks.assert_called_once()

    def test_task_track_stocks_no_data(self, scheduler):
        """Test task_track_stocks with no data"""
        with patch('asset_lens.data.stock_tracker.StockTracker') as mock_tracker_class:
            with patch('asset_lens.data.market_stock_fetcher.market_stock_fetcher') as mock_fetcher:
                mock_tracker_class.return_value = MagicMock()
                mock_fetcher.get_cached_market_stocks.return_value = []
                mock_fetcher.fetch_all_cn_stocks.return_value = []

                result = scheduler.task_track_stocks("test_pool")

                assert result["status"] == "failed"
                assert result["error"] == "没有市场数据"

    def test_task_track_stocks_exception(self, scheduler):
        """Test task_track_stocks with exception"""
        with patch('asset_lens.data.stock_tracker.StockTracker') as mock_tracker_class:
            mock_tracker_class.side_effect = Exception("Tracker error")

            result = scheduler.task_track_stocks("test_pool")

            assert result["status"] == "failed"
            assert "error" in result

    def test_task_detect_monster_success(self, scheduler):
        """Test task_detect_monster success"""
        mock_signal = MagicMock()
        mock_signal.code = "sh600519"
        mock_signal.name = "贵州茅台"
        mock_signal.score = 85.5
        mock_signal.signal_type = "momentum"

        mock_tracker = MagicMock()
        mock_tracker.detect_monster_stocks.return_value = [mock_signal]

        with patch('asset_lens.data.stock_tracker.StockTracker') as mock_tracker_class:
            mock_tracker_class.return_value = mock_tracker

            result = scheduler.task_detect_monster("test_pool")

            assert result["status"] == "completed"
            assert result["details"]["signals_count"] == 1

    def test_task_detect_monster_exception(self, scheduler):
        """Test task_detect_monster with exception"""
        with patch('asset_lens.data.stock_tracker.StockTracker') as mock_tracker_class:
            mock_tracker_class.side_effect = Exception("Detection error")

            result = scheduler.task_detect_monster("test_pool")

            assert result["status"] == "failed"
            assert "error" in result

    def test_task_momentum_screen_success(self, scheduler):
        """Test task_momentum_screen success"""
        screened_stocks = [
            {"code": "sh600519", "name": "贵州茅台", "current_price": 1800, "strategy_score": 85},
        ]

        mock_pool = MagicMock()
        mock_pool.add_stock.return_value = True

        with patch('asset_lens.data.strategy_engine.strategy_engine') as mock_engine:
            with patch('asset_lens.data.stock_pool.StockPool') as mock_pool_class:
                with patch('asset_lens.data.market_stock_fetcher.market_stock_fetcher') as mock_fetcher:
                    mock_engine.screen_stocks.return_value = screened_stocks
                    mock_pool_class.return_value = mock_pool
                    mock_fetcher.get_cached_market_stocks.return_value = [{"code": "sh600519"}]

                    result = scheduler.task_momentum_screen()

                    assert result["status"] == "completed"
                    assert result["details"]["screened_count"] == 1

    def test_task_momentum_screen_fetch_new(self, scheduler):
        """Test task_momentum_screen fetching new data"""
        screened_stocks = [
            {"code": "sh600519", "name": "贵州茅台", "current_price": 1800, "strategy_score": 85},
        ]

        mock_pool = MagicMock()
        mock_pool.add_stock.return_value = True

        with patch('asset_lens.data.strategy_engine.strategy_engine') as mock_engine:
            with patch('asset_lens.data.stock_pool.StockPool') as mock_pool_class:
                with patch('asset_lens.data.market_stock_fetcher.market_stock_fetcher') as mock_fetcher:
                    mock_engine.screen_stocks.return_value = screened_stocks
                    mock_pool_class.return_value = mock_pool
                    mock_fetcher.get_cached_market_stocks.return_value = []
                    mock_fetcher.fetch_all_cn_stocks.return_value = [{"code": "sh600519"}]

                    result = scheduler.task_momentum_screen()

                    assert result["status"] == "completed"
                    mock_fetcher.save_market_stocks.assert_called_once()

    def test_task_momentum_screen_no_data(self, scheduler):
        """Test task_momentum_screen with no data"""
        with patch('asset_lens.data.market_stock_fetcher.market_stock_fetcher') as mock_fetcher:
            mock_fetcher.get_cached_market_stocks.return_value = []
            mock_fetcher.fetch_all_cn_stocks.return_value = []

            result = scheduler.task_momentum_screen()

            assert result["status"] == "failed"
            assert result["error"] == "没有市场数据"

    def test_task_momentum_screen_exception(self, scheduler):
        """Test task_momentum_screen with exception"""
        with patch('asset_lens.data.market_stock_fetcher.market_stock_fetcher') as mock_fetcher:
            mock_fetcher.get_cached_market_stocks.side_effect = Exception("Fetch error")

            result = scheduler.task_momentum_screen()

            assert result["status"] == "failed"
            assert "error" in result


class TestTaskSchedulerDailyTasks:
    """Tests for daily tasks"""

    @pytest.fixture
    def temp_cache_path(self):
        """临时缓存路径"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def scheduler(self, temp_cache_path):
        """创建测试实例"""
        with patch('asset_lens.data.scheduler.config') as mock_config:
            mock_config.cache_path = temp_cache_path
            scheduler = TaskScheduler()
            yield scheduler

    def test_run_daily_tasks(self, scheduler):
        """Test run_daily_tasks"""
        with patch.object(scheduler, 'task_update_all_data') as mock_update:
            with patch.object(scheduler, 'task_momentum_screen') as mock_screen:
                with patch.object(scheduler, 'task_track_stocks') as mock_track:
                    with patch.object(scheduler, 'task_detect_monster') as mock_detect:
                        mock_update.return_value = {"status": "completed"}
                        mock_screen.return_value = {"status": "completed"}
                        mock_track.return_value = {"status": "completed"}
                        mock_detect.return_value = {"status": "completed"}

                        results = scheduler.run_daily_tasks()

                        assert len(results) == 4
                        mock_update.assert_called_once()
                        mock_screen.assert_called_once()
                        mock_track.assert_called_once()
                        mock_detect.assert_called_once()

    def test_get_task_status_with_tasks(self, scheduler):
        """Test get_task_status with existing tasks"""
        scheduler.tasks = {
            "update_all_data": {
                "last_run": "2024-01-01 12:00:00",
                "status": "success",
                "message": "Updated 10 funds",
            }
        }

        result = scheduler.get_task_status()

        assert "tasks" in result
        assert "current_time" in result
        assert "update_all_data" in result["tasks"]


class TestTaskSchedulerLog:
    """Tests for logging functionality"""

    @pytest.fixture
    def temp_cache_path(self):
        """临时缓存路径"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def scheduler(self, temp_cache_path):
        """创建测试实例"""
        with patch('asset_lens.data.scheduler.config') as mock_config:
            mock_config.cache_path = temp_cache_path
            scheduler = TaskScheduler()
            yield scheduler

    def test_load_log_invalid_json(self, scheduler):
        """Test loading invalid JSON log file"""
        with open(scheduler.log_file, "w") as f:
            f.write("invalid json content")

        scheduler._load_log()
        assert scheduler.tasks == {}

    def test_save_log(self, scheduler):
        """Test saving log"""
        scheduler.tasks = {"task1": {"status": "success"}}
        scheduler._save_log()

        assert scheduler.log_file.exists()
        with open(scheduler.log_file, "r") as f:
            data = json.load(f)
            assert data["task1"]["status"] == "success"

    def test_log_task_saves_to_file(self, scheduler):
        """Test that _log_task saves to file"""
        scheduler._log_task("new_task", "success", "Test message")

        with open(scheduler.log_file, "r") as f:
            data = json.load(f)
            assert "new_task" in data
            assert data["new_task"]["status"] == "success"
            assert data["new_task"]["message"] == "Test message"


class TestTaskSchedulerInit:
    """Tests for TaskScheduler initialization"""

    def test_init_creates_directory(self):
        """Test that init creates scheduler directory"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_path = Path(tmp_dir)
            
            with patch('asset_lens.data.scheduler.config') as mock_config:
                mock_config.cache_path = temp_path
                scheduler = TaskScheduler()

                assert scheduler.scheduler_path.exists()
                assert scheduler.scheduler_path == temp_path / "scheduler"

    def test_init_loads_existing_log(self):
        """Test that init loads existing log file"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_path = Path(tmp_dir)
            scheduler_dir = temp_path / "scheduler"
            scheduler_dir.mkdir(parents=True)
            
            log_file = scheduler_dir / "task_log.json"
            existing_data = {"existing_task": {"status": "success"}}
            with open(log_file, "w") as f:
                json.dump(existing_data, f)

            with patch('asset_lens.data.scheduler.config') as mock_config:
                mock_config.cache_path = temp_path
                scheduler = TaskScheduler()

                assert "existing_task" in scheduler.tasks
