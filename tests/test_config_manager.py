"""
Tests for config_manager module.
配置管理器模块测试
"""

import tempfile
from pathlib import Path


class TestDataSourceConfig:
    """数据源配置测试"""

    def test_data_source_config_default(self):
        """测试默认数据源配置"""
        from asset_lens.core.config_manager import DataSourceConfig

        config = DataSourceConfig(name="test")
        assert config.name == "test"
        assert config.priority == 1
        assert config.enabled is True
        assert config.api_key is None
        assert config.timeout == 30
        assert config.retry_times == 3

    def test_data_source_config_custom(self):
        """测试自定义数据源配置"""
        from asset_lens.core.config_manager import DataSourceConfig

        config = DataSourceConfig(
            name="custom",
            priority=5,
            enabled=False,
            api_key="test_key",
            api_url="http://test.com",
            timeout=60,
            retry_times=5,
        )
        assert config.name == "custom"
        assert config.priority == 5
        assert config.enabled is False
        assert config.api_key == "test_key"
        assert config.api_url == "http://test.com"
        assert config.timeout == 60
        assert config.retry_times == 5


class TestMonitorConfig:
    """监控配置测试"""

    def test_monitor_config_default(self):
        """测试默认监控配置"""
        from asset_lens.core.config_manager import MonitorConfig

        config = MonitorConfig()
        assert config.price_threshold == 5.0
        assert config.volatility_threshold == 20.0
        assert config.max_drawdown_threshold == 10.0
        assert config.concentration_threshold == 30.0
        assert config.check_interval == 300
        assert config.enable_alerts is True


class TestUserPreferences:
    """用户偏好测试"""

    def test_user_preferences_default(self):
        """测试默认用户偏好"""
        from asset_lens.core.config_manager import UserPreferences

        prefs = UserPreferences()
        assert prefs.risk_tolerance == "moderate"
        assert prefs.investment_goal == "balanced"
        assert prefs.preferred_sectors == []
        assert prefs.excluded_sectors == []
        assert prefs.max_position_size == 10.0
        assert prefs.rebalance_frequency == "monthly"

    def test_user_preferences_custom(self):
        """测试自定义用户偏好"""
        from asset_lens.core.config_manager import UserPreferences

        prefs = UserPreferences(
            risk_tolerance="aggressive",
            investment_goal="growth",
            preferred_sectors=["科技", "医药"],
            excluded_sectors=["房地产"],
            max_position_size=15.0,
            rebalance_frequency="weekly",
        )
        assert prefs.risk_tolerance == "aggressive"
        assert prefs.preferred_sectors == ["科技", "医药"]


class TestAlertConfig:
    """提醒配置测试"""

    def test_alert_config_default(self):
        """测试默认提醒配置"""
        from asset_lens.core.config_manager import AlertConfig

        config = AlertConfig()
        assert config.enable_email is False
        assert config.enable_qq is True
        assert config.enable_wechat is False
        assert config.daily_report_time == "15:00"
        assert config.weekly_report_day == 4
        assert config.weekly_report_time == "16:00"


class TestConfigManager:
    """配置管理器测试"""

    def test_config_manager_init(self):
        """测试配置管理器初始化"""
        from asset_lens.core.config_manager import ConfigManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.json"
            manager = ConfigManager(config_path)
            assert manager.config is not None
            assert "version" in manager.config

    def test_config_manager_default_config(self):
        """测试默认配置"""
        from asset_lens.core.config_manager import ConfigManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.json"
            manager = ConfigManager(config_path)
            assert manager.config["version"] == "1.0.0"
            assert "data_sources" in manager.config
            assert "monitor" in manager.config

    def test_config_manager_get_data_source_config(self):
        """测试获取数据源配置"""
        from asset_lens.core.config_manager import ConfigManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.json"
            manager = ConfigManager(config_path)
            config = manager.get_data_source_config("eastmoney")
            assert config is not None
            assert config.name == "东方财富"

    def test_config_manager_get_data_source_config_not_found(self):
        """测试获取不存在的数据源配置"""
        from asset_lens.core.config_manager import ConfigManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.json"
            manager = ConfigManager(config_path)
            config = manager.get_data_source_config("not_exist")
            assert config is None

    def test_config_manager_get_monitor_config(self):
        """测试获取监控配置"""
        from asset_lens.core.config_manager import ConfigManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.json"
            manager = ConfigManager(config_path)
            config = manager.get_monitor_config()
            assert config is not None
            assert config.price_threshold == 5.0

    def test_config_manager_get_set(self):
        """测试 get/set 配置项"""
        from asset_lens.core.config_manager import ConfigManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.json"
            manager = ConfigManager(config_path)
            manager.set("test.key", "value")
            assert manager.get("test.key") == "value"
            assert manager.get("not.exist", "default") == "default"

    def test_config_manager_get_user_preferences(self):
        """测试获取用户偏好"""
        from asset_lens.core.config_manager import ConfigManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.json"
            manager = ConfigManager(config_path)
            prefs = manager.get_user_preferences()
            assert prefs is not None
            assert prefs.risk_tolerance == "moderate"

    def test_config_manager_get_alert_config(self):
        """测试获取提醒配置"""
        from asset_lens.core.config_manager import ConfigManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.json"
            manager = ConfigManager(config_path)
            config = manager.get_alert_config()
            assert config is not None
            assert config.enable_qq is True

    def test_config_manager_save(self):
        """测试保存配置"""
        from asset_lens.core.config_manager import ConfigManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.json"
            manager = ConfigManager(config_path)
            manager.set("test_key", "test_value")
            result = manager.save()
            assert result is True

    def test_config_manager_validate(self):
        """测试验证配置"""
        from asset_lens.core.config_manager import ConfigManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.json"
            manager = ConfigManager(config_path)
            assert manager.validate() is True

    def test_config_manager_validate_missing_key(self):
        """测试验证缺少配置项"""
        from asset_lens.core.config_manager import ConfigManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.json"
            manager = ConfigManager(config_path)
            manager.config = {"version": "1.0.0"}
            assert manager.validate() is False

    def test_config_manager_reload(self):
        """测试重新加载配置"""
        from asset_lens.core.config_manager import ConfigManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.json"
            manager = ConfigManager(config_path)
            manager.reload()
            assert "version" in manager.config

    def test_config_manager_get_all_config(self):
        """测试获取所有配置"""
        from asset_lens.core.config_manager import ConfigManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.json"
            manager = ConfigManager(config_path)
            all_config = manager.get_all_config()
            assert isinstance(all_config, dict)
            assert "version" in all_config


class TestCreateConfigManager:
    """创建配置管理器测试"""

    def test_create_config_manager(self):
        """测试创建配置管理器"""
        from asset_lens.core.config_manager import ConfigManager, create_config_manager

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.json"
            manager = create_config_manager(config_path)
            assert manager is not None
            assert isinstance(manager, ConfigManager)

    def test_create_config_manager_default_path(self):
        """测试使用默认路径创建配置管理器"""
        from asset_lens.core.config_manager import create_config_manager

        manager = create_config_manager()
        assert manager is not None
