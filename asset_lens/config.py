"""
Configuration management for asset-lens.
配置管理模块，支持 sample 和 real 数据模式切换

使用 Pydantic BaseSettings 实现：
- 自动从环境变量加载
- 类型验证
- 默认值支持
- .env 文件支持
"""

import json
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    """应用配置 - 使用 Pydantic BaseSettings"""

    data_mode: str = Field(default="sample", description="数据模式: sample 或 real")

    conda_python: str | None = Field(default=None, description="Conda Python 路径")

    finnhub_api_key: str | None = Field(default=None, description="Finnhub API 密钥")
    alphavantage_api_key: str | None = Field(default=None, description="Alpha Vantage API 密钥")
    tushare_token: str | None = Field(default=None, description="Tushare Token")
    fred_api_key: str | None = Field(default=None, description="FRED API 密钥")

    deepseek_api_key: str | None = Field(default=None, description="DeepSeek API 密钥")
    ai_model: str = Field(default="deepseek-chat", description="AI 模型名称")
    ai_cache_ttl: int = Field(default=3600, description="AI 缓存 TTL（秒）")

    joinquant_username: str | None = Field(default=None, description="JoinQuant 用户名")
    joinquant_password: str | None = Field(default=None, description="JoinQuant 密码")

    sample_data_path: str = Field(default="data/sample_data", description="示例数据路径")
    real_data_path: str = Field(default="../ts-demo/data", description="真实数据路径")
    output_path: str = Field(default="output", description="输出路径")
    cache_path: str = Field(default="cache", description="缓存路径")
    config_path: str = Field(default="config", description="配置路径")

    default_usd_rate: float = Field(default=7.1242, description="默认美元汇率")
    default_hkd_rate: float = Field(default=0.9157, description="默认港元汇率")

    min_return_threshold: float = Field(default=2.0, description="最小收益阈值")
    workday_ratio: float = Field(default=0.7, description="工作日比例")

    output_format: str = Field(default="console,csv", description="输出格式")
    report_language: str = Field(default="zh", description="报告语言")

    @field_validator("data_mode")
    @classmethod
    def validate_data_mode(cls, v: str) -> str:
        if v not in ("sample", "real"):
            raise ValueError(f"data_mode 必须是 'sample' 或 'real'，当前值: {v}")
        return v

    @field_validator("finnhub_api_key")
    @classmethod
    def validate_finnhub_api_key(cls, v: str | None) -> str | None:
        if v and len(v) < 10:
            raise ValueError("FINNHUB_API_KEY 格式不正确，密钥长度应该至少 10 个字符")
        return v

    @field_validator("default_usd_rate")
    @classmethod
    def validate_usd_rate(cls, v: float) -> float:
        if not (5.0 < v < 10.0):
            raise ValueError(f"默认美元汇率应该在 5-10 之间，当前值: {v}")
        return v

    @field_validator("default_hkd_rate")
    @classmethod
    def validate_hkd_rate(cls, v: float) -> float:
        if not (0.7 < v < 1.2):
            raise ValueError(f"默认港元汇率应该在 0.7-1.2 之间，当前值: {v}")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


settings = Settings()


class PlatformConfig:
    """平台配置类"""

    def __init__(self, platform_data: dict[str, Any]):
        self.id: str = platform_data.get("id", "")
        self.name: str = platform_data.get("name", "")
        self.field: str = platform_data.get("field", "")
        self.type: str = platform_data.get("type", "")
        self.description: str = platform_data.get("description", "")


class RiskLevelConfig:
    """风险等级配置类"""

    def __init__(self, risk_data: dict[str, Any]):
        self.name: str = risk_data.get("name", "")
        self.color: str = risk_data.get("color", "")
        self.max_allocation: float = risk_data.get("max_allocation", 0.0)
        self.description: str = risk_data.get("description", "")


class InvestmentTypeConfig:
    """投资类型配置类"""

    def __init__(self, type_data: dict[str, Any]):
        self.id: str = type_data.get("id", "")
        self.name: str = type_data.get("name", "")
        self.risk_level: str = type_data.get("risk_level", "unknown")
        self.description: str = type_data.get("description", "")
        self.examples: list[str] = type_data.get("examples", [])


class Config:
    """Configuration class for asset-lens."""

    def __init__(self):
        self._settings = settings

        self.data_mode: str = self._settings.data_mode

        self.finnhub_api_key: str | None = self._settings.finnhub_api_key
        self.alphavantage_api_key: str | None = self._settings.alphavantage_api_key
        self.tushare_token: str | None = self._settings.tushare_token
        self.fred_api_key: str | None = self._settings.fred_api_key

        self.joinquant_username: str | None = self._settings.joinquant_username
        self.joinquant_password: str | None = self._settings.joinquant_password

        self.project_root = Path(__file__).parent.parent
        self.sample_data_path = self.project_root / self._settings.sample_data_path
        self.real_data_path = self._resolve_path(self._settings.real_data_path)
        self.output_path = self.project_root / self._settings.output_path
        self.cache_path = self.project_root / self._settings.cache_path
        self.config_path = self.project_root / self._settings.config_path

        self.default_usd_rate: float = self._settings.default_usd_rate
        self.default_hkd_rate: float = self._settings.default_hkd_rate

        self.min_return_threshold: float = self._settings.min_return_threshold

        self.workday_ratio: float = self._settings.workday_ratio

        output_format_str: str = getattr(self._settings, "output_format", "console,csv")
        self.output_format: list = output_format_str.split(",")  # pylint: disable=no-member

        self.report_language: str = self._settings.report_language

        self._platforms: list[PlatformConfig] | None = None
        self._platform_types: dict[str, str] | None = None
        self._investment_types: list[InvestmentTypeConfig] | None = None
        self._risk_levels: dict[str, RiskLevelConfig] | None = None

    def _resolve_path(self, path_str: str) -> Path:
        """解析路径，支持相对路径和绝对路径，自动选择最新数据目录"""
        path = Path(path_str)
        if path.is_absolute():
            resolved = path
        else:
            resolved = self.project_root / path

        if resolved.exists() and resolved.is_dir():
            money_dirs = sorted(
                [d for d in resolved.iterdir() if d.is_dir() and d.name.startswith("money_csv_")],
                key=lambda x: x.name,
                reverse=True,
            )
            if money_dirs:
                return money_dirs[0]

        return resolved

    def _load_platform_config(self) -> None:
        """加载平台配置文件"""
        if self._platforms is not None:
            return

        config_file = self.project_root / "config" / "platforms.json"
        if not config_file.exists():
            self._platforms = []
            self._platform_types = {}
            return

        try:
            with open(config_file, encoding="utf-8") as f:
                data = json.load(f)

            self._platforms = [PlatformConfig(p) for p in data.get("platforms", [])]
            self._platform_types = data.get("platform_types", {})
        except (OSError, json.JSONDecodeError):
            self._platforms = []
            self._platform_types = {}

    @property
    def platforms(self) -> list[PlatformConfig]:
        """获取平台配置列表"""
        self._load_platform_config()
        return self._platforms or []

    @property
    def platform_types(self) -> dict[str, str]:
        """获取平台类型映射"""
        self._load_platform_config()
        return self._platform_types or {}

    def get_platform_mapping(self) -> dict[str, str]:
        """获取平台名称到字段的映射"""
        return {p.name: p.field for p in self.platforms}

    def get_platform_by_field(self, field: str) -> PlatformConfig | None:
        """根据字段名获取平台配置"""
        for platform in self.platforms:
            if platform.field == field:
                return platform
        return None

    def get_platform_by_name(self, name: str) -> PlatformConfig | None:
        """根据名称获取平台配置"""
        for platform in self.platforms:
            if platform.name == name:
                return platform
        return None

    def _load_investment_type_config(self) -> None:
        """加载投资类型配置文件"""
        if self._investment_types is not None:
            return

        config_file = self.project_root / "config" / "investment_types.json"
        if not config_file.exists():
            self._investment_types = []
            self._risk_levels = {}
            return

        try:
            with open(config_file, encoding="utf-8") as f:
                data = json.load(f)

            self._investment_types = [InvestmentTypeConfig(t) for t in data.get("investment_types", [])]
            self._risk_levels = {k: RiskLevelConfig(v) for k, v in data.get("risk_levels", {}).items()}
        except (OSError, json.JSONDecodeError):
            self._investment_types = []
            self._risk_levels = {}

    @property
    def investment_types(self) -> list[InvestmentTypeConfig]:
        """获取投资类型配置列表"""
        self._load_investment_type_config()
        return self._investment_types or []

    @property
    def risk_levels(self) -> dict[str, RiskLevelConfig]:
        """获取风险等级配置映射"""
        self._load_investment_type_config()
        return self._risk_levels or {}

    def get_investment_type_by_id(self, type_id: str) -> InvestmentTypeConfig | None:
        """根据ID获取投资类型配置"""
        for inv_type in self.investment_types:
            if inv_type.id == type_id:
                return inv_type
        return None

    def get_investment_type_by_name(self, name: str) -> InvestmentTypeConfig | None:
        """根据名称获取投资类型配置"""
        for inv_type in self.investment_types:
            if inv_type.name == name:
                return inv_type
        return None

    def get_risk_level(self, risk_id: str) -> RiskLevelConfig | None:
        """根据ID获取风险等级配置"""
        return self._risk_levels.get(risk_id) if self._risk_levels else None

    @property
    def data_path(self) -> Path:
        """
        根据数据模式返回数据路径
        Returns the data path based on the data mode
        """
        if self.data_mode == "sample":
            return self.project_root / self.sample_data_path
        elif self.data_mode == "real":
            return self.project_root / self.real_data_path
        else:
            from .core.exceptions import ConfigurationError

            raise ConfigurationError(
                f"无效的数据模式: {self.data_mode}。必须是 'sample' 或 'real'", config_key="data_mode"
            )

    @property
    def is_sample_mode(self) -> bool:
        """是否使用示例数据模式"""
        return self.data_mode == "sample"

    @property
    def is_real_mode(self) -> bool:
        """是否使用真实数据模式"""
        return self.data_mode == "real"

    def set_data_mode(self, mode: str) -> None:
        """
        设置数据模式

        Args:
            mode: 数据模式，'sample' 或 'real'
        """
        from .core.exceptions import ConfigurationError

        if mode not in ("sample", "real"):
            raise ConfigurationError(f"无效的数据模式: {mode}。必须是 'sample' 或 'real'", config_key="data_mode")
        self.data_mode = mode

    def ensure_directories(self) -> None:
        """确保所有必要的目录存在"""
        directories = [
            self.project_root / "data" / "real",
            self.project_root / "data" / "sample_data",
            self.project_root / "output",
            self.project_root / "cache",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def get_latest_data_dir(self) -> Path | None:
        """
        获取最新的数据目录（用于 real 模式）
        获取格式：data/real/money_csv_YYYYMMDD 或 data/real/money_YYYYMMDD
        或 ../ts-demo/data/money_csv_YYYYMMDD
        """
        if not self.is_real_mode:
            return self.data_path

        # 首先检查 real_data_path 是否已经是一个 money_csv_* 目录
        if self.real_data_path and (
            self.real_data_path.name.startswith("money_csv_") or
            self.real_data_path.name.startswith("money_")
        ):
            if self.real_data_path.exists():
                return self.real_data_path

        # 其次尝试在 real_data_path 中查找 money_csv_* 目录
        if self.real_data_path and self.real_data_path.exists() and self.real_data_path.is_dir():
            dirs = [
                d
                for d in self.real_data_path.iterdir()
                if d.is_dir() and (d.name.startswith("money_csv_") or d.name.startswith("money_"))
            ]

            if dirs:
                # 按名称排序，返回最新的
                dirs.sort(key=lambda x: x.name, reverse=True)
                return dirs[0]

        # 最后尝试 data/real 目录（向后兼容）
        data_dir = self.project_root / "data" / "real"
        if data_dir.exists():
            dirs = [
                d
                for d in data_dir.iterdir()
                if d.is_dir() and (d.name.startswith("money_csv_") or d.name.startswith("money_"))
            ]

            if dirs:
                dirs.sort(key=lambda x: x.name, reverse=True)
                return dirs[0]

        return None

    def __str__(self) -> str:
        return f"Config(data_mode={self.data_mode}, data_path={self.data_path}, output_path={self.output_path})"


# 全局配置实例
config = Config()
