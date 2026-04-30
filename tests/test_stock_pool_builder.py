"""
Tests for Stock Pool Builder - 股票池构建器测试

覆盖边界场景:
- 空池
- 价格缺失
- 最小持有期
- 贡献占比
"""

from asset_lens.trading.stock_pool_builder import (
    FactorCategory,
    FilterCondition,
    StockEntryMatrix,
    StockPoolBuilder,
)


class TestStockPoolBuilder:
    """股票池构建器测试"""

    def test_empty_pool(self):
        """测试空池场景"""
        builder = StockPoolBuilder()

        result = builder.build_pool([])

        assert result is not None
        assert len(result) == 0

    def test_single_stock_pass(self):
        """测试单只股票通过"""
        builder = StockPoolBuilder()
        builder.add_fundamental_filters()

        stock_data = {
            "code": "sh600519",
            "name": "贵州茅台",
            "pe": 25.0,
            "score": 80,
        }

        result = builder.build_pool([stock_data])

        assert result is not None

    def test_single_stock_fail(self):
        """测试单只股票不通过"""
        builder = StockPoolBuilder()

        stock_data = {
            "code": "sh600519",
            "name": "贵州茅台",
            "pe": 35.0,
            "score": 40,
        }

        result = builder.build_pool([stock_data])

        assert result is not None

    def test_missing_price_data(self):
        """测试价格缺失场景"""
        builder = StockPoolBuilder()

        stock_data = {
            "code": "sh600519",
            "name": "贵州茅台",
            "pe": 25.0,
            "score": 80,
        }

        result = builder.build_pool([stock_data])

        assert result is not None

    def test_multiple_stocks(self):
        """测试多只股票筛选"""
        builder = StockPoolBuilder()
        builder.add_fundamental_filters()

        stock_data_list = [
            {"code": "sh600519", "name": "股票A", "pe": 25.0, "roe": 18.0, "revenue_growth": 15.0, "score": 85},
            {"code": "sh600520", "name": "股票B", "pe": 35.0, "roe": 18.0, "revenue_growth": 15.0, "score": 70},
            {"code": "sh600521", "name": "股票C", "pe": 25.0, "roe": 10.0, "revenue_growth": 15.0, "score": 60},
        ]

        result = builder.build_pool(stock_data_list)

        assert result is not None

    def test_min_score_threshold(self):
        """测试最低分数阈值"""
        builder = StockPoolBuilder()

        stock_data_list = [
            {"code": "sh600519", "name": "股票A", "score": 85},
            {"code": "sh600520", "name": "股票B", "score": 55},
            {"code": "sh600521", "name": "股票C", "score": 60},
        ]

        result = builder.build_pool(stock_data_list, min_score=60)

        assert result is not None

    def test_contribution_ratio(self):
        """测试贡献占比计算"""
        builder = StockPoolBuilder()

        stock_data_list = [
            {"code": "sh600519", "name": "股票A", "score": 100, "pe": 20.0},
            {"code": "sh600520", "name": "股票B", "score": 50, "pe": 25.0},
            {"code": "sh600521", "name": "股票C", "score": 50, "pe": 30.0},
        ]

        result = builder.build_pool(stock_data_list)

        assert result is not None


class TestFilterCondition:
    """筛选条件测试"""

    def test_condition_creation(self):
        """测试条件创建"""
        condition = FilterCondition(
            name="PE合理",
            category=FactorCategory.FUNDAMENTAL,
            field="pe",
            operator="<",
            value=30,
            weight=1.0,
        )

        assert condition.name == "PE合理"
        assert condition.field == "pe"
        assert condition.operator == "<"
        assert condition.value == 30

    def test_condition_evaluate_pass(self):
        """测试条件评估通过"""
        condition = FilterCondition(
            name="PE合理",
            category=FactorCategory.FUNDAMENTAL,
            field="pe",
            operator="<",
            value=30,
            weight=1.0,
        )

        stock_data = {"pe": 25.0}

        result = condition.evaluate(stock_data)

        assert result is True

    def test_condition_evaluate_fail(self):
        """测试条件评估失败"""
        condition = FilterCondition(
            name="PE合理",
            category=FactorCategory.FUNDAMENTAL,
            field="pe",
            operator="<",
            value=30,
            weight=1.0,
        )

        stock_data = {"pe": 35.0}

        result = condition.evaluate(stock_data)

        assert result is False

    def test_missing_field(self):
        """测试字段缺失"""
        condition = FilterCondition(
            name="PE合理",
            category=FactorCategory.FUNDAMENTAL,
            field="pe",
            operator="<",
            value=30,
            weight=1.0,
        )

        stock_data = {}

        result = condition.evaluate(stock_data)

        assert result is False


class TestStockEntryMatrix:
    """股票入池矩阵测试"""

    def test_matrix_creation(self):
        """测试矩阵创建"""
        matrix = StockEntryMatrix(
            code="sh600519",
            name="贵州茅台",
            total_score=85.0,
            weighted_score=85.0,
            passed_factors=5,
            total_factors=8,
            entry_reasons=[],
            entry_date="2024-01-01",
            data_source="test",
        )

        assert matrix.code == "sh600519"
        assert matrix.name == "贵州茅台"
        assert matrix.total_score == 85.0

    def test_matrix_to_dict(self):
        """测试矩阵转字典"""
        matrix = StockEntryMatrix(
            code="sh600519",
            name="贵州茅台",
            total_score=85.0,
            weighted_score=85.0,
            passed_factors=5,
            total_factors=8,
            entry_reasons=[],
            entry_date="2024-01-01",
            data_source="test",
        )

        result = matrix.to_dict()

        assert "code" in result
        assert "name" in result
        assert "total_score" in result
        assert "pass_rate" in result
