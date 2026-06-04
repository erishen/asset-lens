"""
AI Q&A Module.
AI 问答模块 - 投资问题解答和策略咨询

功能:
1. 投资问题解答
2. 策略咨询
3. 知识库查询
4. 历史案例学习
5. 个性化建议
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from ..config import config
from ..utils.json_cache import read_json_cache, write_json_cache


class QuestionType(Enum):
    """问题类型"""

    MARKET_OUTLOOK = "market_outlook"  # 市场展望
    STOCK_ANALYSIS = "stock_analysis"  # 个股分析
    STRATEGY = "strategy"  # 策略咨询
    RISK_MANAGEMENT = "risk_management"  # 风险管理
    PORTFOLIO = "portfolio"  # 持仓问题
    TECHNICAL = "technical"  # 技术分析
    FUNDAMENTAL = "fundamental"  # 基本面分析
    GENERAL = "general"  # 一般问题


@dataclass
class QAContext:
    """问答上下文"""

    user_holdings: list[dict[str, Any]]
    recent_trades: list[dict[str, Any]]
    market_data: dict[str, Any]
    user_preferences: dict[str, Any]


@dataclass
class QAResponse:
    """问答响应"""

    question: str
    question_type: QuestionType
    answer: str
    confidence: float
    sources: list[str]
    related_questions: list[str]
    suggestions: list[str]
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


@dataclass
class KnowledgeEntry:
    """知识库条目"""

    id: str
    title: str
    content: str
    category: str
    tags: list[str]
    created_at: str
    updated_at: str


class AIQAEngine:
    """AI 问答引擎"""

    def __init__(self, cache_path: Path | None = None):
        self.cache_path = cache_path or config.cache_path
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self.knowledge_base_file = self.cache_path / "knowledge_base.json"
        self.qa_history_file = self.cache_path / "qa_history.json"

        self._init_knowledge_base()

    def _init_knowledge_base(self) -> None:
        """初始化知识库"""
        if not self.knowledge_base_file.exists():
            default_knowledge = [
                {
                    "id": "1",
                    "title": "止损策略",
                    "content": "建议设置止损位为买入价的 -8%，严格执行止损纪律。单笔亏损不应超过总资金的 2%。",
                    "category": "risk_management",
                    "tags": ["止损", "风险控制"],
                },
                {
                    "id": "2",
                    "title": "仓位管理",
                    "content": "单只股票仓位不超过 20%，单一行业不超过 40%。保持 20% 以上现金应对机会。",
                    "category": "portfolio",
                    "tags": ["仓位", "分散投资"],
                },
                {
                    "id": "3",
                    "title": "买入时机",
                    "content": "在支撑位附近买入，避免追高。关注成交量放大和主力资金流入信号。",
                    "category": "strategy",
                    "tags": ["买入", "时机"],
                },
                {
                    "id": "4",
                    "title": "卖出时机",
                    "content": "达到目标价位或触发止损时卖出。基本面恶化或技术破位时考虑减仓。",
                    "category": "strategy",
                    "tags": ["卖出", "时机"],
                },
            ]

            write_json_cache(self.knowledge_base_file, default_knowledge)

    def classify_question(self, question: str) -> QuestionType:
        """分类问题类型"""
        question_lower = question.lower()

        keywords_map = {
            QuestionType.MARKET_OUTLOOK: ["市场", "大盘", "趋势", "行情"],
            QuestionType.STOCK_ANALYSIS: ["股票", "个股", "分析", "诊断"],
            QuestionType.STRATEGY: ["策略", "操作", "买卖", "交易"],
            QuestionType.RISK_MANAGEMENT: ["风险", "止损", "仓位"],
            QuestionType.PORTFOLIO: ["持仓", "组合", "配置"],
            QuestionType.TECHNICAL: ["技术", "均线", "macd", "rsi", "k线"],
            QuestionType.FUNDAMENTAL: ["基本面", "pe", "roe", "财报"],
        }

        for q_type, keywords in keywords_map.items():
            if any(k in question_lower for k in keywords):
                return q_type

        return QuestionType.GENERAL

    def search_knowledge(self, query: str, limit: int = 3) -> list[KnowledgeEntry]:
        """搜索知识库"""
        entries = self._load_knowledge_base()
        scored_results: list[tuple[int, KnowledgeEntry]] = []

        query_lower = query.lower()
        for entry in entries:
            score = 0
            if query_lower in entry["title"].lower():
                score += 10
            if query_lower in entry["content"].lower():
                score += 5
            for tag in entry.get("tags", []):
                if tag in query_lower:
                    score += 3

            if score > 0:
                scored_results.append(
                    (
                        score,
                        KnowledgeEntry(
                            id=entry["id"],
                            title=entry["title"],
                            content=entry["content"],
                            category=entry["category"],
                            tags=entry.get("tags", []),
                            created_at=entry.get("created_at", ""),
                            updated_at=entry.get("updated_at", ""),
                        ),
                    )
                )

        scored_results.sort(key=lambda x: x[0], reverse=True)
        return [r[1] for r in scored_results[:limit]]

    def answer_question(
        self,
        question: str,
        context: QAContext | None = None,
    ) -> QAResponse:
        """回答问题"""
        q_type = self.classify_question(question)
        knowledge = self.search_knowledge(question)

        answer = self._generate_answer(question, q_type, knowledge, context)
        confidence = self._calculate_confidence(question, knowledge)
        sources = [k.title for k in knowledge]
        related = self._generate_related_questions(q_type)
        suggestions = self._generate_suggestions(q_type, context)

        response = QAResponse(
            question=question,
            question_type=q_type,
            answer=answer,
            confidence=confidence,
            sources=sources,
            related_questions=related,
            suggestions=suggestions,
        )

        self._save_qa_history(response)
        return response

    def _generate_answer(
        self,
        question: str,
        q_type: QuestionType,
        knowledge: list[KnowledgeEntry],
        context: QAContext | None,
    ) -> str:
        """生成答案"""
        base_answer = knowledge[0].content if knowledge else self._get_default_answer(q_type)

        context_info = ""
        if context and context.user_holdings:
            context_info = f"\n\n根据您的持仓情况，共持有 {len(context.user_holdings)} 只股票。"

        return base_answer + context_info

    def _get_default_answer(self, q_type: QuestionType) -> str:
        """获取默认答案"""
        defaults = {
            QuestionType.MARKET_OUTLOOK: "建议关注宏观经济数据和政策变化，结合技术面分析市场趋势。",
            QuestionType.STOCK_ANALYSIS: "建议从基本面和技术面两个维度分析，关注公司财务状况和股价走势。",
            QuestionType.STRATEGY: "建议制定明确的交易计划，设置止盈止损位，严格执行纪律。",
            QuestionType.RISK_MANAGEMENT: "建议控制单笔交易风险在总资金的 2% 以内，设置止损位。",
            QuestionType.PORTFOLIO: "建议分散投资，单一股票仓位不超过 20%，保持适度现金。",
            QuestionType.TECHNICAL: "建议结合多个技术指标综合判断，避免单一指标决策。",
            QuestionType.FUNDAMENTAL: "建议关注 PE、ROE、营收增长等核心指标，对比行业平均水平。",
            QuestionType.GENERAL: "投资需要耐心和纪律，建议制定计划并严格执行。",
        }
        return defaults.get(q_type, "请提供更多细节，我可以给您更具体的建议。")

    def _calculate_confidence(
        self,
        question: str,
        knowledge: list[KnowledgeEntry],
    ) -> float:
        """计算置信度"""
        if not knowledge:
            return 0.5

        if len(knowledge) >= 2:
            return 0.9
        elif len(knowledge) == 1:
            return 0.75
        else:
            return 0.6

    def _generate_related_questions(self, q_type: QuestionType) -> list[str]:
        """生成相关问题"""
        related_map = {
            QuestionType.MARKET_OUTLOOK: [
                "当前市场处于什么阶段？",
                "如何判断市场底部？",
                "牛市和熊市有什么特征？",
            ],
            QuestionType.STOCK_ANALYSIS: [
                "如何选择优质股票？",
                "如何判断股票估值？",
                "如何分析公司财报？",
            ],
            QuestionType.STRATEGY: [
                "如何制定交易计划？",
                "如何设置止盈止损？",
                "如何控制交易频率？",
            ],
            QuestionType.RISK_MANAGEMENT: [
                "如何控制仓位？",
                "如何设置止损位？",
                "如何避免重大亏损？",
            ],
            QuestionType.PORTFOLIO: [
                "如何构建投资组合？",
                "如何进行资产配置？",
                "如何评估组合风险？",
            ],
            QuestionType.TECHNICAL: [
                "如何使用均线分析？",
                "如何判断买卖信号？",
                "如何识别趋势反转？",
            ],
            QuestionType.FUNDAMENTAL: [
                "如何分析公司盈利能力？",
                "如何判断公司成长性？",
                "如何评估公司价值？",
            ],
            QuestionType.GENERAL: [
                "新手如何开始投资？",
                "如何建立投资体系？",
                "如何提高投资收益？",
            ],
        }
        return related_map.get(q_type, [])

    def _generate_suggestions(
        self,
        q_type: QuestionType,
        context: QAContext | None,
    ) -> list[str]:
        """生成建议"""
        suggestions = []

        if q_type == QuestionType.RISK_MANAGEMENT:
            suggestions.append("建议设置止损位为 -8%")
            suggestions.append("单笔风险控制在总资金 2% 以内")

        if q_type == QuestionType.PORTFOLIO:
            suggestions.append("建议分散投资，单一股票不超过 20%")
            suggestions.append("保持 20% 以上现金应对机会")

        if context and context.user_holdings:
            suggestions.append("根据您的持仓，建议定期复盘")

        return suggestions

    def add_knowledge(self, entry: KnowledgeEntry) -> None:
        """添加知识条目"""
        entries = self._load_knowledge_base()
        entries.append(
            {
                "id": entry.id,
                "title": entry.title,
                "content": entry.content,
                "category": entry.category,
                "tags": entry.tags,
                "created_at": entry.created_at,
                "updated_at": entry.updated_at,
            }
        )

        write_json_cache(self.knowledge_base_file, entries)

    def _load_knowledge_base(self) -> list[dict[str, Any]]:
        """加载知识库"""
        data = read_json_cache(self.knowledge_base_file)
        return data if data else []

    def _save_qa_history(self, response: QAResponse) -> None:
        """保存问答历史"""
        history: list[dict[str, Any]] = read_json_cache(self.qa_history_file) or []

        history.append(
            {
                "question": response.question,
                "type": response.question_type.value,
                "answer": response.answer,
                "confidence": response.confidence,
                "timestamp": response.timestamp,
            }
        )

        if len(history) > 100:
            history = history[-100:]

        write_json_cache(self.qa_history_file, history)

    def get_qa_history(self, limit: int = 20) -> list[dict[str, Any]]:
        """获取问答历史"""
        history = read_json_cache(self.qa_history_file)
        if history:
            return history[-limit:]
        return []


ai_qa_engine = AIQAEngine()
