import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    CONSOLE = "console"
    EMAIL = "email"
    QQ = "qq"
    WECHAT = "wechat"
    WEBHOOK = "webhook"


@dataclass
class NotificationMessage:
    title: str
    content: str
    level: str = "info"
    timestamp: str | None = None

    def __post_init__(self):
        if self.timestamp is None:
            from datetime import datetime

            self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class NotificationService:
    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self._handlers: dict[NotificationChannel, Any] = {}

    def register_handler(self, channel: NotificationChannel, handler: Any) -> None:
        self._handlers[channel] = handler

    def notify(
        self,
        message: NotificationMessage,
        channels: list[NotificationChannel] | None = None,
    ) -> dict[str, bool]:
        if channels is None:
            channels = [NotificationChannel.CONSOLE]

        results = {}
        for channel in channels:
            try:
                if channel == NotificationChannel.CONSOLE:
                    self._send_console(message)
                    results[channel.value] = True
                elif channel in self._handlers:
                    self._handlers[channel](message)
                    results[channel.value] = True
                else:
                    logger.warning(f"未配置通知渠道: {channel.value}")
                    results[channel.value] = False
            except (ValueError, TypeError, RuntimeError) as e:
                logger.error(f"发送通知失败 [{channel.value}]: {e}")
                results[channel.value] = False

        return results

    def _send_console(self, message: NotificationMessage) -> None:
        level_emoji = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "success": "✅",
        }
        emoji = level_emoji.get(message.level, "📢")
        logger.info(f"{emoji} {message.title}")
        logger.info(message.content)

    def notify_risk_alert(
        self,
        alert_type: str,
        level: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> dict[str, bool]:
        content = f"【{level}】{alert_type}\n\n{message}"
        if details:
            content += f"\n\n详细信息: {details}"

        notification = NotificationMessage(
            title=f"⚠️ 风险预警 - {alert_type}",
            content=content,
            level="warning" if level != "critical" else "error",
        )

        return self.notify(notification)


notification_service = NotificationService()
