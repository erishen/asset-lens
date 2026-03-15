"""
Tests for Risk Manager.
风险管理系统测试
"""

import pytest
import numpy as np
from datetime import datetime
from pathlib import Path
import tempfile
import shutil

from asset_lens.monitoring.risk_manager import (
    RiskManager,
    RiskMetrics,
    RiskAlert
)


class TestRiskManager:
    """测试风险管理系统"""

    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.risk_manager = RiskManager()

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_calculate_volatility(self):
        returns = [0.01, -0.02, 0.03, -0.01, 0.02, -0.03, 0.01]
        volatility = self.risk_manager.calculate_volatility(returns)
        
        assert volatility > 0
        assert isinstance(volatility, float)

    def test_calculate_volatility_empty(self):
        volatility = self.risk_manager.calculate_volatility([])
        assert volatility == 0.0

    def test_calculate_max_drawdown(self):
        values = [100, 105, 110, 108, 112, 115, 110, 105, 108, 112]
        max_dd = self.risk_manager.calculate_max_drawdown(values)
        
        assert max_dd > 0
        assert isinstance(max_dd, float)

    def test_calculate_max_drawdown_empty(self):
        max_dd = self.risk_manager.calculate_max_drawdown([])
        assert max_dd == 0.0

    def test_calculate_sharpe_ratio(self):
        returns = [0.01, -0.02, 0.03, -0.01, 0.02, -0.03, 0.01]
        sharpe = self.risk_manager.calculate_sharpe_ratio(returns, risk_free_rate=0.03)
        
        assert isinstance(sharpe, float)

    def test_calculate_sharpe_ratio_empty(self):
        sharpe = self.risk_manager.calculate_sharpe_ratio([])
        assert sharpe == 0.0

    def test_calculate_beta(self):
        stock_returns = [0.01, -0.02, 0.03, -0.01, 0.02]
        market_returns = [0.005, -0.01, 0.02, -0.005, 0.01]
        beta = self.risk_manager.calculate_beta(stock_returns, market_returns)
        
        assert isinstance(beta, float)

    def test_calculate_beta_empty(self):
        beta = self.risk_manager.calculate_beta([], [])
        assert beta == 0.0

    def test_calculate_var_95(self):
        returns = [0.01, -0.02, 0.03, -0.01, 0.02, -0.03, 0.01, -0.05, 0.04, -0.02]
        var_95 = self.risk_manager.calculate_var_95(returns)
        
        assert var_95 > 0
        assert isinstance(var_95, float)

    def test_calculate_var_95_empty(self):
        var_95 = self.risk_manager.calculate_var_95([])
        assert var_95 == 0.0

    def test_calculate_concentration_risk(self):
        holdings = {
            'stock1': 10000,
            'stock2': 20000,
            'stock3': 30000,
            'stock4': 40000
        }
        concentration = self.risk_manager.calculate_concentration_risk(holdings)
        
        assert concentration > 0
        assert isinstance(concentration, float)

    def test_calculate_concentration_risk_empty(self):
        concentration = self.risk_manager.calculate_concentration_risk({})
        assert concentration == 0.0

    def test_calculate_all_metrics(self):
        returns = [0.01, -0.02, 0.03, -0.01, 0.02, -0.03, 0.01]
        values = [100, 105, 110, 108, 112, 115, 110, 105, 108, 112]
        
        metrics = self.risk_manager.calculate_all_metrics(returns, values)
        
        assert isinstance(metrics, RiskMetrics)
        assert metrics.volatility > 0
        assert metrics.max_drawdown > 0
        assert isinstance(metrics.sharpe_ratio, float)
        assert metrics.var_95 > 0

    def test_check_risk_thresholds(self):
        metrics = RiskMetrics(
            volatility=30.0,
            max_drawdown=20.0,
            sharpe_ratio=0.3,
            beta=1.0,
            var_95=5.0,
            concentration_risk=40.0
        )
        
        thresholds = {
            'volatility': 25.0,
            'max_drawdown': 15.0,
            'sharpe_ratio': 0.5,
            'concentration_risk': 30.0
        }
        
        alerts = self.risk_manager.check_risk_thresholds(metrics, thresholds)
        
        assert len(alerts) > 0
        assert any(alert.type == 'volatility' for alert in alerts)
        assert any(alert.type == 'max_drawdown' for alert in alerts)
        assert any(alert.type == 'sharpe_ratio' for alert in alerts)
        assert any(alert.type == 'concentration_risk' for alert in alerts)

    def test_check_risk_thresholds_no_alerts(self):
        metrics = RiskMetrics(
            volatility=15.0,
            max_drawdown=8.0,
            sharpe_ratio=1.5,
            beta=1.0,
            var_95=3.0,
            concentration_risk=20.0
        )
        
        thresholds = {
            'volatility': 25.0,
            'max_drawdown': 15.0,
            'sharpe_ratio': 0.5,
            'concentration_risk': 30.0
        }
        
        alerts = self.risk_manager.check_risk_thresholds(metrics, thresholds)
        assert len(alerts) == 0

    def test_generate_risk_report(self):
        metrics = RiskMetrics(
            volatility=20.0,
            max_drawdown=10.0,
            sharpe_ratio=1.2,
            beta=0.8,
            var_95=4.0,
            concentration_risk=25.0
        )
        
        alerts = [
            RiskAlert(
                level='medium',
                type='volatility',
                message='波动率偏高',
                value=20.0,
                threshold=15.0,
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                suggestion='考虑降低仓位'
            )
        ]
        
        report = self.risk_manager.generate_risk_report(metrics, alerts)
        
        assert "风险管理报告" in report
        assert "波动率: 20.00%" in report
        assert "最大回撤: 10.00%" in report
        assert "夏普比率: 1.20" in report

    def test_save_risk_metrics(self):
        metrics = RiskMetrics(
            volatility=20.0,
            max_drawdown=10.0,
            sharpe_ratio=1.2,
            beta=0.8,
            var_95=4.0,
            concentration_risk=25.0
        )
        
        self.risk_manager.save_risk_metrics(metrics)
        assert len(self.risk_manager.risk_history) == 1


class TestRiskMetrics:
    """测试风险指标"""

    def test_default_metrics(self):
        metrics = RiskMetrics()
        assert metrics.volatility == 0.0
        assert metrics.max_drawdown == 0.0
        assert metrics.sharpe_ratio == 0.0
        assert metrics.beta == 0.0
        assert metrics.var_95 == 0.0
        assert metrics.concentration_risk == 0.0

    def test_custom_metrics(self):
        metrics = RiskMetrics(
            volatility=25.0,
            max_drawdown=15.0,
            sharpe_ratio=1.5,
            beta=1.2,
            var_95=5.0,
            concentration_risk=30.0
        )
        
        assert metrics.volatility == 25.0
        assert metrics.max_drawdown == 15.0
        assert metrics.sharpe_ratio == 1.5
        assert metrics.beta == 1.2
        assert metrics.var_95 == 5.0
        assert metrics.concentration_risk == 30.0


class TestRiskAlert:
    """测试风险预警"""

    def test_alert_creation(self):
        alert = RiskAlert(
            level='high',
            type='max_drawdown',
            message='最大回撤超过阈值',
            value=20.0,
            threshold=15.0,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            suggestion='考虑减仓或止损'
        )
        
        assert alert.level == 'high'
        assert alert.type == 'max_drawdown'
        assert alert.message == '最大回撤超过阈值'
        assert alert.value == 20.0
        assert alert.threshold == 15.0
        assert alert.suggestion == '考虑减仓或止损'
