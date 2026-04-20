"""
Tests for Risk Alert System.
风险预警系统测试
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock


class TestRiskAlertConfig:
    """风险预警配置测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.monitoring.risk_alert import RiskAlertConfig
        assert RiskAlertConfig is not None

    def test_default_config(self):
        """测试默认配置"""
        from asset_lens.monitoring.risk_alert import RiskAlertConfig

        config = RiskAlertConfig()

        assert config.enabled is True
        assert config.max_drawdown_threshold == 15.0
        assert config.volatility_threshold == 25.0
        assert config.concentration_threshold == 30.0
        assert config.stop_loss_percent == -8.0
        assert config.take_profit_percent == 20.0

    def test_custom_config(self):
        """测试自定义配置"""
        from asset_lens.monitoring.risk_alert import RiskAlertConfig

        config = RiskAlertConfig(
            max_drawdown_threshold=20.0,
            stop_loss_percent=-10.0,
        )

        assert config.max_drawdown_threshold == 20.0
        assert config.stop_loss_percent == -10.0


class TestRiskAlertItem:
    """风险预警项测试"""

    def test_alert_item_creation(self):
        """测试预警项创建"""
        from asset_lens.monitoring.risk_alert import RiskAlertItem, AlertLevel, AlertType

        alert = RiskAlertItem(
            id="test_001",
            level=AlertLevel.WARNING,
            type=AlertType.MAX_DRAWDOWN,
            title="测试预警",
            message="这是一个测试预警",
            value=15.5,
            threshold=15.0,
            timestamp="2024-01-01 12:00:00",
            suggestion="建议操作",
        )

        assert alert.id == "test_001"
        assert alert.level == AlertLevel.WARNING
        assert alert.type == AlertType.MAX_DRAWDOWN
        assert alert.value == 15.5

    def test_alert_item_to_dict(self):
        """测试预警项转换为字典"""
        from asset_lens.monitoring.risk_alert import RiskAlertItem, AlertLevel, AlertType

        alert = RiskAlertItem(
            id="test_001",
            level=AlertLevel.WARNING,
            type=AlertType.MAX_DRAWDOWN,
            title="测试预警",
            message="这是一个测试预警",
            value=15.5,
            threshold=15.0,
            timestamp="2024-01-01 12:00:00",
            suggestion="建议操作",
        )

        result = alert.to_dict()

        assert isinstance(result, dict)
        assert result["id"] == "test_001"
        assert result["level"] == "warning"
        assert result["type"] == "max_drawdown"


class TestRiskAlertSystem:
    """风险预警系统测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.monitoring.risk_alert import RiskAlertSystem
        assert RiskAlertSystem is not None

    def test_system_init(self):
        """测试系统初始化"""
        from asset_lens.monitoring.risk_alert import RiskAlertSystem, RiskAlertConfig

        config = RiskAlertConfig()
        system = RiskAlertSystem(config)

        assert system.config is not None
        assert system.config.enabled is True

    def test_check_max_drawdown_below_threshold(self):
        """测试最大回撤低于阈值"""
        from asset_lens.monitoring.risk_alert import RiskAlertSystem, RiskAlertConfig

        config = RiskAlertConfig(max_drawdown_threshold=15.0)
        system = RiskAlertSystem(config)

        alert = system.check_max_drawdown(10.0)

        assert alert is None

    def test_check_max_drawdown_above_threshold(self):
        """测试最大回撤超过阈值"""
        from asset_lens.monitoring.risk_alert import RiskAlertSystem, RiskAlertConfig, AlertLevel

        config = RiskAlertConfig(max_drawdown_threshold=15.0, alert_cooldown_minutes=0)
        system = RiskAlertSystem(config)

        alert = system.check_max_drawdown(20.0)

        assert alert is not None
        assert alert.level in [AlertLevel.WARNING, AlertLevel.DANGER]
        assert alert.value == 20.0

    def test_check_volatility_below_threshold(self):
        """测试波动率低于阈值"""
        from asset_lens.monitoring.risk_alert import RiskAlertSystem, RiskAlertConfig

        config = RiskAlertConfig(volatility_threshold=25.0)
        system = RiskAlertSystem(config)

        alert = system.check_volatility(20.0)

        assert alert is None

    def test_check_volatility_above_threshold(self):
        """测试波动率超过阈值"""
        from asset_lens.monitoring.risk_alert import RiskAlertSystem, RiskAlertConfig

        config = RiskAlertConfig(volatility_threshold=25.0, alert_cooldown_minutes=0)
        system = RiskAlertSystem(config)

        alert = system.check_volatility(30.0)

        assert alert is not None
        assert alert.value == 30.0

    def test_check_concentration_below_threshold(self):
        """测试集中度低于阈值"""
        from asset_lens.monitoring.risk_alert import RiskAlertSystem, RiskAlertConfig

        config = RiskAlertConfig(concentration_threshold=50.0, alert_cooldown_minutes=0)
        system = RiskAlertSystem(config)

        holdings = {"stock_a": 30000, "stock_b": 40000, "stock_c": 30000}
        alert = system.check_concentration(holdings)

        assert alert is None

    def test_check_concentration_above_threshold(self):
        """测试集中度超过阈值"""
        from asset_lens.monitoring.risk_alert import RiskAlertSystem, RiskAlertConfig

        config = RiskAlertConfig(concentration_threshold=30.0, alert_cooldown_minutes=0)
        system = RiskAlertSystem(config)

        holdings = {"stock_a": 50000, "stock_b": 30000, "stock_c": 20000}
        alert = system.check_concentration(holdings)

        assert alert is not None

    def test_check_stop_loss_below_threshold(self):
        """测试止损低于阈值"""
        from asset_lens.monitoring.risk_alert import RiskAlertSystem, RiskAlertConfig

        config = RiskAlertConfig(stop_loss_percent=-8.0)
        system = RiskAlertSystem(config)

        alert = system.check_stop_loss("sh600519", 100.0, 95.0)

        assert alert is None

    def test_check_stop_loss_above_threshold(self):
        """测试止损超过阈值"""
        from asset_lens.monitoring.risk_alert import RiskAlertSystem, RiskAlertConfig, AlertLevel

        config = RiskAlertConfig(stop_loss_percent=-8.0, alert_cooldown_minutes=0)
        system = RiskAlertSystem(config)

        alert = system.check_stop_loss("sh600519", 100.0, 88.0)

        assert alert is not None
        assert alert.level == AlertLevel.DANGER

    def test_check_take_profit_below_threshold(self):
        """测试止盈低于阈值"""
        from asset_lens.monitoring.risk_alert import RiskAlertSystem, RiskAlertConfig

        config = RiskAlertConfig(take_profit_percent=20.0)
        system = RiskAlertSystem(config)

        alert = system.check_take_profit("sh600519", 100.0, 115.0)

        assert alert is None

    def test_check_take_profit_above_threshold(self):
        """测试止盈超过阈值"""
        from asset_lens.monitoring.risk_alert import RiskAlertSystem, RiskAlertConfig, AlertLevel

        config = RiskAlertConfig(take_profit_percent=20.0, alert_cooldown_minutes=0)
        system = RiskAlertSystem(config)

        alert = system.check_take_profit("sh600519", 100.0, 125.0)

        assert alert is not None
        assert alert.level == AlertLevel.INFO

    def test_check_position_limit_below_threshold(self):
        """测试仓位低于阈值"""
        from asset_lens.monitoring.risk_alert import RiskAlertSystem, RiskAlertConfig

        config = RiskAlertConfig(position_limit=80.0)
        system = RiskAlertSystem(config)

        alert = system.check_position_limit(70.0)

        assert alert is None

    def test_check_position_limit_above_threshold(self):
        """测试仓位超过阈值"""
        from asset_lens.monitoring.risk_alert import RiskAlertSystem, RiskAlertConfig

        config = RiskAlertConfig(position_limit=80.0, alert_cooldown_minutes=0)
        system = RiskAlertSystem(config)

        alert = system.check_position_limit(90.0)

        assert alert is not None

    def test_check_price_change_below_threshold(self):
        """测试价格变动低于阈值"""
        from asset_lens.monitoring.risk_alert import RiskAlertSystem, RiskAlertConfig

        config = RiskAlertConfig(price_change_threshold=5.0)
        system = RiskAlertSystem(config)

        alert = system.check_price_change("sh600519", 3.0)

        assert alert is None

    def test_check_price_change_above_threshold(self):
        """测试价格变动超过阈值"""
        from asset_lens.monitoring.risk_alert import RiskAlertSystem, RiskAlertConfig

        config = RiskAlertConfig(price_change_threshold=5.0, alert_cooldown_minutes=0)
        system = RiskAlertSystem(config)

        alert = system.check_price_change("sh600519", 8.0)

        assert alert is not None

    def test_run_all_checks(self):
        """测试运行所有检查"""
        from asset_lens.monitoring.risk_alert import RiskAlertSystem, RiskAlertConfig

        config = RiskAlertConfig(
            max_drawdown_threshold=15.0,
            volatility_threshold=25.0,
            concentration_threshold=30.0,
            position_limit=80.0,
            alert_cooldown_minutes=0,
        )
        system = RiskAlertSystem(config)

        portfolio_data = {
            "max_drawdown": 20.0,
            "volatility": 30.0,
            "position": 90.0,
            "holdings": {"stock_a": 50000, "stock_b": 30000, "stock_c": 20000},
            "stocks": [],
        }

        alerts = system.run_all_checks(portfolio_data)

        assert isinstance(alerts, list)
        assert len(alerts) > 0

    def test_get_alert_summary(self):
        """测试获取预警摘要"""
        from asset_lens.monitoring.risk_alert import RiskAlertSystem, RiskAlertConfig

        config = RiskAlertConfig(alert_cooldown_minutes=0)
        system = RiskAlertSystem(config)

        system.check_max_drawdown(20.0)
        system.check_volatility(30.0)

        summary = system.get_alert_summary()

        assert isinstance(summary, dict)
        assert "total_alerts" in summary
        assert "by_level" in summary

    def test_clear_alerts(self):
        """测试清除预警"""
        from asset_lens.monitoring.risk_alert import RiskAlertSystem, RiskAlertConfig

        config = RiskAlertConfig(alert_cooldown_minutes=0)
        system = RiskAlertSystem(config)

        system.check_max_drawdown(20.0)
        system.clear_alerts()

        summary = system.get_alert_summary()
        assert summary["total_alerts"] == 0

    def test_generate_alert_report(self):
        """测试生成预警报告"""
        from asset_lens.monitoring.risk_alert import RiskAlertSystem, RiskAlertConfig

        config = RiskAlertConfig(alert_cooldown_minutes=0)
        system = RiskAlertSystem(config)

        system.check_max_drawdown(20.0)

        report = system.generate_alert_report()

        assert isinstance(report, str)
        assert "风险预警报告" in report


class TestAlertLevel:
    """预警级别测试"""

    def test_alert_level_values(self):
        """测试预警级别值"""
        from asset_lens.monitoring.risk_alert import AlertLevel

        assert AlertLevel.INFO.value == "info"
        assert AlertLevel.WARNING.value == "warning"
        assert AlertLevel.DANGER.value == "danger"
        assert AlertLevel.CRITICAL.value == "critical"


class TestAlertType:
    """预警类型测试"""

    def test_alert_type_values(self):
        """测试预警类型值"""
        from asset_lens.monitoring.risk_alert import AlertType

        assert AlertType.MAX_DRAWDOWN.value == "max_drawdown"
        assert AlertType.VOLATILITY.value == "volatility"
        assert AlertType.CONCENTRATION.value == "concentration"
        assert AlertType.STOP_LOSS.value == "stop_loss"
        assert AlertType.TAKE_PROFIT.value == "take_profit"
