"""
Tests for Report Modules.
报告模块测试
"""

import pytest
from unittest.mock import patch, MagicMock
import tempfile
from pathlib import Path


class TestReportGenerator:
    """报告生成器测试"""

    def test_module_import(self):
        """测试模块导入"""
        try:
            from asset_lens.report.analyzer import ReportGenerator
            assert ReportGenerator is not None
        except ImportError:
            pytest.skip("ReportGenerator not available")

    @pytest.fixture
    def temp_output_path(self):
        """临时输出路径"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    def test_init(self, temp_output_path):
        """测试初始化"""
        try:
            from asset_lens.report.analyzer import ReportGenerator
            generator = ReportGenerator()
            assert generator is not None
        except ImportError:
            pytest.skip("ReportGenerator not available")


class TestChartGenerator:
    """图表生成器测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.report.charts import ChartGenerator
        assert ChartGenerator is not None

    def test_init(self):
        """测试初始化"""
        from asset_lens.report.charts import ChartGenerator
        generator = ChartGenerator()
        assert generator is not None


class TestHTMLReport:
    """HTML 报告测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.report.html_report import HTMLReportGenerator
        assert HTMLReportGenerator is not None

    @pytest.fixture
    def temp_output_path(self):
        """临时输出路径"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir) / "test_report.html"

    def test_init(self, temp_output_path):
        """测试初始化"""
        from asset_lens.report.html_report import HTMLReportGenerator
        generator = HTMLReportGenerator(temp_output_path)
        assert generator is not None


class TestCalculateReport:
    """计算报告测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.report.calculate_report import CalculateReportGenerator
        assert CalculateReportGenerator is not None

    def test_generator_init(self):
        """测试生成器初始化"""
        from asset_lens.report.calculate_report import CalculateReportGenerator
        generator = CalculateReportGenerator()
        assert generator is not None
