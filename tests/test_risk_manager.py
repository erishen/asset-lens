"""
Tests for risk_manager.py
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from asset_lens.data.risk_manager import (
    PositionAdvice,
    RiskConfig,
    RiskManager,
    RiskWarning,
)


class TestRiskConfig:
    """RiskConfig 测试"""

    def test_default_values(self):
        """测试默认值"""
        config = RiskConfig()
        assert config.max_single_position == 0.2
        assert config.max_total_position == 0.8
        assert config.stop_loss_default == -0.08
        assert config.take_profit_default == 0.15
        assert config.risk_tolerance == "medium"

    def test_custom_values(self):
        """测试自定义值"""
        config = RiskConfig(
            max_single_position=0.3,
            max_total_position=0.9,
            stop_loss_default=-0.05,
            take_profit_default=0.2,
            risk_tolerance="high",
        )
        assert config.max_single_position == 0.3
        assert config.max_total_position == 0.9
        assert config.stop_loss_default == -0.05
        assert config.take_profit_default == 0.2
        assert config.risk_tolerance == "high"


class TestPositionAdvice:
    """PositionAdvice 测试"""

    def test_default_values(self):
        """测试默认值"""
        advice = PositionAdvice(
            code="sh600519",
            name="贵州茅台",
            current_position=0.1,
            suggested_position=0.15,
            action="hold",
            reason="仓位合理",
        )
        assert advice.code == "sh600519"
        assert advice.name == "贵州茅台"
        assert advice.current_position == 0.1
        assert advice.suggested_position == 0.15
        assert advice.action == "hold"
        assert advice.reason == "仓位合理"


class TestRiskWarning:
    """RiskWarning 测试"""

    def test_default_values(self):
        """测试默认值"""
        warning = RiskWarning(
            warning_type="concentration",
            level="high",
            message="持仓过于集中",
        )
        assert warning.warning_type == "concentration"
        assert warning.level == "high"
        assert warning.message == "持仓过于集中"
        assert warning.code is None
        assert warning.timestamp == ""
        assert warning.details == {}

    def test_custom_values(self):
        """测试自定义值"""
        warning = RiskWarning(
            warning_type="stop_loss",
            level="critical",
            message="触及止损线",
            code="sh600519",
            timestamp="2024-01-01 12:00:00",
            details={"profit_rate": -0.08},
        )
        assert warning.warning_type == "stop_loss"
        assert warning.level == "critical"
        assert warning.message == "触及止损线"
        assert warning.code == "sh600519"
        assert warning.timestamp == "2024-01-01 12:00:00"
        assert warning.details == {"profit_rate": -0.08}


class TestRiskManager:
    """RiskManager 测试"""

    @pytest.fixture
    def temp_cache_path(self):
        """临时缓存路径"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def manager(self, temp_cache_path):
        """创建测试实例"""
        with patch('asset_lens.data.risk_manager.config') as mock_config:
            mock_config.cache_path = temp_cache_path
            manager = RiskManager()
            yield manager

    def test_init(self, manager):
        """测试初始化"""
        assert manager.config is not None
        assert manager.config.risk_tolerance == "medium"

    def test_set_risk_tolerance(self, manager):
        """测试设置风险偏好"""
        manager.set_risk_tolerance("high")
        assert manager.config.risk_tolerance == "high"

        manager.set_risk_tolerance("low")
        assert manager.config.risk_tolerance == "low"

    def test_load_warnings_no_file(self, manager):
        """测试加载警告 - 文件不存在"""
        manager._load_warnings()
        assert manager.warnings == []

    def test_load_warnings_with_file(self, manager):
        """测试加载警告 - 有文件"""
        warnings_data = {
            "warnings": [
                {"warning_type": "test", "message": "测试警告", "level": "medium"}
            ]
        }
        with open(manager.warnings_file, "w", encoding="utf-8") as f:
            json.dump(warnings_data, f)

        manager._load_warnings()
        assert len(manager.warnings) == 1

    def test_save_warnings(self, manager):
        """测试保存警告"""
        manager.warnings = [
            RiskWarning(warning_type="test", level="medium", message="测试警告")
        ]
        manager._save_warnings()

        assert manager.warnings_file.exists()
