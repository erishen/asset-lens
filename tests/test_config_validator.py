"""
Tests for config validator.
"""

import tempfile
from pathlib import Path

from asset_lens.core.config_validator import ConfigValidator, ValidationResult, validate_config


class TestValidationResult:
    """Test ValidationResult dataclass"""

    def test_valid_result(self):
        result = ValidationResult(True, [], [])
        assert result.is_valid is True
        assert bool(result) is True

    def test_invalid_result(self):
        result = ValidationResult(False, ["error"], [])
        assert result.is_valid is False
        assert bool(result) is False

    def test_result_with_warnings(self):
        result = ValidationResult(True, [], ["warning"])
        assert result.is_valid is True
        assert len(result.warnings) == 1


class TestConfigValidator:
    """Test ConfigValidator class"""

    def test_validate_env_file_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = ConfigValidator.validate_env_file(Path(temp_dir) / ".env")
            assert result.is_valid is False
            assert len(result.warnings) > 0

    def test_validate_env_file_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            with open(env_path, "w") as f:
                f.write("DATA_MODE=real\n")

            result = ConfigValidator.validate_env_file(env_path)
            assert result.is_valid is True

    def test_validate_env_file_invalid_data_mode(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            with open(env_path, "w") as f:
                f.write("DATA_MODE=invalid\n")

            result = ConfigValidator.validate_env_file(env_path)
            assert result.is_valid is False
            assert len(result.errors) > 0

    def test_validate_api_key_empty(self):
        result = ConfigValidator.validate_api_key("FINNHUB_API_KEY", "")
        assert result.is_valid is False
        assert len(result.warnings) > 0

    def test_validate_api_key_demo(self):
        result = ConfigValidator.validate_api_key("FINNHUB_API_KEY", "demo")
        assert result.is_valid is False
        assert "演示" in result.warnings[0] or "示例" in result.warnings[0]

    def test_validate_api_key_valid(self):
        result = ConfigValidator.validate_api_key("FINNHUB_API_KEY", "abcdefghijklmnopqrstuvwxyz123456")
        assert result.is_valid is True

    def test_validate_data_path_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = ConfigValidator.validate_data_path(Path(temp_dir) / "nonexistent")
            assert result.is_valid is False

    def test_validate_data_path_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            data_path = Path(temp_dir) / "data"
            data_path.mkdir()
            (data_path / "sample_data").mkdir()

            result = ConfigValidator.validate_data_path(data_path)
            assert result.is_valid is True

    def test_validate_cache_path_creates_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "cache"
            result = ConfigValidator.validate_cache_path(cache_path)
            assert result.is_valid is True
            assert cache_path.exists()

    def test_validate_all(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            (project_root / "data" / "sample_data").mkdir(parents=True)
            (project_root / "cache").mkdir()

            env_path = project_root / ".env"
            with open(env_path, "w") as f:
                f.write("DATA_MODE=sample\n")

            results = ConfigValidator.validate_all(project_root)

            assert "env_file" in results
            assert "data_path" in results
            assert "cache_path" in results

    def test_get_validation_summary(self):
        summary = ConfigValidator.get_validation_summary()
        assert "配置验证结果" in summary

    def test_validate_config(self):
        result = validate_config()
        assert isinstance(result, ValidationResult)
