"""
Tests for risk_manager.py
风险管理模块测试
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from asset_lens.trading.risk_manager import PositionAdvice, RiskConfig, RiskManager, RiskWarning


class TestRiskConfig:
    """RiskConfig 测试"""

    def test_default_values(self):
        """测试默认值"""
        config = RiskConfig()
        assert config.max_single_position == 0.2
        assert config.max_total_position == 0.8
        assert config.stop_loss_default == -0.08
        assert config.take_profit_default == 0.15
        assert config.risk_tolerance == "medium"

    def test_custom_values(self):
        """测试自定义值"""
        config = RiskConfig(
            max_single_position=0.3,
            max_total_position=0.9,
            stop_loss_default=-0.05,
            take_profit_default=0.2,
            risk_tolerance="high",
        )
        assert config.max_single_position == 0.3
        assert config.max_total_position == 0.9
        assert config.stop_loss_default == -0.05
        assert config.take_profit_default == 0.2
        assert config.risk_tolerance == "high"


class TestPositionAdvice:
    """PositionAdvice 测试"""

    def test_default_values(self):
        """测试默认值"""
        advice = PositionAdvice(
            code="sh600519",
            name="贵州茅台",
            current_position=0.1,
            suggested_position=0.15,
            action="hold",
            reason="仓位合理",
        )
        assert advice.code == "sh600519"
        assert advice.name == "贵州茅台"
        assert advice.current_position == 0.1
        assert advice.suggested_position == 0.15
        assert advice.action == "hold"
        assert advice.reason == "仓位合理"

    def test_action_types(self):
        """测试动作类型"""
        for action in ["increase", "decrease", "hold"]:
            advice = PositionAdvice(
                code="sh600519",
                name="测试",
                current_position=0.1,
                suggested_position=0.15,
                action=action,
                reason="测试",
            )
            assert advice.action == action


class TestRiskWarning:
    """RiskWarning 测试"""

    def test_default_values(self):
        """测试默认值"""
        warning = RiskWarning(
            warning_type="concentration",
            level="high",
            message="持仓过于集中",
        )
        assert warning.warning_type == "concentration"
        assert warning.level == "high"
        assert warning.message == "持仓过于集中"
        assert warning.code is None
        assert warning.timestamp == ""
        assert warning.details == {}

    def test_custom_values(self):
        """测试自定义值"""
        warning = RiskWarning(
            warning_type="stop_loss",
            level="critical",
            message="触及止损线",
            code="sh600519",
            timestamp="2024-01-01 12:00:00",
            details={"profit_rate": -0.08},
        )
        assert warning.warning_type == "stop_loss"
        assert warning.level == "critical"
        assert warning.message == "触及止损线"
        assert warning.code == "sh600519"
        assert warning.timestamp == "2024-01-01 12:00:00"
        assert warning.details == {"profit_rate": -0.08}

    def test_warning_levels(self):
        """测试预警级别"""
        for level in ["low", "medium", "high", "critical"]:
            warning = RiskWarning(
                warning_type="test",
                level=level,
                message="测试",
            )
            assert warning.level == level


class TestRiskManager:
    """RiskManager 测试"""

    @pytest.fixture
    def temp_cache_path(self):
        """临时缓存路径"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def manager(self, temp_cache_path):
        """创建测试实例"""
        with patch("asset_lens.trading.risk_manager.config") as mock_config:
            mock_config.cache_path = temp_cache_path
            manager = RiskManager()
            yield manager

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.trading.risk_manager import risk_manager

        assert risk_manager is not None

    def test_init(self, manager):
        """测试初始化"""
        assert manager.config is not None
        assert manager.config.risk_tolerance == "medium"

    def test_risk_tolerance_positions(self):
        """测试风险偏好配置"""
        assert "low" in RiskManager.RISK_TOLERANCE_POSITIONS
        assert "medium" in RiskManager.RISK_TOLERANCE_POSITIONS
        assert "high" in RiskManager.RISK_TOLERANCE_POSITIONS

    def test_set_risk_tolerance(self, manager):
        """测试设置风险偏好"""
        manager.set_risk_tolerance("high")
        assert manager.config.risk_tolerance == "high"
        assert manager.config.max_single_position == 0.3

        manager.set_risk_tolerance("low")
        assert manager.config.risk_tolerance == "low"
        assert manager.config.max_single_position == 0.1

    def test_set_risk_tolerance_invalid(self, manager):
        """测试设置无效风险偏好"""
        original = manager.config.risk_tolerance
        manager.set_risk_tolerance("invalid")
        assert manager.config.risk_tolerance == original

    def test_load_warnings_no_file(self, manager):
        """测试加载警告 - 文件不存在"""
        manager._load_warnings()
        assert manager.warnings == []

    def test_load_warnings_with_file(self, manager):
        """测试加载警告 - 有文件"""
        warnings_data = [{"warning_type": "test", "message": "测试警告", "level": "medium"}]
        with open(manager.warnings_file, "w", encoding="utf-8") as f:
            json.dump(warnings_data, f)

        manager._load_warnings()
        assert len(manager.warnings) == 1
        assert manager.warnings[0].warning_type == "test"

    def test_save_warnings(self, manager):
        """测试保存警告"""
        manager.warnings = [RiskWarning(warning_type="test", level="medium", message="测试警告")]
        manager._save_warnings()

        assert manager.warnings_file.exists()

        with open(manager.warnings_file, encoding="utf-8") as f:
            data = json.load(f)

        assert isinstance(data, list)
        assert len(data) == 1

    def test_calculate_stop_loss_take_profit_default(self, manager):
        """测试计算止损止盈 - 默认"""
        result = manager.calculate_stop_loss_take_profit(code="sh600519", buy_price=100.0)

        assert result["code"] == "sh600519"
        assert result["buy_price"] == 100.0
        assert result["stop_loss"] == manager.config.stop_loss_default
        assert result["take_profit"] == manager.config.take_profit_default
        assert result["stop_loss_price"] == 100.0 * (1 + manager.config.stop_loss_default)
        assert result["take_profit_price"] == 100.0 * (1 + manager.config.take_profit_default)
        assert result["method"] == "percentage"

    def test_calculate_stop_loss_take_profit_with_atr(self, manager):
        """测试计算止损止盈 - 使用ATR"""
        result = manager.calculate_stop_loss_take_profit(code="sh600519", buy_price=100.0, atr=5.0)

        assert result["method"] == "atr"
        assert result["stop_loss_price"] == 100.0 - 2 * 5.0
        assert result["take_profit_price"] == 100.0 + 3 * 5.0

    def test_calculate_stop_loss_take_profit_with_strategy(self, manager):
        """测试计算止损止盈 - 使用策略"""
        result = manager.calculate_stop_loss_take_profit(code="sh600519", buy_price=100.0, strategy_name="value")

        assert result["code"] == "sh600519"
        assert "stop_loss" in result
        assert "take_profit" in result

    def test_calculate_stop_loss_take_profit_risk_reward_ratio(self, manager):
        """测试计算止损止盈 - 风险收益比"""
        result = manager.calculate_stop_loss_take_profit(code="sh600519", buy_price=100.0)

        assert result["risk_reward_ratio"] > 0

    def test_check_position_concentration_empty(self, manager):
        """测试检查持仓集中度 - 空持仓"""
        result = manager.check_position_concentration([])

        assert result == []

    def test_check_position_concentration_with_positions(self, manager):
        """测试检查持仓集中度 - 有持仓"""
        holdings = [
            {"code": "sh600519", "name": "贵州茅台", "market_value": 180000, "industry": "白酒"},
            {"code": "sz000001", "name": "平安银行", "market_value": 15000, "industry": "银行"},
        ]

        result = manager.check_position_concentration(holdings)

        assert isinstance(result, list)

    def test_get_risk_summary(self, manager):
        """测试获取风险摘要"""
        with patch("asset_lens.trading.stock_pool.StockPool") as mock_pool:
            mock_pool_instance = MagicMock()
            mock_pool_instance.list_stocks.return_value = []
            mock_pool.return_value = mock_pool_instance

            result = manager.get_risk_summary()

            assert "total_warnings" in result
            assert "config" in result

    def test_generate_risk_warnings(self, manager):
        """测试生成风险预警"""
        with patch("asset_lens.trading.stock_pool.StockPool") as mock_pool:
            mock_pool_instance = MagicMock()
            mock_pool_instance.list_stocks.return_value = []
            mock_pool.return_value = mock_pool_instance

            warnings = manager.check_risks([])

            assert isinstance(warnings, list)

    def test_calculate_position_advice_empty(self, manager):
        """测试计算仓位建议 - 空持仓"""
        advices = manager.get_position_advice([])

        assert isinstance(advices, list)
        assert len(advices) == 0

    def test_calculate_position_advice_with_positions(self, manager):
        """测试计算仓位建议 - 有持仓"""
        holdings = [
            {"code": "sh600519", "name": "贵州茅台", "market_value": 180000, "profit_rate": 5},
        ]

        advices = manager.get_position_advice(holdings)

        assert isinstance(advices, list)


class TestRiskScenarios:
    """风险场景测试"""

    def test_stop_loss_scenario(self):
        """测试止损场景"""
        buy_price = 100.0
        stop_loss_rate = -0.08
        current_price = 90.0

        profit_rate = (current_price - buy_price) / buy_price
        triggered = profit_rate <= stop_loss_rate

        assert triggered is True

    def test_take_profit_scenario(self):
        """测试止盈场景"""
        buy_price = 100.0
        take_profit_rate = 0.15
        current_price = 120.0

        profit_rate = (current_price - buy_price) / buy_price
        triggered = profit_rate >= take_profit_rate

        assert triggered is True

    def test_concentration_warning_scenario(self):
        """测试集中度预警场景 - 分散持仓"""
        positions = [
            {"code": "sh600519", "value": 25000},
            {"code": "sz000001", "value": 25000},
            {"code": "sh601318", "value": 25000},
            {"code": "sh600036", "value": 25000},
        ]

        total_value = sum(p["value"] for p in positions)
        max_position = max(p["value"] / total_value for p in positions)

        warning = max_position > 0.3

        assert warning is False

    def test_high_concentration_warning_scenario(self):
        """测试高集中度预警场景"""
        positions = [
            {"code": "sh600519", "value": 80000},
            {"code": "sz000001", "value": 10000},
            {"code": "sh601318", "value": 10000},
        ]

        total_value = sum(p["value"] for p in positions)
        max_position = max(p["value"] / total_value for p in positions)

        warning = max_position > 0.3

        assert warning is True
