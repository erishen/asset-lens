"""
Notification Service - 通知服务模块
提供多种通知渠道的消息推送功能
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    """通知渠道"""

    CONSOLE = "console"
    EMAIL = "email"
    QQ = "qq"
    WECHAT = "wechat"
    WEBHOOK = "webhook"


@dataclass
class NotificationMessage:
    """通知消息"""

    title: str
    content: str
    level: str = "info"
    timestamp: str | None = None

    def __post_init__(self):
        if self.timestamp is None:
            from datetime import datetime

            self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class NotificationService:
    """通知服务"""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self._handlers: dict[NotificationChannel, Any] = {}

    def register_handler(self, channel: NotificationChannel, handler: Any) -> None:
        """注册渠道处理器"""
        self._handlers[channel] = handler

    def notify(
        self,
        message: NotificationMessage,
        channels: list[NotificationChannel] | None = None,
    ) -> dict[str, bool]:
        """
        发送通知

        Args:
            message: 通知消息
            channels: 发送渠道列表

        Returns:
            各渠道发送结果
        """
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
            except Exception as e:
                logger.error(f"发送通知失败 [{channel.value}]: {e}")
                results[channel.value] = False

        return results

    def _send_console(self, message: NotificationMessage) -> None:
        """发送到控制台"""
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
        """
        发送风险预警通知

        Args:
            alert_type: 预警类型
            level: 预警级别
            message: 预警消息
            details: 详细信息

        Returns:
            各渠道发送结果
        """
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


__all__ = [
    "NotificationChannel",
    "NotificationMessage",
    "NotificationService",
    "notification_service",
]
