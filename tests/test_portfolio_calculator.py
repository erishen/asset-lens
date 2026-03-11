"""
Tests for Portfolio Calculator.
投资组合计算器测试
"""

import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock


class TestPortfolioCalculator:
    """投资组合计算器测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.data.portfolio_calculator import PortfolioCalculator, create_calculator
        assert PortfolioCalculator is not None
        assert create_calculator is not None

    def test_get_us_investment_types(self):
        """测试获取美元投资类型"""
        from asset_lens.data.portfolio_calculator import _get_us_investment_types
        
        types = _get_us_investment_types()
        assert types is not None
        assert len(types) > 0

    def test_get_hk_investment_types(self):
        """测试获取港币投资类型"""
        from asset_lens.data.portfolio_calculator import _get_hk_investment_types
        
        types = _get_hk_investment_types()
        assert types is not None
        assert len(types) > 0

    @pytest.fixture
    def mock_portfolio(self):
        """创建模拟投资组合"""
        portfolio = MagicMock()
        portfolio.usd_rate = Decimal("7.0")
        portfolio.hkd_rate = Decimal("0.9")
        portfolio.products = []
        return portfolio

    @pytest.fixture
    def mock_product(self):
        """创建模拟投资产品"""
        product = MagicMock()
        product.start_date = date(2024, 1, 1)
        product.current_amount = Decimal("10000")
        product.initial_amount = Decimal("8000")
        product.investment_type = MagicMock()
        product.investment_type.value = "基金"
        product.usd_rate = None
        product.hkd_rate = None
        product.transaction_records = None
        return product

    def test_calculator_init(self, mock_portfolio):
        """测试计算器初始化"""
        from asset_lens.data.portfolio_calculator import PortfolioCalculator
        
        calculator = PortfolioCalculator(mock_portfolio)
        assert calculator._portfolio == mock_portfolio
        assert calculator._cache == {}

    def test_clear_cache(self, mock_portfolio):
        """测试清除缓存"""
        from asset_lens.data.portfolio_calculator import PortfolioCalculator
        
        calculator = PortfolioCalculator(mock_portfolio)
        calculator._cache["test"] = "value"
        calculator.clear_cache()
        assert calculator._cache == {}

    def test_get_cache_key(self, mock_portfolio):
        """测试生成缓存键"""
        from asset_lens.data.portfolio_calculator import PortfolioCalculator
        
        calculator = PortfolioCalculator(mock_portfolio)
        key = calculator._get_cache_key("method", "arg1", "arg2")
        assert "method" in key

    def test_convert_amount_rmb(self, mock_portfolio, mock_product):
        """测试人民币金额转换"""
        from asset_lens.data.portfolio_calculator import PortfolioCalculator
        from asset_lens.data.models import InvestmentType
        
        mock_product.investment_type = InvestmentType.FUND
        calculator = PortfolioCalculator(mock_portfolio)
        
        amount = Decimal("10000")
        converted = calculator._convert_amount(amount, mock_product)
        assert converted == amount

    def test_convert_amount_usd(self, mock_portfolio, mock_product):
        """测试美元金额转换"""
        from asset_lens.data.portfolio_calculator import PortfolioCalculator
        from asset_lens.data.models import InvestmentType
        
        mock_product.investment_type = InvestmentType.US_STOCK
        calculator = PortfolioCalculator(mock_portfolio)
        
        amount = Decimal("1000")
        converted = calculator._convert_amount(amount, mock_product)
        assert converted == amount * mock_portfolio.usd_rate

    def test_convert_amount_hkd(self, mock_portfolio, mock_product):
        """测试港币金额转换"""
        from asset_lens.data.portfolio_calculator import PortfolioCalculator
        from asset_lens.data.models import InvestmentType
        
        mock_product.investment_type = InvestmentType.HK_STOCK
        calculator = PortfolioCalculator(mock_portfolio)
        
        amount = Decimal("10000")
        converted = calculator._convert_amount(amount, mock_product)
        assert converted == amount * mock_portfolio.hkd_rate

    def test_calculate_total_value(self, mock_portfolio, mock_product):
        """测试计算总资产"""
        from asset_lens.data.portfolio_calculator import PortfolioCalculator
        from asset_lens.data.models import InvestmentType
        
        mock_product.investment_type = InvestmentType.FUND
        mock_portfolio.products = [mock_product]
        
        calculator = PortfolioCalculator(mock_portfolio)
        total = calculator.calculate_total_value()
        assert total == Decimal("10000")

    def test_calculate_total_value_with_cache(self, mock_portfolio, mock_product):
        """测试计算总资产 - 使用缓存"""
        from asset_lens.data.portfolio_calculator import PortfolioCalculator
        from asset_lens.data.models import InvestmentType
        
        mock_product.investment_type = InvestmentType.FUND
        mock_portfolio.products = [mock_product]
        
        calculator = PortfolioCalculator(mock_portfolio)
        calculator._cache["total_value"] = Decimal("50000")
        
        total = calculator.calculate_total_value()
        assert total == Decimal("50000")

    def test_calculate_total_value_skip_no_start_date(self, mock_portfolio):
        """测试计算总资产 - 跳过没有开始日期的产品"""
        from asset_lens.data.portfolio_calculator import PortfolioCalculator
        
        product = MagicMock()
        product.start_date = None
        product.current_amount = Decimal("10000")
        mock_portfolio.products = [product]
        
        calculator = PortfolioCalculator(mock_portfolio)
        total = calculator.calculate_total_value()
        assert total == Decimal("0")

    def test_calculate_total_initial(self, mock_portfolio, mock_product):
        """测试计算总初始投资"""
        from asset_lens.data.portfolio_calculator import PortfolioCalculator
        from asset_lens.data.models import InvestmentType
        
        mock_product.investment_type = InvestmentType.FUND
        mock_portfolio.products = [mock_product]
        
        calculator = PortfolioCalculator(mock_portfolio)
        initial = calculator.calculate_total_initial()
        assert initial == Decimal("8000")

    def test_calculate_total_profit(self, mock_portfolio, mock_product):
        """测试计算总收益"""
        from asset_lens.data.portfolio_calculator import PortfolioCalculator
        from asset_lens.data.models import InvestmentType
        
        mock_product.investment_type = InvestmentType.FUND
        mock_portfolio.products = [mock_product]
        
        calculator = PortfolioCalculator(mock_portfolio)
        profit = calculator.calculate_total_profit()
        assert profit == Decimal("2000")

    def test_calculate_overall_return_rate(self, mock_portfolio, mock_product):
        """测试计算整体收益率"""
        from asset_lens.data.portfolio_calculator import PortfolioCalculator
        from asset_lens.data.models import InvestmentType
        
        mock_product.investment_type = InvestmentType.FUND
        mock_portfolio.products = [mock_product]
        
        calculator = PortfolioCalculator(mock_portfolio)
        rate = calculator.calculate_overall_return_rate()
        assert rate == Decimal("25")

    def test_calculate_overall_return_rate_zero_initial(self, mock_portfolio):
        """测试计算整体收益率 - 初始为零"""
        from asset_lens.data.portfolio_calculator import PortfolioCalculator
        
        mock_portfolio.products = []
        
        calculator = PortfolioCalculator(mock_portfolio)
        rate = calculator.calculate_overall_return_rate()
        assert rate is None

    def test_get_type_distribution(self, mock_portfolio, mock_product):
        """测试获取类型分布"""
        from asset_lens.data.portfolio_calculator import PortfolioCalculator
        from asset_lens.data.models import InvestmentType
        
        mock_product.investment_type = InvestmentType.FUND
        mock_portfolio.products = [mock_product]
        
        calculator = PortfolioCalculator(mock_portfolio)
        distribution = calculator.get_type_distribution()
        
        assert "基金" in distribution
        assert distribution["基金"]["count"] == 1
        assert distribution["基金"]["total_value"] == Decimal("10000")

    def test_get_type_distribution_with_cache(self, mock_portfolio, mock_product):
        """测试获取类型分布 - 使用缓存"""
        from asset_lens.data.portfolio_calculator import PortfolioCalculator
        
        cached_data = {"基金": {"count": 5, "total_value": Decimal("50000"), "products": [], "percentage": Decimal("100")}}
        
        calculator = PortfolioCalculator(mock_portfolio)
        calculator._cache["type_distribution"] = cached_data
        
        distribution = calculator.get_type_distribution()
        assert distribution == cached_data

    def test_get_risk_distribution(self, mock_portfolio, mock_product):
        """测试获取风险分布"""
        from asset_lens.data.portfolio_calculator import PortfolioCalculator
        
        mock_product.risk_level = MagicMock()
        mock_product.risk_level.value = "中"
        mock_portfolio.products = [mock_product]
        
        calculator = PortfolioCalculator(mock_portfolio)
        distribution = calculator.get_risk_distribution()
        
        assert "中" in distribution
        assert distribution["中"]["count"] == 1

    def test_create_calculator(self, mock_portfolio):
        """测试创建计算器工厂函数"""
        from asset_lens.data.portfolio_calculator import create_calculator
        
        calculator = create_calculator(mock_portfolio)
        assert calculator is not None
        assert calculator._portfolio == mock_portfolio


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
        total_return = 0.1
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
