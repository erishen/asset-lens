"""
Tests for Investment Monitor.
投资监控系统测试
"""

import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from asset_lens.monitoring.investment_monitor import Alert, InvestmentMonitor, MonitorConfig


class TestInvestmentMonitor:
    """测试投资监控系统"""

    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config = MonitorConfig(
            price_threshold=5.0,
            volatility_threshold=20.0,
            max_drawdown_threshold=10.0,
            concentration_threshold=30.0,
            check_interval=300,
        )
        self.monitor = InvestmentMonitor(self.config)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_monitor_creation(self):
        assert self.monitor.config is not None
        assert self.monitor.config.price_threshold == 5.0

    def test_run_asset_lens_command(self):
        result = self.monitor.run_asset_lens_command("version")
        assert "success" in result

    def test_monitor_portfolio_performance(self):
        result = self.monitor.monitor_portfolio_performance()
        assert "status" in result
        assert "timestamp" in result

    def test_monitor_stock_prices(self):
        result = self.monitor.monitor_stock_prices(["sh600519"])
        assert "stocks" in result
        assert "timestamp" in result

    def test_monitor_market_indices(self):
        result = self.monitor.monitor_market_indices()
        assert "indices" in result
        assert "timestamp" in result

    def test_check_price_alerts(self):
        stock_data = {"stocks": {"sh600519": {"status": "success", "data": {"change_percent": 6.0}}}}

        alerts = self.monitor.check_price_alerts(stock_data)
        assert len(alerts) > 0
        assert alerts[0].type == "price_change"

    def test_check_concentration_risk(self):
        portfolio_data = {}
        alert = self.monitor.check_concentration_risk(portfolio_data)
        assert alert is None or isinstance(alert, Alert)

    def test_generate_daily_report(self):
        report = self.monitor.generate_daily_report()
        assert "投资监控每日报告" in report
        assert datetime.now().strftime("%Y-%m-%d") in report

    def test_generate_weekly_report(self):
        report = self.monitor.generate_weekly_report()
        assert "投资监控周度报告" in report
        assert datetime.now().strftime("%Y-%m-%d") in report

    def test_save_alert(self):
        alert = Alert(
            level="high",
            type="price_change",
            message="测试预警",
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            data={"test": "data"},
        )

        self.monitor.save_alert(alert)
        assert len(self.monitor.alerts) == 1
        assert self.monitor.alerts[0].message == "测试预警"

    def test_run_continuous_monitoring(self):
        self.monitor.run_continuous_monitoring()
        assert self.monitor.running is True

        self.monitor.stop_monitoring()
        assert self.monitor.running is False


class TestMonitorConfig:
    """测试监控配置"""

    def test_default_config(self):
        config = MonitorConfig()
        assert config.price_threshold == 5.0
        assert config.volatility_threshold == 20.0
        assert config.max_drawdown_threshold == 10.0
        assert config.concentration_threshold == 30.0
        assert config.check_interval == 300
        assert config.enable_alerts is True

    def test_custom_config(self):
        config = MonitorConfig(
            price_threshold=10.0,
            volatility_threshold=30.0,
            max_drawdown_threshold=15.0,
            concentration_threshold=40.0,
            check_interval=600,
            enable_alerts=False,
        )
        assert config.price_threshold == 10.0
        assert config.volatility_threshold == 30.0
        assert config.max_drawdown_threshold == 15.0
        assert config.concentration_threshold == 40.0
        assert config.check_interval == 600
        assert config.enable_alerts is False


class TestAlert:
    """测试预警信息"""

    def test_alert_creation(self):
        alert = Alert(
            level="high",
            type="price_change",
            message="股票价格变动超过阈值",
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            data={"code": "sh600519", "change_percent": 6.0},
        )

        assert alert.level == "high"
        assert alert.type == "price_change"
        assert alert.message == "股票价格变动超过阈值"
        assert alert.data["code"] == "sh600519"
