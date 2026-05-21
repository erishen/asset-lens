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

import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from .http_client import close_session

    yield
    await close_session()


app = FastAPI(
    title="Asset Lens API",
    description="Personal Asset Operating System API",
    version="1.0.0",
    lifespan=lifespan,
)

CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173,http://localhost:3002,http://localhost:8080"
).split(",")
CORS_METHODS = os.getenv("CORS_METHODS", "GET,POST,PUT,DELETE,OPTIONS").split(",")
CORS_HEADERS = os.getenv("CORS_HEADERS", "Content-Type,Authorization,Accept").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=CORS_METHODS,
    allow_headers=CORS_HEADERS,
)

from .dashboard_enhanced import router as dashboard_router
from .routes import (
    backup_router,
    chat_router,
    compare_router,
    market_router,
    ml_router,
    portfolio_router,
    recommendation_router,
    report_router,
    risk_router,
    stock_pool_router,
    stock_router,
    strategy_router,
    system_router,
)

app.include_router(stock_router)
app.include_router(portfolio_router)
app.include_router(strategy_router)
app.include_router(market_router)
app.include_router(compare_router)
app.include_router(risk_router)
app.include_router(system_router)
app.include_router(backup_router)
app.include_router(recommendation_router)
app.include_router(stock_pool_router)
app.include_router(report_router)
app.include_router(dashboard_router)
app.include_router(ml_router)
app.include_router(chat_router)

from asset_lens.api.main import register_exception_handlers
from asset_lens.api.main import router as api_v1_router

app.include_router(api_v1_router)
register_exception_handlers(app)


@app.get("/")
async def root():
    """Dashboard 页面"""
    static_path = Path(__file__).parent / "static" / "index.html"
    if static_path.exists():
        return FileResponse(str(static_path))
    return {
        "name": "Asset Lens API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


@app.get("/dashboard")
async def dashboard():
    """Dashboard 页面"""
    static_path = Path(__file__).parent / "static" / "index.html"
    if static_path.exists():
        return FileResponse(str(static_path))
    return {"error": "Dashboard not found"}


static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


from .websocket import manager


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
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                action = message.get("action", "")

                if action == "subscribe":
                    codes = message.get("codes", [])
                    await websocket.send_json(
                        {
                            "type": "subscribed",
                            "codes": codes,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        }
                    )

                elif action == "ping":
                    await websocket.send_json({"type": "pong"})

                elif action == "get_market_indexes":
                    indexes = await _get_market_indexes()
                    await websocket.send_json(
                        {
                            "type": "market_indexes",
                            "data": indexes,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        }
                    )

                elif action == "get_stock_quotes":
                    codes = message.get("codes", [])
                    quotes = await _get_stock_quotes(codes)
                    await websocket.send_json(
                        {
                            "type": "stock_quotes",
                            "data": quotes,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        }
                    )

            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})

    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def _get_market_indexes():
    """获取市场指数数据"""
    from .http_client import async_get

    indexes = []
    index_codes = [
        ("sh000001", "上证指数"),
        ("sz399001", "深证成指"),
        ("sz399006", "创业板指"),
        ("sh000300", "沪深300"),
        ("sh000016", "上证50"),
    ]

    headers = {
        "Referer": "http://finance.sina.com.cn",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    for code, name in index_codes:
        try:
            url = f"http://hq.sinajs.cn/list={code}"
            async with await async_get(url, headers=headers, timeout=3) as response:
                if response.status == 200:
                    content = await response.text()
                    pattern = f'var hq_str_{code}="'
                    start = content.find(pattern)

                    if start != -1:
                        start += len(pattern)
                        end = content.find('";', start)
                        data_str = content[start:end]
                        parts = data_str.split(",")

                        if len(parts) >= 32:
                            indexes.append(
                                {
                                    "code": code,
                                    "name": name,
                                    "price": float(parts[3]) if parts[3] else 0,
                                    "change": float(parts[3]) - float(parts[2]) if parts[3] and parts[2] else 0,
                                    "changePercent": ((float(parts[3]) - float(parts[2])) / float(parts[2]) * 100)
                                    if parts[2] and parts[3]
                                    else 0,
                                }
                            )
        except (ValueError, TypeError):
            pass

    return indexes


async def _get_stock_quotes(codes: list[str]):
    """获取股票行情数据"""
    from .http_client import async_get

    quotes = []
    headers = {
        "Referer": "http://finance.sina.com.cn",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    for code in codes[:10]:
        try:
            url = f"http://hq.sinajs.cn/list={code}"
            async with await async_get(url, headers=headers, timeout=3) as response:
                if response.status == 200:
                    content = await response.text()
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
                            change_percent = (
                                ((current_price - prev_close) / prev_close * 100) if prev_close > 0 else 0
                            )

                            quotes.append(
                                {
                                    "code": code,
                                    "name": parts[0],
                                    "current_price": current_price,
                                    "change_percent": change_percent,
                                    "volume": float(parts[8]) if parts[8] else 0,
                                    "amount": float(parts[9]) if parts[9] else 0,
                                }
                            )
        except (ValueError, TypeError):
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
