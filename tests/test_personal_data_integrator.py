"""
Tests for Personal Data Integrator.
个人数据整合模块测试
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime

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

    def test_with_data(self):
        """测试有数据"""
        record = WeeklyIndexRecord(
            date="2024-01-01",
            indices={"hs300": 3500.0, "szzs": 3000.0},
            etfs={"qqq": 400.0, "spy": 450.0},
            rates={"usd_rate": 7.0, "hkd_rate": 0.9},
        )
        assert record.indices["hs300"] == 3500.0
        assert record.etfs["qqq"] == 400.0
        assert record.rates["usd_rate"] == 7.0


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
            ts_demo_path="/path/to/ts-demo",
            index_file_pattern="custom_index.csv",
        )
        assert config.ts_demo_path == "/path/to/ts-demo"
        assert config.index_file_pattern == "custom_index.csv"


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
            mock_config.project_root = temp_cache_path
            integrator = PersonalDataIntegrator()
            yield integrator

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.data.personal_data_integrator import personal_data_integrator
        assert personal_data_integrator is not None

    def test_init(self, integrator):
        """测试初始化"""
        assert integrator is not None
        assert integrator.cache_path is not None
        assert integrator.weekly_records is not None

    def test_index_mapping(self, integrator):
        """测试指数映射"""
        assert "沪深300" in integrator.INDEX_MAPPING
        assert integrator.INDEX_MAPPING["沪深300"] == "hs300"
        assert "上证指数" in integrator.INDEX_MAPPING
        assert integrator.INDEX_MAPPING["上证指数"] == "szzs"

    def test_etf_mapping(self, integrator):
        """测试ETF映射"""
        assert "QQQ" in integrator.ETF_MAPPING
        assert integrator.ETF_MAPPING["QQQ"] == "qqq"
        assert "SPY" in integrator.ETF_MAPPING
        assert integrator.ETF_MAPPING["SPY"] == "spy"

    def test_rate_mapping(self, integrator):
        """测试汇率映射"""
        assert "美元汇率" in integrator.RATE_MAPPING
        assert integrator.RATE_MAPPING["美元汇率"] == "usd_rate"
        assert "港元汇率" in integrator.RATE_MAPPING
        assert integrator.RATE_MAPPING["港元汇率"] == "hkd_rate"

    def test_load_cache_empty(self, integrator):
        """测试加载缓存 - 空文件"""
        integrator._load_cache()
        assert integrator.weekly_records == []

    def test_load_cache_with_data(self, integrator):
        """测试加载缓存 - 有数据"""
        cache_data = {
            "weekly_records": [
                {
                    "date": "2024-01-01",
                    "indices": {"hs300": 3500.0},
                    "etfs": {"qqq": 400.0},
                    "rates": {"usd_rate": 7.0},
                }
            ]
        }
        with open(integrator.cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f)

        integrator._load_cache()
        assert len(integrator.weekly_records) == 1
        assert integrator.weekly_records[0].date == "2024-01-01"

    def test_save_cache(self, integrator):
        """测试保存缓存"""
        integrator.weekly_records = [
            WeeklyIndexRecord(
                date="2024-01-01",
                indices={"hs300": 3500.0},
                etfs={"qqq": 400.0},
                rates={"usd_rate": 7.0},
            )
        ]
        integrator._save_cache()

        assert integrator.cache_file.exists()

        with open(integrator.cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "weekly_records" in data
        assert len(data["weekly_records"]) == 1

    def test_load_weekly_data_no_path(self, integrator):
        """测试加载每周数据 - 无路径"""
        integrator.config.ts_demo_path = ""
        loaded = integrator.load_weekly_data()
        assert loaded == 0

    def test_parse_index_file(self, integrator, temp_cache_path):
        """测试解析指数文件"""
        index_file = temp_cache_path / "test_index.csv"
        with open(index_file, "w", encoding="utf-8", newline="") as f:
            import csv
            writer = csv.writer(f)
            writer.writerow(["指数", "数值"])
            writer.writerow(["沪深300", "3500.5"])
            writer.writerow(["上证指数", "3000.25"])

        indices = integrator._parse_index_file(index_file)
        assert "hs300" in indices
        assert indices["hs300"] == 3500.5
        assert "szzs" in indices
        assert indices["szzs"] == 3000.25

    def test_parse_index_file_empty(self, integrator, temp_cache_path):
        """测试解析指数文件 - 空文件"""
        index_file = temp_cache_path / "empty_index.csv"
        with open(index_file, "w", encoding="utf-8") as f:
            f.write("")

        indices = integrator._parse_index_file(index_file)
        assert indices == {}

    def test_parse_etf_file(self, integrator, temp_cache_path):
        """测试解析ETF文件"""
        etf_file = temp_cache_path / "test_etf.csv"
        with open(etf_file, "w", encoding="utf-8", newline="") as f:
            import csv
            writer = csv.writer(f)
            writer.writerow(["ETF", "数值"])
            writer.writerow(["QQQ", "400.5"])
            writer.writerow(["SPY", "450.25"])

        etfs = integrator._parse_etf_file(etf_file)
        assert "qqq" in etfs
        assert etfs["qqq"] == 400.5
        assert "spy" in etfs
        assert etfs["spy"] == 450.25

    def test_parse_etf_file_empty(self, integrator, temp_cache_path):
        """测试解析ETF文件 - 空文件"""
        etf_file = temp_cache_path / "empty_etf.csv"
        with open(etf_file, "w", encoding="utf-8") as f:
            f.write("")

        etfs = integrator._parse_etf_file(etf_file)
        assert etfs == {}

    def test_parse_asset_file(self, integrator, temp_cache_path):
        """测试解析资产文件"""
        asset_file = temp_cache_path / "test_asset.csv"
        with open(asset_file, "w", encoding="utf-8", newline="") as f:
            import csv
            writer = csv.writer(f)
            writer.writerow(["项目", "数值", "美元汇率", "港元汇率"])
            writer.writerow(["测试", "100", "7.0", "0.9"])

        rates = integrator._parse_asset_file(asset_file)
        assert "usd_rate" in rates
        assert rates["usd_rate"] == 7.0
        assert "hkd_rate" in rates
        assert rates["hkd_rate"] == 0.9

    def test_parse_asset_file_empty(self, integrator, temp_cache_path):
        """测试解析资产文件 - 空文件"""
        asset_file = temp_cache_path / "empty_asset.csv"
        with open(asset_file, "w", encoding="utf-8") as f:
            f.write("")

        rates = integrator._parse_asset_file(asset_file)
        assert rates == {}

    def test_get_latest_rates(self, integrator):
        """测试获取最新汇率"""
        integrator.weekly_records = [
            WeeklyIndexRecord(
                date="2024-01-01",
                indices={},
                etfs={},
                rates={"usd_rate": 7.0, "hkd_rate": 0.9},
            )
        ]

        summary = integrator.get_market_summary()
        assert summary is not None
        assert "rates" in summary
        assert summary["rates"]["usd_rate"] == 7.0

    def test_get_latest_rates_empty(self, integrator):
        """测试获取最新汇率 - 空记录"""
        summary = integrator.get_market_summary()
        assert summary is not None

    def test_get_index_history(self, integrator):
        """测试获取指数历史"""
        integrator.weekly_records = [
            WeeklyIndexRecord(
                date="2024-01-01",
                indices={"hs300": 3500.0},
                etfs={},
                rates={},
            ),
            WeeklyIndexRecord(
                date="2024-01-08",
                indices={"hs300": 3600.0},
                etfs={},
                rates={},
            ),
        ]

        history = integrator.get_index_history("hs300")
        assert len(history) == 2
        assert history[0][0] == "2024-01-01"
        assert history[0][1] == 3500.0

    def test_get_index_history_empty(self, integrator):
        """测试获取指数历史 - 空记录"""
        history = integrator.get_index_history("hs300")
        assert history == []

    def test_get_etf_history(self, integrator):
        """测试获取ETF历史"""
        integrator.weekly_records = [
            WeeklyIndexRecord(
                date="2024-01-01",
                indices={},
                etfs={"qqq": 400.0},
                rates={},
            ),
        ]

        history = integrator.get_etf_history("qqq")
        assert len(history) == 1
        assert history[0][1] == 400.0

    def test_get_etf_history_empty(self, integrator):
        """测试获取ETF历史 - 空记录"""
        history = integrator.get_etf_history("qqq")
        assert history == []

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
                indices={"hs300": 3600.0},
                etfs={},
                rates={},
            ),
        ]

        change = integrator.calculate_index_change("hs300")
        assert change is not None
        assert len(change) == 3

    def test_calculate_index_change_single_record(self, integrator):
        """测试计算指数变化 - 单条记录"""
        integrator.weekly_records = [
            WeeklyIndexRecord(
                date="2024-01-01",
                indices={"hs300": 3500.0},
                etfs={},
                rates={},
            ),
        ]

        result = integrator.calculate_index_change("hs300")
        assert result is not None
        assert len(result) == 3

    def test_calculate_index_change_empty(self, integrator):
        """测试计算指数变化 - 空记录"""
        result = integrator.calculate_index_change("hs300")
        assert result is not None
        assert result == (0, 0, 0)


class TestPersonalDataScenarios:
    """个人数据场景测试"""

    def test_weekly_tracking_scenario(self):
        """测试每周追踪场景"""
        records = []
        
        for week in range(4):
            record = WeeklyIndexRecord(
                date=f"2024-0{week + 1}-01",
                indices={"hs300": 3500.0 + week * 50},
                etfs={"qqq": 400.0 + week * 10},
                rates={"usd_rate": 7.0 + week * 0.1},
            )
            records.append(record)

        assert len(records) == 4
        assert records[-1].indices["hs300"] == 3650.0

    def test_rate_change_scenario(self):
        """测试汇率变化场景"""
        records = [
            WeeklyIndexRecord(
                date="2024-01-01",
                indices={},
                etfs={},
                rates={"usd_rate": 7.0},
            ),
            WeeklyIndexRecord(
                date="2024-02-01",
                indices={},
                etfs={},
                rates={"usd_rate": 7.2},
            ),
        ]

        rate_change = (records[1].rates["usd_rate"] - records[0].rates["usd_rate"]) / records[0].rates["usd_rate"] * 100
        assert rate_change == pytest.approx(2.86, rel=0.1)
