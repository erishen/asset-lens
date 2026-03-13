"""
Tests for AI Components Module
"""

import pytest
from pathlib import Path
from datetime import datetime
from asset_lens.ai import PromptBuilder, ResultParser, AICacheManager
from asset_lens.ai.result_parser import ParsedResult


class TestPromptBuilder:
    """Prompt 构建器测试"""

    def test_build_portfolio_analysis_prompt(self):
        """测试投资组合分析 Prompt 构建"""
        data = {
            "total_value": 100000,
            "total_profit": 10000,
            "overall_return_rate": 10.0,
            "total_products": 5,
            "risk_distribution": {
                "低风险": {"percentage": 30},
                "中风险": {"percentage": 50},
                "高风险": {"percentage": 20},
            },
            "type_distribution": {
                "股票": {"percentage": 40},
                "基金": {"percentage": 60},
            },
            "low_returns": [],
        }
        
        prompt = PromptBuilder.build_portfolio_analysis_prompt(data)
        
        assert "投资组合概览" in prompt
        assert "100000" in prompt or "10.00万" in prompt
        assert "风险分布" in prompt
        assert "投资类型分布" in prompt

    def test_build_risk_assessment_prompt(self):
        """测试风险评估 Prompt 构建"""
        data = {
            "total_value": 100000,
            "risk_distribution": {
                "低风险": {"total_value": 30000},
                "中风险": {"total_value": 50000},
                "高风险": {"total_value": 20000},
            },
        }
        
        prompt = PromptBuilder.build_risk_assessment_prompt(data)
        
        assert "风险分布分析" in prompt

    def test_build_suggestion_prompt(self):
        """测试投资建议 Prompt 构建"""
        data = {
            "total_value": 100000,
            "total_profit": 10000,
            "overall_return_rate": 10.0,
        }
        
        prompt = PromptBuilder.build_suggestion_prompt(data, risk_preference="balanced")
        
        assert "投资组合数据" in prompt
        assert "balanced" in prompt
        assert "建议" in prompt

    def test_get_system_prompt(self):
        """测试获取系统 Prompt"""
        prompt = PromptBuilder.get_system_prompt()
        
        assert "投资顾问" in prompt
        assert len(prompt) > 0

    def test_format_money(self):
        """测试金额格式化"""
        assert PromptBuilder._format_money(10000) == "1.00万"
        assert PromptBuilder._format_money(5000) == "5000.00"
        assert PromptBuilder._format_money("invalid") == "0.00"


class TestResultParser:
    """结果解析器测试"""

    def test_parse_json_response(self):
        """测试 JSON 响应解析"""
        response = '''
        这里是一些文本
        ```json
        {
            "summary": "投资组合表现良好",
            "risk_assessment": "风险适中",
            "suggestions": ["建议1", "建议2"],
            "warnings": ["警告1"],
            "score": 75
        }
        ```
        '''
        
        result = ResultParser.parse_json_response(response)
        
        assert result.success is True
        assert result.summary == "投资组合表现良好"
        assert result.risk_assessment == "风险适中"
        assert len(result.suggestions) == 2
        assert len(result.warnings) == 1
        assert result.score == 75

    def test_parse_json_response_invalid(self):
        """测试无效 JSON 响应"""
        response = "这不是 JSON 格式的响应"
        
        result = ResultParser.parse_json_response(response)
        
        assert result.success is False

    def test_parse_markdown_response(self):
        """测试 Markdown 响应解析"""
        response = """
        ## 投资摘要
        投资组合表现良好。
        
        ## 风险评估
        风险适中。
        
        ## 投资建议
        - 建议1
        - 建议2
        
        ## 风险警告
        - 警告1
        
        ## 综合评分：75
        """
        
        result = ResultParser.parse_markdown_response(response)
        
        assert result.success is True
        assert len(result.suggestions) > 0
        assert result.score == 75

    def test_extract_score(self):
        """测试评分提取"""
        assert ResultParser._extract_score("评分：80") == 80
        assert ResultParser._extract_score("综合评分：90") == 90
        assert ResultParser._extract_score("score: 85") == 85
        assert ResultParser._extract_score("没有评分") == 60  # 默认值

    def test_to_dict(self):
        """测试转换为字典"""
        result = ParsedResult(
            success=True,
            summary="测试摘要",
            risk_assessment="测试风险",
            suggestions=["建议1"],
            warnings=["警告1"],
            score=80,
        )
        
        data = ResultParser.to_dict(result)
        
        assert data["success"] is True
        assert data["summary"] == "测试摘要"
        assert data["score"] == 80


class TestAICacheManager:
    """AI 缓存管理器测试"""

    def test_initialization(self, tmp_path):
        """测试初始化"""
        manager = AICacheManager(cache_dir=tmp_path, ttl=3600, enabled=True)
        
        assert manager.enabled is True
        assert manager.ttl == 3600
        assert manager.cache_dir == tmp_path

    def test_generate_key(self, tmp_path):
        """测试生成缓存键"""
        manager = AICacheManager(cache_dir=tmp_path)
        data = {
            "total_value": 100000,
            "total_profit": 10000,
            "total_products": 5,
        }
        
        key1 = manager.generate_key(data)
        key2 = manager.generate_key(data)
        
        assert key1 == key2  # 相同数据生成相同键
        assert key1.startswith("ai_")

    def test_set_and_get(self, tmp_path):
        """测试设置和获取缓存"""
        manager = AICacheManager(cache_dir=tmp_path, enabled=True)
        key = "test_key"
        data = {"summary": "测试结果", "score": 80}
        
        # 设置缓存
        result = manager.set(key, data)
        assert result is True
        
        # 获取缓存
        cached = manager.get(key)
        assert cached is not None
        assert cached["summary"] == "测试结果"

    def test_get_nonexistent(self, tmp_path):
        """测试获取不存在的缓存"""
        manager = AICacheManager(cache_dir=tmp_path)
        
        result = manager.get("nonexistent_key")
        
        assert result is None

    def test_delete(self, tmp_path):
        """测试删除缓存"""
        manager = AICacheManager(cache_dir=tmp_path, enabled=True)
        key = "test_key"
        data = {"test": "data"}
        
        manager.set(key, data)
        result = manager.delete(key)
        
        assert result is True
        assert manager.get(key) is None

    def test_clear(self, tmp_path):
        """测试清除所有缓存"""
        manager = AICacheManager(cache_dir=tmp_path, enabled=True)
        
        manager.set("key1", {"data": 1})
        manager.set("key2", {"data": 2})
        
        count = manager.clear()
        
        assert count >= 2
        assert manager.get("key1") is None
        assert manager.get("key2") is None

    def test_disabled_cache(self, tmp_path):
        """测试禁用缓存"""
        manager = AICacheManager(cache_dir=tmp_path, enabled=False)
        
        # 禁用时不应该缓存
        result = manager.set("key", {"data": "test"})
        assert result is False
        
        cached = manager.get("key")
        assert cached is None

    def test_get_stats(self, tmp_path):
        """测试获取统计信息"""
        manager = AICacheManager(cache_dir=tmp_path, enabled=True)
        
        manager.set("key1", {"data": 1})
        
        stats = manager.get_stats()
        
        assert stats["enabled"] is True
        assert stats["memory_cache_count"] == 1
        assert stats["file_cache_count"] == 1
