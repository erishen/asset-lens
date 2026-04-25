"""
Real-time Signal Pusher.
实时信号推送模块 - 提供买卖信号、止损提醒、异动提醒等推送功能

功能:
1. 买卖信号推送 (微信/钉钉/Webhook)
2. 止损提醒
3. 仓位调整建议
4. 异动提醒 (涨跌幅/成交量)
5. 关键价位提醒
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from enum import Enum

from ..config import config


class SignalType(Enum):
    """信号类型"""
    BUY = "buy"
    SELL = "sell"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    POSITION_ADJUST = "position_adjust"
    PRICE_ALERT = "price_alert"
    VOLUME_ALERT = "volume_alert"
    NEWS_ALERT = "news_alert"


class Priority(Enum):
    """优先级"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Signal:
    """交易信号"""
    code: str
    name: str
    signal_type: SignalType
    price: float
    change_percent: float
    confidence: float
    reason: str
    suggestion: str
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    priority: Priority = Priority.MEDIUM


@dataclass
class PushConfig:
    """推送配置"""
    enable_wechat: bool = False
    enable_dingtalk: bool = False
    enable_webhook: bool = False
    enable_console: bool = True
    webhook_url: str = ""
    dingtalk_token: str = ""


class SignalPusher:
    """信号推送器"""

    def __init__(self, push_config: PushConfig | None = None, cache_path: Path | None = None):
        self.config = push_config or PushConfig()
        self.cache_path = cache_path or config.cache_path
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self.signal_history_file = self.cache_path / "signal_history.json"
        self._handlers: list[Callable[[Signal], None]] = []

    def add_handler(self, handler: Callable[[Signal], None]) -> None:
        """添加信号处理器"""
        self._handlers.append(handler)

    def push(self, signal: Signal) -> bool:
        """推送信号"""
        self._save_signal(signal)

        results = []

        if self.config.enable_console:
            results.append(self._push_to_console(signal))

        if self.config.enable_webhook and self.config.webhook_url:
            results.append(self._push_to_webhook(signal))

        if self.config.enable_dingtalk and self.config.dingtalk_token:
            results.append(self._push_to_dingtalk(signal))

        for handler in self._handlers:
            try:
                handler(signal)
                results.append(True)
            except Exception as e:
                print(f"⚠️ 自定义处理器执行失败: {e}")

        return any(results)

    def _push_to_console(self, signal: Signal) -> bool:
        """推送到控制台"""
        emoji_map = {
            SignalType.BUY: "🟢",
            SignalType.SELL: "🔴",
            SignalType.STOP_LOSS: "⛔",
            SignalType.TAKE_PROFIT: "💰",
            SignalType.POSITION_ADJUST: "📊",
            SignalType.PRICE_ALERT: "🔔",
            SignalType.VOLUME_ALERT: "📈",
            SignalType.NEWS_ALERT: "📰",
        }

        emoji = emoji_map.get(signal.signal_type, "📌")
        priority_emoji = "❗" if signal.priority == Priority.HIGH else ""

        print(f"\n{emoji} {priority_emoji}【{signal.signal_type.value.upper()}】{signal.name} ({signal.code})")
        print(f"   价格: {signal.price:.2f} ({signal.change_percent:+.2f}%)")
        print(f"   置信度: {signal.confidence:.1%}")
        print(f"   原因: {signal.reason}")
        print(f"   建议: {signal.suggestion}")
        print(f"   时间: {signal.timestamp}")

        return True

    def _push_to_webhook(self, signal: Signal) -> bool:
        """推送到 Webhook"""
        try:
            import requests

            payload = {
                "signal_type": signal.signal_type.value,
                "code": signal.code,
                "name": signal.name,
                "price": signal.price,
                "change_percent": signal.change_percent,
                "confidence": signal.confidence,
                "reason": signal.reason,
                "suggestion": signal.suggestion,
                "timestamp": signal.timestamp,
                "priority": signal.priority.value,
            }

            r = requests.post(self.config.webhook_url, json=payload, timeout=10)
            return r.status_code == 200

        except Exception as e:
            print(f"⚠️ Webhook 推送失败: {e}")
            return False

    def _push_to_dingtalk(self, signal: Signal) -> bool:
        """推送到钉钉"""
        try:
            import requests

            title_map = {
                SignalType.BUY: "买入信号",
                SignalType.SELL: "卖出信号",
                SignalType.STOP_LOSS: "止损提醒",
                SignalType.TAKE_PROFIT: "止盈提醒",
            }

            title = title_map.get(signal.signal_type, "交易提醒")

            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "title": f"{title}: {signal.name}",
                    "text": f"### {title}\n\n"
                            f"**股票**: {signal.name} ({signal.code})\n\n"
                            f"**价格**: {signal.price:.2f} ({signal.change_percent:+.2f}%)\n\n"
                            f"**置信度**: {signal.confidence:.1%}\n\n"
                            f"**原因**: {signal.reason}\n\n"
                            f"**建议**: {signal.suggestion}\n\n"
                            f"> 时间: {signal.timestamp}"
                }
            }

            url = f"https://oapi.dingtalk.com/robot/send?access_token={self.config.dingtalk_token}"
            r = requests.post(url, json=payload, timeout=10)
            return r.status_code == 200

        except Exception as e:
            print(f"⚠️ 钉钉推送失败: {e}")
            return False

    def _save_signal(self, signal: Signal) -> None:
        """保存信号历史"""
        history = []

        if self.signal_history_file.exists():
            try:
                with open(self.signal_history_file, encoding='utf-8') as f:
                    history = json.load(f)
            except Exception:
                history = []

        history.append({
            'code': signal.code,
            'name': signal.name,
            'type': signal.signal_type.value,
            'price': signal.price,
            'change': signal.change_percent,
            'confidence': signal.confidence,
            'reason': signal.reason,
            'suggestion': signal.suggestion,
            'timestamp': signal.timestamp,
            'priority': signal.priority.value,
        })

        if len(history) > 1000:
            history = history[-1000:]

        with open(self.signal_history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    def get_recent_signals(self, limit: int = 20) -> list[dict[str, Any]]:
        """获取最近信号"""
        if not self.signal_history_file.exists():
            return []

        try:
            with open(self.signal_history_file, encoding='utf-8') as f:
                history = json.load(f)
            return history[-limit:]
        except Exception:
            return []


class SignalGenerator:
    """信号生成器"""

    def __init__(self, pusher: SignalPusher | None = None):
        self.pusher = pusher or SignalPusher()

    def generate_buy_signal(
        self,
        code: str,
        name: str,
        price: float,
        change_percent: float,
        confidence: float,
        reasons: list[str],
    ) -> Signal:
        """生成买入信号"""
        reason = "; ".join(reasons[:3])

        if confidence >= 0.8:
            suggestion = "强烈建议买入，仓位可放大至 2x"
            priority = Priority.HIGH
        elif confidence >= 0.7:
            suggestion = "建议买入，标准仓位"
            priority = Priority.MEDIUM
        else:
            suggestion = "可考虑小仓位试探"
            priority = Priority.LOW

        signal = Signal(
            code=code,
            name=name,
            signal_type=SignalType.BUY,
            price=price,
            change_percent=change_percent,
            confidence=confidence,
            reason=reason,
            suggestion=suggestion,
            priority=priority,
        )

        self.pusher.push(signal)
        return signal

    def generate_sell_signal(
        self,
        code: str,
        name: str,
        price: float,
        change_percent: float,
        confidence: float,
        reasons: list[str],
    ) -> Signal:
        """生成卖出信号"""
        reason = "; ".join(reasons[:3])

        if confidence >= 0.7:
            suggestion = "建议卖出"
            priority = Priority.HIGH
        else:
            suggestion = "可考虑减仓"
            priority = Priority.MEDIUM

        signal = Signal(
            code=code,
            name=name,
            signal_type=SignalType.SELL,
            price=price,
            change_percent=change_percent,
            confidence=confidence,
            reason=reason,
            suggestion=suggestion,
            priority=priority,
        )

        self.pusher.push(signal)
        return signal

    def generate_stop_loss_signal(
        self,
        code: str,
        name: str,
        price: float,
        change_percent: float,
        buy_price: float,
        loss_percent: float,
    ) -> Signal:
        """生成止损信号"""
        signal = Signal(
            code=code,
            name=name,
            signal_type=SignalType.STOP_LOSS,
            price=price,
            change_percent=change_percent,
            confidence=1.0,
            reason=f"亏损 {loss_percent:.1f}%，触发止损线",
            suggestion="立即卖出止损",
            priority=Priority.HIGH,
        )

        self.pusher.push(signal)
        return signal

    def generate_price_alert(
        self,
        code: str,
        name: str,
        price: float,
        change_percent: float,
        alert_type: str,
        threshold: float,
    ) -> Signal:
        """生成价格预警"""
        if change_percent > 0:
            reason = f"涨幅 {change_percent:.2f}% 超过阈值 {threshold}%"
            suggestion = "关注是否需要止盈"
        else:
            reason = f"跌幅 {abs(change_percent):.2f}% 超过阈值 {threshold}%"
            suggestion = "关注是否需要止损"

        signal = Signal(
            code=code,
            name=name,
            signal_type=SignalType.PRICE_ALERT,
            price=price,
            change_percent=change_percent,
            confidence=1.0,
            reason=reason,
            suggestion=suggestion,
            priority=Priority.MEDIUM,
        )

        self.pusher.push(signal)
        return signal


signal_pusher = SignalPusher()
signal_generator = SignalGenerator(signal_pusher)
