from asset_lens.notification.notification_models import (
    EnhancedNotificationChannel,
    EnhancedNotificationMessage,
    NotificationConfig,
)


class TestEnhancedNotificationChannel:
    def test_values(self):
        assert EnhancedNotificationChannel.CONSOLE.value == "console"
        assert EnhancedNotificationChannel.EMAIL.value == "email"
        assert EnhancedNotificationChannel.DINGTALK.value == "dingtalk"
        assert EnhancedNotificationChannel.WECOM.value == "wecom"
        assert EnhancedNotificationChannel.TELEGRAM.value == "telegram"
        assert EnhancedNotificationChannel.FEISHU.value == "feishu"
        assert EnhancedNotificationChannel.SERVERCHAN.value == "serverchan"
        assert EnhancedNotificationChannel.WEBHOOK.value == "webhook"


class TestNotificationConfig:
    def test_defaults(self):
        cfg = NotificationConfig()
        assert cfg.enabled is True
        assert cfg.dingtalk_webhook == ""
        assert cfg.telegram_bot_token == ""
        assert cfg.email_smtp_server == "smtp.gmail.com"
        assert cfg.email_smtp_port == 587
        assert cfg.default_channels == ["console"]
        assert cfg.cooldown_minutes == 60

    def test_custom(self):
        cfg = NotificationConfig(
            enabled=False,
            dingtalk_webhook="https://example.com/webhook",
            telegram_bot_token="123:abc",
            cooldown_minutes=30,
        )
        assert cfg.enabled is False
        assert cfg.dingtalk_webhook == "https://example.com/webhook"
        assert cfg.cooldown_minutes == 30


class TestEnhancedNotificationMessage:
    def test_creation(self):
        msg = EnhancedNotificationMessage(
            title="Test",
            content="Hello",
            level="info",
            timestamp="2025-01-01 10:00:00",
            metadata={"key": "value"},
        )
        assert msg.title == "Test"
        assert msg.metadata == {"key": "value"}

    def test_to_dict(self):
        msg = EnhancedNotificationMessage(
            title="Alert",
            content="Price dropped",
            level="warning",
            timestamp="2025-01-01 10:00:00",
            metadata={"stock": "600519"},
        )
        d = msg.to_dict()
        assert d["title"] == "Alert"
        assert d["level"] == "warning"
        assert d["metadata"]["stock"] == "600519"

    def test_default_metadata(self):
        msg = EnhancedNotificationMessage(
            title="Test",
            content="Hello",
            level="info",
            timestamp="2025-01-01",
        )
        assert msg.metadata == {}
