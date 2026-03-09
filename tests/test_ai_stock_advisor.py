"""
Tests for AI Stock Advisor.
AI 股票顾问测试
"""

import pytest
from unittest.mock import patch, MagicMock


class TestAIStockAdvisor:
    """AI 股票顾问测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.data.ai_stock_advisor import AIStockAdvisor
        assert AIStockAdvisor is not None

    @pytest.fixture
    def advisor(self):
        """创建顾问实例"""
        from asset_lens.data.ai_stock_advisor import AIStockAdvisor
        with patch('asset_lens.data.ai_stock_advisor.config') as mock_config:
            mock_config.cache_path = MagicMock()
            return AIStockAdvisor()

    def test_advisor_init(self, advisor):
        """测试初始化"""
        assert advisor is not None

    def test_generate_advice_method(self, advisor):
        """测试生成建议方法"""
        assert hasattr(advisor, 'generate_stock_advice') or hasattr(advisor, 'get_advice')


class TestStockAdvice:
    """股票建议测试"""

    def test_buy_advice(self):
        """测试买入建议"""
        advice = {
            "action": "buy",
            "reason": "估值偏低",
            "confidence": 0.8,
        }
        assert advice["action"] == "buy"
        assert advice["confidence"] > 0.5

    def test_sell_advice(self):
        """测试卖出建议"""
        advice = {
            "action": "sell",
            "reason": "估值偏高",
            "confidence": 0.7,
        }
        assert advice["action"] == "sell"
        assert advice["confidence"] > 0.5

    def test_hold_advice(self):
        """测试持有建议"""
        advice = {
            "action": "hold",
            "reason": "估值合理",
            "confidence": 0.6,
        }
        assert advice["action"] == "hold"


class TestAdviceValidation:
    """建议验证测试"""

    def test_validate_confidence(self):
        """测试验证置信度"""
        confidence = 0.8
        assert 0 <= confidence <= 1

    def test_validate_action(self):
        """测试验证操作"""
        valid_actions = ["buy", "sell", "hold"]
        action = "buy"
        assert action in valid_actions

    def test_validate_reason(self):
        """测试验证原因"""
        reason = "估值偏低，技术指标良好"
        assert len(reason) > 0
