"""
Web API for asset-lens.
Web API 服务 - 提供 REST API 接口

功能:
1. 投资组合分析 API
2. 股票查询 API
3. 策略管理 API
4. 报告生成 API
5. WebSocket 实时数据推送

使用方法:
    uvicorn asset_lens.web.api:app --reload --port 8000
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
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

from .routes import compare_router, risk_router, system_router

app.include_router(compare_router)
app.include_router(risk_router)
app.include_router(system_router)


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
    获取股票行情 - 使用新浪财经接口

    Args:
        code: 股票代码（如 sh600519）
    """
    import requests

    try:
        from ..utils.http_client import safe_get
        
        url = f"http://hq.sinajs.cn/list={code}"
        headers = {
            "Referer": "http://finance.sina.com.cn",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
        response = safe_get(url, headers=headers, timeout=10)

        if response is None:
            raise HTTPException(status_code=503, detail="服务暂时不可用，请稍后重试")

        if response.status_code == 200:
            content = response.text
            pattern = f'var hq_str_{code}="'
            start = content.find(pattern)

            if start == -1:
                raise HTTPException(status_code=404, detail=f"股票 {code} 不存在")

            start += len(pattern)
            end = content.find('";', start)
            data_str = content[start:end]

            if not data_str:
                raise HTTPException(status_code=404, detail=f"股票 {code} 数据为空")

            parts = data_str.split(",")
            if len(parts) >= 32:
                name = parts[0]
                open_price = float(parts[1]) if parts[1] else 0
                prev_close = float(parts[2]) if parts[2] else 0
                current_price = float(parts[3]) if parts[3] else 0
                high = float(parts[4]) if parts[4] else 0
                low = float(parts[5]) if parts[5] else 0
                volume = float(parts[8]) if parts[8] else 0
                amount = float(parts[9]) if parts[9] else 0

                change_amount = current_price - prev_close if prev_close > 0 else 0
                change_percent = (change_amount / prev_close * 100) if prev_close > 0 else 0

                return StockQuote(
                    code=code,
                    name=name,
                    current_price=current_price,
                    change_percent=change_percent,
                    change_amount=change_amount,
                    volume=int(volume),
                    amount=amount,
                    high=high,
                    low=low,
                    open=open_price,
                    prev_close=prev_close,
                )

        raise HTTPException(status_code=404, detail=f"股票 {code} 获取失败")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取股票行情失败: {str(e)}")


@app.get("/api/stock/search")
async def search_stocks(keyword: str = Query(..., description="搜索关键词")):
    """
    搜索股票

    Args:
        keyword: 搜索关键词
    """
    from ..strategy.screener import stock_screener

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
    from ..strategy.engine import strategy_engine

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
    from ..strategy.engine import strategy_engine

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
    from ..strategy.engine import strategy_engine

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


@app.get("/api/market/indexes")
async def get_market_indexes():
    """获取市场指数数据 - 使用新浪财经接口"""
    import requests

    domestic_indexes = [
        ("sh000001", "上证指数"),
        ("sz399001", "深证成指"),
        ("sz399006", "创业板指"),
        ("sh000300", "沪深300"),
        ("sh000016", "上证50"),
        ("sz399005", "中小板指"),
    ]

    indexes = []

    try:
        codes = ",".join([code for code, _ in domestic_indexes])
        url = f"http://hq.sinajs.cn/list={codes}"
        headers = {
            "Referer": "http://finance.sina.com.cn",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            content = response.text

            for code, name in domestic_indexes:
                try:
                    pattern = f'var hq_str_{code}="'
                    start = content.find(pattern)
                    if start == -1:
                        indexes.append({
                            "code": code,
                            "name": name,
                            "price": 0,
                            "change": 0,
                            "changePercent": 0,
                            "error": "数据未找到",
                        })
                        continue

                    start += len(pattern)
                    end = content.find('";', start)
                    data_str = content[start:end]

                    if not data_str:
                        indexes.append({
                            "code": code,
                            "name": name,
                            "price": 0,
                            "change": 0,
                            "changePercent": 0,
                            "error": "数据为空",
                        })
                        continue

                    parts = data_str.split(",")
                    if len(parts) >= 32:
                        index_name = parts[0]
                        open_price = float(parts[1]) if parts[1] else 0
                        prev_close = float(parts[2]) if parts[2] else 0
                        current_price = float(parts[3]) if parts[3] else 0
                        high = float(parts[4]) if parts[4] else 0
                        low = float(parts[5]) if parts[5] else 0
                        volume = float(parts[8]) if parts[8] else 0
                        amount = float(parts[9]) if parts[9] else 0

                        change = current_price - prev_close if prev_close > 0 else 0
                        change_percent = (change / prev_close * 100) if prev_close > 0 else 0

                        indexes.append({
                            "code": code,
                            "name": index_name or name,
                            "price": current_price,
                            "change": change,
                            "changePercent": change_percent,
                            "open": open_price,
                            "prev_close": prev_close,
                            "high": high,
                            "low": low,
                            "volume": int(volume),
                            "amount": amount,
                        })
                    else:
                        indexes.append({
                            "code": code,
                            "name": name,
                            "price": 0,
                            "change": 0,
                            "changePercent": 0,
                            "error": "数据格式错误",
                        })

                except Exception as e:
                    indexes.append({
                        "code": code,
                        "name": name,
                        "price": 0,
                        "change": 0,
                        "changePercent": 0,
                        "error": str(e),
                    })

        else:
            for code, name in domestic_indexes:
                indexes.append({
                    "code": code,
                    "name": name,
                    "price": 0,
                    "change": 0,
                    "changePercent": 0,
                    "error": f"HTTP {response.status_code}",
                })

    except Exception as e:
        for code, name in domestic_indexes:
            indexes.append({
                "code": code,
                "name": name,
                "price": 0,
                "change": 0,
                "changePercent": 0,
                "error": str(e),
            })

    return {
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "indexes": indexes,
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
                    "annual_return": float(p.annual_return or 0),
                    "initial_amount": float(p.initial_amount or 0),
                }
            )

        return {"items": items}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/risk/summary")
async def get_risk_summary():
    """获取风险摘要"""
    from ..risk import risk_service

    try:
        summary = risk_service.get_risk_summary()
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


@app.get("/api/stock/kline/{code}")
async def get_stock_kline(
    code: str,
    period: str = Query("daily", description="周期: daily, weekly, monthly"),
    count: int = Query(60, description="数据条数"),
):
    """
    获取股票 K 线数据

    Args:
        code: 股票代码（如 sh600519）
        period: 周期
        count: 数据条数
    """
    import requests

    try:
        # 使用新浪财经历史数据接口
        # scale: 5=5分钟, 15=15分钟, 30=30分钟, 60=60分钟, 240=日K
        url = "http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"

        if period == "daily":
            scale = "240"
        elif period == "weekly":
            # 新浪周K不支持，使用腾讯API
            return await _get_kline_tencent(code, "week", count)
        elif period == "monthly":
            # 新浪月K不支持，使用腾讯API
            return await _get_kline_tencent(code, "month", count)
        else:
            scale = "240"

        params: Dict[str, Any] = {
            "symbol": code,
            "scale": scale,
            "ma": "no",
            "datalen": count,
        }
        headers = {
            "Referer": "http://finance.sina.com.cn",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
        response = requests.get(url, params=params, headers=headers, timeout=15)

        if response.status_code == 200:
            data = response.json()
            if data and isinstance(data, list):
                kline_data: List[Dict[str, Any]] = []
                for item in data:
                    kline_data.append({
                        "date": item.get("day", ""),
                        "open": float(item.get("open", 0)),
                        "close": float(item.get("close", 0)),
                        "high": float(item.get("high", 0)),
                        "low": float(item.get("low", 0)),
                        "volume": float(item.get("volume", 0)),
                    })
                return {"code": code, "period": period, "count": len(kline_data), "data": kline_data}

        return {"code": code, "period": period, "count": 0, "data": [], "error": "获取数据失败"}

    except Exception as e:
        return {"code": code, "period": period, "count": 0, "data": [], "error": str(e)}


async def _get_kline_tencent(code: str, ktype: str, count: int):
    """使用腾讯API获取周K/月K数据"""
    import requests
    import json

    try:
        # 腾讯K线API
        # ktype: day, week, month
        url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
        params = {
            "param": f"{code},{ktype},,,{count},qfq",
        }
        headers = {
            "Referer": "https://gu.qq.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
        response = requests.get(url, params=params, headers=headers, timeout=15)

        if response.status_code == 200:
            data = response.json()
            stock_data = data.get("data", {}).get(code, {})
            # 周K在 qfqweek，月K在 qfqmonth
            key = f"qfq{ktype}"
            kline_list = stock_data.get(key, [])
            
            if kline_list:
                kline_data = []
                for item in kline_list:
                    # 跳过分红信息（dict类型）
                    if isinstance(item, dict):
                        continue
                    kline_data.append({
                        "date": item[0] if len(item) > 0 else "",
                        "open": float(item[1]) if len(item) > 1 else 0,
                        "close": float(item[2]) if len(item) > 2 else 0,
                        "high": float(item[3]) if len(item) > 3 else 0,
                        "low": float(item[4]) if len(item) > 4 else 0,
                        "volume": float(item[5]) if len(item) > 5 else 0,
                    })
                period_map = {"day": "daily", "week": "weekly", "month": "monthly"}
                return {"code": code, "period": period_map.get(ktype, ktype), "count": len(kline_data), "data": kline_data}

        period_map = {"day": "daily", "week": "weekly", "month": "monthly"}
        return {"code": code, "period": period_map.get(ktype, ktype), "count": 0, "data": [], "error": "获取数据失败"}

    except Exception as e:
        period_map = {"day": "daily", "week": "weekly", "month": "monthly"}
        return {"code": code, "period": period_map.get(ktype, ktype), "count": 0, "data": [], "error": str(e)}


@app.get("/api/portfolio/performance")
async def get_portfolio_performance():
    """获取投资组合历史收益曲线数据"""
    from ..data.csv_parser import CSVParser
    from ..config import config

    try:
        # 使用 config 中的 data_path
        data_path = config.data_path
        
        # 查找 money_csv_* 子目录
        data_dirs = sorted([d for d in data_path.iterdir() if d.is_dir() and d.name.startswith("money_csv_")])
        if not data_dirs:
            return {"error": f"未找到数据目录，请检查 {data_path}"}
        
        # 使用最新的数据目录
        data_dir = data_dirs[-1]
        products = CSVParser.load_data_from_dir(data_dir)

        # 按类型汇总收益
        type_performance: Dict[str, List[Dict]] = {}
        total_initial: float = 0.0
        total_current: float = 0.0

        for product in products:
            # InvestmentType 枚举的 value 已经是中文名称
            ptype = product.investment_type.value if hasattr(product, 'investment_type') and product.investment_type else "其他"
            
            if ptype not in type_performance:
                type_performance[ptype] = []

            type_performance[ptype].append({
                "name": product.name,
                "initial": float(product.initial_amount or 0),
                "current": float(product.current_amount or 0),
                "profit": float(product.profit_amount or 0),
                "return_rate": float(product.return_rate or 0),
            })

            total_initial += float(product.initial_amount or 0)
            total_current += float(product.current_amount or 0)

        # 计算各类型汇总
        type_summary = []
        for ptype, items in type_performance.items():
            type_initial = sum(i["initial"] for i in items)
            type_current = sum(i["current"] for i in items)
            type_profit = sum(i["profit"] for i in items)
            type_return = (type_profit / type_initial * 100) if type_initial > 0 else 0

            type_summary.append({
                "type": ptype,
                "count": len(items),
                "initial": type_initial,
                "current": type_current,
                "profit": type_profit,
                "return_rate": type_return,
            })

        # 模拟历史收益曲线（基于当前数据推算）
        import random
        from datetime import datetime, timedelta

        history = []
        base_value = total_initial
        total_return_rate = ((total_current - total_initial) / total_initial * 100) if total_initial > 0 else 0

        for i in range(30):
            date = (datetime.now() - timedelta(days=29 - i)).strftime("%Y-%m-%d")
            # 模拟波动
            progress = i / 29
            simulated_return = total_return_rate * progress * (0.8 + random.random() * 0.4)
            simulated_value = base_value * (1 + simulated_return / 100)

            history.append({
                "date": date,
                "value": round(simulated_value, 2),
                "return_rate": round(simulated_return, 2),
            })

        return {
            "total_initial": total_initial,
            "total_current": total_current,
            "total_profit": total_current - total_initial,
            "total_return_rate": ((total_current - total_initial) / total_initial * 100) if total_initial > 0 else 0,
            "type_summary": type_summary,
            "history": history,
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    except Exception as e:
        return {"error": str(e)}


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass


manager = ConnectionManager()


@app.websocket("/ws/market")
async def websocket_market(websocket: WebSocket):
    """
    WebSocket 实时市场数据推送
    
    推送内容:
    - 市场指数实时数据
    - 股票池实时行情
    """
    await manager.connect(websocket)
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                action = message.get("action", "")
                
                if action == "subscribe":
                    # 订阅特定股票
                    codes = message.get("codes", [])
                    await websocket.send_json({
                        "type": "subscribed",
                        "codes": codes,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                
                elif action == "ping":
                    # 心跳检测
                    await websocket.send_json({"type": "pong"})
                
                elif action == "get_market_indexes":
                    # 获取市场指数
                    indexes = await _get_market_indexes()
                    await websocket.send_json({
                        "type": "market_indexes",
                        "data": indexes,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                
                elif action == "get_stock_quotes":
                    # 获取股票行情
                    codes = message.get("codes", [])
                    quotes = await _get_stock_quotes(codes)
                    await websocket.send_json({
                        "type": "stock_quotes",
                        "data": quotes,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def _get_market_indexes():
    """获取市场指数数据"""
    import requests
    
    indexes = []
    index_codes = [
        ("sh000001", "上证指数"),
        ("sz399001", "深证成指"),
        ("sz399006", "创业板指"),
        ("sh000300", "沪深300"),
        ("sh000016", "上证50"),
    ]
    
    for code, name in index_codes:
        try:
            url = f"http://hq.sinajs.cn/list={code}"
            headers = {
                "Referer": "http://finance.sina.com.cn",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                content = response.text
                pattern = f'var hq_str_{code}="'
                start = content.find(pattern)
                
                if start != -1:
                    start += len(pattern)
                    end = content.find('";', start)
                    data_str = content[start:end]
                    parts = data_str.split(",")
                    
                    if len(parts) >= 32:
                        indexes.append({
                            "code": code,
                            "name": name,
                            "price": float(parts[3]) if parts[3] else 0,
                            "change": float(parts[3]) - float(parts[2]) if parts[3] and parts[2] else 0,
                            "changePercent": ((float(parts[3]) - float(parts[2])) / float(parts[2]) * 100) if parts[2] and parts[3] else 0,
                        })
        except Exception:
            pass
    
    return indexes


async def _get_stock_quotes(codes: List[str]):
    """获取股票行情数据"""
    import requests
    
    quotes = []
    for code in codes[:10]:  # 限制最多10只
        try:
            url = f"http://hq.sinajs.cn/list={code}"
            headers = {
                "Referer": "http://finance.sina.com.cn",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                content = response.text
                pattern = f'var hq_str_{code}="'
                start = content.find(pattern)
                
                if start != -1:
                    start += len(pattern)
                    end = content.find('";', start)
                    data_str = content[start:end]
                    parts = data_str.split(",")
                    
                    if len(parts) >= 32:
                        current_price = float(parts[3]) if parts[3] else 0
                        prev_close = float(parts[2]) if parts[2] else 0
                        change_percent = ((current_price - prev_close) / prev_close * 100) if prev_close > 0 else 0
                        
                        quotes.append({
                            "code": code,
                            "name": parts[0],
                            "current_price": current_price,
                            "change_percent": change_percent,
                            "volume": float(parts[8]) if parts[8] else 0,
                            "amount": float(parts[9]) if parts[9] else 0,
                        })
        except Exception:
            pass
    
    return quotes


@app.get("/api/realtime/status")
async def get_realtime_status():
    """获取实时推送服务状态"""
    return {
        "websocket_connections": len(manager.active_connections),
        "status": "running",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


@app.get("/api/stock-pool")
async def get_stock_pool():
    """获取股票池数据"""
    from ..trading.stock_pool import StockPool
    from ..config import config

    try:
        pool_path = config.cache_path / "stock_pools"
        
        if not pool_path.exists():
            return {
                "stocks": [],
                "count": 0,
                "message": "股票池为空，请先运行策略选股"
            }

        # 只读取正式的股票池文件，排除测试文件
        pool_files = [
            f for f in pool_path.glob("*_pool.json")
            if not f.name.startswith("test_")
        ]
        
        if not pool_files:
            return {
                "stocks": [],
                "count": 0,
                "message": "股票池为空"
            }

        all_stocks: Dict[str, dict] = {}
        pool_info: Dict[str, dict] = {}
        
        for pool_file in pool_files:
            pool = StockPool(pool_file.stem.replace("_pool", ""))
            
            # 获取策略信息
            strategy_name = pool.pool_name
            min_score = 60.0
            update_time = ""
            
            if hasattr(pool, 'config') and pool.config:
                if hasattr(pool.config, 'strategy_name'):
                    strategy_name = pool.config.strategy_name
                if hasattr(pool.config, 'min_score'):
                    min_score = pool.config.min_score
            
            if hasattr(pool, 'update_time'):
                update_time = pool.update_time
            
            pool_info[pool.pool_name] = {
                "name": pool.pool_name,
                "strategy_name": strategy_name,
                "min_score": min_score,
                "update_time": update_time,
            }
            
            for code, position in pool.positions.items():
                # 过滤掉北交所股票（代码以 sh92 或 bj 开头）
                if code.startswith("sh92") or code.startswith("bj"):
                    continue
                    
                if position.status in ["watching", "holding"]:
                    if code in all_stocks:
                        all_stocks[code]["selected_count"] += position.selected_count
                        all_stocks[code]["max_profit_rate"] = max(
                            all_stocks[code]["max_profit_rate"], position.max_profit_rate
                        )
                        all_stocks[code]["min_profit_rate"] = min(
                            all_stocks[code]["min_profit_rate"], position.min_profit_rate
                        )
                        all_stocks[code]["strategies"].append(strategy_name)
                    else:
                        all_stocks[code] = {
                            "code": position.code,
                            "name": position.name,
                            "buy_price": position.buy_price,
                            "current_price": position.current_price,
                            "buy_date": position.buy_date,
                            "status": position.status,
                            "profit_rate": ((position.current_price - position.buy_price) / position.buy_price * 100) if position.buy_price > 0 else 0,
                            "selected_count": position.selected_count,
                            "max_profit_rate": position.max_profit_rate,
                            "min_profit_rate": position.min_profit_rate,
                            "strategies": [strategy_name],
                        }

        stocks_list = sorted(all_stocks.values(), key=lambda x: x.get("selected_count", 0), reverse=True)

        return {
            "stocks": stocks_list,
            "count": len(stocks_list),
            "pools": pool_info,
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    except Exception as e:
        return {"stocks": [], "count": 0, "error": str(e)}


@app.get("/api/report/export")
async def export_report():
    """导出投资报告 HTML"""
    from fastapi.responses import Response
    from ..data.csv_parser import CSVParser

    try:
        products = CSVParser.load_data()

        total_assets = sum(float(p.current_amount or 0) for p in products)
        total_initial = sum(float(p.initial_amount or 0) for p in products)
        total_profit = total_assets - total_initial
        total_return = (total_profit / total_initial * 100) if total_initial > 0 else 0

        rows_html = ""
        for p in products[:50]:
            profit = float(getattr(p, 'profit', 0) or 0)
            profit_rate = float(getattr(p, 'return_rate', 0) or 0)
            profit_class = "positive" if profit >= 0 else "negative"
            ptype = getattr(p, 'investment_type', None)
            ptype_str = ptype.value if ptype else "其他"
            rows_html += f"""
                <tr>
                    <td>{p.name}</td>
                    <td>{ptype_str}</td>
                    <td>{float(p.current_amount or 0):,.2f} CNY</td>
                    <td class="{profit_class}">{profit:,.2f} CNY</td>
                    <td class="{profit_class}">{profit_rate:.2f}%</td>
                </tr>"""

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Investment Report - Asset Lens</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #333; border-bottom: 2px solid #00d2ff; padding-bottom: 10px; }}
                h2 {{ color: #666; margin-top: 30px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background: #f5f5f5; }}
                .positive {{ color: #00c853; }}
                .negative {{ color: #ff5252; }}
                .summary {{ background: #f9f9f9; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .summary-item {{ display: inline-block; margin-right: 40px; }}
                .summary-label {{ color: #888; font-size: 14px; }}
                .summary-value {{ font-size: 24px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>Asset Lens Investment Report</h1>
            <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>

            <div class="summary">
                <div class="summary-item">
                    <div class="summary-label">Total Assets</div>
                    <div class="summary-value">{total_assets:,.2f} CNY</div>
                </div>
                <div class="summary-item">
                    <div class="summary-label">Total Profit</div>
                    <div class="summary-value {'positive' if total_profit >= 0 else 'negative'}">
                        {total_profit:,.2f} CNY
                    </div>
                </div>
                <div class="summary-item">
                    <div class="summary-label">Return Rate</div>
                    <div class="summary-value {'positive' if total_return >= 0 else 'negative'}">
                        {total_return:.2f}%
                    </div>
                </div>
                <div class="summary-item">
                    <div class="summary-label">Positions</div>
                    <div class="summary-value">{len(products)}</div>
                </div>
            </div>

            <h2>Holdings Detail</h2>
            <table>
                <tr>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Current Value</th>
                    <th>Profit</th>
                    <th>Return Rate</th>
                </tr>
                {rows_html}
            </table>

            <p style="color: #888; margin-top: 40px;">
                Asset Lens - Personal Asset Operating System<br>
                This report is for reference only and does not constitute investment advice.
            </p>
        </body>
        </html>
        """

        return Response(
            content=html_content,
            media_type="text/html; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename=investment_report_{datetime.now().strftime('%Y%m%d')}.html"
            },
        )

    except Exception as e:
        return {"error": str(e)}
