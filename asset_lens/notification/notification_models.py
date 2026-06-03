from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..notification.service import NotificationMessage


class EnhancedNotificationChannel(Enum):
    CONSOLE = "console"
    EMAIL = "email"
    DINGTALK = "dingtalk"
    WECOM = "wecom"
    TELEGRAM = "telegram"
    FEISHU = "feishu"
    SERVERCHAN = "serverchan"
    WEBHOOK = "webhook"


@dataclass
class NotificationConfig:
    enabled: bool = True

    dingtalk_webhook: str = ""
    dingtalk_secret: str = ""

    wecom_webhook: str = ""

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    feishu_webhook: str = ""
    feishu_secret: str = ""

    email_smtp_server: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_recipients: list[str] = field(default_factory=list)

    serverchan_key: str = ""

    default_channels: list[str] = field(default_factory=lambda: ["console"])

    cooldown_minutes: int = 60


@dataclass
class EnhancedNotificationMessage(NotificationMessage):
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content,
            "level": self.level,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }
