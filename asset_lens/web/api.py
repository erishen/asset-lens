"""
Web API for asset-lens.
Web API 服务 - 提供 REST API 接口

功能:
1. 投资组合分析 API
2. 股票查询 API
3. 策略管理 API
4. 报告生成 API

使用方法:
    uvicorn asset_lens.web.api:app --reload --port 8000
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..config import config

app = FastAPI(
    title="Asset Lens API",
    description="Personal Asset Operating System API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class StockQuote(BaseModel):
    """股票行情模型"""

    code: str
    name: str = ""
    current_price: float = 0
    change_percent: float = 0
    change_amount: float = 0
    volume: float = 0
    amount: float = 0
    high: float = 0
    low: float = 0
    open: float = 0
    prev_close: float = 0


class PortfolioSummary(BaseModel):
    """投资组合摘要模型"""

    total_assets: float = 0
    total_profit: float = 0
    total_return: float = 0
    position_count: int = 0


class StrategyInfo(BaseModel):
    """策略信息模型"""

    name: str
    description: str = ""
    buy_conditions: int = 0
    sell_conditions: int = 0
    position_size: float = 0
    max_positions: int = 0
    stop_loss: float = 0
    take_profit: float = 0


class HealthResponse(BaseModel):
    """健康检查响应"""

    status: str
    version: str
    timestamp: str


@app.get("/", response_model=Dict[str, str])
async def root():
    """API 根路径"""
    return {
        "name": "Asset Lens API",
        "version": "1.0.0",
        "description": "Personal Asset Operating System",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


@app.get("/api/stock/quote/{code}", response_model=StockQuote)
async def get_stock_quote(code: str):
    """
    获取股票行情

    Args:
        code: 股票代码（如 sh600519）
    """
    from ..data.multi_source_fetcher import multi_source_fetcher

    quote = multi_source_fetcher.fetch_stock_quote(code)

    if quote is None:
        raise HTTPException(status_code=404, detail=f"股票 {code} 不存在或获取失败")

    return StockQuote(**quote)


@app.get("/api/stock/search")
async def search_stocks(keyword: str = Query(..., description="搜索关键词")):
    """
    搜索股票

    Args:
        keyword: 搜索关键词
    """
    from ..data.stock_screener import stock_screener

    stocks = stock_screener._load_market_stocks()

    results = []
    for stock in stocks[:500]:
        code = stock.get("code", "")
        name = stock.get("name", "")

        if keyword.upper() in code.upper() or keyword in name:
            results.append(
                {
                    "code": code,
                    "name": name,
                    "market": stock.get("market", "A股"),
                }
            )

    return {"keyword": keyword, "count": len(results), "results": results[:20]}


@app.get("/api/portfolio/summary", response_model=PortfolioSummary)
async def get_portfolio_summary():
    """获取投资组合摘要"""
    from decimal import Decimal

    from ..data.csv_parser import CSVParser
    from ..data.models import Portfolio

    try:
        products = CSVParser.load_data()
        portfolio = Portfolio(
            products=products,
            usd_rate=Decimal(str(config.default_usd_rate)),
            hkd_rate=Decimal(str(config.default_hkd_rate)),
        )

        total_assets = sum(float(p.current_amount or 0) for p in portfolio.products)
        total_profit = sum(float(p.profit_amount or 0) for p in portfolio.products)
        total_return = (total_profit / total_assets * 100) if total_assets > 0 else 0

        return PortfolioSummary(
            total_assets=total_assets,
            total_profit=total_profit,
            total_return=total_return,
            position_count=len(portfolio.products),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/strategies", response_model=List[StrategyInfo])
async def list_strategies():
    """获取策略列表"""
    from ..data.strategy_engine import strategy_engine

    strategies = strategy_engine.list_strategies()

    return [
        StrategyInfo(
            name=s.get("name", ""),
            description=s.get("description", ""),
            buy_conditions=s.get("buy_conditions", 0),
            sell_conditions=s.get("sell_conditions", 0),
            position_size=s.get("position_size", 0),
            max_positions=s.get("max_positions", 0),
            stop_loss=s.get("stop_loss", 0),
            take_profit=s.get("take_profit", 0),
        )
        for s in strategies
    ]


@app.get("/api/strategies/{strategy_name}")
async def get_strategy(strategy_name: str):
    """获取策略详情"""
    from ..data.strategy_engine import strategy_engine

    strategy = strategy_engine.get_strategy(strategy_name)

    if strategy is None:
        raise HTTPException(status_code=404, detail=f"策略 {strategy_name} 不存在")

    return {
        "name": strategy.name,
        "description": strategy.description,
        "buy_conditions": [
            {"name": c.name, "weight": c.weight, "value": c.value} for c in strategy.buy_conditions
        ],
        "sell_conditions": [
            {"name": c.name, "weight": c.weight, "value": c.value} for c in strategy.sell_conditions
        ],
        "position_size": strategy.position_size,
        "max_positions": strategy.max_positions,
        "stop_loss": strategy.stop_loss,
        "take_profit": strategy.take_profit,
    }


@app.post("/api/strategies/{strategy_name}/evaluate/{code}")
async def evaluate_stock(strategy_name: str, code: str):
    """评估股票"""
    from ..data.multi_source_fetcher import multi_source_fetcher
    from ..data.strategy_engine import strategy_engine

    strategy = strategy_engine.get_strategy(strategy_name)
    if strategy is None:
        raise HTTPException(status_code=404, detail=f"策略 {strategy_name} 不存在")

    quote = multi_source_fetcher.fetch_stock_quote(code)
    if quote is None:
        raise HTTPException(status_code=404, detail=f"股票 {code} 不存在")

    evaluation = strategy_engine.evaluate_stock(quote, strategy_name)

    return {
        "strategy": strategy_name,
        "code": code,
        "match": evaluation.get("match", False),
        "score": evaluation.get("score", 0),
        "details": evaluation.get("details", {}),
    }


@app.get("/api/recommendations/stocks")
async def recommend_stocks(
    strategy_name: Optional[str] = None,
    max_stocks: int = Query(10, ge=1, le=50),
):
    """推荐股票"""
    from ..data.intelligent_recommender import intelligent_recommender

    recommendations = intelligent_recommender.recommend_stocks(
        strategy_name=strategy_name,
        max_stocks=max_stocks,
    )

    return {
        "strategy": strategy_name,
        "count": len(recommendations),
        "recommendations": [
            {
                "code": r.code,
                "name": r.name,
                "score": r.score,
                "reason": r.reason,
                "strategy_match": r.strategy_match,
                "risk_level": r.risk_level,
                "confidence": r.confidence,
            }
            for r in recommendations
        ],
    }


@app.get("/api/recommendations/strategies")
async def recommend_strategies(
    risk_preference: str = Query("moderate", description="风险偏好"),
    investment_period: str = Query("medium", description="投资周期"),
):
    """推荐策略"""
    from ..data.intelligent_recommender import intelligent_recommender

    recommendations = intelligent_recommender.recommend_strategy(
        risk_preference=risk_preference,
        investment_period=investment_period,
    )

    return {
        "risk_preference": risk_preference,
        "investment_period": investment_period,
        "count": len(recommendations),
        "recommendations": [
            {
                "strategy_name": r.strategy_name,
                "score": r.score,
                "reason": r.reason,
                "expected_return": r.expected_return,
                "risk_level": r.risk_level,
                "confidence": r.confidence,
            }
            for r in recommendations
        ],
    }


@app.get("/api/market/environment")
async def get_market_environment():
    """获取市场环境"""
    from ..data.market_environment import market_environment_analyzer

    env = market_environment_analyzer.analyze_environment()

    return {
        "market_type": env.market_type,
        "risk_level": env.risk_level,
        "sentiment": env.sentiment,
        "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


@app.get("/api/backup/status")
async def get_backup_status():
    """获取备份状态"""
    from ..data.backup_manager import backup_manager

    return backup_manager.get_backup_status()


@app.post("/api/backup/create")
async def create_backup():
    """创建备份"""
    from ..data.backup_manager import backup_manager

    result = backup_manager.create_backup()

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("errors", ["备份失败"]))

    return result


@app.get("/api/backup/list")
async def list_backups():
    """列出备份"""
    from ..data.backup_manager import backup_manager

    backups = backup_manager.list_backups()

    return {
        "count": len(backups),
        "backups": backups,
    }


@app.get("/api/data-sources/status")
async def get_data_sources_status():
    """获取数据源状态"""
    from ..data.multi_source_fetcher import multi_source_fetcher

    return multi_source_fetcher.get_source_status()


@app.get("/api/notification/config")
async def get_notification_config():
    """获取通知配置"""
    from ..data.notification_manager import notification_manager

    return {
        "email_enabled": notification_manager.config.email_enabled,
        "wechat_enabled": notification_manager.config.wechat_enabled,
    }


@app.get("/api/portfolio/items")
async def get_portfolio_items():
    """获取投资组合详情列表"""
    from decimal import Decimal

    from ..data.csv_parser import CSVParser
    from ..data.models import InvestmentType, Portfolio

    try:
        products = CSVParser.load_data()
        portfolio = Portfolio(
            products=products,
            usd_rate=Decimal(str(config.default_usd_rate)),
            hkd_rate=Decimal(str(config.default_hkd_rate)),
        )

        items = []
        for p in portfolio.products:
            if not p.start_date:
                continue

            current_amount = float(p.current_amount or 0)
            profit_amount = float(p.profit_amount or 0)
            profit_rate = float(p.return_rate or 0)

            type_name = p.investment_type.value if p.investment_type else "其他"
            type_map = {
                "stock": "A股",
                "fund": "基金",
                "bond": "债券",
                "cash": "现金",
                "us_stock": "美股",
                "hk_stock": "港股",
                "usd_fund": "QDII基金",
                "hk_dividend_fund": "港股基金",
                "hk_cash": "港币现金",
            }
            type_name = type_map.get(type_name, type_name)

            items.append(
                {
                    "name": p.name,
                    "type": type_name,
                    "current_amount": current_amount,
                    "profit": profit_amount,
                    "profit_rate": profit_rate,
                    "initial_amount": float(p.initial_amount or 0),
                }
            )

        return {"items": items}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/risk/summary")
async def get_risk_summary():
    """获取风险摘要"""
    from ..core.risk_manager import risk_manager

    try:
        summary = risk_manager.get_risk_summary()
        return summary
    except Exception as e:
        return {
            "risk_score": 50,
            "risk_level": "中等",
            "warnings": [],
        }


from pathlib import Path

from fastapi.staticfiles import StaticFiles

static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.get("/dashboard")
async def dashboard():
    """Dashboard 页面"""
    from fastapi.responses import FileResponse

    static_path = Path(__file__).parent / "static" / "index.html"
    if static_path.exists():
        return FileResponse(str(static_path))
    return {"error": "Dashboard not found"}
