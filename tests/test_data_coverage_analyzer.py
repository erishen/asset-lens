"""
Tests for Data Coverage Analyzer.
数据覆盖率分析器测试
"""

from asset_lens.data.data_coverage_analyzer import (
    CoverageReport,
    DataCoverageAnalyzer,
    DataCoverageEnhancer,
    DataCoverageResult,
)


class TestCoverageReport:
    """测试覆盖率报告"""

    def test_empty_report(self):
        """测试空报告"""
        report = CoverageReport()
        assert report.total_expected == 0
        assert report.total_actual == 0
        assert report.coverage_rate == 0.0
        assert report.missing_items == []
        assert report.by_category == {}

    def test_calculate_coverage(self):
        """测试计算覆盖率"""
        report = CoverageReport(total_expected=100, total_actual=95)
        report.calculate_coverage()
        assert report.coverage_rate == 95.0

    def test_calculate_coverage_zero(self):
        """测试零预期覆盖率"""
        report = CoverageReport(total_expected=0, total_actual=0)
        report.calculate_coverage()
        assert report.coverage_rate == 0.0


class TestDataCoverageResult:
    """测试覆盖率结果"""

    def test_create_result(self):
        """测试创建结果"""
        result = DataCoverageResult(
            overall_coverage=95.0,
            categories={},
            recommendations=[],
            missing_data_points=5,
            total_data_points=100,
        )
        assert result.overall_coverage == 95.0
        assert result.missing_data_points == 5
        assert result.total_data_points == 100


class TestDataCoverageAnalyzer:
    """测试数据覆盖率分析器"""

    def test_init(self):
        """测试初始化"""
        analyzer = DataCoverageAnalyzer()
        assert analyzer is not None
        assert "transactions" in analyzer.categories
        assert "holdings" in analyzer.categories

    def test_analyze(self):
        """测试分析"""
        analyzer = DataCoverageAnalyzer()
        result = analyzer.analyze()
        assert isinstance(result, DataCoverageResult)
        assert result.overall_coverage >= 0
        assert isinstance(result.categories, dict)


class TestDataCoverageEnhancer:
    """测试数据覆盖率增强器"""

    def test_init(self):
        """测试初始化"""
        enhancer = DataCoverageEnhancer()
        assert enhancer is not None
