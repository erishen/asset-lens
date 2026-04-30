"""
Tests for AI analyzer module.
"""

from asset_lens.core.ai_analyzer import AIAnalysisResult, AIAnalyzer


class TestAIAnalysisResult:
    """Test AIAnalysisResult dataclass"""

    def test_creation(self):
        """Test creating AIAnalysisResult"""
        result = AIAnalysisResult(
            summary="Test summary",
            risk_assessment="Test risk",
            suggestions=["Suggestion 1"],
            warnings=["Warning 1"],
            score=75,
        )

        assert result.summary == "Test summary"
        assert result.risk_assessment == "Test risk"
        assert len(result.suggestions) == 1
        assert len(result.warnings) == 1
        assert result.score == 75


class TestAIAnalyzer:
    """Test AIAnalyzer class"""

    def test_init(self):
        """Test initialization"""
        analyzer = AIAnalyzer()
        assert analyzer.risk_keywords is not None
        assert analyzer.use_cache is True

    def test_analyze_portfolio_profit(self):
        """Test analyzing profitable portfolio"""
        analyzer = AIAnalyzer()

        portfolio_data = {
            "total_value": 100000,
            "total_profit": 10000,
            "overall_return_rate": 10.0,
            "total_products": 10,
            "risk_distribution": {
                "高": {"total_value": 30000, "percentage": 30},
                "中": {"total_value": 40000, "percentage": 40},
                "低": {"total_value": 30000, "percentage": 30},
            },
            "type_distribution": {
                "股票": {"total_value": 30000, "percentage": 30},
                "债券": {"total_value": 40000, "percentage": 40},
                "货币": {"total_value": 30000, "percentage": 30},
            },
            "products": [
                {
                    "name": "Product 1",
                    "profit_amount": 1000,
                    "return_rate": 5,
                    "current_amount": 10000,
                    "investment_days": 100,
                },
                {
                    "name": "Product 2",
                    "profit_amount": 2000,
                    "return_rate": 8,
                    "current_amount": 20000,
                    "investment_days": 200,
                },
            ],
            "low_returns": [],
        }

        result = analyzer.analyze_portfolio(portfolio_data)

        assert result is not None
        assert len(result.summary) > 0
        assert result.score > 0

    def test_analyze_portfolio_loss(self):
        """Test analyzing losing portfolio"""
        analyzer = AIAnalyzer()

        portfolio_data = {
            "total_value": 100000,
            "total_profit": -5000,
            "overall_return_rate": -5.0,
            "total_products": 5,
            "risk_distribution": {
                "高": {"total_value": 60000},
                "中": {"total_value": 30000},
                "低": {"total_value": 10000},
            },
            "products": [
                {
                    "name": "Product 1",
                    "profit_amount": -1000,
                    "return_rate": -5,
                    "current_amount": 10000,
                    "investment_days": 100,
                },
            ],
            "low_returns": [{"name": "Low Return Product"}],
        }

        result = analyzer.analyze_portfolio(portfolio_data)

        assert result is not None
        assert "亏损" in result.summary

    def test_assess_risk_high(self):
        """Test high risk assessment"""
        analyzer = AIAnalyzer()

        data = {
            "total_value": 100000,
            "risk_distribution": {
                "高": {"total_value": 60000},
                "中": {"total_value": 30000},
                "低": {"total_value": 10000},
            },
        }

        result = analyzer._assess_risk(data)
        assert "风险较高" in result

    def test_assess_risk_low(self):
        """Test low risk assessment"""
        analyzer = AIAnalyzer()

        data = {
            "total_value": 100000,
            "risk_distribution": {
                "高": {"total_value": 10000},
                "中": {"total_value": 30000},
                "低": {"total_value": 60000},
            },
        }

        result = analyzer._assess_risk(data)
        assert "风险较低" in result

    def test_generate_suggestions(self):
        """Test generating suggestions"""
        analyzer = AIAnalyzer()

        data = {
            "low_returns": [
                {"name": "Low 1"},
                {"name": "Low 2"},
                {"name": "Low 3"},
                {"name": "Low 4"},
                {"name": "Low 5"},
                {"name": "Low 6"},
            ],
            "products": [
                {"profit_amount": -100},
            ],
            "type_distribution": {
                "股票": {"total_value": 60000},
            },
            "total_value": 100000,
        }

        suggestions = analyzer._generate_suggestions(data)
        assert len(suggestions) > 0

    def test_generate_warnings(self):
        """Test generating warnings"""
        analyzer = AIAnalyzer()

        data = {
            "products": [
                {"name": "Loss Product", "return_rate": -10, "current_amount": 50000},
            ],
            "risk_distribution": {
                "高": {"total_value": 70000},
            },
            "total_value": 100000,
        }

        warnings = analyzer._generate_warnings(data)
        assert len(warnings) > 0

    def test_calculate_score(self):
        """Test calculating score"""
        analyzer = AIAnalyzer()

        data = {
            "overall_return_rate": 15.0,
            "risk_distribution": {"高": {}, "中": {}, "低": {}},
            "total_products": 15,
        }

        score = analyzer._calculate_score(data)
        assert 0 <= score <= 100

    def test_format_money(self):
        """Test formatting money"""
        analyzer = AIAnalyzer()

        assert analyzer._format_money(10000) == "1.00万"
        assert analyzer._format_money(5000) == "5000.00"
        assert analyzer._format_money("invalid") == "0.00"

    def test_generate_investment_advice(self):
        """Test generating investment advice"""
        analyzer = AIAnalyzer()

        portfolio_data = {
            "total_value": 100000,
            "total_profit": 5000,
            "overall_return_rate": 5.0,
            "total_products": 10,
            "risk_distribution": {
                "高": {"total_value": 20000},
                "中": {"total_value": 50000},
                "低": {"total_value": 30000},
            },
            "products": [],
            "low_returns": [],
        }

        advice = analyzer.generate_investment_advice(portfolio_data, "balanced")

        assert "summary" in advice
        assert "score" in advice
        assert "recommended_allocation" in advice

    def test_get_score_level(self):
        """Test getting score level"""
        analyzer = AIAnalyzer()

        assert analyzer._get_score_level(85) == "优秀"
        assert analyzer._get_score_level(65) == "良好"
        assert analyzer._get_score_level(45) == "一般"
        assert analyzer._get_score_level(25) == "需改进"

    def test_get_recommended_allocation(self):
        """Test getting recommended allocation"""
        analyzer = AIAnalyzer()

        conservative = analyzer._get_recommended_allocation("conservative")
        assert conservative["货币基金"] == 30

        balanced = analyzer._get_recommended_allocation("balanced")
        assert balanced["混合基金"] == 30

        aggressive = analyzer._get_recommended_allocation("aggressive")
        assert aggressive["股票基金"] == 40
