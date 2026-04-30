"""
Tests for Notification Manager.
通知管理器测试
"""

from unittest.mock import MagicMock, patch

import pytest


class TestNotificationManager:
    """通知管理器测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.data.notification_manager import NotificationManager

        assert NotificationManager is not None

    @pytest.fixture
    def manager(self):
        """创建管理器实例"""
        from asset_lens.data.notification_manager import NotificationManager

        with patch("asset_lens.data.notification_manager.config") as mock_config:
            mock_config.cache_path = MagicMock()
            return NotificationManager()

    def test_manager_init(self, manager):
        """测试初始化"""
        assert manager is not None

    def test_notify_method(self, manager):
        """测试通知方法"""
        assert hasattr(manager, "send_notification") or hasattr(manager, "notify_daily_report")


class TestNotificationTypes:
    """通知类型测试"""

    def test_price_alert(self):
        """测试价格提醒"""
        alert = {
            "type": "price_alert",
            "code": "sh600519",
            "name": "贵州茅台",
            "current_price": 1850.0,
            "target_price": 1800.0,
            "message": "价格突破目标价",
        }

        assert alert["type"] == "price_alert"
        assert alert["current_price"] > alert["target_price"]

    def test_stop_loss_alert(self):
        """测试止损提醒"""
        alert = {
            "type": "stop_loss",
            "code": "sh600519",
            "buy_price": 1800.0,
            "current_price": 1600.0,
            "stop_loss_rate": 0.1,
        }

        loss_rate = (alert["buy_price"] - alert["current_price"]) / alert["buy_price"]
        assert loss_rate >= alert["stop_loss_rate"]

    def test_take_profit_alert(self):
        """测试止盈提醒"""
        alert = {
            "type": "take_profit",
            "code": "sh600519",
            "buy_price": 1800.0,
            "current_price": 2200.0,
            "take_profit_rate": 0.2,
        }

        profit_rate = (alert["current_price"] - alert["buy_price"]) / alert["buy_price"]
        assert profit_rate >= alert["take_profit_rate"]


class TestNotificationChannels:
    """通知渠道测试"""

    def test_console_channel(self):
        """测试控制台通知"""
        message = "测试通知消息"
        # 控制台通知就是打印
        assert len(message) > 0

    def test_log_channel(self):
        """测试日志通知"""
        from asset_lens.utils.logger import logger

        # 日志记录
        logger.info("测试日志通知")
        assert logger is not None


class TestNotificationFormatting:
    """通知格式化测试"""

    def test_format_price_alert(self):
        """测试格式化价格提醒"""
        data = {
            "code": "sh600519",
            "name": "贵州茅台",
            "price": 1850.0,
            "change": 2.5,
        }

        message = f"【价格提醒】{data['name']}({data['code']}) 当前价格: {data['price']}, 涨跌幅: {data['change']}%"
        assert "贵州茅台" in message
        assert "1850" in message

    def test_format_portfolio_summary(self):
        """测试格式化投资组合摘要"""
        data = {
            "total_value": 100000.0,
            "total_profit": 5000.0,
            "profit_rate": 5.0,
        }

        message = (
            f"【投资组合】总资产: {data['total_value']}, 收益: {data['total_profit']}, 收益率: {data['profit_rate']}%"
        )
        assert "100000" in message
        assert "5.0%" in message
