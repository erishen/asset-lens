from asset_lens.ai.prompt_builder import PromptBuilder


class TestBuildPortfolioAnalysisPrompt:
    def test_basic_data(self):
        data = {
            "total_value": 200000,
            "total_profit": 30000,
            "overall_return_rate": 15.0,
            "total_products": 8,
            "risk_distribution": {
                "低风险": {"percentage": 40},
                "高风险": {"percentage": 60},
            },
            "type_distribution": {
                "股票": {"percentage": 50},
                "基金": {"percentage": 50},
            },
            "low_returns": [],
        }
        prompt = PromptBuilder.build_portfolio_analysis_prompt(data)
        assert "投资组合概览" in prompt
        assert "20.00万" in prompt
        assert "3.00万" in prompt
        assert "15.0%" in prompt
        assert "8 个" in prompt
        assert "低风险" in prompt
        assert "高风险" in prompt
        assert "股票" in prompt
        assert "基金" in prompt
        assert "分析要求" in prompt

    def test_with_low_returns(self):
        data = {
            "total_value": 100000,
            "total_profit": 5000,
            "overall_return_rate": 5.0,
            "total_products": 3,
            "risk_distribution": {},
            "type_distribution": {},
            "low_returns": [
                {"name": "产品A", "annual_return": "1.5%"},
                {"name": "产品B", "annual_return": "0.8%"},
            ],
        }
        prompt = PromptBuilder.build_portfolio_analysis_prompt(data)
        assert "低收益产品" in prompt
        assert "2 个" in prompt
        assert "产品A" in prompt
        assert "产品B" in prompt

    def test_low_returns_truncated_to_five(self):
        data = {
            "total_value": 0,
            "total_profit": 0,
            "overall_return_rate": 0,
            "total_products": 0,
            "risk_distribution": {},
            "type_distribution": {},
            "low_returns": [{"name": f"产品{i}", "annual_return": "0.5%"} for i in range(8)],
        }
        prompt = PromptBuilder.build_portfolio_analysis_prompt(data)
        assert "产品0" in prompt
        assert "产品4" in prompt
        assert "产品5" not in prompt

    def test_empty_data(self):
        data = {}
        prompt = PromptBuilder.build_portfolio_analysis_prompt(data)
        assert "投资组合概览" in prompt
        assert "0.00" in prompt

    def test_missing_optional_fields(self):
        data = {
            "total_value": 50000,
            "total_profit": 2000,
            "overall_return_rate": 4.0,
            "total_products": 2,
        }
        prompt = PromptBuilder.build_portfolio_analysis_prompt(data)
        assert "投资组合概览" in prompt


class TestBuildRiskAssessmentPrompt:
    def test_basic_risk(self):
        data = {
            "total_value": 100000,
            "risk_distribution": {
                "低风险": {"total_value": 40000},
                "高风险": {"total_value": 60000},
            },
        }
        prompt = PromptBuilder.build_risk_assessment_prompt(data)
        assert "风险分布分析" in prompt
        assert "低风险" in prompt
        assert "高风险" in prompt
        assert "40.0%" in prompt
        assert "60.0%" in prompt

    def test_zero_total_value(self):
        data = {
            "total_value": 0,
            "risk_distribution": {
                "低风险": {"total_value": 0},
            },
        }
        prompt = PromptBuilder.build_risk_assessment_prompt(data)
        assert "风险分布分析" in prompt

    def test_empty_risk_distribution(self):
        data = {"total_value": 100000, "risk_distribution": {}}
        prompt = PromptBuilder.build_risk_assessment_prompt(data)
        assert "风险分布分析" in prompt
        assert "调整建议" in prompt


class TestBuildSuggestionPrompt:
    def test_default_risk_preference(self):
        data = {"total_value": 100000, "total_profit": 5000, "overall_return_rate": 5.0}
        prompt = PromptBuilder.build_suggestion_prompt(data)
        assert "balanced" in prompt
        assert "投资组合数据" in prompt

    def test_custom_risk_preference(self):
        data = {"total_value": 50000, "total_profit": -1000, "overall_return_rate": -2.0}
        prompt = PromptBuilder.build_suggestion_prompt(data, risk_preference="aggressive")
        assert "aggressive" in prompt

    def test_empty_data(self):
        data = {}
        prompt = PromptBuilder.build_suggestion_prompt(data)
        assert "投资组合数据" in prompt


class TestFormatMoney:
    def test_large_amount(self):
        assert PromptBuilder._format_money(100000) == "10.00万"
        assert PromptBuilder._format_money(50000) == "5.00万"
        assert PromptBuilder._format_money(10000) == "1.00万"

    def test_small_amount(self):
        assert PromptBuilder._format_money(9999) == "9999.00"
        assert PromptBuilder._format_money(0) == "0.00"
        assert PromptBuilder._format_money(100) == "100.00"

    def test_invalid_input(self):
        assert PromptBuilder._format_money("abc") == "0.00"
        assert PromptBuilder._format_money(None) == "0.00"

    def test_negative_amount(self):
        assert PromptBuilder._format_money(-5000) == "-5000.00"
        assert PromptBuilder._format_money(-20000) == "-20000.00"

    def test_float_input(self):
        assert PromptBuilder._format_money(12345.67) == "1.23万"


class TestGetSystemPrompt:
    def test_returns_non_empty_string(self):
        prompt = PromptBuilder.get_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "投资顾问" in prompt
