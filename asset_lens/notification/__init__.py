"""
Notification Module - 通知模块
支持多渠道通知：Telegram、Email、Webhook
"""

import json
import logging
import smtplib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    """通知渠道"""
    TELEGRAM = "telegram"
    EMAIL = "email"
    WEBHOOK = "webhook"
    CONSOLE = "console"


@dataclass
class NotificationMessage:
    """通知消息"""
    title: str
    content: str
    level: str = "info"  # info, warning, error, critical
    timestamp: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class NotificationHandler(ABC):
    """通知处理器基类"""

    @abstractmethod
    def send(self, message: NotificationMessage) -> bool:
        """发送通知"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查渠道是否可用"""
        pass


class ConsoleHandler(NotificationHandler):
    """控制台通知处理器"""

    def send(self, message: NotificationMessage) -> bool:
        level_emoji = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "critical": "🚨",
        }
        emoji = level_emoji.get(message.level, "📢")
        print(f"\n{emoji} [{message.level.upper()}] {message.title}")
        print(f"时间: {message.timestamp}")
        print(f"内容: {message.content}")
        return True

    def is_available(self) -> bool:
        return True


class TelegramHandler(NotificationHandler):
    """Telegram 通知处理器"""

    def __init__(self, bot_token: str | None = None, chat_id: str | None = None):
        self.bot_token = bot_token
        self.chat_id = chat_id

    def send(self, message: NotificationMessage) -> bool:
        if not self.is_available():
            return False

        try:
            import requests

            level_emoji = {
                "info": "ℹ️",
                "warning": "⚠️",
                "error": "❌",
                "critical": "🚨",
            }
            emoji = level_emoji.get(message.level, "📢")

            text = f"{emoji} *{message.title}*\n\n{message.content}\n\n_时间: {message.timestamp}_"

            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            response = requests.post(
                url,
                data={
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": "Markdown",
                },
                timeout=10,
            )

            return response.status_code == 200
        except Exception as e:
            logger.error(f"Telegram 通知发送失败: {e}")
            return False

    def is_available(self) -> bool:
        return bool(self.bot_token and self.chat_id and self.bot_token != "" and self.chat_id != "")


class EmailHandler(NotificationHandler):
    """邮件通知处理器"""

    def __init__(
        self,
        smtp_server: str | None = None,
        smtp_port: int = 587,
        smtp_user: str | None = None,
        smtp_password: str | None = None,
        from_addr: str | None = None,
        to_addrs: list[str] | None = None,
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_addr = from_addr or smtp_user
        self.to_addrs = to_addrs or []

    def send(self, message: NotificationMessage) -> bool:
        if not self.is_available():
            return False

        if not self.from_addr:
            return False

        try:
            msg = MIMEMultipart()
            msg["From"] = self.from_addr
            msg["To"] = ", ".join(self.to_addrs)
            msg["Subject"] = f"[{message.level.upper()}] {message.title}"

            body = f"""
{message.content}

时间: {message.timestamp}
---
此邮件由 Asset Lens 自动发送
"""
            msg.attach(MIMEText(body, "plain", "utf-8"))

            assert self.smtp_server is not None
            assert self.smtp_user is not None
            assert self.smtp_password is not None

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_addr, self.to_addrs, msg.as_string())

            return True
        except Exception as e:
            logger.error(f"邮件通知发送失败: {e}")
            return False

    def is_available(self) -> bool:
        return bool(
            self.smtp_server
            and self.smtp_user
            and self.smtp_password
            and self.to_addrs
            and self.from_addr
        )


class WebhookHandler(NotificationHandler):
    """Webhook 通知处理器"""

    def __init__(self, webhook_url: str | None = None):
        self.webhook_url = webhook_url

    def send(self, message: NotificationMessage) -> bool:
        if not self.is_available():
            return False

        try:
            import requests

            payload = {
                "title": message.title,
                "content": message.content,
                "level": message.level,
                "timestamp": message.timestamp,
                "metadata": message.metadata,
            }

            assert self.webhook_url is not None

            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10,
            )

            return response.status_code == 200
        except Exception as e:
            logger.error(f"Webhook 通知发送失败: {e}")
            return False

    def is_available(self) -> bool:
        return bool(self.webhook_url and self.webhook_url != "")


class NotificationService:
    """通知服务"""

    def __init__(self, config_path: Path | None = None):
        self.config_path = config_path or Path.home() / ".asset_lens" / "notification_config.json"
        self._handlers: dict[NotificationChannel, NotificationHandler] = {
            NotificationChannel.CONSOLE: ConsoleHandler(),
        }
        self._load_config()

    def _load_config(self) -> None:
        """加载配置"""
        if not self.config_path.exists():
            return

        try:
            with open(self.config_path, encoding="utf-8") as f:
                config = json.load(f)

            if "telegram" in config:
                tg = config["telegram"]
                self._handlers[NotificationChannel.TELEGRAM] = TelegramHandler(
                    bot_token=tg.get("bot_token"),
                    chat_id=tg.get("chat_id"),
                )

            if "email" in config:
                em = config["email"]
                self._handlers[NotificationChannel.EMAIL] = EmailHandler(
                    smtp_server=em.get("smtp_server"),
                    smtp_port=em.get("smtp_port", 587),
                    smtp_user=em.get("smtp_user"),
                    smtp_password=em.get("smtp_password"),
                    to_addrs=em.get("to_addrs", []),
                )

            if "webhook" in config:
                wh = config["webhook"]
                self._handlers[NotificationChannel.WEBHOOK] = WebhookHandler(
                    webhook_url=wh.get("url"),
                )
        except Exception as e:
            logger.error(f"加载通知配置失败: {e}")

    def register_handler(
        self,
        channel: NotificationChannel,
        handler: NotificationHandler,
    ) -> None:
        """注册通知处理器"""
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
            channels: 指定渠道列表（默认使用所有可用渠道）
            
        Returns:
            各渠道发送结果
        """
        if channels is None:
            channels = list(self._handlers.keys())

        results: dict[str, bool] = {}

        for channel in channels:
            handler = self._handlers.get(channel)
            if handler is None:
                results[channel.value] = False
                continue

            if not handler.is_available():
                results[channel.value] = False
                continue

            try:
                success = handler.send(message)
                results[channel.value] = success
            except Exception as e:
                logger.error(f"发送通知失败 [{channel.value}]: {e}")
                results[channel.value] = False

        return results

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
        notification = NotificationMessage(
            title=f"风险预警: {alert_type}",
            content=message,
            level=level,
            metadata=details or {},
        )

        return self.notify(notification)


notification_service = NotificationService()


__all__ = [
    "NotificationChannel",
    "NotificationMessage",
    "NotificationHandler",
    "NotificationService",
    "notification_service",
]
