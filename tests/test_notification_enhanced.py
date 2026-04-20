"""
Tests for Enhanced Notification Service.
增强版通知服务测试
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock


class TestNotificationConfig:
    """通知配置测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.notification.enhanced_notification import NotificationConfig
        assert NotificationConfig is not None

    def test_default_config(self):
        """测试默认配置"""
        from asset_lens.notification.enhanced_notification import NotificationConfig

        config = NotificationConfig()

        assert config.enabled is True
        assert config.cooldown_minutes == 60
        assert "console" in config.default_channels

    def test_custom_config(self):
        """测试自定义配置"""
        from asset_lens.notification.enhanced_notification import NotificationConfig

        config = NotificationConfig(
            dingtalk_webhook="https://example.com/webhook",
            telegram_bot_token="test_token",
            telegram_chat_id="test_chat_id",
        )

        assert config.dingtalk_webhook == "https://example.com/webhook"
        assert config.telegram_bot_token == "test_token"


class TestNotificationMessage:
    """通知消息测试"""

    def test_message_creation(self):
        """测试消息创建"""
        from asset_lens.notification.enhanced_notification import NotificationMessage

        message = NotificationMessage(
            title="测试标题",
            content="测试内容",
            level="info",
        )

        assert message.title == "测试标题"
        assert message.content == "测试内容"
        assert message.level == "info"
        assert message.timestamp is not None

    def test_message_to_dict(self):
        """测试消息转换为字典"""
        from asset_lens.notification.enhanced_notification import NotificationMessage

        message = NotificationMessage(
            title="测试标题",
            content="测试内容",
            level="warning",
        )

        result = message.to_dict()

        assert isinstance(result, dict)
        assert result["title"] == "测试标题"
        assert result["level"] == "warning"


class TestEnhancedNotificationService:
    """增强版通知服务测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.notification.enhanced_notification import EnhancedNotificationService
        assert EnhancedNotificationService is not None

    def test_service_init(self):
        """测试服务初始化"""
        from asset_lens.notification.enhanced_notification import (
            EnhancedNotificationService,
            NotificationConfig,
        )

        config = NotificationConfig()
        service = EnhancedNotificationService(config)

        assert service.config is not None
        assert service.config.enabled is True

    def test_send_console_notification(self):
        """测试发送控制台通知"""
        from asset_lens.notification.enhanced_notification import (
            EnhancedNotificationService,
            NotificationConfig,
            NotificationMessage,
        )

        config = NotificationConfig()
        service = EnhancedNotificationService(config)

        message = NotificationMessage(
            title="测试通知",
            content="这是一条测试消息",
            level="info",
        )

        results = service.send(message, ["console"], skip_cooldown=True)

        assert "console" in results
        assert results["console"] is True

    def test_send_disabled_service(self):
        """测试禁用服务时发送"""
        from asset_lens.notification.enhanced_notification import (
            EnhancedNotificationService,
            NotificationConfig,
            NotificationMessage,
        )

        config = NotificationConfig(enabled=False)
        service = EnhancedNotificationService(config)

        message = NotificationMessage(
            title="测试通知",
            content="测试内容",
        )

        results = service.send(message, ["console"])

        assert len(results) == 0

    def test_notify_risk_alert(self):
        """测试发送风险预警"""
        from asset_lens.notification.enhanced_notification import (
            EnhancedNotificationService,
            NotificationConfig,
        )

        config = NotificationConfig(cooldown_minutes=0)
        service = EnhancedNotificationService(config)

        results = service.notify_risk_alert(
            alert_type="止损预警",
            level="danger",
            message="股票触及止损线",
            suggestion="建议止损",
            channels=["console"],
        )

        assert results is not None
        assert "console" in results

    def test_notify_trade_signal(self):
        """测试发送交易信号"""
        from asset_lens.notification.enhanced_notification import (
            EnhancedNotificationService,
            NotificationConfig,
        )

        config = NotificationConfig(cooldown_minutes=0)
        service = EnhancedNotificationService(config)

        results = service.notify_trade_signal(
            code="sh600519",
            name="贵州茅台",
            signal_type="buy",
            price=1800.0,
            reason="技术指标买入信号",
            channels=["console"],
        )

        assert results is not None
        assert "console" in results

    def test_notify_daily_report(self):
        """测试发送每日报告"""
        from asset_lens.notification.enhanced_notification import (
            EnhancedNotificationService,
            NotificationConfig,
        )

        config = NotificationConfig(cooldown_minutes=0)
        service = EnhancedNotificationService(config)

        report_data = {
            "total_assets": 100000,
            "total_profit": 10000,
            "total_return": 0.1,
        }

        results = service.notify_daily_report(report_data, ["console"])

        assert results is not None
        assert "console" in results

    def test_get_history(self):
        """测试获取通知历史"""
        from asset_lens.notification.enhanced_notification import (
            EnhancedNotificationService,
            NotificationConfig,
            NotificationMessage,
        )

        config = NotificationConfig()
        service = EnhancedNotificationService(config)

        message = NotificationMessage(
            title="测试通知",
            content="测试内容",
        )
        service.send(message, ["console"], skip_cooldown=True)

        history = service.get_history()

        assert isinstance(history, list)

    def test_test_channel(self):
        """测试测试通知渠道"""
        from asset_lens.notification.enhanced_notification import (
            EnhancedNotificationService,
            NotificationConfig,
        )

        config = NotificationConfig()
        service = EnhancedNotificationService(config)

        result = service.test_channel("console")

        assert result is True

    def test_cooldown_mechanism(self):
        """测试冷却机制"""
        from asset_lens.notification.enhanced_notification import (
            EnhancedNotificationService,
            NotificationConfig,
            NotificationMessage,
        )

        config = NotificationConfig(cooldown_minutes=60)
        service = EnhancedNotificationService(config)

        message = NotificationMessage(
            title="测试通知",
            content="测试内容",
            level="warning",
        )

        results1 = service.send(message, ["console"], skip_cooldown=False)
        results2 = service.send(message, ["console"], skip_cooldown=False)

        assert "console" in results1
        assert len(results2) == 0


class TestNotificationChannel:
    """通知渠道测试"""

    def test_channel_values(self):
        """测试通知渠道值"""
        from asset_lens.notification.enhanced_notification import NotificationChannel

        assert NotificationChannel.CONSOLE.value == "console"
        assert NotificationChannel.DINGTALK.value == "dingtalk"
        assert NotificationChannel.WECOM.value == "wecom"
        assert NotificationChannel.TELEGRAM.value == "telegram"
        assert NotificationChannel.FEISHU.value == "feishu"


class TestNotificationHistory:
    """通知历史测试"""

    def test_history_init(self):
        """测试历史初始化"""
        from asset_lens.notification.enhanced_notification import NotificationHistory
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            history = NotificationHistory(Path(tmpdir))
            assert isinstance(history.history, list)

    def test_history_add(self):
        """测试历史添加"""
        from asset_lens.notification.enhanced_notification import (
            NotificationHistory,
            NotificationMessage,
        )
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            history = NotificationHistory(Path(tmpdir))

            message = NotificationMessage(
                title="测试",
                content="内容",
            )
            history.add(message, ["console"], {"console": True})

            assert len(history.history) == 1

    def test_history_get_recent(self):
        """测试获取最近历史"""
        from asset_lens.notification.enhanced_notification import (
            NotificationHistory,
            NotificationMessage,
        )
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            history = NotificationHistory(Path(tmpdir))

            message = NotificationMessage(
                title="测试",
                content="内容",
            )
            history.add(message, ["console"], {"console": True})

            recent = history.get_recent(24)

            assert isinstance(recent, list)
