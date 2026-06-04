"""
Task Scheduler for asset-lens.
定时任务调度器 - 支持定时执行数据更新、风险检查、报告生成等任务

功能:
1. 定时数据更新
2. 定时风险检查
3. 定时报告生成
4. 定时备份
5. 自定义任务
6. 任务历史记录
7. 错误重试机制
"""

import json
import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from ..utils.json_cache import read_json_cache, write_json_cache

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScheduleType(Enum):
    """调度类型"""

    INTERVAL = "interval"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CRON = "cron"


@dataclass
class TaskConfig:
    """任务配置"""

    name: str
    func: Callable
    schedule_type: ScheduleType
    schedule_value: Any
    enabled: bool = True
    max_retries: int = 3
    retry_delay: int = 60
    timeout: int = 300
    description: str = ""


@dataclass
class TaskResult:
    """任务执行结果"""

    task_name: str
    status: TaskStatus
    start_time: str
    end_time: str | None = None
    duration: float = 0.0
    result: Any = None
    error: str | None = None
    retry_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_name": self.task_name,
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "result": str(self.result) if self.result else None,
            "error": self.error,
            "retry_count": self.retry_count,
        }


@dataclass
class TaskHistory:
    """任务历史"""

    task_name: str
    results: list[TaskResult] = field(default_factory=list)
    last_run: str | None = None
    next_run: str | None = None
    total_runs: int = 0
    success_count: int = 0
    fail_count: int = 0

    def add_result(self, result: TaskResult):
        self.results.append(result)
        self.results = self.results[-100:]
        self.last_run = result.start_time
        self.total_runs += 1
        if result.status == TaskStatus.COMPLETED:
            self.success_count += 1
        elif result.status == TaskStatus.FAILED:
            self.fail_count += 1


class TaskScheduler:
    """任务调度器"""

    def __init__(self, cache_path: Path | None = None):
        self._cache_path = cache_path or Path("cache/scheduler")
        self._cache_path.mkdir(parents=True, exist_ok=True)

        self._tasks: dict[str, TaskConfig] = {}
        self._history: dict[str, TaskHistory] = {}
        self._running: bool = False
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

        self._load_history()

    def _load_history(self):
        """加载任务历史"""
        history_file = self._cache_path / "task_history.json"
        data = read_json_cache(history_file)
        if data:
            for name, hist in data.items():
                self._history[name] = TaskHistory(
                    task_name=name,
                    last_run=hist.get("last_run"),
                    next_run=hist.get("next_run"),
                    total_runs=hist.get("total_runs", 0),
                    success_count=hist.get("success_count", 0),
                    fail_count=hist.get("fail_count", 0),
                )

    def _save_history(self):
        """保存任务历史"""
        history_file = self._cache_path / "task_history.json"
        data = {}
        for name, hist in self._history.items():
            data[name] = {
                "last_run": hist.last_run,
                "next_run": hist.next_run,
                "total_runs": hist.total_runs,
                "success_count": hist.success_count,
                "fail_count": hist.fail_count,
            }
        write_json_cache(history_file, data)

    def register_task(self, config: TaskConfig) -> None:
        """注册任务"""
        with self._lock:
            self._tasks[config.name] = config
            if config.name not in self._history:
                self._history[config.name] = TaskHistory(task_name=config.name)
            logger.info(f"注册任务: {config.name}")

    def unregister_task(self, name: str) -> bool:
        """注销任务"""
        with self._lock:
            if name in self._tasks:
                del self._tasks[name]
                logger.info(f"注销任务: {name}")
                return True
            return False

    def enable_task(self, name: str) -> bool:
        """启用任务"""
        if name in self._tasks:
            self._tasks[name].enabled = True
            return True
        return False

    def disable_task(self, name: str) -> bool:
        """禁用任务"""
        if name in self._tasks:
            self._tasks[name].enabled = False
            return True
        return False

    def _calculate_next_run(self, config: TaskConfig) -> datetime | None:
        """计算下次运行时间"""
        now = datetime.now()

        if config.schedule_type == ScheduleType.INTERVAL:
            minutes = config.schedule_value
            return now + timedelta(minutes=minutes)

        elif config.schedule_type == ScheduleType.DAILY:
            hour, minute = config.schedule_value
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run

        elif config.schedule_type == ScheduleType.WEEKLY:
            weekday, hour, minute = config.schedule_value
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            days_ahead = (weekday - next_run.weekday()) % 7
            if days_ahead == 0 and next_run <= now:
                days_ahead = 7
            next_run += timedelta(days=days_ahead)
            return next_run

        return None

    def _should_run(self, config: TaskConfig) -> bool:
        """检查任务是否应该运行"""
        if not config.enabled:
            return False

        hist = self._history.get(config.name)
        if not hist or not hist.last_run:
            return True

        try:
            last_run = datetime.strptime(hist.last_run, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return True

        now = datetime.now()

        if config.schedule_type == ScheduleType.INTERVAL:
            minutes = config.schedule_value
            elapsed_seconds: float = (now - last_run).total_seconds()
            return bool(elapsed_seconds >= minutes * 60)

        elif config.schedule_type == ScheduleType.DAILY:
            hour, minute = config.schedule_value
            scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            return bool(scheduled_time > last_run and now >= scheduled_time)

        elif config.schedule_type == ScheduleType.WEEKLY:
            weekday, hour, minute = config.schedule_value
            if now.weekday() == weekday:
                scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if scheduled_time > last_run and now >= scheduled_time:
                    return True
            return False

        return False

    def _execute_task(self, config: TaskConfig) -> TaskResult:
        """执行任务"""
        result = TaskResult(
            task_name=config.name,
            status=TaskStatus.RUNNING,
            start_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        retry_count = 0
        last_error = None

        while retry_count <= config.max_retries:
            try:
                logger.info(f"执行任务: {config.name} (尝试 {retry_count + 1}/{config.max_retries + 1})")

                task_result = config.func()

                result.status = TaskStatus.COMPLETED
                result.result = task_result
                result.end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                result.duration = (
                    datetime.strptime(result.end_time, "%Y-%m-%d %H:%M:%S")
                    - datetime.strptime(result.start_time, "%Y-%m-%d %H:%M:%S")
                ).total_seconds()
                result.retry_count = retry_count

                logger.info(f"任务完成: {config.name}, 耗时: {result.duration:.2f}s")
                break

            except Exception as e:
                last_error = str(e)
                retry_count += 1
                result.retry_count = retry_count

                if retry_count <= config.max_retries:
                    logger.warning(f"任务失败，{config.retry_delay}秒后重试: {config.name}, 错误: {e}")
                    time.sleep(config.retry_delay)
                else:
                    result.status = TaskStatus.FAILED
                    result.error = last_error
                    result.end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    result.duration = (
                        datetime.strptime(result.end_time, "%Y-%m-%d %H:%M:%S")
                        - datetime.strptime(result.start_time, "%Y-%m-%d %H:%M:%S")
                    ).total_seconds()

                    logger.error(f"任务最终失败: {config.name}, 错误: {last_error}")

        return result

    def run_task(self, name: str) -> TaskResult | None:
        """手动运行任务"""
        if name not in self._tasks:
            logger.warning(f"任务不存在: {name}")
            return None

        config = self._tasks[name]
        result = self._execute_task(config)

        with self._lock:
            if name not in self._history:
                self._history[name] = TaskHistory(task_name=name)
            self._history[name].add_result(result)
            self._save_history()

        return result

    def _run_loop(self):
        """调度循环"""
        logger.info("任务调度器启动")

        while self._running:
            try:
                with self._lock:
                    tasks_to_run = [(name, config) for name, config in self._tasks.items() if self._should_run(config)]

                for name, config in tasks_to_run:
                    if not self._running:
                        break

                    result = self._execute_task(config)

                    with self._lock:
                        if name in self._history:
                            self._history[name].add_result(result)
                            next_run = self._calculate_next_run(config)
                            if next_run:
                                self._history[name].next_run = next_run.strftime("%Y-%m-%d %H:%M:%S")
                        self._save_history()

                time.sleep(60)

            except Exception as e:
                logger.error(f"调度循环错误: {e}")
                time.sleep(60)

        logger.info("任务调度器停止")

    def start(self):
        """启动调度器"""
        if self._running:
            logger.warning("调度器已在运行")
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("任务调度器已启动")

    def stop(self):
        """停止调度器"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("任务调度器已停止")

    def is_running(self) -> bool:
        """检查调度器是否运行"""
        return self._running

    def get_task_status(self, name: str) -> dict[str, Any] | None:
        """获取任务状态"""
        if name not in self._tasks:
            return None

        config = self._tasks[name]
        hist = self._history.get(name, TaskHistory(task_name=name))

        return {
            "name": config.name,
            "description": config.description,
            "enabled": config.enabled,
            "schedule_type": config.schedule_type.value,
            "schedule_value": config.schedule_value,
            "last_run": hist.last_run,
            "next_run": hist.next_run,
            "total_runs": hist.total_runs,
            "success_count": hist.success_count,
            "fail_count": hist.fail_count,
        }

    def get_all_tasks(self) -> list[dict[str, Any]]:
        """获取所有任务状态"""
        tasks: list[dict[str, Any]] = []
        for name in self._tasks:
            status = self.get_task_status(name)
            if status is not None:
                tasks.append(status)
        return tasks

    def get_task_history(self, name: str, limit: int = 10) -> list[dict[str, Any]]:
        """获取任务执行历史"""
        if name not in self._history:
            return []

        return [r.to_dict() for r in self._history[name].results[-limit:]]


task_scheduler = TaskScheduler()


def register_default_tasks():
    """注册默认任务"""

    def update_data_task():
        from asset_lens.db.migration import DataMigration

        migration = DataMigration()
        result = migration.fetch_and_store_history(
            codes=[],
            days=90,
            data_source="auto",
            delay=0.2,
        )
        return f"更新 {result['success']} 只股票数据"

    def risk_check_task():
        from asset_lens.data.csv_parser import CSVParser
        from asset_lens.monitoring.risk_alert import risk_alert_system

        parser = CSVParser()
        products = parser.load_data()

        holdings: dict[str, float] = {}
        portfolio_data: dict[str, Any] = {
            "holdings": holdings,
            "position": 100,
            "stocks": [],
        }

        for product in products:
            current = float(product.current_amount or product.total_amount or 0)
            if current > 0:
                code = product.code if hasattr(product, "code") else (product.name or "unknown")
                portfolio_data["holdings"][code] = current

        alerts = risk_alert_system.run_all_checks(portfolio_data)
        return f"发现 {len(alerts)} 条预警"

    def backup_task():
        import shutil

        from asset_lens.config import config

        backup_dir = config.cache_path / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"backup_{timestamp}.json"

        data_file = config.cache_path / "investment_data.json"
        if data_file.exists():
            shutil.copy(data_file, backup_file)

        old_backups = sorted(backup_dir.glob("backup_*.json"))[:-7]
        for old in old_backups:
            old.unlink()

        return f"备份完成: {backup_file.name}"

    def report_task():
        from asset_lens.data.csv_parser import CSVParser

        parser = CSVParser()
        products = parser.load_data()

        total_assets = sum(float(p.current_amount or p.total_amount or 0) for p in products)
        total_profit = sum(float(p.profit_amount or 0) for p in products)

        return f"总资产: ¥{total_assets:,.2f}, 收益: ¥{total_profit:,.2f}"

    task_scheduler.register_task(
        TaskConfig(
            name="update_data",
            func=update_data_task,
            schedule_type=ScheduleType.DAILY,
            schedule_value=(9, 30),
            description="每日更新股票数据",
        )
    )

    task_scheduler.register_task(
        TaskConfig(
            name="risk_check",
            func=risk_check_task,
            schedule_type=ScheduleType.INTERVAL,
            schedule_value=60,
            description="每小时风险检查",
        )
    )

    task_scheduler.register_task(
        TaskConfig(
            name="backup",
            func=backup_task,
            schedule_type=ScheduleType.DAILY,
            schedule_value=(23, 0),
            description="每日备份",
        )
    )

    task_scheduler.register_task(
        TaskConfig(
            name="daily_report",
            func=report_task,
            schedule_type=ScheduleType.DAILY,
            schedule_value=(15, 30),
            description="每日报告",
        )
    )
