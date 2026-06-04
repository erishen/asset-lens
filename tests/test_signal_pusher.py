"""
Tests for Signal Pusher.
实时信号推送模块测试
"""

import json
from unittest.mock import MagicMock, patch

from asset_lens.analysis.signal_pusher import (
    Priority,
    PushConfig,
    Signal,
    SignalGenerator,
    SignalPusher,
    SignalType,
    signal_generator,
    signal_pusher,
)


class TestSignal:
    """测试信号数据类"""

    def test_create_signal(self):
        """测试创建信号"""
        signal = Signal(
            code="sh600519",
            name="贵州茅台",
            signal_type=SignalType.BUY,
            price=1800.0,
            change_percent=2.5,
            confidence=0.85,
            reason="ML预测上涨",
            suggestion="建议买入",
            priority=Priority.HIGH,
        )

        assert signal.code == "sh600519"
        assert signal.signal_type == SignalType.BUY
        assert signal.price == 1800.0
        assert signal.confidence == 0.85
        assert signal.priority == Priority.HIGH

    def test_signal_default_timestamp(self):
        """测试默认时间戳"""
        signal = Signal(
            code="sh600519",
            name="贵州茅台",
            signal_type=SignalType.BUY,
            price=1800.0,
            change_percent=2.5,
            confidence=0.85,
            reason="测试",
            suggestion="测试",
        )

        assert signal.timestamp is not None
        assert signal.priority == Priority.MEDIUM


class TestPushConfig:
    """测试推送配置"""

    def test_default_config(self):
        """测试默认配置"""
        config = PushConfig()

        assert config.enable_wechat is False
        assert config.enable_dingtalk is False
        assert config.enable_webhook is False
        assert config.enable_console is True

    def test_custom_config(self):
        """测试自定义配置"""
        config = PushConfig(
            enable_webhook=True,
            webhook_url="https://example.com/webhook",
        )

        assert config.enable_webhook is True
        assert config.webhook_url == "https://example.com/webhook"


class TestSignalPusher:
    """测试信号推送器"""

    def test_init(self, tmp_path):
        """测试初始化"""
        pusher = SignalPusher(cache_path=tmp_path)
        assert pusher.cache_path == tmp_path
        assert pusher.signal_history_file == tmp_path / "signal_history.json"

    def test_push_to_console(self, tmp_path):
        """测试推送到控制台"""
        config = PushConfig(enable_console=True)
        pusher = SignalPusher(push_config=config, cache_path=tmp_path)

        signal = Signal(
            code="sh600519",
            name="贵州茅台",
            signal_type=SignalType.BUY,
            price=1800.0,
            change_percent=2.5,
            confidence=0.85,
            reason="测试买入",
            suggestion="建议买入",
            priority=Priority.HIGH,
        )

        with patch("asset_lens.analysis.signal_pusher.logger") as mock_logger:
            result = pusher._push_to_console(signal)

        assert result is True

    @patch("requests.post")
    def test_push_to_webhook_success(self, mock_post, tmp_path):
        """测试 Webhook 推送成功"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        config = PushConfig(
            enable_webhook=True,
            webhook_url="https://example.com/webhook",
        )
        pusher = SignalPusher(push_config=config, cache_path=tmp_path)

        signal = Signal(
            code="sh600519",
            name="贵州茅台",
            signal_type=SignalType.BUY,
            price=1800.0,
            change_percent=2.5,
            confidence=0.85,
            reason="测试",
            suggestion="测试",
        )

        result = pusher._push_to_webhook(signal)

        assert result is True
        mock_post.assert_called_once()

    @patch("requests.post")
    def test_push_to_webhook_failure(self, mock_post, tmp_path):
        """测试 Webhook 推送失败"""
        mock_post.side_effect = ConnectionError("Network error")

        config = PushConfig(
            enable_webhook=True,
            webhook_url="https://example.com/webhook",
        )
        pusher = SignalPusher(push_config=config, cache_path=tmp_path)

        signal = Signal(
            code="sh600519",
            name="贵州茅台",
            signal_type=SignalType.BUY,
            price=1800.0,
            change_percent=2.5,
            confidence=0.85,
            reason="测试",
            suggestion="测试",
        )

        result = pusher._push_to_webhook(signal)

        assert result is False

    def test_save_signal(self, tmp_path):
        """测试保存信号"""
        pusher = SignalPusher(cache_path=tmp_path)

        signal = Signal(
            code="sh600519",
            name="贵州茅台",
            signal_type=SignalType.BUY,
            price=1800.0,
            change_percent=2.5,
            confidence=0.85,
            reason="测试",
            suggestion="测试",
        )

        pusher._save_signal(signal)

        assert pusher.signal_history_file.exists()

        with open(pusher.signal_history_file, encoding="utf-8") as f:
            history = json.load(f)

        assert len(history) == 1
        assert history[0]["code"] == "sh600519"

    def test_get_recent_signals(self, tmp_path):
        """测试获取最近信号"""
        pusher = SignalPusher(cache_path=tmp_path)

        for i in range(5):
            signal = Signal(
                code=f"sh60051{i}",
                name=f"股票{i}",
                signal_type=SignalType.BUY,
                price=10.0 + i,
                change_percent=1.0,
                confidence=0.8,
                reason="测试",
                suggestion="测试",
            )
            pusher._save_signal(signal)

        recent = pusher.get_recent_signals(limit=3)

        assert len(recent) == 3

    def test_add_handler(self, tmp_path):
        """测试添加自定义处理器"""
        config = PushConfig(enable_console=False)
        pusher = SignalPusher(push_config=config, cache_path=tmp_path)

        handler_calls = []

        def custom_handler(signal):
            handler_calls.append(signal.code)

        pusher.add_handler(custom_handler)

        signal = Signal(
            code="sh600519",
            name="贵州茅台",
            signal_type=SignalType.BUY,
            price=1800.0,
            change_percent=2.5,
            confidence=0.85,
            reason="测试",
            suggestion="测试",
        )

        pusher.push(signal)

        assert len(handler_calls) == 1
        assert handler_calls[0] == "sh600519"


class TestSignalGenerator:
    """测试信号生成器"""

    def test_generate_buy_signal_high_confidence(self, tmp_path):
        """测试高置信度买入信号"""
        pusher = SignalPusher(cache_path=tmp_path)
        generator = SignalGenerator(pusher=pusher)

        signal = generator.generate_buy_signal(
            code="sh600519",
            name="贵州茅台",
            price=1800.0,
            change_percent=2.5,
            confidence=0.85,
            reasons=["ML预测上涨", "资金流入"],
        )

        assert signal.signal_type == SignalType.BUY
        assert signal.confidence == 0.85
        assert signal.priority == Priority.HIGH
        assert "强烈建议买入" in signal.suggestion

    def test_generate_buy_signal_medium_confidence(self, tmp_path):
        """测试中等置信度买入信号"""
        pusher = SignalPusher(cache_path=tmp_path)
        generator = SignalGenerator(pusher=pusher)

        signal = generator.generate_buy_signal(
            code="sh600519",
            name="贵州茅台",
            price=1800.0,
            change_percent=2.5,
            confidence=0.72,
            reasons=["ML预测上涨"],
        )

        assert signal.priority == Priority.MEDIUM
        assert "标准仓位" in signal.suggestion

    def test_generate_buy_signal_low_confidence(self, tmp_path):
        """测试低置信度买入信号"""
        pusher = SignalPusher(cache_path=tmp_path)
        generator = SignalGenerator(pusher=pusher)

        signal = generator.generate_buy_signal(
            code="sh600519",
            name="贵州茅台",
            price=1800.0,
            change_percent=2.5,
            confidence=0.65,
            reasons=["ML预测上涨"],
        )

        assert signal.priority == Priority.LOW
        assert "小仓位试探" in signal.suggestion

    def test_generate_sell_signal(self, tmp_path):
        """测试卖出信号"""
        pusher = SignalPusher(cache_path=tmp_path)
        generator = SignalGenerator(pusher=pusher)

        signal = generator.generate_sell_signal(
            code="sh600519",
            name="贵州茅台",
            price=1700.0,
            change_percent=-2.5,
            confidence=0.75,
            reasons=["ML预测下跌", "资金流出"],
        )

        assert signal.signal_type == SignalType.SELL
        assert signal.confidence == 0.75
        assert signal.priority == Priority.HIGH

    def test_generate_stop_loss_signal(self, tmp_path):
        """测试止损信号"""
        pusher = SignalPusher(cache_path=tmp_path)
        generator = SignalGenerator(pusher=pusher)

        signal = generator.generate_stop_loss_signal(
            code="sh600519",
            name="贵州茅台",
            price=1650.0,
            change_percent=-8.3,
            buy_price=1800.0,
            loss_percent=-8.3,
        )

        assert signal.signal_type == SignalType.STOP_LOSS
        assert signal.confidence == 1.0
        assert signal.priority == Priority.HIGH
        assert "止损" in signal.reason

    def test_generate_price_alert_up(self, tmp_path):
        """测试上涨价格预警"""
        pusher = SignalPusher(cache_path=tmp_path)
        generator = SignalGenerator(pusher=pusher)

        signal = generator.generate_price_alert(
            code="sh600519",
            name="贵州茅台",
            price=1900.0,
            change_percent=5.5,
            alert_type="up",
            threshold=5.0,
        )

        assert signal.signal_type == SignalType.PRICE_ALERT
        assert "涨幅" in signal.reason
        assert "止盈" in signal.suggestion

    def test_generate_price_alert_down(self, tmp_path):
        """测试下跌价格预警"""
        pusher = SignalPusher(cache_path=tmp_path)
        generator = SignalGenerator(pusher=pusher)

        signal = generator.generate_price_alert(
            code="sh600519",
            name="贵州茅台",
            price=1700.0,
            change_percent=-5.5,
            alert_type="down",
            threshold=5.0,
        )

        assert signal.signal_type == SignalType.PRICE_ALERT
        assert "跌幅" in signal.reason
        assert "止损" in signal.suggestion


class TestSignalPusherInstance:
    """测试全局实例"""

    def test_global_pusher_exists(self):
        """测试全局推送器实例存在"""
        assert signal_pusher is not None
        assert isinstance(signal_pusher, SignalPusher)

    def test_global_generator_exists(self):
        """测试全局生成器实例存在"""
        assert signal_generator is not None
        assert isinstance(signal_generator, SignalGenerator)


class TestSignalTypeEnum:
    """测试信号类型枚举"""

    def test_signal_types(self):
        """测试所有信号类型"""
        assert SignalType.BUY.value == "buy"
        assert SignalType.SELL.value == "sell"
        assert SignalType.STOP_LOSS.value == "stop_loss"
        assert SignalType.TAKE_PROFIT.value == "take_profit"
        assert SignalType.POSITION_ADJUST.value == "position_adjust"
        assert SignalType.PRICE_ALERT.value == "price_alert"
        assert SignalType.VOLUME_ALERT.value == "volume_alert"
        assert SignalType.NEWS_ALERT.value == "news_alert"


class TestPriorityEnum:
    """测试优先级枚举"""

    def test_priorities(self):
        """测试所有优先级"""
        assert Priority.HIGH.value == "high"
        assert Priority.MEDIUM.value == "medium"
        assert Priority.LOW.value == "low"
