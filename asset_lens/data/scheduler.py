"""
Scheduler for asset-lens.
定时任务模块 - 自动执行每日数据记录、股票跟踪等任务

功能:
1. 每日数据更新 - 更新市场数据、基金净值
2. 股票池跟踪 - 记录股票池每日表现
3. 妖股检测 - 每日检测妖股信号
4. 报告生成 - 定期生成投资报告
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import config


class TaskScheduler:
    """定时任务调度器"""

    def __init__(self):
        self.cache_path = config.cache_path
        self.scheduler_path = self.cache_path / "scheduler"
        self.scheduler_path.mkdir(parents=True, exist_ok=True)
        self.log_file = self.scheduler_path / "task_log.json"
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self._load_log()

    def _load_log(self) -> None:
        """加载任务日志"""
        if self.log_file.exists():
            try:
                with open(self.log_file, "r", encoding="utf-8") as f:
                    self.tasks = json.load(f)
            except Exception:
                self.tasks = {}

    def _save_log(self) -> None:
        """保存任务日志"""
        with open(self.log_file, "w", encoding="utf-8") as f:
            json.dump(self.tasks, f, ensure_ascii=False, indent=2)

    def _log_task(self, task_name: str, status: str, message: str = "") -> None:
        """记录任务执行日志"""
        self.tasks[task_name] = {
            "last_run": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": status,
            "message": message,
        }
        self._save_log()

    def task_update_all_data(self) -> Dict[str, Any]:
        """
        任务: 更新所有数据

        Returns:
            执行结果
        """
        from .fund_fetcher import fetch_portfolio_fund_quotes
        from .stock_fetcher import stock_fetcher

        result: Dict[str, Any] = {
            "task": "update_all_data",
            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "running",
            "details": {},
        }

        try:
            fund_result = fetch_portfolio_fund_quotes()
            details_dict: Dict[str, Any] = result["details"]
            details_dict["funds"] = {
                "count": len(fund_result.get("data", {})),
                "status": "success" if fund_result.get("data") else "failed",
            }

            stock_codes_map = stock_fetcher._load_stock_codes_config()
            stock_codes = list(set(stock_codes_map.values()))
            if stock_codes:
                stock_result = stock_fetcher.fetch_multiple_stocks(stock_codes)
                details_dict["stocks"] = {
                    "count": len(stock_result.get("data", {})),
                    "status": "success" if stock_result.get("data") else "failed",
                }

            result["status"] = "completed"
            result["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            funds_info: Dict[str, Any] = details_dict.get("funds", {})
            self._log_task("update_all_data", "success", f"更新了 {funds_info.get('count', 0)} 只基金")

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            self._log_task("update_all_data", "failed", str(e))

        return result

    def task_track_stocks(self, pool_name: str = "momentum") -> Dict[str, Any]:
        """
        任务: 记录股票池每日数据

        Args:
            pool_name: 股票池名称

        Returns:
            执行结果
        """
        from .stock_tracker import StockTracker
        from .market_stock_fetcher import market_stock_fetcher

        result: Dict[str, Any] = {
            "task": "track_stocks",
            "pool_name": pool_name,
            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "running",
            "details": {},
        }

        try:
            tracker = StockTracker(pool_name)
            stocks = market_stock_fetcher.get_cached_market_stocks()

            if not stocks:
                stocks = market_stock_fetcher.fetch_all_cn_stocks()
                if stocks:
                    market_stock_fetcher.save_market_stocks(stocks)

            details_dict: Dict[str, Any] = result["details"]
            if stocks:
                count = tracker.record_batch(stocks)
                details_dict["recorded"] = count
                result["status"] = "completed"
                self._log_task("track_stocks", "success", f"记录了 {count} 只股票")
            else:
                result["status"] = "failed"
                result["error"] = "没有市场数据"
                self._log_task("track_stocks", "failed", "没有市场数据")

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            self._log_task("track_stocks", "failed", str(e))

        return result

    def task_detect_monster(self, pool_name: str = "momentum") -> Dict[str, Any]:
        """
        任务: 检测妖股信号

        Args:
            pool_name: 股票池名称

        Returns:
            执行结果
        """
        from .stock_tracker import StockTracker

        result: Dict[str, Any] = {
            "task": "detect_monster",
            "pool_name": pool_name,
            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "running",
            "details": {},
        }

        try:
            tracker = StockTracker(pool_name)
            signals = tracker.detect_monster_stocks()

            details_dict: Dict[str, Any] = result["details"]
            details_dict["signals_count"] = len(signals)
            details_dict["signals"] = [
                {
                    "code": s.code,
                    "name": s.name,
                    "score": s.score,
                    "signal_type": s.signal_type,
                }
                for s in signals[:10]
            ]
            result["status"] = "completed"
            self._log_task("detect_monster", "success", f"检测到 {len(signals)} 个妖股信号")

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            self._log_task("detect_monster", "failed", str(e))

        return result

    def task_momentum_screen(self) -> Dict[str, Any]:
        """
        任务: 动量策略选股

        Returns:
            执行结果
        """
        from .strategy_engine import strategy_engine
        from .stock_pool import StockPool
        from .market_stock_fetcher import market_stock_fetcher

        result: Dict[str, Any] = {
            "task": "momentum_screen",
            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "running",
            "details": {},
        }

        try:
            stocks = market_stock_fetcher.get_cached_market_stocks()
            if not stocks:
                stocks = market_stock_fetcher.fetch_all_cn_stocks()
                if stocks:
                    market_stock_fetcher.save_market_stocks(stocks)

            if stocks:
                results_list = strategy_engine.screen_stocks(stocks, "momentum", 60)
                details_dict: Dict[str, Any] = result["details"]
                details_dict["screened_count"] = len(results_list)

                pool = StockPool("momentum")
                added = 0
                for stock in results_list[:20]:
                    code = stock.get("code", "")
                    name = stock.get("name", "")
                    price = stock.get("current_price", 0)
                    score = stock.get("strategy_score", 0)
                    if pool.add_stock(code, name, price, "watching", f"策略得分: {score:.1f}", strategy_score=score):
                        added += 1

                details_dict["added_to_pool"] = added
                result["status"] = "completed"
                self._log_task("momentum_screen", "success", f"筛选出 {len(results_list)} 只，添加 {added} 只到股票池")
            else:
                result["status"] = "failed"
                result["error"] = "没有市场数据"
                self._log_task("momentum_screen", "failed", "没有市场数据")

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            self._log_task("momentum_screen", "failed", str(e))

        return result

    def run_daily_tasks(self) -> List[Dict[str, Any]]:
        """
        运行每日任务

        Returns:
            任务执行结果列表
        """
        results = []

        print(f"\n{'=' * 60}")
        print(f"📅 每日任务开始 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'=' * 60}")

        print("\n1️⃣ 更新数据...")
        results.append(self.task_update_all_data())

        print("\n2️⃣ 动量策略选股...")
        results.append(self.task_momentum_screen())

        print("\n3️⃣ 记录股票池数据...")
        results.append(self.task_track_stocks("momentum"))

        print("\n4️⃣ 检测妖股信号...")
        results.append(self.task_detect_monster("momentum"))

        print(f"\n{'=' * 60}")
        print(f"✅ 每日任务完成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'=' * 60}")

        return results

    def start_scheduler(
        self,
        daily_time: str = "09:30",
        run_on_start: bool = False,
    ) -> None:
        """
        启动定时调度器

        Args:
            daily_time: 每日执行时间
            run_on_start: 是否在启动时立即执行一次
        """
        print(f"\n🚀 启动定时任务调度器")
        print(f"   每日执行时间: {daily_time}")

        if run_on_start:
            print("   立即执行一次...")
            self.run_daily_tasks()

        hour, minute = map(int, daily_time.split(":"))

        print("   调度器运行中，按 Ctrl+C 停止...")

        try:
            while True:
                now = datetime.now()
                target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

                if now >= target:
                    target = target + timedelta(days=1)

                wait_seconds = (target - now).total_seconds()
                print(f"   下次执行时间: {target.strftime('%Y-%m-%d %H:%M:%S')} ({int(wait_seconds // 3600)}小时后)")

                time.sleep(min(wait_seconds, 3600))

                if datetime.now() >= target:
                    self.run_daily_tasks()

        except KeyboardInterrupt:
            print("\n\n⏹️ 调度器已停止")

    def get_task_status(self) -> Dict[str, Any]:
        """
        获取任务状态

        Returns:
            任务状态
        """
        return {
            "tasks": self.tasks,
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }


task_scheduler = TaskScheduler()
