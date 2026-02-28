"""
Tests for config module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from asset_lens.config import Config


class TestConfig:
    """Test Config class"""

    def test_config_default_values(self):
        config = Config()
        assert config.data_mode is not None
        assert config.cache_path is not None

    def test_config_data_mode_property(self):
        config = Config()
        assert config.data_mode in ["sample", "real"]

    def test_config_cache_path_property(self):
        config = Config()
        assert isinstance(config.cache_path, Path)

    def test_config_output_path_property(self):
        config = Config()
        assert isinstance(config.output_path, Path)

    def test_config_data_path_property(self):
        config = Config()
        assert isinstance(config.data_path, Path)

    def test_config_usd_rate_default(self):
        config = Config()
        assert config.default_usd_rate is not None
        assert isinstance(config.default_usd_rate, float)

    def test_config_hkd_rate_default(self):
        config = Config()
        assert config.default_hkd_rate is not None
        assert isinstance(config.default_hkd_rate, float)

    def test_config_min_return_threshold_default(self):
        config = Config()
        assert config.min_return_threshold is not None

    def test_config_workday_ratio_default(self):
        config = Config()
        assert config.workday_ratio is not None

    def test_config_output_format_default(self):
        config = Config()
        assert config.output_format is not None

    def test_config_report_language_default(self):
        config = Config()
        assert config.report_language is not None


class TestConfigSingleton:
    """Test Config singleton"""

    def test_config_singleton(self):
        from asset_lens.config import config as config1
        from asset_lens.config import config as config2
        assert config1 is config2
