"""
Unified Configuration System.
统一配置系统 - 支持 YAML/JSON 配置文件
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


@dataclass
class DataSourceConfig:
    """数据源配置"""
    name: str
    priority: int = 1
    enabled: bool = True
    api_key: str | None = None
    api_url: str | None = None
    timeout: int = 30
    retry_times: int = 3


@dataclass
class MonitorConfig:
    """监控配置"""
    price_threshold: float = 5.0
    volatility_threshold: float = 20.0
    max_drawdown_threshold: float = 10.0
    concentration_threshold: float = 30.0
    check_interval: int = 300
    enable_alerts: bool = True


@dataclass
class UserPreferences:
    """用户偏好设置"""
    risk_tolerance: str = "moderate"
    investment_goal: str = "balanced"
    preferred_sectors: list[str] = field(default_factory=list)
    excluded_sectors: list[str] = field(default_factory=list)
    max_position_size: float = 10.0
    rebalance_frequency: str = "monthly"


@dataclass
class AlertConfig:
    """提醒配置"""
    enable_email: bool = False
    enable_qq: bool = True
    enable_wechat: bool = False
    daily_report_time: str = "15:00"
    weekly_report_day: int = 4
    weekly_report_time: str = "16:00"


class ConfigManager:
    """配置管理器"""

    DEFAULT_CONFIG = {
        "version": "1.0.0",
        "environment": "development",
        "data_sources": {
            "eastmoney": {
                "name": "东方财富",
                "priority": 1,
                "enabled": True,
                "timeout": 30,
                "retry_times": 3
            },
            "sina": {
                "name": "新浪",
                "priority": 2,
                "enabled": True,
                "timeout": 30,
                "retry_times": 3
            },
            "baostock": {
                "name": "Baostock",
                "priority": 3,
                "enabled": True,
                "timeout": 30,
                "retry_times": 2
            }
        },
        "monitor": {
            "price_threshold": 5.0,
            "volatility_threshold": 20.0,
            "max_drawdown_threshold": 10.0,
            "concentration_threshold": 30.0,
            "check_interval": 300,
            "enable_alerts": True
        },
        "user_preferences": {
            "risk_tolerance": "moderate",
            "investment_goal": "balanced",
            "preferred_sectors": [],
            "excluded_sectors": [],
            "max_position_size": 10.0,
            "rebalance_frequency": "monthly"
        },
        "alerts": {
            "enable_email": False,
            "enable_qq": True,
            "enable_wechat": False,
            "daily_report_time": "15:00",
            "weekly_report_day": 4,
            "weekly_report_time": "16:00"
        },
        "cache": {
            "ttl": 3600,
            "max_size": 100,
            "enabled": True
        }
    }

    def __init__(self, config_path: Path | None = None):
        self.config_path = config_path or Path("config/asset_lens.yaml")
        self.config: dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
        """加载配置文件"""
        if self.config_path.exists():
            try:
                with open(self.config_path, encoding='utf-8') as f:
                    if self.config_path.suffix in ['.yaml', '.yml']:
                        if YAML_AVAILABLE:
                            self.config = yaml.safe_load(f)
                        else:
                            logger.warning("YAML not available, using default config")
                            self.config = self.DEFAULT_CONFIG.copy()
                    else:
                        self.config = json.load(f)
                logger.info(f"配置文件加载成功: {self.config_path}")
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
                self.config = self.DEFAULT_CONFIG.copy()
        else:
            logger.info("配置文件不存在，使用默认配置")
            self.config = self.DEFAULT_CONFIG.copy()
            self._create_default_config()

    def _create_default_config(self):
        """创建默认配置文件"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                if self.config_path.suffix in ['.yaml', '.yml']:
                    if YAML_AVAILABLE:
                        yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False)
                    else:
                        json.dump(self.config, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info(f"默认配置文件已创建: {self.config_path}")
        except Exception as e:
            logger.error(f"创建默认配置文件失败: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """设置配置项"""
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def get_data_source_config(self, name: str) -> DataSourceConfig | None:
        """获取数据源配置"""
        data_sources = self.get('data_sources', {})
        if name in data_sources:
            source_data = data_sources[name]
            return DataSourceConfig(
                name=source_data.get('name', name),
                priority=source_data.get('priority', 1),
                enabled=source_data.get('enabled', True),
                api_key=source_data.get('api_key'),
                api_url=source_data.get('api_url'),
                timeout=source_data.get('timeout', 30),
                retry_times=source_data.get('retry_times', 3)
            )
        return None

    def get_monitor_config(self) -> MonitorConfig:
        """获取监控配置"""
        monitor_data = self.get('monitor', {})
        return MonitorConfig(
            price_threshold=monitor_data.get('price_threshold', 5.0),
            volatility_threshold=monitor_data.get('volatility_threshold', 20.0),
            max_drawdown_threshold=monitor_data.get('max_drawdown_threshold', 10.0),
            concentration_threshold=monitor_data.get('concentration_threshold', 30.0),
            check_interval=monitor_data.get('check_interval', 300),
            enable_alerts=monitor_data.get('enable_alerts', True)
        )

    def get_user_preferences(self) -> UserPreferences:
        """获取用户偏好"""
        prefs_data = self.get('user_preferences', {})
        return UserPreferences(
            risk_tolerance=prefs_data.get('risk_tolerance', 'moderate'),
            investment_goal=prefs_data.get('investment_goal', 'balanced'),
            preferred_sectors=prefs_data.get('preferred_sectors', []),
            excluded_sectors=prefs_data.get('excluded_sectors', []),
            max_position_size=prefs_data.get('max_position_size', 10.0),
            rebalance_frequency=prefs_data.get('rebalance_frequency', 'monthly')
        )

    def get_alert_config(self) -> AlertConfig:
        """获取提醒配置"""
        alert_data = self.get('alerts', {})
        return AlertConfig(
            enable_email=alert_data.get('enable_email', False),
            enable_qq=alert_data.get('enable_qq', True),
            enable_wechat=alert_data.get('enable_wechat', False),
            daily_report_time=alert_data.get('daily_report_time', '15:00'),
            weekly_report_day=alert_data.get('weekly_report_day', 4),
            weekly_report_time=alert_data.get('weekly_report_time', '16:00')
        )

    def save(self):
        """保存配置"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                if self.config_path.suffix in ['.yaml', '.yml']:
                    if YAML_AVAILABLE:
                        yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False)
                    else:
                        json.dump(self.config, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info(f"配置文件已保存: {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False

    def reload(self):
        """重新加载配置"""
        self._load_config()

    def validate(self) -> bool:
        """验证配置"""
        required_keys = ['version', 'environment', 'data_sources', 'monitor']
        for key in required_keys:
            if key not in self.config:
                logger.error(f"配置缺少必需项: {key}")
                return False
        return True

    def get_all_config(self) -> dict[str, Any]:
        """获取所有配置"""
        return self.config.copy()


def create_config_manager(config_path: Path | None = None) -> ConfigManager:
    """创建配置管理器实例"""
    return ConfigManager(config_path)
