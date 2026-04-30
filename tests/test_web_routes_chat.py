"""
Tests for Web Routes - Chat API.
聊天 API 路由测试
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "asset_lens"))

from asset_lens.web.routes.chat import (
    _generate_fallback_answer,
    _generate_related_questions,
    _generate_suggestions,
    router,
)


@pytest.fixture
def app():
    """创建测试应用"""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return TestClient(app)


class TestChatQA:
    """测试聊天问答"""

    def test_chat_qa_fast_mode(self, client):
        """测试快速模式问答"""
        response = client.post(
            "/api/chat/qa",
            json={
                "message": "如何控制风险？",
                "fast_mode": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "suggestions" in data
        assert "related_questions" in data

    def test_chat_qa_with_rag(self, client):
        """测试带 RAG 的问答"""
        with patch("asset_lens.web.routes.chat._query_rag", new_callable=AsyncMock) as mock_rag:
            mock_rag.return_value = [{"content": "风险控制是投资的关键", "source": "投资指南", "category": "风险管理"}]

            response = client.post(
                "/api/chat/qa",
                json={
                    "message": "风险控制",
                    "use_rag": True,
                    "fast_mode": True,
                },
            )

            assert response.status_code == 200

    def test_chat_qa_portfolio_analysis(self, client):
        """测试投资组合分析"""
        with patch("asset_lens.web.routes.chat._query_rag", new_callable=AsyncMock) as mock_rag:
            mock_rag.return_value = []

            response = client.post(
                "/api/chat/qa",
                json={
                    "message": "我的投资组合如何？",
                    "use_portfolio": True,
                    "fast_mode": True,
                },
            )

            assert response.status_code == 200


class TestGenerateSuggestions:
    """测试建议生成"""

    def test_suggestions_for_risk(self):
        """测试风险相关建议"""
        suggestions = _generate_suggestions("如何控制风险？")

        assert len(suggestions) == 3
        assert any("止损" in s for s in suggestions)

    def test_suggestions_for_stop_loss(self):
        """测试止损相关建议"""
        suggestions = _generate_suggestions("止损策略")

        assert len(suggestions) == 3
        assert any("止损" in s for s in suggestions)

    def test_suggestions_for_trend(self):
        """测试趋势相关建议"""
        suggestions = _generate_suggestions("市场趋势分析")

        assert len(suggestions) == 3
        assert any("趋势" in s or "市场" in s for s in suggestions)

    def test_suggestions_default(self):
        """测试默认建议"""
        suggestions = _generate_suggestions("其他问题")

        assert len(suggestions) == 3


class TestGenerateRelatedQuestions:
    """测试相关问题生成"""

    def test_related_for_risk(self):
        """测试风险相关问题"""
        questions = _generate_related_questions("风险管理")

        assert len(questions) == 2

    def test_related_for_stop_loss(self):
        """测试止损相关问题"""
        questions = _generate_related_questions("止损设置")

        assert len(questions) == 2

    def test_related_default(self):
        """测试默认相关问题"""
        questions = _generate_related_questions("其他话题")

        assert len(questions) == 2


class TestGenerateFallbackAnswer:
    """测试后备答案生成"""

    def test_fallback_with_rag_results(self):
        """测试带 RAG 结果的后备答案"""
        rag_results = [
            {"content": "风险控制很重要", "source": "投资指南"},
            {"content": "分散投资降低风险", "source": "风险管理"},
        ]

        answer = _generate_fallback_answer("风险控制", rag_results)

        assert "知识库" in answer or "风险" in answer

    def test_fallback_for_risk(self):
        """测试风险后备答案"""
        answer = _generate_fallback_answer("如何控制风险？", [])

        assert "风险" in answer
        assert "分散" in answer or "止损" in answer

    def test_fallback_for_trend(self):
        """测试趋势后备答案"""
        answer = _generate_fallback_answer("市场趋势如何？", [])

        assert "趋势" in answer or "市场" in answer

    def test_fallback_for_stop_loss(self):
        """测试止损后备答案"""
        answer = _generate_fallback_answer("止损策略", [])

        assert "止损" in answer

    def test_fallback_for_position(self):
        """测试仓位后备答案"""
        answer = _generate_fallback_answer("仓位管理", [])

        assert "仓位" in answer or "配置" in answer

    def test_fallback_default(self):
        """测试默认后备答案"""
        answer = _generate_fallback_answer("其他问题", [])

        assert len(answer) > 0


class TestGetPortfolioAnalysis:
    """测试投资组合分析"""

    def test_get_portfolio_analysis(self, client):
        """测试获取投资组合分析"""
        response = client.get("/api/chat/portfolio")

        assert response.status_code == 200
        data = response.json()
        assert "success" in data


class TestGetSignals:
    """测试获取信号"""

    def test_get_signals(self, client):
        """测试获取技术信号"""
        with patch.dict(sys.modules, {"scanner": MagicMock()}):
            mock_scanner = sys.modules["scanner"]
            mock_signal = MagicMock()
            mock_signal.code = "000001"
            mock_signal.name = "平安银行"
            mock_signal.signal_type.value = "buy"
            mock_signal.strength.value = "strong"
            mock_signal.score = 80
            mock_signal.price = 10.0
            mock_signal.change_percent = 2.5
            mock_signal.date = "2024-01-01"

            mock_result = MagicMock()
            mock_result.top_signals = [mock_signal]
            mock_result.total_stocks = 100
            mock_result.signals_found = 10
            mock_result.summary = "测试摘要"

            mock_scanner.run_scan.return_value = mock_result

            response = client.post(
                "/api/chat/signals",
                json={"min_score": 50, "limit": 10},
            )

            assert response.status_code == 200


class TestGetMarketTiming:
    """测试获取大盘择时"""

    def test_get_market_timing(self, client):
        """测试获取大盘择时"""
        with patch.dict(sys.modules, {"strategy": MagicMock()}):
            mock_strategy = sys.modules["strategy"]
            mock_result = MagicMock()
            mock_result.state.value = "bullish"
            mock_result.score = 75
            mock_result.signal = "建议持有"
            mock_result.ma_trend = "up"
            mock_result.rsi_level = 60
            mock_result.volatility = "low"
            mock_result.breadth = 0.7

            mock_strategy.run_market_timing.return_value = mock_result

            response = client.get("/api/chat/timing")

            assert response.status_code == 200


class TestQueryRAG:
    """测试 RAG 查询"""

    def test_query_rag(self, client):
        """测试 RAG 知识库查询"""
        with patch("asset_lens.web.routes.chat._query_rag", new_callable=AsyncMock) as mock_rag:
            mock_rag.return_value = [{"content": "测试内容", "title": "测试标题", "source": "测试来源"}]

            response = client.post(
                "/api/chat/rag",
                json={"query": "测试查询", "k": 5},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1


class TestGetConfig:
    """测试获取配置"""

    def test_get_config(self, client):
        """测试获取配置信息"""
        response = client.get("/api/chat/config")

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "services" in data
