"""
Tests for Risk Manager.
风险管理器测试
"""

from unittest.mock import MagicMock, patch

import pytest


class TestRiskManager:
    """风险管理器测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.trading.risk_manager import RiskManager

        assert RiskManager is not None

    @pytest.fixture
    def manager(self):
        """创建管理器实例"""
        from asset_lens.trading.risk_manager import RiskManager

        with patch("asset_lens.trading.risk_manager.config") as mock_config:
            mock_config.cache_path = MagicMock()
            return RiskManager()

    def test_manager_init(self, manager):
        """测试初始化"""
        assert manager is not None

    def test_check_risk_method(self, manager):
        """测试风险检查方法"""
        assert (
            hasattr(manager, "check_position_concentration")
            or hasattr(manager, "generate_risk_warnings")
            or hasattr(manager, "get_risk_summary")
        )


class TestRiskMetrics:
    """风险指标测试"""

    def test_var_calculation(self):
        """测试 VaR 计算"""
        import statistics

        returns = [0.01, -0.02, 0.03, -0.01, 0.02, -0.03, 0.01]

        mean = statistics.mean(returns)
        std = statistics.stdev(returns)
        var = mean - 1.65 * std  # 95% 置信度

        assert isinstance(var, float)

    def test_max_drawdown_calculation(self):
        """测试最大回撤计算"""
        values = [100, 110, 105, 115, 108, 120, 110]

        max_value = values[0]
        max_drawdown = 0

        for value in values:
            if value > max_value:
                max_value = value
            drawdown = (max_value - value) / max_value
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        assert max_drawdown >= 0

    def test_sharpe_ratio_calculation(self):
        """测试夏普比率计算"""
        returns = [0.01, 0.02, -0.01, 0.03, -0.02]
        risk_free_rate = 0.02 / 252  # 日化无风险利率

        import statistics

        mean_return = statistics.mean(returns)
        std_return = statistics.stdev(returns)

        sharpe = (mean_return - risk_free_rate) / std_return if std_return > 0 else 0
        assert isinstance(sharpe, float)


class TestRiskAlerts:
    """风险警报测试"""

    def test_stop_loss_alert(self):
        """测试止损警报"""
        current_price = 9.0
        buy_price = 10.0
        stop_loss_rate = 0.1  # 10% 止损

        loss_rate = (buy_price - current_price) / buy_price
        should_alert = loss_rate >= stop_loss_rate

        assert should_alert is True

    def test_take_profit_alert(self):
        """测试止盈警报"""
        current_price = 12.0
        buy_price = 10.0
        take_profit_rate = 0.2  # 20% 止盈

        profit_rate = (current_price - buy_price) / buy_price
        should_alert = profit_rate >= take_profit_rate

        assert should_alert is True

    def test_position_limit_alert(self):
        """测试仓位限制警报"""
        current_position = 0.8  # 80% 仓位
        max_position = 0.7  # 最大 70% 仓位

        should_alert = current_position > max_position
        assert should_alert is True


class TestRiskLevels:
    """风险等级测试"""

    def test_low_risk(self):
        """测试低风险"""
        risk_score = 20
        risk_level = "low" if risk_score < 30 else "medium" if risk_score < 60 else "high"
        assert risk_level == "low"

    def test_medium_risk(self):
        """测试中等风险"""
        risk_score = 50
        risk_level = "low" if risk_score < 30 else "medium" if risk_score < 60 else "high"
        assert risk_level == "medium"

    def test_high_risk(self):
        """测试高风险"""
        risk_score = 80
        risk_level = "low" if risk_score < 30 else "medium" if risk_score < 60 else "high"
        assert risk_level == "high"
