"""
Tests for Notification Manager
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from asset_lens.data.notification_manager import (
    NotificationManager,
    NotificationConfig,
)


@pytest.fixture
def notification_manager():
    """创建通知管理器实例"""
    return NotificationManager()


class TestNotificationConfig:
    """测试通知配置"""

    def test_config_creation(self):
        """测试创建配置"""
        config = NotificationConfig(
            email_enabled=True,
            email_smtp_server="smtp.gmail.com",
            email_smtp_port=587,
            email_username="test@gmail.com",
            email_password="password",
            email_recipients=["user@example.com"],
            wechat_enabled=True,
            wechat_server_key="test_key",
        )

        assert config.email_enabled is True
        assert config.email_smtp_server == "smtp.gmail.com"
        assert config.email_smtp_port == 587
        assert config.email_username == "test@gmail.com"
        assert config.email_password == "password"
        assert config.email_recipients == ["user@example.com"]
        assert config.wechat_enabled is True
        assert config.wechat_server_key == "test_key"

    def test_config_defaults(self):
        """测试配置默认值"""
        config = NotificationConfig()

        assert config.email_enabled is False
        assert config.email_smtp_server == "smtp.gmail.com"
        assert config.email_smtp_port == 587
        assert config.email_username == ""
        assert config.email_password == ""
        assert config.email_recipients == []
        assert config.wechat_enabled is False
        assert config.wechat_server_key == ""


class TestNotificationManager:
    """测试通知管理器"""

    def test_init(self, notification_manager):
        """测试初始化"""
        assert notification_manager.config is not None
        assert notification_manager.template_path is not None

    def test_send_email_disabled(self, notification_manager):
        """测试发送邮件 - 未启用"""
        notification_manager.config.email_enabled = False

        result = notification_manager.send_email("Test", "Content")

        assert result is False

    def test_send_email_no_recipients(self, notification_manager):
        """测试发送邮件 - 无收件人"""
        notification_manager.config.email_enabled = True
        notification_manager.config.email_recipients = []

        result = notification_manager.send_email("Test", "Content")

        assert result is False

    def test_send_wechat_disabled(self, notification_manager):
        """测试发送微信 - 未启用"""
        notification_manager.config.wechat_enabled = False

        result = notification_manager.send_wechat("Test", "Content")

        assert result is False

    def test_send_wechat_no_key(self, notification_manager):
        """测试发送微信 - 无 Key"""
        notification_manager.config.wechat_enabled = True
        notification_manager.config.wechat_server_key = ""

        result = notification_manager.send_wechat("Test", "Content")

        assert result is False

    def test_send_notification_email_only_disabled(self, notification_manager):
        """测试发送通知 - 仅邮件但未启用"""
        notification_manager.config.email_enabled = False
        notification_manager.config.wechat_enabled = False

        result = notification_manager.send_notification(
            "Test", "Content", channels=["email"]
        )

        assert result["email"] is False

    def test_send_notification_wechat_only_disabled(self, notification_manager):
        """测试发送通知 - 仅微信但未启用"""
        notification_manager.config.email_enabled = False
        notification_manager.config.wechat_enabled = False

        result = notification_manager.send_notification(
            "Test", "Content", channels=["wechat"]
        )

        assert result["wechat"] is False

    def test_format_daily_report_text(self, notification_manager):
        """测试格式化每日报告文本"""
        data = {
            "total_assets": 100000,
            "total_profit": 5000,
            "total_return": 0.05,
            "positions": [
                {"name": "贵州茅台", "code": "sh600519", "profit_rate": 0.1},
            ],
        }

        text = notification_manager._format_daily_report_text(data)

        assert "每日投资报告" in text
        assert "100,000" in text  # 格式化后带有逗号
        assert "5,000" in text

    def test_format_daily_report_html(self, notification_manager):
        """测试格式化每日报告 HTML"""
        data = {
            "total_assets": 100000,
            "total_profit": 5000,
            "total_return": 0.05,
            "positions": [
                {"name": "贵州茅台", "code": "sh600519", "profit_rate": 0.1},
            ],
        }

        html = notification_manager._format_daily_report_html(data)

        assert "<!DOCTYPE html>" in html
        assert "每日投资报告" in html
        assert "100,000" in html  # 格式化后带有逗号

    def test_notify_daily_report_disabled(self, notification_manager):
        """测试发送每日报告 - 未启用"""
        notification_manager.config.email_enabled = False
        notification_manager.config.wechat_enabled = False

        report_data = {
            "total_assets": 100000,
            "total_profit": 5000,
            "total_return": 0.05,
            "positions": [],
        }

        result = notification_manager.notify_daily_report(report_data)

        # send_notification returns a dict, not a bool
        assert isinstance(result, dict)

    def test_notify_risk_alert_disabled(self, notification_manager):
        """测试发送风险预警 - 未启用"""
        notification_manager.config.email_enabled = False
        notification_manager.config.wechat_enabled = False

        alert_data = {
            "type": "market_crash",
            "level": "high",
            "message": "市场大幅下跌",
            "recommendation": "降低仓位",
        }

        result = notification_manager.notify_risk_alert(alert_data)

        # send_notification returns a dict, not a bool
        assert isinstance(result, dict)

    def test_notify_trade_signal_disabled(self, notification_manager):
        """测试发送交易信号 - 未启用"""
        notification_manager.config.email_enabled = False
        notification_manager.config.wechat_enabled = False

        signal_data = {
            "code": "sh600519",
            "name": "贵州茅台",
            "signal_type": "buy",
            "price": 1800.0,
            "reason": "技术指标买入信号",
        }

        result = notification_manager.notify_trade_signal(signal_data)

        # send_notification returns a dict, not a bool
        assert isinstance(result, dict)
