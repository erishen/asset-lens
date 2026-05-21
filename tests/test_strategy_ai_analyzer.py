"""
Tests for strategy AI analyzer module.
策略 AI 分析器模块测试
"""

from unittest.mock import patch


class TestAIDecision:
    """AI 决策枚举测试"""

    def test_ai_decision_values(self):
        """测试 AI 决策枚举值"""
        from asset_lens.strategy.ai_analyzer import AIDecision

        assert AIDecision.BUY.value == "buy"
        assert AIDecision.SELL.value == "sell"
        assert AIDecision.HOLD.value == "hold"
        assert AIDecision.WAIT.value == "wait"


class TestAIAnalysisResult:
    """AI 分析结果测试"""

    def test_ai_analysis_result_default(self):
        """测试默认值"""
        from asset_lens.strategy.ai_analyzer import AIAnalysisResult, AIDecision

        result = AIAnalysisResult(
            decision=AIDecision.WAIT,
            confidence=50,
            reasoning="test",
            risk_level="medium",
            key_factors=[],
            market_sentiment="中性",
        )
        assert result.decision == AIDecision.WAIT
        assert result.confidence == 50
        assert result.suggested_price is None
        assert result.stop_loss is None
        assert result.take_profit is None

    def test_ai_analysis_result_full(self):
        """测试完整值"""
        from asset_lens.strategy.ai_analyzer import AIAnalysisResult, AIDecision

        result = AIAnalysisResult(
            decision=AIDecision.BUY,
            confidence=80,
            reasoning="强烈买入信号",
            risk_level="low",
            key_factors=["技术面好", "基本面强"],
            market_sentiment="乐观",
            suggested_price=100.0,
            stop_loss=90.0,
            take_profit=120.0,
            holding_period=30,
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
        )
        assert result.decision == AIDecision.BUY
        assert result.confidence == 80
        assert result.suggested_price == 100.0
        assert result.stop_loss == 90.0
        assert result.take_profit == 120.0
        assert result.holding_period == 30
        assert result.prompt_tokens == 100


class TestAIAnalyzer:
    """AI 分析器测试"""

    def test_ai_analyzer_init_no_api_key(self):
        """测试无 API Key 初始化"""
        with patch.dict("os.environ", {}, clear=True):
            from asset_lens.strategy.ai_analyzer import LegacyAIAnalyzer

            analyzer = LegacyAIAnalyzer()
            assert analyzer.enabled is False

    def test_ai_analyzer_init_with_api_key(self):
        """测试有 API Key 初始化"""
        with patch.dict("os.environ", {"DEEPSEEK_API_KEY": "test_key"}):
            from asset_lens.strategy.ai_analyzer import LegacyAIAnalyzer

            analyzer = LegacyAIAnalyzer()
            assert analyzer.enabled is True
            assert analyzer.api_key == "test_key"

    def test_build_analysis_prompt(self):
        """测试构建分析提示词"""
        with patch.dict("os.environ", {}, clear=True):
            from asset_lens.strategy.ai_analyzer import LegacyAIAnalyzer

            analyzer = LegacyAIAnalyzer()

            stock_data = {
                "code": "sh600519",
                "name": "贵州茅台",
                "price": 1800,
                "change_percent": 2.5,
                "volume": 1000000,
                "turnover_rate": 0.5,
                "market_cap": 20000,
                "pe_ratio": 30,
            }

            prompt = analyzer._build_analysis_prompt(stock_data)
            assert "sh600519" in prompt
            assert "贵州茅台" in prompt

    def test_build_analysis_prompt_with_market_data(self):
        """测试构建分析提示词（含市场数据）"""
        with patch.dict("os.environ", {}, clear=True):
            from asset_lens.strategy.ai_analyzer import LegacyAIAnalyzer

            analyzer = LegacyAIAnalyzer()

            stock_data = {"code": "sh600519", "name": "测试", "price": 100}
            market_data = {"index_change": 1.5}

            prompt = analyzer._build_analysis_prompt(stock_data, market_data=market_data)
            assert "大盘" in prompt

    def test_build_analysis_prompt_with_strategy_signal(self):
        """测试构建分析提示词（含策略信号）"""
        with patch.dict("os.environ", {}, clear=True):
            from asset_lens.strategy.ai_analyzer import LegacyAIAnalyzer

            analyzer = LegacyAIAnalyzer()

            stock_data = {"code": "sh600519", "name": "测试", "price": 100}

            prompt = analyzer._build_analysis_prompt(stock_data, strategy_signal="买入信号")
            assert "策略" in prompt

    def test_default_result(self):
        """测试默认结果"""
        with patch.dict("os.environ", {}, clear=True):
            from asset_lens.strategy.ai_analyzer import AIDecision, LegacyAIAnalyzer

            analyzer = LegacyAIAnalyzer()

            result = analyzer._default_result("测试原因")
            assert result.decision == AIDecision.WAIT
            assert result.confidence == 0
            assert result.reasoning == "测试原因"
            assert result.risk_level == "medium"

    def test_parse_response_valid_json(self):
        """测试解析有效 JSON 响应"""
        from asset_lens.strategy.ai_analyzer import AIDecision, LegacyAIAnalyzer

        analyzer = LegacyAIAnalyzer()

        content = (
            '{"d": "buy", "c": 80, "r": "技术面好", "rl": "low", "kf": ["因素1"], "ms": "乐观", "sl": 90, "tp": 110}'
        )
        result = analyzer._parse_response(content, 100, 50, 150)

        assert result.decision == AIDecision.BUY
        assert result.confidence == 80
        assert result.reasoning == "技术面好"
        assert result.risk_level == "low"
        assert result.stop_loss == 90
        assert result.take_profit == 110

    def test_parse_response_invalid_json(self):
        """测试解析无效 JSON 响应"""
        from asset_lens.strategy.ai_analyzer import AIDecision, LegacyAIAnalyzer

        analyzer = LegacyAIAnalyzer()

        content = "invalid json"
        result = analyzer._parse_response(content)

        assert result.decision == AIDecision.WAIT
        assert "失败" in result.reasoning

    def test_analyze_stock_sync_disabled(self):
        """测试同步分析（未启用）"""
        with patch.dict("os.environ", {}, clear=True):
            from asset_lens.strategy.ai_analyzer import AIDecision, LegacyAIAnalyzer

            analyzer = LegacyAIAnalyzer()

            result = analyzer.analyze_stock_sync({"code": "sh600519"})
            assert result.decision == AIDecision.WAIT
            assert "未启用" in result.reasoning

    def test_batch_analyze(self):
        """测试批量分析"""
        with patch.dict("os.environ", {}, clear=True):
            from asset_lens.strategy.ai_analyzer import LegacyAIAnalyzer

            analyzer = LegacyAIAnalyzer()

            stocks = [
                {"code": "sh600519", "name": "茅台"},
                {"code": "sz000001", "name": "平安"},
            ]

            results = analyzer.batch_analyze(stocks)
            assert len(results) == 2
            assert "sh600519" in results
            assert "sz000001" in results


class TestAITradingAdvisor:
    """AI 交易顾问测试"""

    def test_advisor_init(self):
        """测试初始化"""
        from asset_lens.strategy.ai_analyzer import AITradingAdvisor

        advisor = AITradingAdvisor()
        assert advisor.analyzer is not None

    def test_evaluate_buy_signal_disabled(self):
        """测试评估买入信号（未启用）"""
        with patch.dict("os.environ", {}, clear=True):
            from asset_lens.strategy.ai_analyzer import AITradingAdvisor

            advisor = AITradingAdvisor()

            result = advisor.evaluate_buy_signal(stock_data={"code": "sh600519"}, strategy_score=80)
            assert result["action"] == "skip"
            assert result["strategy_only"] is True

    def test_combine_decisions_buy_high_score(self):
        """测试组合决策（高分买入）"""
        from asset_lens.strategy.ai_analyzer import AIAnalysisResult, AIDecision, AITradingAdvisor

        advisor = AITradingAdvisor()

        ai_result = AIAnalysisResult(
            decision=AIDecision.BUY,
            confidence=80,
            reasoning="强烈买入",
            risk_level="low",
            key_factors=[],
            market_sentiment="乐观",
        )

        decision = advisor._combine_decisions(80, ai_result)
        assert decision["action"] == "buy"

    def test_combine_decisions_wait(self):
        """测试组合决策（观望）"""
        from asset_lens.strategy.ai_analyzer import AIAnalysisResult, AIDecision, AITradingAdvisor

        advisor = AITradingAdvisor()

        ai_result = AIAnalysisResult(
            decision=AIDecision.WAIT,
            confidence=50,
            reasoning="等待时机",
            risk_level="medium",
            key_factors=[],
            market_sentiment="中性",
        )

        decision = advisor._combine_decisions(60, ai_result)
        assert decision["action"] == "wait"

    def test_combine_sell_decisions_stop_loss(self):
        """测试卖出决策（止损）"""
        from asset_lens.strategy.ai_analyzer import AIAnalysisResult, AIDecision, AITradingAdvisor

        advisor = AITradingAdvisor()

        ai_result = AIAnalysisResult(
            decision=AIDecision.HOLD,
            confidence=50,
            reasoning="继续持有",
            risk_level="medium",
            key_factors=[],
            market_sentiment="中性",
        )

        decision = advisor._combine_sell_decisions(-8, 10, ai_result)
        assert decision["action"] == "sell"
        assert "止损" in decision["reason"]

    def test_combine_sell_decisions_take_profit(self):
        """测试卖出决策（止盈）"""
        from asset_lens.strategy.ai_analyzer import AIAnalysisResult, AIDecision, AITradingAdvisor

        advisor = AITradingAdvisor()

        ai_result = AIAnalysisResult(
            decision=AIDecision.HOLD,
            confidence=50,
            reasoning="继续持有",
            risk_level="medium",
            key_factors=[],
            market_sentiment="中性",
        )

        decision = advisor._combine_sell_decisions(20, 10, ai_result)
        assert decision["action"] == "sell"
        assert "止盈" in decision["reason"]

    def test_evaluate_sell_signal_disabled(self):
        """测试评估卖出信号（未启用）"""
        with patch.dict("os.environ", {}, clear=True):
            from asset_lens.strategy.ai_analyzer import AITradingAdvisor

            advisor = AITradingAdvisor()

            result = advisor.evaluate_sell_signal(
                stock_data={"code": "sh600519"}, holding_data={"profit_rate": 5, "holding_days": 10}
            )
            assert result["action"] == "skip"
            assert result["strategy_only"] is True


class TestGlobalInstances:
    """全局实例测试"""

    def test_ai_analyzer_instance(self):
        """测试全局 AI 分析器实例"""
        from asset_lens.strategy.ai_analyzer import ai_analyzer

        assert ai_analyzer is not None

    def test_ai_trading_advisor_instance(self):
        """测试全局 AI 交易顾问实例"""
        from asset_lens.strategy.ai_analyzer import ai_trading_advisor

        assert ai_trading_advisor is not None
