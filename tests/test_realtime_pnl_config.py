import json
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pytest

from asset_lens.core.realtime_pnl_config import RealtimePnlConfigMixin


class FakeRealtimePnl(RealtimePnlConfigMixin):
    def __init__(self, tmp_path: Path):
        self._fund_codes_map = None
        self._stock_codes_map = None
        self.fund_cache_file = tmp_path / "fund_cache.json"
        self.stock_cache_file = tmp_path / "stock_cache.json"
        self.domestic_cache_file = tmp_path / "domestic_cache.json"
        self.foreign_cache_file = tmp_path / "foreign_cache.json"


@pytest.fixture
def tmp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def fake_pnl(tmp_dir):
    return FakeRealtimePnl(tmp_dir)


class TestLoadFundCodesConfig:
    def test_cached_result(self, fake_pnl):
        fake_pnl._fund_codes_map = {"test": "000001"}
        result = fake_pnl._load_fund_codes_config()
        assert result == {"test": "000001"}

    def test_file_not_exists(self, fake_pnl, tmp_dir):
        with patch("asset_lens.core.realtime_pnl_config.config") as mock_config:
            mock_config.project_root = tmp_dir
            result = fake_pnl._load_fund_codes_config()
        assert result == {}

    def test_valid_config(self, fake_pnl, tmp_dir):
        config_data = {
            "funds": [
                {"name": "沪深300ETF", "code": "510300", "keywords": ["沪深300"]},
                {"name": "中证500ETF", "code": "510500"},
            ]
        }
        config_file = tmp_dir / "config" / "fund_stock_codes.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(json.dumps(config_data), encoding="utf-8")

        with patch("asset_lens.core.realtime_pnl_config.config") as mock_config:
            mock_config.project_root = tmp_dir
            result = fake_pnl._load_fund_codes_config()

        assert result["沪深300ETF"] == "510300"
        assert result["沪深300"] == "510300"
        assert result["中证500ETF"] == "510500"

    def test_invalid_json(self, fake_pnl, tmp_dir):
        config_file = tmp_dir / "config" / "fund_stock_codes.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text("not json", encoding="utf-8")

        with patch("asset_lens.core.realtime_pnl_config.config") as mock_config:
            mock_config.project_root = tmp_dir
            result = fake_pnl._load_fund_codes_config()
        assert result == {}

    def test_not_dict_root(self, fake_pnl, tmp_dir):
        config_file = tmp_dir / "config" / "fund_stock_codes.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text("[]", encoding="utf-8")

        with patch("asset_lens.core.realtime_pnl_config.config") as mock_config:
            mock_config.project_root = tmp_dir
            result = fake_pnl._load_fund_codes_config()
        assert result == {}

    def test_funds_not_list(self, fake_pnl, tmp_dir):
        config_file = tmp_dir / "config" / "fund_stock_codes.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(json.dumps({"funds": "not_list"}), encoding="utf-8")

        with patch("asset_lens.core.realtime_pnl_config.config") as mock_config:
            mock_config.project_root = tmp_dir
            result = fake_pnl._load_fund_codes_config()
        assert result == {}

    def test_fund_with_empty_name(self, fake_pnl, tmp_dir):
        config_file = tmp_dir / "config" / "fund_stock_codes.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(json.dumps({"funds": [{"name": "", "code": "510300"}]}), encoding="utf-8")

        with patch("asset_lens.core.realtime_pnl_config.config") as mock_config:
            mock_config.project_root = tmp_dir
            result = fake_pnl._load_fund_codes_config()
        assert result == {}


class TestLoadStockCodesConfig:
    def test_cached_result(self, fake_pnl):
        fake_pnl._stock_codes_map = {"test": "600519"}
        result = fake_pnl._load_stock_codes_config()
        assert result == {"test": "600519"}

    def test_valid_config(self, fake_pnl, tmp_dir):
        config_data = {
            "stocks": [
                {"name": "贵州茅台", "code": "600519", "keywords": ["茅台"]},
            ]
        }
        config_file = tmp_dir / "config" / "fund_stock_codes.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(json.dumps(config_data), encoding="utf-8")

        with patch("asset_lens.core.realtime_pnl_config.config") as mock_config:
            mock_config.project_root = tmp_dir
            result = fake_pnl._load_stock_codes_config()

        assert result["贵州茅台"] == "600519"
        assert result["茅台"] == "600519"

    def test_file_not_exists(self, fake_pnl, tmp_dir):
        with patch("asset_lens.core.realtime_pnl_config.config") as mock_config:
            mock_config.project_root = tmp_dir
            result = fake_pnl._load_stock_codes_config()
        assert result == {}


class TestReadFundQuotesFromCache:
    def test_file_not_exists(self, fake_pnl):
        result = fake_pnl._read_fund_quotes_from_cache()
        assert result == {}

    def test_valid_cache(self, fake_pnl):
        data = {"data": {"510300": {"change_percent": 1.5}, "510500": {"change_percent": -0.8}}}
        fake_pnl.fund_cache_file.write_text(json.dumps(data), encoding="utf-8")
        result = fake_pnl._read_fund_quotes_from_cache()
        assert result["510300"] == Decimal("1.5")
        assert result["510500"] == Decimal("-0.8")

    def test_invalid_json(self, fake_pnl):
        fake_pnl.fund_cache_file.write_text("bad json", encoding="utf-8")
        result = fake_pnl._read_fund_quotes_from_cache()
        assert result == {}


class TestReadStockQuotesFromCache:
    def test_file_not_exists(self, fake_pnl):
        result = fake_pnl._read_stock_quotes_from_cache()
        assert result == {}

    def test_valid_cache(self, fake_pnl):
        data = {"data": {"600519": {"change_percent": 2.3}}}
        fake_pnl.stock_cache_file.write_text(json.dumps(data), encoding="utf-8")
        result = fake_pnl._read_stock_quotes_from_cache()
        assert result["600519"] == Decimal("2.3")


class TestReadIndexMovesFromCache:
    def test_no_cache_files(self, fake_pnl):
        result = fake_pnl.read_index_moves_from_cache()
        assert result == {}

    def test_domestic_cache(self, fake_pnl):
        domestic_data = {
            "指数数据": {
                "上证指数": {"涨跌幅": 1.2, "周期表现": {"周涨跌幅": 2.5}},
                "沪深300": {"涨跌幅": 0.8},
            }
        }
        fake_pnl.domestic_cache_file.write_text(json.dumps(domestic_data), encoding="utf-8")
        result = fake_pnl.read_index_moves_from_cache()
        assert result["SHComp"] == Decimal("1.2")
        assert result["HS300"] == Decimal("0.8")

    def test_weekly_mode(self, fake_pnl):
        domestic_data = {
            "指数数据": {
                "上证指数": {"涨跌幅": 1.2, "周期表现": {"周涨跌幅": 3.0}},
            }
        }
        fake_pnl.domestic_cache_file.write_text(json.dumps(domestic_data), encoding="utf-8")
        result = fake_pnl.read_index_moves_from_cache(is_weekly=True)
        assert result["SHComp"] == Decimal("3.0")

    def test_foreign_cache(self, fake_pnl):
        foreign_data = {
            "指数数据": {
                "QQQ": {"涨跌幅": 1.5},
                "SPY": {"涨跌幅": 0.9},
            }
        }
        fake_pnl.foreign_cache_file.write_text(json.dumps(foreign_data), encoding="utf-8")
        result = fake_pnl.read_index_moves_from_cache()
        assert result["Nasdaq"] == Decimal("1.5")
        assert result["SP500"] == Decimal("0.9")

    def test_invalid_domestic_json(self, fake_pnl):
        fake_pnl.domestic_cache_file.write_text("bad", encoding="utf-8")
        result = fake_pnl.read_index_moves_from_cache()
        assert result == {}
