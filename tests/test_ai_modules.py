"""Smoke tests for asset_lens.ai module."""

from asset_lens.ai.prompt_builder import PromptBuilder
from asset_lens.ai.result_parser import ParsedResult, ResultParser


class TestPromptBuilder:
    def test_build_portfolio_analysis_prompt_returns_string(self):
        data = {
            "total_value": 100000,
            "total_profit": 5000,
            "overall_return_rate": 5.0,
            "total_products": 10,
            "risk_distribution": {"低": {"percentage": 30}, "中": {"percentage": 50}},
            "type_distribution": {"基金": {"percentage": 60}, "股票": {"percentage": 40}},
            "low_returns": [],
        }
        result = PromptBuilder.build_portfolio_analysis_prompt(data)
        assert isinstance(result, str)
        assert "投资组合概览" in result
        assert "10.00万" in result

    def test_build_portfolio_analysis_prompt_with_low_returns(self):
        data = {
            "total_value": 50000,
            "total_profit": -1000,
            "overall_return_rate": -2.0,
            "total_products": 5,
            "risk_distribution": {},
            "type_distribution": {},
            "low_returns": [{"name": "基金A", "annual_return": 0.5}],
        }
        result = PromptBuilder.build_portfolio_analysis_prompt(data)
        assert isinstance(result, str)
        assert "低收益" in result

    def test_format_money(self):
        result = PromptBuilder._format_money(12345.67)
        assert isinstance(result, str)


class TestResultParser:
    def test_parse_json_response_valid(self):
        response = '{"summary": "测试", "risk_assessment": "低", "suggestions": ["建议1"], "warnings": [], "score": 80}'
        result = ResultParser.parse_json_response(response)
        assert isinstance(result, ParsedResult)
        assert result.success is True
        assert result.summary == "测试"
        assert result.score == 80

    def test_parse_json_response_with_surrounding_text(self):
        response = '这是AI的分析结果：{"summary": "好", "score": 90}，以上是分析。'
        result = ResultParser.parse_json_response(response)
        assert isinstance(result, ParsedResult)
        assert result.success is True
        assert result.summary == "好"

    def test_parse_json_response_invalid(self):
        response = "这不是JSON格式"
        result = ResultParser.parse_json_response(response)
        assert isinstance(result, ParsedResult)
        assert result.success is False

    def test_parsed_result_defaults(self):
        result = ParsedResult(success=True)
        assert result.summary == ""
        assert result.suggestions == []
        assert result.warnings == []
        assert result.score == 60
