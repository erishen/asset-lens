"""
Configuration management for asset-lens.
配置管理模块，支持 sample 和 real 数据模式切换
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """Configuration class for asset-lens."""

    def __init__(self):
        # 数据模式：sample 或 real
        self.data_mode: str = os.getenv("DATA_MODE", "sample")

        # API 密钥
        self.finnhub_api_key: str | None = os.getenv("FINNHUB_API_KEY")
        self.alphavantage_api_key: str | None = os.getenv("ALPHAVANTAGE_API_KEY")
        self.finnhub_api_key: str | None = os.getenv("FINNHUB_API_KEY")

        # 路径配置
        self.project_root = Path(__file__).parent.parent
        self.sample_data_path = Path(os.getenv("SAMPLE_DATA_PATH", "data/sample_data"))
        self.real_data_path = Path(os.getenv("REAL_DATA_PATH", "data/real"))
        self.output_path = Path(os.getenv("OUTPUT_PATH", "output"))
        self.cache_path = Path(os.getenv("CACHE_PATH", "cache"))

        # 货币汇率配置
        self.default_usd_rate: float = float(os.getenv("DEFAULT_USD_RATE", "7.1242"))
        self.default_hkd_rate: float = float(os.getenv("DEFAULT_HKD_RATE", "0.9157"))

        # 分析配置
        self.min_return_threshold: float = float(
            os.getenv("MIN_RETURN_THRESHOLD", "2.0")
        )

        # 定投计算配置
        self.workday_ratio: float = float(os.getenv("WORKDAY_RATIO", "0.7"))

        # 输出格式
        self.output_format: list = os.getenv("OUTPUT_FORMAT", "console,csv").split(",")

        # 报告语言
        self.report_language: str = os.getenv("REPORT_LANGUAGE", "zh")

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
                f"无效的数据模式: {self.data_mode}。必须是 'sample' 或 'real'",
                config_key="data_mode"
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
            if d.is_dir()
            and (d.name.startswith("money_csv_") or d.name.startswith("money_"))
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
