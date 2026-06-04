"""
Enhanced Notification Service for asset-lens.
增强版通知服务 - 支持钉钉、企业微信、Telegram、飞书等多渠道

功能:
1. 钉钉机器人通知
2. 企业微信机器人通知
3. Telegram Bot 通知
4. 飞书机器人通知
5. 邮件通知
6. Server酱微信通知
7. 通知模板管理
8. 通知历史记录
"""

import base64
import hashlib
import hmac
import logging
import time
import urllib.parse
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

from ..utils.json_cache import read_json_cache_dict, write_json_cache
from .notification_models import (
    EnhancedNotificationChannel,
    EnhancedNotificationMessage,
    NotificationConfig,
)

logger = logging.getLogger(__name__)

__all__ = [
    "EnhancedNotificationChannel",
    "EnhancedNotificationMessage",
    "EnhancedNotificationService",
    "NotificationConfig",
    "NotificationHistory",
    "enhanced_notification_service",
]


class NotificationHistory:
    """通知历史记录"""

    def __init__(self, cache_path: Path):
        self.history_file = cache_path / "notification_history.json"
        self.history: list[dict[str, Any]] = self._load_history()

    def _load_history(self) -> list[dict[str, Any]]:
        data = read_json_cache_dict(self.history_file)
        return data if isinstance(data, list) else []

    def _save_history(self):
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        write_json_cache(self.history_file, self.history[-500:])

    def add(self, message: EnhancedNotificationMessage, channels: list[str], results: dict[str, bool]):
        """添加通知记录"""
        record = {
            "title": message.title,
            "level": message.level,
            "channels": channels,
            "results": results,
            "timestamp": message.timestamp,
        }
        self.history.append(record)
        self._save_history()

    def get_recent(self, hours: int = 24) -> list[dict[str, Any]]:
        """获取最近的通知记录"""
        cutoff = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return [r for r in self.history[-100:] if r.get("timestamp", "") >= cutoff]


class EnhancedNotificationService:
    """增强版通知服务"""

    def __init__(self, config: NotificationConfig | None = None):
        self.config = config or NotificationConfig()
        self._cache_path = Path("cache")
        self._cache_path.mkdir(parents=True, exist_ok=True)
        self._history = NotificationHistory(self._cache_path)
        self._last_sent: dict[str, str] = {}
        self._handlers: dict[EnhancedNotificationChannel, Callable] = {
            EnhancedNotificationChannel.CONSOLE: self._send_console,
            EnhancedNotificationChannel.DINGTALK: self._send_dingtalk,
            EnhancedNotificationChannel.WECOM: self._send_wecom,
            EnhancedNotificationChannel.TELEGRAM: self._send_telegram,
            EnhancedNotificationChannel.FEISHU: self._send_feishu,
            EnhancedNotificationChannel.SERVERCHAN: self._send_serverchan,
        }

    def _should_send(self, key: str) -> bool:
        """检查是否应该发送（冷却时间检查）"""
        if self.config.cooldown_minutes <= 0:
            return True

        last_time = self._last_sent.get(key)
        if not last_time:
            return True

        try:
            last_dt = datetime.strptime(last_time, "%Y-%m-%d %H:%M:%S")
            elapsed = (datetime.now() - last_dt).total_seconds() / 60
            return elapsed >= self.config.cooldown_minutes
        except ValueError:
            return True

    def _mark_sent(self, key: str):
        """标记已发送"""
        self._last_sent[key] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def send(
        self,
        message: EnhancedNotificationMessage,
        channels: list[str] | None = None,
        skip_cooldown: bool = False,
    ) -> dict[str, bool]:
        """
        发送通知

        Args:
            message: 通知消息
            channels: 发送渠道列表
            skip_cooldown: 是否跳过冷却时间

        Returns:
            各渠道发送结果
        """
        if not self.config.enabled:
            logger.warning("通知服务未启用")
            return {}

        if channels is None:
            channels = self.config.default_channels

        key = f"{message.level}_{hash(message.title)}"
        if not skip_cooldown and not self._should_send(key):
            logger.debug(f"通知在冷却时间内，跳过: {message.title}")
            return {}

        results = {}

        for channel_str in channels:
            try:
                channel = EnhancedNotificationChannel(channel_str)

                if channel in self._handlers:
                    success = self._handlers[channel](message)
                    results[channel.value] = success
                else:
                    logger.warning(f"不支持的通知渠道: {channel.value}")
                    results[channel.value] = False

            except ValueError:
                logger.warning(f"无效的通知渠道: {channel_str}")
                results[channel_str] = False
            except (RuntimeError, ConnectionError) as e:
                logger.error(f"发送通知失败 [{channel_str}]: {e}")
                results[channel_str] = False

        if any(results.values()):
            self._mark_sent(key)

        self._history.add(message, channels, results)

        return results

    def _send_console(self, message: EnhancedNotificationMessage) -> bool:
        """发送到控制台"""
        level_emoji = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "success": "✅",
            "critical": "🚨",
        }
        emoji = level_emoji.get(message.level, "📢")
        logger.info(f"{emoji} {message.title}")
        logger.info(f"   {message.content}")
        logger.info(f"   时间: {message.timestamp}")
        return True

    def _send_dingtalk(self, message: EnhancedNotificationMessage) -> bool:
        """发送到钉钉机器人"""
        if not self.config.dingtalk_webhook:
            logger.warning("钉钉 Webhook 未配置")
            return False

        try:
            url = self.config.dingtalk_webhook

            if self.config.dingtalk_secret:
                timestamp = str(round(time.time() * 1000))
                string_to_sign = f"{timestamp}\n{self.config.dingtalk_secret}"
                hmac_code = hmac.new(
                    self.config.dingtalk_secret.encode("utf-8"),
                    string_to_sign.encode("utf-8"),
                    digestmod=hashlib.sha256,
                ).digest()
                sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
                url = f"{url}&timestamp={timestamp}&sign={sign}"

            data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": message.title,
                    "text": f"### {message.title}\n\n{message.content}\n\n> 时间: {message.timestamp}",
                },
            }

            response = requests.post(url, json=data, timeout=10)
            result = response.json()

            if result.get("errcode") == 0:
                logger.info(f"钉钉通知发送成功: {message.title}")
                return True
            else:
                logger.error(f"钉钉通知发送失败: {result.get('errmsg', 'Unknown error')}")
                return False

        except (ConnectionError, TimeoutError, ValueError) as e:
            logger.error(f"钉钉通知发送失败: {e}")
            return False

    def _send_wecom(self, message: EnhancedNotificationMessage) -> bool:
        """发送到企业微信机器人"""
        if not self.config.wecom_webhook:
            logger.warning("企业微信 Webhook 未配置")
            return False

        try:
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "content": f"### {message.title}\n\n{message.content}\n\n> 时间: {message.timestamp}",
                },
            }

            response = requests.post(self.config.wecom_webhook, json=data, timeout=10)
            result = response.json()

            if result.get("errcode") == 0:
                logger.info(f"企业微信通知发送成功: {message.title}")
                return True
            else:
                logger.error(f"企业微信通知发送失败: {result.get('errmsg', 'Unknown error')}")
                return False

        except (ConnectionError, TimeoutError, ValueError) as e:
            logger.error(f"企业微信通知发送失败: {e}")
            return False

    def _send_telegram(self, message: EnhancedNotificationMessage) -> bool:
        """发送到 Telegram Bot"""
        if not self.config.telegram_bot_token or not self.config.telegram_chat_id:
            logger.warning("Telegram Bot 配置不完整")
            return False

        try:
            url = f"https://api.telegram.org/bot{self.config.telegram_bot_token}/sendMessage"

            level_emoji = {
                "info": "ℹ️",
                "warning": "⚠️",
                "error": "❌",
                "success": "✅",
                "critical": "🚨",
            }
            emoji = level_emoji.get(message.level, "📢")

            text = f"{emoji} *{message.title}*\n\n{message.content}\n\n_时间: {message.timestamp}_"

            data = {
                "chat_id": self.config.telegram_chat_id,
                "text": text,
                "parse_mode": "Markdown",
            }

            response = requests.post(url, json=data, timeout=10)
            result = response.json()

            if result.get("ok"):
                logger.info(f"Telegram 通知发送成功: {message.title}")
                return True
            else:
                logger.error(f"Telegram 通知发送失败: {result.get('description', 'Unknown error')}")
                return False

        except (ConnectionError, TimeoutError, ValueError) as e:
            logger.error(f"Telegram 通知发送失败: {e}")
            return False

    def _send_feishu(self, message: EnhancedNotificationMessage) -> bool:
        """发送到飞书机器人"""
        if not self.config.feishu_webhook:
            logger.warning("飞书 Webhook 未配置")
            return False

        try:
            url = self.config.feishu_webhook

            if self.config.feishu_secret:
                timestamp = str(round(time.time()))
                string_to_sign = f"{timestamp}\n{self.config.feishu_secret}"
                hmac_code = hmac.new(
                    self.config.feishu_secret.encode("utf-8"),
                    string_to_sign.encode("utf-8"),
                    digestmod=hashlib.sha256,
                ).digest()
                sign = base64.b64encode(hmac_code).decode("utf-8")

                data = {
                    "timestamp": timestamp,
                    "sign": sign,
                    "msg_type": "interactive",
                    "card": {
                        "header": {
                            "title": {"tag": "plain_text", "content": message.title},
                            "template": "blue" if message.level == "info" else "red",
                        },
                        "elements": [
                            {"tag": "div", "text": {"tag": "plain_text", "content": message.content}},
                            {"tag": "div", "text": {"tag": "plain_text", "content": f"时间: {message.timestamp}"}},
                        ],
                    },
                }
            else:
                data = {
                    "msg_type": "text",
                    "content": {"text": f"{message.title}\n\n{message.content}\n\n时间: {message.timestamp}"},
                }

            response = requests.post(url, json=data, timeout=10)
            result = response.json()

            if result.get("StatusCode") == 0 or result.get("code") == 0:
                logger.info(f"飞书通知发送成功: {message.title}")
                return True
            else:
                logger.error(f"飞书通知发送失败: {result}")
                return False

        except (ConnectionError, TimeoutError, ValueError) as e:
            logger.error(f"飞书通知发送失败: {e}")
            return False

    def _send_serverchan(self, message: EnhancedNotificationMessage) -> bool:
        """发送到 Server酱（微信）"""
        if not self.config.serverchan_key:
            logger.warning("Server酱 Key 未配置")
            return False

        try:
            url = f"https://sctapi.ftqq.com/{self.config.serverchan_key}.send"
            data = {
                "title": message.title,
                "desp": f"### {message.title}\n\n{message.content}\n\n> 时间: {message.timestamp}",
            }

            response = requests.post(url, data=data, timeout=10)
            result = response.json()

            if result.get("code") == 0:
                logger.info(f"Server酱通知发送成功: {message.title}")
                return True
            else:
                logger.error(f"Server酱通知发送失败: {result.get('message', 'Unknown error')}")
                return False

        except (ConnectionError, TimeoutError, ValueError) as e:
            logger.error(f"Server酱通知发送失败: {e}")
            return False

    def notify_risk_alert(
        self,
        alert_type: str,
        level: str,
        message: str,
        suggestion: str = "",
        channels: list[str] | None = None,
    ) -> dict[str, bool]:
        """
        发送风险预警通知

        Args:
            alert_type: 预警类型
            level: 预警级别
            message: 预警消息
            suggestion: 建议
            channels: 发送渠道

        Returns:
            各渠道发送结果
        """
        level_emoji = {
            "info": "ℹ️",
            "warning": "⚠️",
            "danger": "🟠",
            "critical": "🚨",
        }
        emoji = level_emoji.get(level, "⚠️")

        content = f"**类型**: {alert_type}\n**级别**: {level}\n\n{message}"
        if suggestion:
            content += f"\n\n**建议**: {suggestion}"

        notification = EnhancedNotificationMessage(
            title=f"{emoji} 风险预警 - {alert_type}",
            content=content,
            level=level if level in ["info", "warning", "error", "success", "critical"] else "warning",
        )

        return self.send(notification, channels)

    def notify_trade_signal(
        self,
        code: str,
        name: str,
        signal_type: str,
        price: float,
        reason: str = "",
        channels: list[str] | None = None,
    ) -> dict[str, bool]:
        """
        发送交易信号通知

        Args:
            code: 股票代码
            name: 股票名称
            signal_type: 信号类型
            price: 价格
            reason: 原因
            channels: 发送渠道

        Returns:
            各渠道发送结果
        """
        signal_emoji = "🟢" if "buy" in signal_type.lower() else "🔴"
        direction = "买入" if "buy" in signal_type.lower() else "卖出"

        content = f"**股票**: {name} ({code})\n**信号**: {direction}\n**价格**: ¥{price:.2f}"
        if reason:
            content += f"\n\n**原因**: {reason}"

        notification = EnhancedNotificationMessage(
            title=f"{signal_emoji} 交易信号 - {name}",
            content=content,
            level="info",
        )

        return self.send(notification, channels)

    def notify_daily_report(
        self,
        report_data: dict[str, Any],
        channels: list[str] | None = None,
    ) -> dict[str, bool]:
        """
        发送每日报告通知

        Args:
            report_data: 报告数据
            channels: 发送渠道

        Returns:
            各渠道发送结果
        """
        total_assets = report_data.get("total_assets", 0)
        total_profit = report_data.get("total_profit", 0)
        total_return = report_data.get("total_return", 0)

        profit_emoji = "📈" if total_profit >= 0 else "📉"

        content = f"""**总资产**: ¥{total_assets:,.2f}
**总收益**: ¥{total_profit:,.2f}
**收益率**: {total_return:.2%}

**日期**: {datetime.now().strftime("%Y-%m-%d")}"""

        notification = EnhancedNotificationMessage(
            title=f"📊 每日投资报告 {profit_emoji}",
            content=content,
            level="success" if total_profit >= 0 else "warning",
        )

        return self.send(notification, channels)

    def get_history(self, hours: int = 24) -> list[dict[str, Any]]:
        """获取通知历史"""
        return self._history.get_recent(hours)

    def test_channel(self, channel: str) -> bool:
        """测试通知渠道"""
        message = EnhancedNotificationMessage(
            title="🧪 通知测试",
            content="这是一条测试消息，如果您收到此消息，说明通知渠道配置正确。",
            level="info",
        )
        results = self.send(message, [channel], skip_cooldown=True)
        return results.get(channel, False)


enhanced_notification_service = EnhancedNotificationService()
