"""
Investment Monitoring System - 实时投资监控系统
整合多维度监控、风险管理、报告生成
"""

import json
import logging
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logging.raiseExceptions = False

logger = logging.getLogger(__name__)


def _safe_log(level: str, msg: str):
    """安全日志函数 - 忽略日志流关闭错误"""
    try:
        if sys.stderr is None or sys.stderr.closed:
            return
        for handler in logger.handlers:
            if hasattr(handler, "stream") and (
                handler.stream is None or (hasattr(handler.stream, "closed") and handler.stream.closed)
            ):
                return
        if not logger.handlers:
            return
        log_func = getattr(logger, level, None)
        if log_func:
            log_func(msg)
    except Exception as e:
        logger.debug(f"忽略异常: {e}")


@dataclass
class MonitorConfig:
    """监控配置"""

    price_threshold: float = 5.0
    volatility_threshold: float = 20.0
    max_drawdown_threshold: float = 10.0
    concentration_threshold: float = 30.0
    check_interval: int = 300
    enable_alerts: bool = True


@dataclass
class Alert:
    """预警信息"""

    level: str
    type: str
    message: str
    timestamp: str
    data: dict[str, Any] = field(default_factory=dict)


class InvestmentMonitor:
    """实时投资监控系统"""

    def __init__(self, config: MonitorConfig | None = None):
        self.config = config or MonitorConfig()
        self.alerts: list[Alert] = []
        self.running = False
        self._cache_path = Path("cache")
        self._cache_path.mkdir(parents=True, exist_ok=True)

    def run_asset_lens_command(self, command: str, args: list[str] | None = None) -> dict[str, Any]:
        """运行 asset-lens 命令"""
        try:
            # 处理命令路径，将旧命令映射到新的命令组结构
            command_mapping = {
                "version": ["system", "version"],
                "check": ["system", "check"],
                "analyze": ["analyze", "portfolio"],
                "fetch-stock": ["data", "fetch-stock"],
                "fetch-fund": ["data", "fetch-fund"],
            }

            # 如果命令在映射中，使用新的命令路径
            cmd_parts = command_mapping.get(command, [command])

            cmd = ["python", "-m", "asset_lens", *cmd_parts]
            if args:
                cmd.extend(args)

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(Path.cwd()))

            if result.returncode == 0:
                return {"success": True, "output": result.stdout}
            else:
                return {"success": False, "error": result.stderr}
        except Exception as e:
            _safe_log("error", f"运行命令失败: {command}, {e}")
            return {"success": False, "error": str(e)}

    def monitor_portfolio_performance(self) -> dict[str, Any]:
        """监控投资组合表现"""
        _safe_log("info", "监控投资组合表现...")

        result = self.run_asset_lens_command("analyze")

        if result["success"]:
            return {
                "status": "success",
                "data": result["output"],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        else:
            return {
                "status": "error",
                "error": result["error"],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

    def monitor_stock_prices(self, stock_codes: list[str]) -> dict[str, Any]:
        """监控股票价格"""
        _safe_log("info", f"监控股票价格: {stock_codes}")

        results = {}
        for code in stock_codes:
            result = self.run_asset_lens_command("fetch-stock", [code])
            if result["success"]:
                results[code] = {"status": "success", "data": result["output"]}
            else:
                results[code] = {"status": "error", "error": result["error"]}

        return {"stocks": results, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    def monitor_market_indices(self) -> dict[str, Any]:
        """监控市场指数"""
        _safe_log("info", "监控市场指数...")

        indices = {"sh000300": "沪深300", "sh000016": "上证50", "sz399006": "创业板指", "sh000688": "科创50"}

        results = {}
        for code, name in indices.items():
            result = self.run_asset_lens_command("fetch-stock", [code])
            if result["success"]:
                results[name] = {"code": code, "data": result["output"]}

        return {"indices": results, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    def check_price_alerts(self, stock_data: dict[str, Any]) -> list[Alert]:
        """检查价格预警"""
        alerts = []

        for code, data in stock_data.get("stocks", {}).items():
            if data.get("status") == "success":
                try:
                    output = data["data"]
                    if "change_percent" in output:
                        change_percent = float(output["change_percent"])

                        if abs(change_percent) >= self.config.price_threshold:
                            level = "high" if abs(change_percent) >= 10 else "medium"
                            alert = Alert(
                                level=level,
                                type="price_change",
                                message=f"{code} 价格变动 {change_percent:+.2f}%",
                                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                data={"code": code, "change_percent": change_percent},
                            )
                            alerts.append(alert)
                except (ValueError, KeyError) as e:
                    _safe_log("error", f"解析价格数据失败: {code}, {e}")

        return alerts

    def check_concentration_risk(self, portfolio_data: dict[str, Any]) -> Alert | None:
        """检查集中度风险"""
        _safe_log("info", "检查集中度风险...")

        result = self.run_asset_lens_command("stock-pool-status")

        if result["success"]:
            try:
                output = result["output"]

                if "concentration" in output:
                    concentration = float(output["concentration"])

                    if concentration >= self.config.concentration_threshold:
                        return Alert(
                            level="high",
                            type="concentration_risk",
                            message=f"投资组合集中度过高: {concentration:.2f}%",
                            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            data={"concentration": concentration},
                        )
            except (ValueError, KeyError) as e:
                _safe_log("error", f"解析集中度数据失败: {e}")

        return None

    def generate_daily_report(self) -> str:
        """生成每日监控报告"""
        _safe_log("info", "生成每日监控报告...")

        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("📊 投资监控每日报告")
        report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("=" * 60)
        report_lines.append("")

        portfolio = self.monitor_portfolio_performance()
        if portfolio["status"] == "success":
            report_lines.append("📈 投资组合表现:")
            report_lines.append(portfolio["data"][:500])
            report_lines.append("")

        indices = self.monitor_market_indices()
        report_lines.append("📊 市场指数:")
        for name, data in indices.get("indices", {}).items():
            report_lines.append(f"  • {name} ({data['code']})")
        report_lines.append("")

        if self.alerts:
            report_lines.append("⚠️ 预警信息:")
            report_lines.extend(f"  [{alert.level}] {alert.type}: {alert.message}" for alert in self.alerts[-5:])
            report_lines.append("")

        report_lines.append("💡 投资建议:")
        report_lines.append("  • 关注市场指数走势")
        report_lines.append("  • 定期检查投资组合风险")
        report_lines.append("  • 保持投资纪律")
        report_lines.append("")
        report_lines.append("=" * 60)

        return "\n".join(report_lines)

    def generate_weekly_report(self) -> str:
        """生成每周分析报告"""
        _safe_log("info", "生成每周分析报告...")

        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("📊 投资监控周度报告")
        report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("=" * 60)
        report_lines.append("")

        report_lines.append("🎯 本周市场回顾:")
        report_lines.append("  • 市场指数表现分析")
        report_lines.append("  • 投资组合收益评估")
        report_lines.append("  • 风险指标监控")
        report_lines.append("")

        report_lines.append("📊 数据分析:")
        report_lines.append("  • 使用 asset-lens 实时市场数据")
        report_lines.append("  • 动量策略筛选结果")
        report_lines.append("  • 风险收益评估")
        report_lines.append("")

        report_lines.append("💡 下周策略:")
        report_lines.append("  • 关注动量策略选股")
        report_lines.append("  • 控制投资组合风险")
        report_lines.append("  • 保持长期投资视角")
        report_lines.append("")

        report_lines.append("=" * 60)

        return "\n".join(report_lines)

    def save_alert(self, alert: Alert):
        """保存预警信息"""
        self.alerts.append(alert)

        alert_file = self._cache_path / "alerts.json"
        alerts_data = []

        if alert_file.exists():
            try:
                with open(alert_file, encoding="utf-8") as f:
                    alerts_data = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                _safe_log("warning", f"加载告警历史失败: {e}")
                alerts_data = []

        alerts_data.append(
            {
                "level": alert.level,
                "type": alert.type,
                "message": alert.message,
                "timestamp": alert.timestamp,
                "data": alert.data,
            }
        )

        with open(alert_file, "w", encoding="utf-8") as f:
            json.dump(alerts_data, f, ensure_ascii=False, indent=2)

    def run_continuous_monitoring(self):
        """运行持续监控"""
        _safe_log("info", "启动持续监控...")
        self.running = True

        def monitor_task():
            while self.running:
                try:
                    portfolio = self.monitor_portfolio_performance()

                    concentration_alert = self.check_concentration_risk(portfolio)
                    if concentration_alert:
                        self.save_alert(concentration_alert)
                        _safe_log("warning", f"预警: {concentration_alert.message}")

                    time.sleep(self.config.check_interval)

                except Exception as e:
                    _safe_log("error", f"监控任务异常: {e}")
                    time.sleep(60)

        monitor_thread = threading.Thread(target=monitor_task)
        monitor_thread.daemon = True
        monitor_thread.start()

        _safe_log("info", "持续监控已启动")

    def stop_monitoring(self):
        """停止监控"""
        self.running = False
        _safe_log("info", "监控已停止")


def create_monitor(config: MonitorConfig | None = None) -> InvestmentMonitor:
    """创建监控实例"""
    return InvestmentMonitor(config)
