"""
Tests for AI Q&A Module.
AI 问答模块测试
"""

from asset_lens.analysis.ai_qa import AIQAEngine, KnowledgeEntry, QAContext, QAResponse, QuestionType, ai_qa_engine


class TestQuestionType:
    """测试问题类型枚举"""

    def test_question_types(self):
        """测试所有问题类型"""
        assert QuestionType.MARKET_OUTLOOK.value == "market_outlook"
        assert QuestionType.STOCK_ANALYSIS.value == "stock_analysis"
        assert QuestionType.STRATEGY.value == "strategy"
        assert QuestionType.RISK_MANAGEMENT.value == "risk_management"
        assert QuestionType.PORTFOLIO.value == "portfolio"
        assert QuestionType.TECHNICAL.value == "technical"
        assert QuestionType.FUNDAMENTAL.value == "fundamental"
        assert QuestionType.GENERAL.value == "general"


class TestQAContext:
    """测试问答上下文"""

    def test_create_context(self):
        """测试创建上下文"""
        context = QAContext(
            user_holdings=[{"code": "sh600519", "name": "贵州茅台"}],
            recent_trades=[],
            market_data={},
            user_preferences={},
        )

        assert len(context.user_holdings) == 1


class TestQAResponse:
    """测试问答响应"""

    def test_create_response(self):
        """测试创建响应"""
        response = QAResponse(
            question="如何设置止损？",
            question_type=QuestionType.RISK_MANAGEMENT,
            answer="建议设置止损位为 -8%",
            confidence=0.9,
            sources=["止损策略"],
            related_questions=["如何控制仓位？"],
            suggestions=["严格执行止损纪律"],
        )

        assert response.question == "如何设置止损？"
        assert response.question_type == QuestionType.RISK_MANAGEMENT
        assert response.confidence == 0.9


class TestKnowledgeEntry:
    """测试知识库条目"""

    def test_create_entry(self):
        """测试创建条目"""
        entry = KnowledgeEntry(
            id="1",
            title="止损策略",
            content="建议设置止损位为 -8%",
            category="risk_management",
            tags=["止损", "风险控制"],
            created_at="2024-01-01",
            updated_at="2024-01-01",
        )

        assert entry.id == "1"
        assert entry.title == "止损策略"


class TestAIQAEngine:
    """测试 AI 问答引擎"""

    def test_init(self, tmp_path):
        """测试初始化"""
        engine = AIQAEngine(cache_path=tmp_path)
        assert engine.cache_path == tmp_path
        assert engine.knowledge_base_file.exists()

    def test_init_knowledge_base(self, tmp_path):
        """测试初始化知识库"""
        engine = AIQAEngine(cache_path=tmp_path)

        entries = engine._load_knowledge_base()
        assert len(entries) >= 4

    def test_classify_question_market(self, tmp_path):
        """测试分类市场问题"""
        engine = AIQAEngine(cache_path=tmp_path)

        q_type = engine.classify_question("当前市场趋势如何？")
        assert q_type == QuestionType.MARKET_OUTLOOK

    def test_classify_question_stock(self, tmp_path):
        """测试分类个股问题"""
        engine = AIQAEngine(cache_path=tmp_path)

        q_type = engine.classify_question("如何分析这只股票？")
        assert q_type == QuestionType.STOCK_ANALYSIS

    def test_classify_question_strategy(self, tmp_path):
        """测试分类策略问题"""
        engine = AIQAEngine(cache_path=tmp_path)

        q_type = engine.classify_question("有什么好的交易策略？")
        assert q_type == QuestionType.STRATEGY

    def test_classify_question_risk(self, tmp_path):
        """测试分类风险问题"""
        engine = AIQAEngine(cache_path=tmp_path)

        q_type = engine.classify_question("如何设置止损？")
        assert q_type == QuestionType.RISK_MANAGEMENT

    def test_classify_question_portfolio(self, tmp_path):
        """测试分类持仓问题"""
        engine = AIQAEngine(cache_path=tmp_path)

        q_type = engine.classify_question("如何管理持仓？")
        assert q_type == QuestionType.PORTFOLIO

    def test_classify_question_technical(self, tmp_path):
        """测试分类技术问题"""
        engine = AIQAEngine(cache_path=tmp_path)

        q_type = engine.classify_question("如何看均线？")
        assert q_type == QuestionType.TECHNICAL

        q_type = engine.classify_question("MACD 怎么用？")
        assert q_type == QuestionType.TECHNICAL

    def test_classify_question_fundamental(self, tmp_path):
        """测试分类基本面问题"""
        engine = AIQAEngine(cache_path=tmp_path)

        q_type = engine.classify_question("如何看 PE？")
        assert q_type == QuestionType.FUNDAMENTAL

    def test_classify_question_general(self, tmp_path):
        """测试分类一般问题"""
        engine = AIQAEngine(cache_path=tmp_path)

        q_type = engine.classify_question("今天天气怎么样？")
        assert q_type == QuestionType.GENERAL

    def test_search_knowledge(self, tmp_path):
        """测试搜索知识库"""
        engine = AIQAEngine(cache_path=tmp_path)

        results = engine.search_knowledge("止损")

        assert len(results) > 0
        assert "止损" in results[0].title or "止损" in results[0].content

    def test_search_knowledge_no_match(self, tmp_path):
        """测试搜索无匹配"""
        engine = AIQAEngine(cache_path=tmp_path)

        results = engine.search_knowledge("xyz123不存在的关键词")

        assert len(results) == 0

    def test_answer_question(self, tmp_path):
        """测试回答问题"""
        engine = AIQAEngine(cache_path=tmp_path)

        response = engine.answer_question("如何设置止损？")

        assert response.question == "如何设置止损？"
        assert response.question_type == QuestionType.RISK_MANAGEMENT
        assert len(response.answer) > 0
        assert response.confidence > 0

    def test_answer_question_with_context(self, tmp_path):
        """测试带上下文回答问题"""
        engine = AIQAEngine(cache_path=tmp_path)

        context = QAContext(
            user_holdings=[{"code": "sh600519", "name": "贵州茅台"}],
            recent_trades=[],
            market_data={},
            user_preferences={},
        )

        response = engine.answer_question("如何管理持仓？", context=context)

        assert "持仓" in response.answer or len(response.suggestions) > 0

    def test_calculate_confidence_high(self, tmp_path):
        """测试计算高置信度"""
        engine = AIQAEngine(cache_path=tmp_path)

        knowledge = [
            KnowledgeEntry(
                id="1",
                title="止损策略",
                content="内容1",
                category="risk",
                tags=[],
                created_at="",
                updated_at="",
            ),
            KnowledgeEntry(
                id="2",
                title="止损方法",
                content="内容2",
                category="risk",
                tags=[],
                created_at="",
                updated_at="",
            ),
        ]

        confidence = engine._calculate_confidence("止损", knowledge)
        assert confidence == 0.9

    def test_calculate_confidence_medium(self, tmp_path):
        """测试计算中等置信度"""
        engine = AIQAEngine(cache_path=tmp_path)

        knowledge = [
            KnowledgeEntry(
                id="1",
                title="止损策略",
                content="内容",
                category="risk",
                tags=[],
                created_at="",
                updated_at="",
            ),
        ]

        confidence = engine._calculate_confidence("止损", knowledge)
        assert confidence == 0.75

    def test_calculate_confidence_low(self, tmp_path):
        """测试计算低置信度"""
        engine = AIQAEngine(cache_path=tmp_path)

        confidence = engine._calculate_confidence("止损", [])
        assert confidence == 0.5

    def test_generate_related_questions(self, tmp_path):
        """测试生成相关问题"""
        engine = AIQAEngine(cache_path=tmp_path)

        related = engine._generate_related_questions(QuestionType.RISK_MANAGEMENT)

        assert len(related) == 3
        assert any("止损" in q for q in related)

    def test_generate_suggestions(self, tmp_path):
        """测试生成建议"""
        engine = AIQAEngine(cache_path=tmp_path)

        suggestions = engine._generate_suggestions(QuestionType.RISK_MANAGEMENT, None)

        assert len(suggestions) > 0
        assert any("止损" in s for s in suggestions)

    def test_add_knowledge(self, tmp_path):
        """测试添加知识"""
        engine = AIQAEngine(cache_path=tmp_path)

        entry = KnowledgeEntry(
            id="test1",
            title="测试知识",
            content="这是测试内容",
            category="test",
            tags=["测试"],
            created_at="2024-01-01",
            updated_at="2024-01-01",
        )

        engine.add_knowledge(entry)

        results = engine.search_knowledge("测试知识")
        assert len(results) > 0

    def test_get_qa_history(self, tmp_path):
        """测试获取问答历史"""
        engine = AIQAEngine(cache_path=tmp_path)

        engine.answer_question("问题1")
        engine.answer_question("问题2")

        history = engine.get_qa_history()

        assert len(history) >= 2


class TestAIQAEngineInstance:
    """测试全局实例"""

    def test_global_instance_exists(self):
        """测试全局实例存在"""
        assert ai_qa_engine is not None
        assert isinstance(ai_qa_engine, AIQAEngine)
