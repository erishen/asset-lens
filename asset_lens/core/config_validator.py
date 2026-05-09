"""
Configuration validator for asset-lens.
配置验证器
"""

from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar


@dataclass
class ValidationResult:
    """验证结果"""

    is_valid: bool
    errors: list[str]
    warnings: list[str]

    def __bool__(self) -> bool:
        return self.is_valid


class ConfigValidator:
    """配置验证器"""

    REQUIRED_ENV_VARS: ClassVar[list[str]] = []
    OPTIONAL_ENV_VARS: ClassVar[list[str]] = []
    DEFAULT_VALUES: ClassVar[dict[str, str]] = {
        "data_mode": "sample",
        "output_path": "output",
        "default_usd_rate": "7.25",
        "default_hkd_rate": "1.0",
    }

    @classmethod
    def validate_env_file(cls, env_path: Path | None = None) -> ValidationResult:
        """验证 .env 文件"""
        if env_path is None:
            env_path = Path(".env")

        if not env_path.exists():
            return ValidationResult(False, [], [f".env 文件不存在: {env_path}"])

        errors: list[str] = []
        warnings: list[str] = []

        try:
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("#"):
                        continue

                    if "=" not in line:
                        continue

                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()

                    if key in cls.REQUIRED_ENV_VARS and not value:
                        errors.append(f"缺少必需的环境变量: {key}")

                    if key in cls.OPTIONAL_ENV_VARS and not value:
                        warnings.append(f"可选环境变量 {key} 未设置")

                    if key.lower() == "data_mode" and value not in ["sample", "real"]:
                        errors.append(f"无效的 data_mode: {value}")

                    if key == "output_path" and not Path(value).exists():
                        warnings.append(f"输出路径不存在: {value}")

            return ValidationResult(
                len(errors) == 0,
                errors,
                warnings,
            )

        except Exception as e:
            return ValidationResult(
                False,
                [f"读取 .env 文件失败: {e}"],
                [],
            )

    @classmethod
    def validate_api_key(cls, api_name: str, api_key: str) -> ValidationResult:
        """验证 API Key"""
        if not api_key:
            return ValidationResult(False, [], [f"{api_name} 未设置"])

        if api_key == "demo":
            return ValidationResult(False, [], [f"{api_name} 使用的是演示/示例 Key"])

        if len(api_key) < 10:
            return ValidationResult(False, [f"{api_name} 长度不能小于10"], [])

        return ValidationResult(True, [], [])

    @classmethod
    def validate_data_path(cls, data_path: Path | None = None) -> ValidationResult:
        """验证数据路径"""
        if data_path is None:
            data_path = Path("data")

        if not data_path.exists():
            return ValidationResult(False, [f"数据路径不存在: {data_path}"], [])

        sample_data = data_path / "sample_data"
        if not sample_data.exists():
            return ValidationResult(False, [f"示例数据路径不存在: {sample_data}"], [])

        return ValidationResult(True, [], [])

    @classmethod
    def validate_cache_path(cls, cache_path: Path | None = None) -> ValidationResult:
        """验证缓存路径"""
        if cache_path is None:
            cache_path = Path("cache")

        if not cache_path.exists():
            try:
                cache_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return ValidationResult(False, [f"无法创建缓存路径: {e}"], [])

        return ValidationResult(True, [], [])

    @classmethod
    def validate_all(cls, project_root: Path | None = None) -> dict[str, ValidationResult]:
        """验证所有配置"""
        if project_root is None:
            project_root = Path.cwd()

        results: dict[str, ValidationResult] = {}

        env_result = cls.validate_env_file(project_root / ".env")
        results["env_file"] = env_result

        data_result = cls.validate_data_path(project_root / "data")
        results["data_path"] = data_result

        cache_result = cls.validate_cache_path(project_root / "cache")
        results["cache_path"] = cache_result

        return results

    @classmethod
    def get_validation_summary(cls) -> str:
        """获取验证摘要"""
        results = cls.validate_all()

        lines = ["配置验证结果:", ""]
        all_valid = True

        for name, result in results.items():
            status = "✅" if result.is_valid else "❌"
            lines.append(f"  {status} {name}: {'有效' if result.is_valid else '无效'}")

            if result.errors:
                for error in result.errors:
                    lines.append(f"    - 错误: {error}")
                all_valid = False

            if result.warnings:
                for warning in result.warnings:
                    lines.append(f"    - 警告: {warning}")

        lines.append("")
        lines.append(f"总体状态: {'✅ 配置有效' if all_valid else '❌ 配置存在问题'}")

        return "\n".join(lines)


def validate_config(config_path: Path | None = None) -> ValidationResult:
    """验证配置文件（便捷函数）"""
    return ConfigValidator.validate_env_file(config_path)
