"""
Tests for config module.
配置模块测试
"""

from pathlib import Path

from asset_lens.config import Config, config


class TestConfig:
    """Test Config class"""

    def test_config_singleton(self):
        """Test that config is a singleton"""
        from asset_lens.config import config as config2

        assert config is config2

    def test_config_has_data_mode(self):
        """Test that config has data_mode attribute"""
        assert hasattr(config, "data_mode")

    def test_config_has_project_root(self):
        """Test that config has project_root attribute"""
        assert hasattr(config, "project_root")
        assert config.project_root.exists()

    def test_config_has_data_path(self):
        """Test that config has data_path property"""
        assert hasattr(config, "data_path")

    def test_config_has_platforms(self):
        """Test that config has platforms property"""
        assert hasattr(config, "platforms")

    def test_config_has_investment_types(self):
        """Test that config has investment_types property"""
        assert hasattr(config, "investment_types")


class TestConfigDataMode:
    """Test config data mode"""

    def test_data_mode_property(self):
        """Test data_mode property"""
        original_mode = config.data_mode
        config.data_mode = "sample"
        assert config.data_mode == "sample"
        config.data_mode = original_mode

    def test_is_sample_mode(self):
        """Test is_sample_mode property"""
        original_mode = config.data_mode
        config.data_mode = "sample"
        assert config.is_sample_mode is True
        assert config.is_real_mode is False
        config.data_mode = original_mode

    def test_is_real_mode(self):
        """Test is_real_mode property"""
        original_mode = config.data_mode
        config.data_mode = "real"
        assert config.is_real_mode is True
        assert config.is_sample_mode is False
        config.data_mode = original_mode

    def test_data_mode_affects_data_path(self):
        """Test that data mode affects data path"""
        original_mode = config.data_mode

        config.data_mode = "sample"
        sample_path = config.data_path

        config.data_mode = "real"
        real_path = config.data_path

        # Paths should be different
        assert sample_path != real_path

        config.data_mode = original_mode


class TestConfigPaths:
    """Test config paths"""

    def test_data_path_property(self):
        """Test data_path property"""
        path = config.data_path
        assert path is not None
        assert isinstance(path, Path)

    def test_ensure_directories(self):
        """Test ensure_directories method"""
        # Should not raise any errors
        config.ensure_directories()

    def test_get_latest_data_dir(self):
        """Test get_latest_data_dir method"""
        latest_dir = config.get_latest_data_dir()
        # May return None if no data directories exist
        assert latest_dir is None or isinstance(latest_dir, Path)


class TestConfigPlatforms:
    """Test config platforms"""

    def test_platforms_property(self):
        """Test platforms property"""
        platforms = config.platforms
        assert platforms is not None
        assert len(platforms) > 0

    def test_get_platform_by_name(self):
        """Test get_platform_by_name method"""
        platform = config.get_platform_by_name("微信")
        # May return None if not found
        assert platform is None or hasattr(platform, "name")

    def test_get_platform_by_field(self):
        """Test get_platform_by_field method"""
        platform = config.get_platform_by_field("微信")
        # May return None if not found
        assert platform is None or hasattr(platform, "name")

    def test_platform_types(self):
        """Test platform_types property"""
        types = config.platform_types
        assert types is not None
        assert isinstance(types, dict)

    def test_get_platform_mapping(self):
        """Test get_platform_mapping method"""
        mapping = config.get_platform_mapping()
        assert mapping is not None
        assert isinstance(mapping, dict)


class TestConfigInvestmentTypes:
    """Test config investment types"""

    def test_investment_types_property(self):
        """Test investment_types property"""
        types = config.investment_types
        assert types is not None
        assert len(types) > 0

    def test_get_investment_type_by_id(self):
        """Test get_investment_type_by_id method"""
        inv_type = config.get_investment_type_by_id("stock")
        # May return None if not found
        assert inv_type is None or hasattr(inv_type, "name")

    def test_get_investment_type_by_name(self):
        """Test get_investment_type_by_name method"""
        inv_type = config.get_investment_type_by_name("股票")
        # May return None if not found
        assert inv_type is None or hasattr(inv_type, "name")

    def test_risk_levels(self):
        """Test risk_levels property"""
        levels = config.risk_levels
        assert levels is not None
        assert isinstance(levels, dict)

    def test_get_risk_level(self):
        """Test get_risk_level method"""
        level = config.get_risk_level("low")
        # May return None if not found
        assert level is None or hasattr(level, "name")


class TestConfigStr:
    """Test config string representation"""

    def test_str_representation(self):
        """Test config string representation"""
        str_repr = str(config)
        assert str_repr is not None
        assert isinstance(str_repr, str)

    def test_repr(self):
        """Test config repr"""
        repr_str = repr(config)
        assert repr_str is not None


class TestConfigEdgeCases:
    """Test config edge cases"""

    def test_invalid_data_mode(self):
        """Test setting invalid data mode"""
        original_mode = config.data_mode
        # Setting invalid mode should not crash
        try:
            config.data_mode = "invalid"
        except Exception:
            pass
        finally:
            config.data_mode = original_mode

    def test_get_platform_by_name_not_found(self):
        """Test get_platform_by_name with non-existent name"""
        platform = config.get_platform_by_name("nonexistent_platform")
        assert platform is None

    def test_get_platform_by_field_not_found(self):
        """Test get_platform_by_field with non-existent field"""
        platform = config.get_platform_by_field("nonexistent_field")
        assert platform is None

    def test_get_investment_type_by_id_not_found(self):
        """Test get_investment_type_by_id with non-existent id"""
        inv_type = config.get_investment_type_by_id("nonexistent_id")
        assert inv_type is None

    def test_get_investment_type_by_name_not_found(self):
        """Test get_investment_type_by_name with non-existent name"""
        inv_type = config.get_investment_type_by_name("nonexistent_type")
        assert inv_type is None

    def test_get_risk_level_not_found(self):
        """Test get_risk_level with non-existent id"""
        level = config.get_risk_level("nonexistent_level")
        assert level is None


class TestConfigInitialization:
    """Test config initialization"""

    def test_config_initialization(self):
        """Test that config can be initialized"""
        test_config = Config()
        assert test_config is not None

    def test_config_loads_platform_config(self):
        """Test that config loads platform config"""
        test_config = Config()
        assert test_config.platforms is not None

    def test_config_loads_investment_type_config(self):
        """Test that config loads investment type config"""
        test_config = Config()
        assert test_config.investment_types is not None
