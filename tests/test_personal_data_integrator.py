"""
Tests for personal_data_integrator.py
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from asset_lens.data.personal_data_integrator import (
    PersonalDataConfig,
    PersonalDataIntegrator,
    WeeklyIndexRecord,
)


class TestWeeklyIndexRecord:
    """WeeklyIndexRecord 测试"""

    def test_default_values(self):
        """测试默认值"""
        record = WeeklyIndexRecord(
            date="2024-01-01",
            indices={},
            etfs={},
            rates={},
        )
        assert record.date == "2024-01-01"
        assert record.indices == {}
        assert record.etfs == {}
        assert record.rates == {}

    def test_custom_values(self):
        """测试自定义值"""
        record = WeeklyIndexRecord(
            date="2024-01-01",
            indices={"hs300": 3500.0, "szzs": 3000.0},
            etfs={"qqq": 400.0},
            rates={"usd_rate": 7.2},
        )
        assert record.date == "2024-01-01"
        assert record.indices["hs300"] == 3500.0
        assert record.etfs["qqq"] == 400.0
        assert record.rates["usd_rate"] == 7.2


class TestPersonalDataConfig:
    """PersonalDataConfig 测试"""

    def test_default_values(self):
        """测试默认值"""
        config = PersonalDataConfig()
        assert config.ts_demo_path == ""
        assert config.index_file_pattern == "股市指数-表格 1.csv"
        assert config.etf_file_pattern == "美元ETF-表格 1.csv"
        assert config.asset_file_pattern == "资产汇总-表格 1.csv"

    def test_custom_values(self):
        """测试自定义值"""
        config = PersonalDataConfig(
            ts_demo_path="/path/to/data",
            index_file_pattern="custom_index.csv",
            etf_file_pattern="custom_etf.csv",
            asset_file_pattern="custom_asset.csv",
        )
        assert config.ts_demo_path == "/path/to/data"
        assert config.index_file_pattern == "custom_index.csv"
        assert config.etf_file_pattern == "custom_etf.csv"
        assert config.asset_file_pattern == "custom_asset.csv"


class TestPersonalDataIntegrator:
    """PersonalDataIntegrator 测试"""

    @pytest.fixture
    def temp_cache_path(self):
        """临时缓存路径"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def integrator(self, temp_cache_path):
        """创建测试实例"""
        with patch('asset_lens.data.personal_data_integrator.config') as mock_config:
            mock_config.cache_path = temp_cache_path
            integrator = PersonalDataIntegrator()
            yield integrator

    def test_init(self, integrator):
        """测试初始化"""
        assert integrator.config is not None
        assert integrator.cache_file is not None

    def test_load_cache_no_file(self, integrator):
        """测试加载缓存 - 文件不存在"""
        integrator._load_cache()
        assert integrator.weekly_records == []

    def test_load_cache_with_file(self, integrator):
        """测试加载缓存 - 有文件"""
        cache_data = {
            "weekly_records": [
                {
                    "date": "2024-01-01",
                    "indices": {"hs300": 3500.0},
                    "etfs": {},
                    "rates": {},
                }
            ]
        }
        with open(integrator.cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f)

        integrator._load_cache()
        assert len(integrator.weekly_records) == 1

    def test_save_cache(self, integrator):
        """测试保存缓存"""
        integrator.weekly_records = [
            WeeklyIndexRecord(
                date="2024-01-01",
                indices={"hs300": 3500.0},
                etfs={},
                rates={},
            )
        ]
        integrator._save_cache()

        assert integrator.cache_file.exists()

    def test_get_index_history_with_data(self, integrator):
        """测试获取指数历史 - 有数据"""
        integrator.weekly_records = [
            WeeklyIndexRecord(
                date="2024-01-01",
                indices={"hs300": 3500.0, "szzs": 3000.0},
                etfs={},
                rates={},
            ),
            WeeklyIndexRecord(
                date="2024-01-08",
                indices={"hs300": 3550.0, "szzs": 3050.0},
                etfs={},
                rates={},
            ),
        ]

        result = integrator.get_index_history("hs300")

        assert len(result) == 2
        assert result[0][1] == 3500.0
        assert result[1][1] == 3550.0

    def test_get_etf_history_with_data(self, integrator):
        """测试获取 ETF 历史 - 有数据"""
        integrator.weekly_records = [
            WeeklyIndexRecord(
                date="2024-01-01",
                indices={},
                etfs={"qqq": 400.0, "spy": 480.0},
                rates={},
            ),
        ]

        result = integrator.get_etf_history("qqq")

        assert len(result) == 1
        assert result[0][1] == 400.0

    def test_get_rate_history_with_data(self, integrator):
        """测试获取汇率历史 - 有数据"""
        integrator.weekly_records = [
            WeeklyIndexRecord(
                date="2024-01-01",
                indices={},
                etfs={},
                rates={"usd_rate": 7.2, "hkd_rate": 0.92},
            ),
        ]

        result = integrator.get_rate_history("usd_rate")

        assert len(result) == 1
        assert result[0][1] == 7.2

    def test_calculate_index_change(self, integrator):
        """测试计算指数变化"""
        integrator.weekly_records = [
            WeeklyIndexRecord(
                date="2024-01-01",
                indices={"hs300": 3500.0},
                etfs={},
                rates={},
            ),
            WeeklyIndexRecord(
                date="2024-01-08",
                indices={"hs300": 3550.0},
                etfs={},
                rates={},
            ),
        ]

        current, change_pct, change = integrator.calculate_index_change("hs300")

        assert current == 3550.0
        assert change == 50.0
        assert change_pct == pytest.approx(1.43, rel=0.01)

    def test_get_market_summary_empty(self, integrator):
        """测试获取市场摘要 - 空数据"""
        result = integrator.get_market_summary()

        assert "error" in result

    def test_get_market_summary_with_data(self, integrator):
        """测试获取市场摘要 - 有数据"""
        integrator.weekly_records = [
            WeeklyIndexRecord(
                date="2024-01-01",
                indices={"hs300": 3500.0, "szzs": 3000.0},
                etfs={"qqq": 400.0},
                rates={"usd_rate": 7.2},
            ),
        ]

        result = integrator.get_market_summary()

        assert "indices" in result or "error" not in result
