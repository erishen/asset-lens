"""
Tests for Alert Monitor.
异动提醒模块测试
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from asset_lens.analysis.alert_monitor import (
    AlertMonitor,
    AlertType,
    AlertThreshold,
    StockSnapshot,
    StockAlert,
    alert_monitor,
)


class TestAlertThreshold:
    """测试异动阈值配置"""

    def test_default_threshold(self):
        """测试默认阈值"""
        threshold = AlertThreshold()

        assert threshold.price_up_percent == 5.0
        assert threshold.price_down_percent == -5.0
        assert threshold.volume_surge_ratio == 2.0
        assert threshold.volume_shrink_ratio == 0.5

    def test_custom_threshold(self):
        """测试自定义阈值"""
        threshold = AlertThreshold(
            price_up_percent=3.0,
            price_down_percent=-3.0,
        )

        assert threshold.price_up_percent == 3.0
        assert threshold.price_down_percent == -3.0


class TestStockSnapshot:
    """测试股票快照"""

    def test_create_snapshot(self):
        """测试创建快照"""
        snapshot = StockSnapshot(
            code="sh600519",
            name="贵州茅台",
            price=1800.0,
            change_percent=2.5,
            volume=1000000,
            turnover=1800000000,
            high=1820.0,
            low=1780.0,
            open=1790.0,
            prev_close=1756.0,
        )

        assert snapshot.code == "sh600519"
        assert snapshot.price == 1800.0
        assert snapshot.change_percent == 2.5

    def test_is_limit_up(self):
        """测试涨停判断"""
        snapshot = StockSnapshot(
            code="sh600519",
            name="贵州茅台",
            price=1920.0,
            change_percent=9.95,
            volume=1000000,
            turnover=0,
            high=1920.0,
            low=1850.0,
            open=1850.0,
            prev_close=1756.0,
        )

        assert snapshot.is_limit_up is True
        assert snapshot.is_limit_down is False

    def test_is_limit_down(self):
        """测试跌停判断"""
        snapshot = StockSnapshot(
            code="sh600519",
            name="贵州茅台",
            price=1580.0,
            change_percent=-9.95,
            volume=1000000,
            turnover=0,
            high=1700.0,
            low=1580.0,
            open=1750.0,
            prev_close=1756.0,
        )

        assert snapshot.is_limit_down is True
        assert snapshot.is_limit_up is False

    def test_amplitude(self):
        """测试振幅计算"""
        snapshot = StockSnapshot(
            code="sh600519",
            name="贵州茅台",
            price=1800.0,
            change_percent=2.5,
            volume=1000000,
            turnover=0,
            high=1820.0,
            low=1780.0,
            open=1790.0,
            prev_close=1800.0,
        )

        assert snapshot.amplitude == pytest.approx(2.22, rel=0.1)


class TestStockAlert:
    """测试股票异动"""

    def test_create_alert(self):
        """测试创建异动"""
        alert = StockAlert(
            code="sh600519",
            name="贵州茅台",
            alert_type=AlertType.PRICE_UP,
            current_price=1800.0,
            change_percent=5.5,
            description="涨幅超过阈值",
            severity="high",
        )

        assert alert.code == "sh600519"
        assert alert.alert_type == AlertType.PRICE_UP


class TestAlertMonitor:
    """测试异动监控器"""

    def test_init(self, tmp_path):
        """测试初始化"""
        monitor = AlertMonitor(cache_path=tmp_path)
        assert monitor.cache_path == tmp_path

    def test_check_price_alert_up(self, tmp_path):
        """测试涨幅异动"""
        monitor = AlertMonitor(cache_path=tmp_path)

        snapshot = StockSnapshot(
            code="sh600519",
            name="贵州茅台",
            price=1800.0,
            change_percent=6.5,
            volume=1000000,
            turnover=0,
            high=1820.0,
            low=1780.0,
            open=1790.0,
            prev_close=1756.0,
        )

        alert = monitor.check_price_alert(snapshot)

        assert alert is not None
        assert alert.alert_type == AlertType.PRICE_UP
        assert "涨幅" in alert.description

    def test_check_price_alert_down(self, tmp_path):
        """测试跌幅异动"""
        monitor = AlertMonitor(cache_path=tmp_path)

        snapshot = StockSnapshot(
            code="sh600519",
            name="贵州茅台",
            price=1650.0,
            change_percent=-6.5,
            volume=1000000,
            turnover=0,
            high=1750.0,
            low=1650.0,
            open=1750.0,
            prev_close=1756.0,
        )

        alert = monitor.check_price_alert(snapshot)

        assert alert is not None
        assert alert.alert_type == AlertType.PRICE_DOWN
        assert "跌幅" in alert.description

    def test_check_price_alert_no_alert(self, tmp_path):
        """测试无价格异动"""
        monitor = AlertMonitor(cache_path=tmp_path)

        snapshot = StockSnapshot(
            code="sh600519",
            name="贵州茅台",
            price=1800.0,
            change_percent=2.0,
            volume=1000000,
            turnover=0,
            high=1820.0,
            low=1780.0,
            open=1790.0,
            prev_close=1756.0,
        )

        alert = monitor.check_price_alert(snapshot)

        assert alert is None

    def test_check_volume_alert_surge(self, tmp_path):
        """测试放量异动"""
        monitor = AlertMonitor(cache_path=tmp_path)

        snapshot = StockSnapshot(
            code="sh600519",
            name="贵州茅台",
            price=1800.0,
            change_percent=2.0,
            volume=3000000,
            turnover=0,
            high=1820.0,
            low=1780.0,
            open=1790.0,
            prev_close=1756.0,
        )

        alert = monitor.check_volume_alert(snapshot, avg_volume=1000000)

        assert alert is not None
        assert alert.alert_type == AlertType.VOLUME_SURGE

    def test_check_volume_alert_shrink(self, tmp_path):
        """测试缩量异动"""
        monitor = AlertMonitor(cache_path=tmp_path)

        snapshot = StockSnapshot(
            code="sh600519",
            name="贵州茅台",
            price=1800.0,
            change_percent=2.0,
            volume=300000,
            turnover=0,
            high=1820.0,
            low=1780.0,
            open=1790.0,
            prev_close=1756.0,
        )

        alert = monitor.check_volume_alert(snapshot, avg_volume=1000000)

        assert alert is not None
        assert alert.alert_type == AlertType.VOLUME_SHRINK

    def test_check_limit_alert_up(self, tmp_path):
        """测试涨停异动"""
        monitor = AlertMonitor(cache_path=tmp_path)

        snapshot = StockSnapshot(
            code="sh600519",
            name="贵州茅台",
            price=1920.0,
            change_percent=10.0,
            volume=1000000,
            turnover=0,
            high=1920.0,
            low=1850.0,
            open=1850.0,
            prev_close=1756.0,
        )

        alert = monitor.check_limit_alert(snapshot)

        assert alert is not None
        assert alert.alert_type == AlertType.LIMIT_UP

    def test_check_limit_alert_down(self, tmp_path):
        """测试跌停异动"""
        monitor = AlertMonitor(cache_path=tmp_path)

        snapshot = StockSnapshot(
            code="sh600519",
            name="贵州茅台",
            price=1580.0,
            change_percent=-10.0,
            volume=1000000,
            turnover=0,
            high=1700.0,
            low=1580.0,
            open=1750.0,
            prev_close=1756.0,
        )

        alert = monitor.check_limit_alert(snapshot)

        assert alert is not None
        assert alert.alert_type == AlertType.LIMIT_DOWN

    def test_check_price_level_support_break(self, tmp_path):
        """测试跌破支撑"""
        monitor = AlertMonitor(cache_path=tmp_path)

        snapshot = StockSnapshot(
            code="sh600519",
            name="贵州茅台",
            price=1700.0,
            change_percent=-3.0,
            volume=1000000,
            turnover=0,
            high=1750.0,
            low=1700.0,
            open=1750.0,
            prev_close=1756.0,
        )

        alert = monitor.check_price_level_alert(snapshot, support_level=1750.0)

        assert alert is not None
        assert alert.alert_type == AlertType.SUPPORT_BREAK

    def test_check_price_level_resistance_break(self, tmp_path):
        """测试突破阻力"""
        monitor = AlertMonitor(cache_path=tmp_path)

        snapshot = StockSnapshot(
            code="sh600519",
            name="贵州茅台",
            price=1850.0,
            change_percent=5.0,
            volume=1000000,
            turnover=0,
            high=1860.0,
            low=1800.0,
            open=1800.0,
            prev_close=1756.0,
        )

        alert = monitor.check_price_level_alert(snapshot, resistance_level=1820.0)

        assert alert is not None
        assert alert.alert_type == AlertType.RESISTANCE_BREAK

    def test_monitor_returns_alerts(self, tmp_path):
        """测试监控返回异动"""
        monitor = AlertMonitor(cache_path=tmp_path)

        snapshot = StockSnapshot(
            code="sh600519",
            name="贵州茅台",
            price=1920.0,
            change_percent=10.0,
            volume=3000000,
            turnover=0,
            high=1920.0,
            low=1850.0,
            open=1850.0,
            prev_close=1756.0,
        )

        alerts = monitor.monitor(snapshot, avg_volume=1000000)

        assert len(alerts) >= 2

    def test_save_alert(self, tmp_path):
        """测试保存异动"""
        from asset_lens.analysis.signal_pusher import Priority

        monitor = AlertMonitor(cache_path=tmp_path)

        alert = StockAlert(
            code="sh600519",
            name="贵州茅台",
            alert_type=AlertType.PRICE_UP,
            current_price=1800.0,
            change_percent=6.5,
            description="涨幅超过阈值",
            severity=Priority.HIGH,
        )

        monitor._save_alert(alert)

        assert monitor.alert_history_file.exists()

        with open(monitor.alert_history_file, encoding="utf-8") as f:
            history = json.load(f)

        assert len(history) == 1
        assert history[0]["code"] == "sh600519"

    def test_get_recent_alerts(self, tmp_path):
        """测试获取最近异动"""
        from asset_lens.analysis.signal_pusher import Priority

        monitor = AlertMonitor(cache_path=tmp_path)

        for i in range(5):
            alert = StockAlert(
                code=f"sh60051{i}",
                name=f"股票{i}",
                alert_type=AlertType.PRICE_UP,
                current_price=10.0 + i,
                change_percent=5.0,
                description="测试",
                severity=Priority.MEDIUM,
            )
            monitor._save_alert(alert)

        recent = monitor.get_recent_alerts(limit=3)

        assert len(recent) == 3


class TestAlertMonitorInstance:
    """测试全局实例"""

    def test_global_instance_exists(self):
        """测试全局实例存在"""
        assert alert_monitor is not None
        assert isinstance(alert_monitor, AlertMonitor)


class TestAlertTypeEnum:
    """测试异动类型枚举"""

    def test_alert_types(self):
        """测试所有异动类型"""
        assert AlertType.PRICE_UP.value == "price_up"
        assert AlertType.PRICE_DOWN.value == "price_down"
        assert AlertType.VOLUME_SURGE.value == "volume_surge"
        assert AlertType.LIMIT_UP.value == "limit_up"
        assert AlertType.LIMIT_DOWN.value == "limit_down"
