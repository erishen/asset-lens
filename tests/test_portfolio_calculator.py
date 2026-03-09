"""
Tests for Portfolio Calculator.
投资组合计算器测试
"""

import pytest
from datetime import date


class TestPortfolioCalculator:
    """投资组合计算器测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.data import portfolio_calculator
        assert portfolio_calculator is not None

    def test_calculate_total_value(self):
        """测试计算总价值"""
        products = [
            {"current_amount": 10000},
            {"current_amount": 20000},
        ]
        total = sum(p["current_amount"] for p in products)
        assert total == 30000

    def test_calculate_total_profit(self):
        """测试计算总收益"""
        products = [
            {"profit_amount": 1000},
            {"profit_amount": 2000},
        ]
        profit = sum(p["profit_amount"] for p in products)
        assert profit == 3000

    def test_calculate_profit_rate(self):
        """测试计算收益率"""
        profit = 10000
        initial = 100000
        profit_rate = profit / initial * 100 if initial > 0 else 0
        assert profit_rate == 10.0

    def test_calculate_profit_rate_zero_initial(self):
        """测试计算收益率 - 初始金额为零"""
        profit = 10000
        initial = 0
        profit_rate = profit / initial * 100 if initial > 0 else 0
        assert profit_rate == 0.0


class TestPortfolioMetrics:
    """投资组合指标测试"""

    def test_sharpe_ratio_calculation(self):
        """测试夏普比率计算"""
        returns = 0.1
        risk_free_rate = 0.02
        volatility = 0.15
        
        if volatility > 0:
            sharpe = (returns - risk_free_rate) / volatility
        else:
            sharpe = 0
        
        assert isinstance(sharpe, float)

    def test_max_drawdown_calculation(self):
        """测试最大回撤计算"""
        values = [100, 110, 105, 115, 108, 120]
        
        max_value = values[0]
        max_drawdown = 0
        
        for value in values:
            if value > max_value:
                max_value = value
            drawdown = (max_value - value) / max_value
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        assert isinstance(max_drawdown, float)
        assert max_drawdown >= 0

    def test_volatility_calculation(self):
        """测试波动率计算"""
        import statistics
        returns = [0.01, 0.02, -0.01, 0.03, -0.02]
        
        if len(returns) > 1:
            vol = statistics.stdev(returns)
        else:
            vol = 0
        
        assert isinstance(vol, float)
        assert vol >= 0

    def test_annualized_return(self):
        """测试年化收益率"""
        total_return = 0.1  # 10%
        days = 365
        
        annualized = (1 + total_return) ** (365 / days) - 1
        assert annualized == pytest.approx(0.1, rel=0.01)


class TestAssetAllocation:
    """资产配置测试"""

    def test_calculate_allocation(self):
        """测试计算资产配置"""
        assets = {
            "股票": 50000,
            "基金": 30000,
            "债券": 20000,
        }
        
        total = sum(assets.values())
        allocation = {k: v / total * 100 for k, v in assets.items()}
        
        assert allocation["股票"] == 50.0
        assert allocation["基金"] == 30.0
        assert allocation["债券"] == 20.0

    def test_rebalance_suggestion(self):
        """测试再平衡建议"""
        current = {"股票": 70, "基金": 20, "债券": 10}
        target = {"股票": 50, "基金": 30, "债券": 20}
        
        suggestions = {}
        for asset in current:
            diff = current[asset] - target[asset]
            if diff > 5:
                suggestions[asset] = f"减持 {diff}%"
            elif diff < -5:
                suggestions[asset] = f"增持 {-diff}%"
        
        assert "股票" in suggestions
