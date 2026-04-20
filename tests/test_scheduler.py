"""
Tests for Task Scheduler.
定时任务调度器测试
"""

import pytest
import time
from datetime import datetime
from unittest.mock import patch, MagicMock


class TestTaskConfig:
    """任务配置测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.scheduler.task_scheduler import TaskConfig
        assert TaskConfig is not None

    def test_task_config_creation(self):
        """测试任务配置创建"""
        from asset_lens.scheduler.task_scheduler import TaskConfig, ScheduleType

        def dummy_func():
            return "done"

        config = TaskConfig(
            name="test_task",
            func=dummy_func,
            schedule_type=ScheduleType.INTERVAL,
            schedule_value=60,
            description="测试任务",
        )

        assert config.name == "test_task"
        assert config.enabled is True
        assert config.max_retries == 3
        assert config.description == "测试任务"


class TestTaskResult:
    """任务结果测试"""

    def test_task_result_creation(self):
        """测试任务结果创建"""
        from asset_lens.scheduler.task_scheduler import TaskResult, TaskStatus

        result = TaskResult(
            task_name="test_task",
            status=TaskStatus.COMPLETED,
            start_time="2024-01-01 12:00:00",
            end_time="2024-01-01 12:00:01",
            duration=1.0,
            result="success",
        )

        assert result.task_name == "test_task"
        assert result.status == TaskStatus.COMPLETED
        assert result.duration == 1.0

    def test_task_result_to_dict(self):
        """测试任务结果转换为字典"""
        from asset_lens.scheduler.task_scheduler import TaskResult, TaskStatus

        result = TaskResult(
            task_name="test_task",
            status=TaskStatus.COMPLETED,
            start_time="2024-01-01 12:00:00",
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["task_name"] == "test_task"
        assert result_dict["status"] == "completed"


class TestTaskScheduler:
    """任务调度器测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.scheduler.task_scheduler import TaskScheduler
        assert TaskScheduler is not None

    def test_scheduler_init(self):
        """测试调度器初始化"""
        from asset_lens.scheduler.task_scheduler import TaskScheduler
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            scheduler = TaskScheduler(Path(tmpdir))
            assert scheduler is not None
            assert not scheduler.is_running()

    def test_register_task(self):
        """测试注册任务"""
        from asset_lens.scheduler.task_scheduler import TaskScheduler, TaskConfig, ScheduleType
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            scheduler = TaskScheduler(Path(tmpdir))

            def dummy_func():
                return "done"

            config = TaskConfig(
                name="test_task",
                func=dummy_func,
                schedule_type=ScheduleType.INTERVAL,
                schedule_value=60,
            )

            scheduler.register_task(config)

            tasks = scheduler.get_all_tasks()
            assert len(tasks) == 1
            assert tasks[0]["name"] == "test_task"

    def test_unregister_task(self):
        """测试注销任务"""
        from asset_lens.scheduler.task_scheduler import TaskScheduler, TaskConfig, ScheduleType
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            scheduler = TaskScheduler(Path(tmpdir))

            def dummy_func():
                return "done"

            config = TaskConfig(
                name="test_task",
                func=dummy_func,
                schedule_type=ScheduleType.INTERVAL,
                schedule_value=60,
            )

            scheduler.register_task(config)
            result = scheduler.unregister_task("test_task")

            assert result is True
            assert len(scheduler.get_all_tasks()) == 0

    def test_enable_disable_task(self):
        """测试启用/禁用任务"""
        from asset_lens.scheduler.task_scheduler import TaskScheduler, TaskConfig, ScheduleType
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            scheduler = TaskScheduler(Path(tmpdir))

            def dummy_func():
                return "done"

            config = TaskConfig(
                name="test_task",
                func=dummy_func,
                schedule_type=ScheduleType.INTERVAL,
                schedule_value=60,
            )

            scheduler.register_task(config)

            scheduler.disable_task("test_task")
            status = scheduler.get_task_status("test_task")
            assert status["enabled"] is False

            scheduler.enable_task("test_task")
            status = scheduler.get_task_status("test_task")
            assert status["enabled"] is True

    def test_run_task(self):
        """测试运行任务"""
        from asset_lens.scheduler.task_scheduler import TaskScheduler, TaskConfig, ScheduleType
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            scheduler = TaskScheduler(Path(tmpdir))

            def dummy_func():
                return "test_result"

            config = TaskConfig(
                name="test_task",
                func=dummy_func,
                schedule_type=ScheduleType.INTERVAL,
                schedule_value=60,
            )

            scheduler.register_task(config)
            result = scheduler.run_task("test_task")

            assert result is not None
            assert result.status.value == "completed"
            assert result.result == "test_result"

    def test_run_nonexistent_task(self):
        """测试运行不存在的任务"""
        from asset_lens.scheduler.task_scheduler import TaskScheduler
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            scheduler = TaskScheduler(Path(tmpdir))

            result = scheduler.run_task("nonexistent")

            assert result is None

    def test_get_task_status(self):
        """测试获取任务状态"""
        from asset_lens.scheduler.task_scheduler import TaskScheduler, TaskConfig, ScheduleType
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            scheduler = TaskScheduler(Path(tmpdir))

            def dummy_func():
                return "done"

            config = TaskConfig(
                name="test_task",
                func=dummy_func,
                schedule_type=ScheduleType.DAILY,
                schedule_value=(9, 30),
                description="测试任务",
            )

            scheduler.register_task(config)
            status = scheduler.get_task_status("test_task")

            assert status is not None
            assert status["name"] == "test_task"
            assert status["description"] == "测试任务"
            assert status["enabled"] is True

    def test_get_all_tasks(self):
        """测试获取所有任务"""
        from asset_lens.scheduler.task_scheduler import TaskScheduler, TaskConfig, ScheduleType
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            scheduler = TaskScheduler(Path(tmpdir))

            def dummy_func():
                return "done"

            config1 = TaskConfig(
                name="task1",
                func=dummy_func,
                schedule_type=ScheduleType.INTERVAL,
                schedule_value=60,
            )
            config2 = TaskConfig(
                name="task2",
                func=dummy_func,
                schedule_type=ScheduleType.DAILY,
                schedule_value=(10, 0),
            )

            scheduler.register_task(config1)
            scheduler.register_task(config2)

            tasks = scheduler.get_all_tasks()

            assert len(tasks) == 2

    def test_get_task_history(self):
        """测试获取任务历史"""
        from asset_lens.scheduler.task_scheduler import TaskScheduler, TaskConfig, ScheduleType
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            scheduler = TaskScheduler(Path(tmpdir))

            def dummy_func():
                return "done"

            config = TaskConfig(
                name="test_task",
                func=dummy_func,
                schedule_type=ScheduleType.INTERVAL,
                schedule_value=60,
            )

            scheduler.register_task(config)
            scheduler.run_task("test_task")

            history = scheduler.get_task_history("test_task")

            assert isinstance(history, list)
            assert len(history) == 1

    def test_start_stop(self):
        """测试启动/停止调度器"""
        from asset_lens.scheduler.task_scheduler import TaskScheduler
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            scheduler = TaskScheduler(Path(tmpdir))

            scheduler.start()
            assert scheduler.is_running()

            time.sleep(0.5)

            scheduler.stop()
            assert not scheduler.is_running()


class TestScheduleType:
    """调度类型测试"""

    def test_schedule_type_values(self):
        """测试调度类型值"""
        from asset_lens.scheduler.task_scheduler import ScheduleType

        assert ScheduleType.INTERVAL.value == "interval"
        assert ScheduleType.DAILY.value == "daily"
        assert ScheduleType.WEEKLY.value == "weekly"
        assert ScheduleType.MONTHLY.value == "monthly"


class TestTaskStatus:
    """任务状态测试"""

    def test_task_status_values(self):
        """测试任务状态值"""
        from asset_lens.scheduler.task_scheduler import TaskStatus

        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"


class TestTaskHistory:
    """任务历史测试"""

    def test_task_history_creation(self):
        """测试任务历史创建"""
        from asset_lens.scheduler.task_scheduler import TaskHistory

        history = TaskHistory(task_name="test_task")

        assert history.task_name == "test_task"
        assert history.total_runs == 0
        assert history.success_count == 0

    def test_task_history_add_result(self):
        """测试添加任务结果"""
        from asset_lens.scheduler.task_scheduler import TaskHistory, TaskResult, TaskStatus

        history = TaskHistory(task_name="test_task")

        result = TaskResult(
            task_name="test_task",
            status=TaskStatus.COMPLETED,
            start_time="2024-01-01 12:00:00",
        )

        history.add_result(result)

        assert history.total_runs == 1
        assert history.success_count == 1


class TestRetryMechanism:
    """重试机制测试"""

    def test_retry_on_failure(self):
        """测试失败重试"""
        from asset_lens.scheduler.task_scheduler import TaskScheduler, TaskConfig, ScheduleType
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            scheduler = TaskScheduler(Path(tmpdir))

            call_count = [0]

            def failing_func():
                call_count[0] += 1
                if call_count[0] < 2:
                    raise Exception("Temporary error")
                return "success"

            config = TaskConfig(
                name="retry_task",
                func=failing_func,
                schedule_type=ScheduleType.INTERVAL,
                schedule_value=60,
                max_retries=3,
                retry_delay=0.1,
            )

            scheduler.register_task(config)
            result = scheduler.run_task("retry_task")

            assert result.status.value == "completed"
            assert call_count[0] == 2

    def test_max_retries_exceeded(self):
        """测试超过最大重试次数"""
        from asset_lens.scheduler.task_scheduler import TaskScheduler, TaskConfig, ScheduleType
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            scheduler = TaskScheduler(Path(tmpdir))

            def always_failing():
                raise Exception("Always fails")

            config = TaskConfig(
                name="always_fail_task",
                func=always_failing,
                schedule_type=ScheduleType.INTERVAL,
                schedule_value=60,
                max_retries=2,
                retry_delay=0.1,
            )

            scheduler.register_task(config)
            result = scheduler.run_task("always_fail_task")

            assert result.status.value == "failed"
            assert result.retry_count == 3
