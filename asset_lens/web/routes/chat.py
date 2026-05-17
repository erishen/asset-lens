"""
Chat API Router for Invest Assistant.
投资助手 API - 整合多个数据源
"""

import contextlib
import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """聊天请求"""

    message: str
    context: dict[str, Any] | None = None
    use_rag: bool = True
    use_signals: bool = False
    use_portfolio: bool = False
    fast_mode: bool = True  # 默认使用快速模式


class ChatResponse(BaseModel):
    """聊天响应"""

    response: str
    sources: list[str]
    confidence: float
    suggestions: list[str]
    related_questions: list[str]


class SignalsRequest(BaseModel):
    """信号请求"""

    signal_type: str | None = None
    min_score: int = 50
    limit: int = 10


class RAGRequest(BaseModel):
    """RAG 请求"""

    query: str
    k: int = 5


class RAGResponse(BaseModel):
    """RAG 响应"""

    results: list[dict[str, Any]]
    total: int


@router.post("/qa", response_model=ChatResponse)
async def chat_qa(request: ChatRequest):
    """
    投资问答

    整合 AI 问答引擎和 RAG 知识库
    """
    try:
        from pathlib import Path

        rag_results = []
        if request.use_rag:
            rag_results = await _query_rag(request.message)

        rag_context = ""
        if rag_results:
            rag_context = "\n\n**相关知识库内容:**\n"
            for r in rag_results[:3]:
                content = r.get("content", "")[:500]
                rag_context += f"- {content}\n"

        # 快速模式：直接使用后备答案
        if request.fast_mode:
            response_text = _generate_fallback_answer(request.message, rag_results)
        else:
            system_prompt = """你是一位专业的投资顾问，具有丰富的金融市场经验。

回答要求：
1. 简洁专业，不超过200字
2. 给出具体可操作的建议
3. 必须提醒相关风险
4. 避免模糊和空泛的回答
5. 如有知识库参考内容，优先基于知识库回答

回答格式：
- 先给出核心观点
- 再列出2-3个要点
- 最后提醒风险"""

            user_message = request.message
            if rag_context:
                user_message = f"{request.message}\n{rag_context}"

            Path(__file__).parent.parent.parent.parent.parent / "langchain-llm-toolkit"
            response_text = None

            try:
                import requests

                ollama_models = ["gemma4", "llama3", "qwen2.5", "deepseek-r1"]
                ollama_model = None

                try:
                    resp = requests.get("http://localhost:11434/api/tags", timeout=2)
                    if resp.status_code == 200:
                        models = resp.json().get("models", [])
                        model_names = [m.get("name", "").split(":")[0] for m in models]
                        for m in ollama_models:
                            if m in model_names:
                                ollama_model = m
                                break
                except Exception:
                    pass

                if ollama_model:
                    full_prompt = f"{system_prompt}\n\n用户问题: {user_message}"
                    resp = requests.post(
                        "http://localhost:11434/api/chat",
                        json={
                            "model": ollama_model,
                            "messages": [{"role": "user", "content": full_prompt}],
                            "stream": False,
                            "options": {"num_predict": 300, "temperature": 0.7},
                        },
                        timeout=45,
                    )
                    if resp.status_code == 200:
                        result = resp.json()
                        message = result.get("message", {})
                        response_text = message.get("content", "")
                        if not response_text:
                            thinking = message.get("thinking", "")
                            if thinking:
                                response_text = thinking
                        if not response_text:
                            logger.warning(f"Ollama returned empty response: {result}")
            except Exception as e:
                logger.warning(f"Ollama generation failed: {e}")

            if not response_text:
                response_text = _generate_fallback_answer(request.message, rag_results)

        suggestions = _generate_suggestions(request.message)
        related_questions = _generate_related_questions(request.message)

        return ChatResponse(
            response=response_text or "",
            sources=["RAG"] if rag_results else [],
            confidence=0.85 if rag_results else 0.7,
            suggestions=suggestions,
            related_questions=related_questions,
        )

    except Exception as e:
        logger.error(f"Chat QA error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


def _generate_suggestions(question: str) -> list[str]:
    """根据问题生成建议问题"""
    question_lower = question.lower()

    if "风险" in question_lower:
        return [
            "如何设置止损点？",
            "如何分散投资风险？",
            "什么是仓位管理？",
        ]
    elif "止损" in question_lower:
        return [
            "止损后如何重新入场？",
            "如何避免频繁止损？",
            "止损比例设置多少合适？",
        ]
    elif "趋势" in question_lower or "市场" in question_lower:
        return [
            "如何判断市场顶部和底部？",
            "当前市场适合入场吗？",
            "如何利用均线判断趋势？",
        ]
    elif "仓位" in question_lower or "配置" in question_lower:
        return [
            "如何动态调整仓位？",
            "不同市场环境如何配置？",
            "仓位和止损如何配合？",
        ]
    elif "止盈" in question_lower:
        return [
            "止盈后如何再入场？",
            "如何设置移动止盈？",
            "止盈和止损如何平衡？",
        ]
    else:
        return [
            "如何控制投资风险？",
            "当前市场趋势如何？",
            "如何制定投资计划？",
        ]


def _generate_related_questions(question: str) -> list[str]:
    """生成相关问题"""
    question_lower = question.lower()

    if "风险" in question_lower:
        return ["什么是系统性风险？", "如何应对黑天鹅事件？"]
    elif "止损" in question_lower:
        return ["止损后心态如何调整？", "如何避免止损后踏空？"]
    elif "趋势" in question_lower:
        return ["趋势反转信号有哪些？", "如何确认趋势形成？"]
    elif "仓位" in question_lower:
        return ["满仓有什么风险？", "空仓策略何时使用？"]
    else:
        return ["什么时候应该止损？", "如何选择投资标的？"]


def _generate_fallback_answer(question: str, rag_results: list) -> str:
    """生成后备答案"""
    if rag_results:
        sources = set()
        contents = []
        for r in rag_results[:3]:
            content = r.get("content", "")[:400]
            source = r.get("source", "") or r.get("category", "")
            if source:
                sources.add(source)
            if content and content not in contents:
                contents.append(content)

        answer = "📚 **根据知识库检索结果：**\n\n"
        for _i, content in enumerate(contents[:2], 1):
            answer += f"{content}\n\n"

        if sources:
            answer += f"📖 **参考来源：** {', '.join(list(sources)[:3])}\n\n"

        answer += "💡 如需更详细分析，可切换到 AI 模式获取深度解读。"
        return answer

    question_lower = question.lower()
    if "风险" in question_lower:
        return "⚠️ **投资风险管理的关键原则：**\n\n1. **分散投资**：不要把所有资金投入单一标的\n2. **设置止损**：每笔交易设置明确的止损点\n3. **控制仓位**：单笔投资不超过总资金的 10-20%\n4. **保持现金**：预留 20-30% 现金应对机会\n\n📌 **风险提示：** 投资有风险，入市需谨慎。"
    elif "趋势" in question_lower or "市场" in question_lower:
        return "📈 **判断市场趋势的方法：**\n\n1. **技术面**：关注均线系统、成交量变化\n2. **基本面**：关注宏观经济、政策变化\n3. **情绪面**：关注市场情绪指标\n\n📌 **建议：** 综合多个维度判断，避免单一指标决策。"
    elif "止损" in question_lower:
        return "🛡️ **止损策略建议：**\n\n1. **固定比例止损**：设置 5-10% 的止损线\n2. **技术止损**：跌破支撑位或均线时止损\n3. **时间止损**：持仓超过一定时间无突破则止损\n\n📌 **重要：** 止损是保护本金的重要手段，建议严格执行。"
    elif "仓位" in question_lower or "配置" in question_lower:
        return "💰 **仓位管理建议：**\n\n1. **金字塔建仓**：越跌越买，分批建仓\n2. **倒金字塔减仓**：越涨越卖，分批止盈\n3. **动态平衡**：定期调整各品种仓位比例\n\n📌 **原则：** 永不满仓，保持灵活。"
    elif "止盈" in question_lower:
        return "🎯 **止盈策略建议：**\n\n1. **目标止盈**：达到预期收益即卖出\n2. **移动止盈**：随价格上涨上移止盈点\n3. **分批止盈**：分多次卖出锁定利润\n\n📌 **提醒：** 会买的是徒弟，会卖的是师傅。"
    else:
        return f"💡 **关于「{question}」的建议：**\n\n1. 结合自身风险承受能力\n2. 做好充分的研究和分析\n3. 制定明确的投资计划\n4. 严格执行纪律\n\n📌 如需更具体的建议，请提供更多背景信息或切换到 AI 模式。"


@router.get("/portfolio")
async def get_portfolio_analysis():
    """
    获取投资组合分析

    整合 asset-lens 投资数据
    """
    try:
        from pathlib import Path

        from asset_lens.core.ai_analyzer import ai_analyzer
        from asset_lens.data.csv_parser import CSVParser

        data_dir = Path(__file__).parent.parent.parent.parent / "data"
        csv_file = data_dir / "投资产品.csv"

        if not csv_file.exists():
            csv_file = data_dir / "sample_data" / "投资产品-脱敏.csv"

        if not csv_file.exists():
            return {
                "success": True,
                "summary": "投资组合数据文件不存在，请先导入数据",
                "risk_assessment": "暂无风险评估",
                "suggestions": ["请导入投资产品数据"],
                "warnings": [],
                "score": 0,
            }

        parser = CSVParser
        products = parser.parse_csv_file(csv_file)

        if not products:
            return {
                "success": True,
                "summary": "暂无投资产品数据",
                "risk_assessment": "暂无风险评估",
                "suggestions": ["请添加投资产品"],
                "warnings": [],
                "score": 0,
            }

        total_value = sum(float(p.current_amount or 0) for p in products)
        total_cost = sum(float(p.initial_amount or 0) for p in products)
        total_profit = total_value - total_cost
        profit_rate = (total_profit / total_cost * 100) if total_cost > 0 else 0

        portfolio_data: dict[str, Any] = {
            "total_value": total_value,
            "total_profit": total_profit,
            "overall_return_rate": round(profit_rate, 2),
            "total_products": len(products),
            "risk_distribution": {},
            "type_distribution": {},
            "products": [
                {
                    "name": p.name,
                    "current_amount": float(p.current_amount or 0),
                    "profit_amount": float(p.current_amount or 0) - float(p.initial_amount or 0),
                    "return_rate": (
                        (float(p.current_amount or 0) - float(p.initial_amount or 0))
                        / float(p.initial_amount or 1)
                        * 100
                    )
                    if p.initial_amount
                    else 0,
                }
                for p in products[:20]
            ],
        }

        analysis = ai_analyzer.analyze_portfolio(portfolio_data)

        return {
            "success": True,
            "summary": analysis.summary,
            "risk_assessment": analysis.risk_assessment,
            "suggestions": analysis.suggestions,
            "warnings": analysis.warnings,
            "score": analysis.score,
        }

    except Exception as e:
        logger.error(f"Portfolio analysis error: {e}")
        return {
            "success": False,
            "error": str(e),
            "summary": f"分析失败: {e!s}",
            "risk_assessment": "",
            "suggestions": [],
            "warnings": [],
            "score": 0,
        }


@router.post("/signals")
async def get_signals(request: SignalsRequest):
    """
    获取技术信号

    整合 stock-analyzer 信号扫描
    """
    try:
        import sys
        from pathlib import Path

        stock_analyzer_path = Path(__file__).parent.parent.parent.parent.parent / "stock-analyzer"

        if not stock_analyzer_path.exists():
            return {"success": False, "error": "stock-analyzer 目录不存在", "signals": []}

        src_path = stock_analyzer_path / "src"
        if not src_path.exists():
            return {"success": False, "error": "stock-analyzer/src 目录不存在", "signals": []}

        sys.path.insert(0, str(src_path))

        try:
            from scanner import SignalType, run_scan
        except ImportError as e:
            return {"success": False, "error": f"无法导入 scanner 模块: {e}", "signals": []}

        db_path = stock_analyzer_path / "data" / "stock_analysis.db"
        if not db_path.exists():
            return {"success": False, "error": "stock-analyzer 数据库不存在，请先运行 ETL", "signals": []}

        signal_type = None
        if request.signal_type:
            with contextlib.suppress(ValueError):
                signal_type = SignalType(request.signal_type)

        result = run_scan(
            db_path=db_path,
            signal_type=signal_type,
            min_score=request.min_score,
        )

        signals = [
            {
                "code": s.code,
                "name": s.name or s.code,
                "signal_type": s.signal_type.value,
                "strength": s.strength.value,
                "score": s.score,
                "price": s.price,
                "change_percent": s.change_percent,
                "date": s.date,
            }
            for s in result.top_signals[: request.limit]
        ]

        return {
            "success": True,
            "total_stocks": result.total_stocks,
            "signals_found": result.signals_found,
            "signals": signals,
            "summary": result.summary,
        }

    except Exception as e:
        logger.error(f"Signals error: {e}")
        return {"success": False, "error": str(e), "signals": []}


@router.get("/timing")
async def get_market_timing():
    """
    获取大盘择时

    整合 stock-analyzer 大盘择时
    """
    try:
        import sys
        from pathlib import Path

        stock_analyzer_path = Path(__file__).parent.parent.parent.parent.parent / "stock-analyzer"

        if not stock_analyzer_path.exists():
            return {"success": False, "error": "stock-analyzer 目录不存在"}

        src_path = stock_analyzer_path / "src"
        if not src_path.exists():
            return {"success": False, "error": "stock-analyzer/src 目录不存在"}

        sys.path.insert(0, str(src_path))

        try:
            from strategy import run_market_timing
        except ImportError as e:
            return {"success": False, "error": f"无法导入 strategy 模块: {e}"}

        db_path = stock_analyzer_path / "data" / "stock_analysis.db"
        if not db_path.exists():
            return {"success": False, "error": "stock-analyzer 数据库不存在，请先运行 ETL"}

        result = run_market_timing(db_path)

        return {
            "success": True,
            "state": result.state.value,
            "score": result.score,
            "position_advice": result.signal,
            "indicators": {
                "ma_trend": {"value": result.ma_trend, "signal": result.ma_trend},
                "rsi_level": {"value": result.rsi_level, "signal": result.rsi_level},
                "volatility": {"value": result.volatility, "signal": result.volatility},
                "breadth": {"value": result.breadth, "signal": "市场宽度"},
            },
        }

    except Exception as e:
        logger.error(f"Market timing error: {e}")
        return {"success": False, "error": str(e)}


@router.post("/rag", response_model=RAGResponse)
async def query_rag(request: RAGRequest):
    """
    RAG 知识库查询

    整合 langchain-llm-toolkit RAG 系统
    """
    try:
        results = await _query_rag(request.query, request.k)
        return RAGResponse(results=results, total=len(results))

    except Exception as e:
        logger.error(f"RAG query error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


async def _query_rag(query: str, k: int = 5) -> list[dict[str, Any]]:
    """查询 RAG 知识库"""
    try:
        import os
        import sys
        from pathlib import Path

        rag_path = Path(__file__).parent.parent.parent.parent.parent / "langchain-llm-toolkit"
        if not rag_path.exists():
            return []

        sys_path = rag_path / "src"
        sys.path.insert(0, str(sys_path))

        try:
            from langchain_llm_toolkit import RAGSystem
        except ImportError:
            return []

        qdrant_path = os.getenv("QDRANT_PATH", str(rag_path / "qdrant_storage"))
        collection = os.getenv("QDRANT_COLLECTION", "langchain_documents")

        rag_system = RAGSystem(
            vector_store_type="qdrant",
            embedding_type="ollama",
            embedding_model="snowflake-arctic-embed2",
            llm_model="ollama/gemma4",
            qdrant_persist_dir=qdrant_path,
            collection_name=collection,
        )

        rag_system.load_vector_store(qdrant_path)
        documents = rag_system.retrieve_documents(query, k=k)

        results = [
            {
                "content": doc.page_content,
                "title": doc.metadata.get("title", ""),
                "source": doc.metadata.get("source", ""),
                "category": doc.metadata.get("category", ""),
            }
            for doc in documents
        ]

        return results

    except Exception as e:
        logger.warning(f"RAG query failed: {e}")
        return []


@router.get("/config")
async def get_config():
    """
    获取配置信息

    整合 lobster 配置
    """
    try:
        import json
        from pathlib import Path

        config_files = {
            "asset_lens": Path(__file__).parent.parent.parent.parent / "config" / "asset_lens.yaml",
            "lobster": Path.home() / ".lobster" / "config.json",
        }

        configs = {}
        for name, path in config_files.items():
            if path.exists():
                try:
                    if path.suffix == ".json":
                        with open(path) as f:
                            configs[name] = json.load(f)
                    else:
                        configs[name] = {"path": str(path), "exists": True}
                except Exception:
                    configs[name] = {"error": "读取失败"}

        return {
            "success": True,
            "configs": configs,
            "services": {
                "asset_lens": "http://localhost:8000",
                "stock_analyzer": "http://localhost:8001",
                "ollama": "http://localhost:11434",
            },
        }

    except Exception as e:
        logger.error(f"Config error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
