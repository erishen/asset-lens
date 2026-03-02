"""
Configuration management for asset-lens.
配置管理模块，支持 sample 和 real 数据模式切换
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv

load_dotenv()


class PlatformConfig:
    """平台配置类"""

    def __init__(self, platform_data: Dict[str, Any]):
        self.id: str = platform_data.get("id", "")
        self.name: str = platform_data.get("name", "")
        self.field: str = platform_data.get("field", "")
        self.type: str = platform_data.get("type", "")
        self.description: str = platform_data.get("description", "")


class RiskLevelConfig:
    """风险等级配置类"""

    def __init__(self, risk_data: Dict[str, Any]):
        self.name: str = risk_data.get("name", "")
        self.color: str = risk_data.get("color", "")
        self.max_allocation: float = risk_data.get("max_allocation", 0.0)
        self.description: str = risk_data.get("description", "")


class InvestmentTypeConfig:
    """投资类型配置类"""

    def __init__(self, type_data: Dict[str, Any]):
        self.id: str = type_data.get("id", "")
        self.name: str = type_data.get("name", "")
        self.risk_level: str = type_data.get("risk_level", "unknown")
        self.description: str = type_data.get("description", "")
        self.examples: List[str] = type_data.get("examples", [])


class Config:
    """Configuration class for asset-lens."""

    def __init__(self):
        self.data_mode: str = os.getenv("DATA_MODE", "sample")

        self.finnhub_api_key: str | None = os.getenv("FINNHUB_API_KEY")
        self.alphavantage_api_key: str | None = os.getenv("ALPHAVANTAGE_API_KEY")

        self.project_root = Path(__file__).parent.parent
        self.sample_data_path = Path(os.getenv("SAMPLE_DATA_PATH", "data/sample_data"))
        self.real_data_path = Path(os.getenv("REAL_DATA_PATH", "data/real"))
        self.output_path = Path(os.getenv("OUTPUT_PATH", "output"))
        self.cache_path = Path(os.getenv("CACHE_PATH", "cache"))

        self.default_usd_rate: float = float(os.getenv("DEFAULT_USD_RATE", "7.1242"))
        self.default_hkd_rate: float = float(os.getenv("DEFAULT_HKD_RATE", "0.9157"))

        self.min_return_threshold: float = float(os.getenv("MIN_RETURN_THRESHOLD", "2.0"))

        self.workday_ratio: float = float(os.getenv("WORKDAY_RATIO", "0.7"))

        self.output_format: list = os.getenv("OUTPUT_FORMAT", "console,csv").split(",")

        self.report_language: str = os.getenv("REPORT_LANGUAGE", "zh")

        self._platforms: List[PlatformConfig] | None = None
        self._platform_types: Dict[str, str] | None = None
        self._investment_types: List[InvestmentTypeConfig] | None = None
        self._risk_levels: Dict[str, RiskLevelConfig] | None = None

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
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._platforms = [PlatformConfig(p) for p in data.get("platforms", [])]
            self._platform_types = data.get("platform_types", {})
        except (json.JSONDecodeError, IOError):
            self._platforms = []
            self._platform_types = {}

    @property
    def platforms(self) -> List[PlatformConfig]:
        """获取平台配置列表"""
        self._load_platform_config()
        return self._platforms or []

    @property
    def platform_types(self) -> Dict[str, str]:
        """获取平台类型映射"""
        self._load_platform_config()
        return self._platform_types or {}

    def get_platform_mapping(self) -> Dict[str, str]:
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
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._investment_types = [InvestmentTypeConfig(t) for t in data.get("investment_types", [])]
            self._risk_levels = {k: RiskLevelConfig(v) for k, v in data.get("risk_levels", {}).items()}
        except (json.JSONDecodeError, IOError):
            self._investment_types = []
            self._risk_levels = {}

    @property
    def investment_types(self) -> List[InvestmentTypeConfig]:
        """获取投资类型配置列表"""
        self._load_investment_type_config()
        return self._investment_types or []

    @property
    def risk_levels(self) -> Dict[str, RiskLevelConfig]:
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
        """
        if not self.is_real_mode:
            return self.data_path

        data_dir = self.project_root / "data" / "real"
        if not data_dir.exists():
            return None

        # 查找所有 money_csv_* 或 money_* 目录
        dirs = [
            d
            for d in data_dir.iterdir()
            if d.is_dir() and (d.name.startswith("money_csv_") or d.name.startswith("money_"))
        ]

        if not dirs:
            return None

        # 按名称排序，返回最新的
        dirs.sort(key=lambda x: x.name, reverse=True)
        return dirs[0]

    def __str__(self) -> str:
        return (
            f"Config(data_mode={self.data_mode}, "
            f"data_path={self.data_path}, "
            f"output_path={self.output_path})"
        )


# 全局配置实例
config = Config()
