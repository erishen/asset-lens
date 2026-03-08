"""
Tests for scheduler.py
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from asset_lens.data.scheduler import TaskScheduler, run_with_timeout


class TestRunWithTimeout:
    """run_with_timeout 测试"""

    def test_run_with_timeout_success(self):
        """测试正常执行"""
        def success_func():
            return {"result": "success"}

        result = run_with_timeout(success_func, 5, "test_task")
        assert result["result"] == "success"

    def test_run_with_timeout_exception(self):
        """测试执行异常"""
        def error_func():
            raise ValueError("test error")

        result = run_with_timeout(error_func, 5, "test_task")
        assert "error" in result


class TestTaskScheduler:
    """TaskScheduler 测试"""

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

    def test_init(self, scheduler):
        """测试初始化"""
        assert scheduler.scheduler_path.exists()
        assert scheduler.log_file is not None

    def test_load_log_no_file(self, scheduler):
        """测试加载日志 - 文件不存在"""
        scheduler._load_log()
        assert scheduler.tasks == {}

    def test_load_log_with_file(self, scheduler):
        """测试加载日志 - 有文件"""
        log_data = {"task1": {"status": "success"}}
        with open(scheduler.log_file, "w", encoding="utf-8") as f:
            json.dump(log_data, f)

        scheduler._load_log()
        assert scheduler.tasks["task1"]["status"] == "success"

    def test_log_task(self, scheduler):
        """测试记录任务日志"""
        scheduler._log_task("test_task", "success", "test message")

        assert "test_task" in scheduler.tasks
        assert scheduler.tasks["test_task"]["status"] == "success"
        assert scheduler.log_file.exists()

    def test_get_task_status(self, scheduler):
        """测试获取任务状态"""
        scheduler.tasks = {
            "task1": {"status": "success", "last_run": "2024-01-01 12:00:00"},
        }

        result = scheduler.get_task_status()

        assert "tasks" in result
        assert "task1" in result["tasks"]


class TestSchedulerIntegration:
    """调度器集成测试"""

    @pytest.fixture
    def temp_cache_path(self):
        """临时缓存路径"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    def test_full_workflow(self, temp_cache_path):
        """测试完整工作流"""
        with patch('asset_lens.data.scheduler.config') as mock_config:
            mock_config.cache_path = temp_cache_path
            scheduler = TaskScheduler()

            scheduler._log_task("task1", "success", "test")
            assert "task1" in scheduler.tasks

            status = scheduler.get_task_status()
            assert "task1" in status["tasks"]
