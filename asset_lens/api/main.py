"""
Asset-Lens REST API.
基于 FastAPI 的 REST API 实现 - 带 API Key 认证和限流

此模块提供带认证的 API 路由，挂载到 web.api 的主应用上
"""

import os
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from asset_lens.api.response import ERROR_CODES, create_error_response, create_success_response

router = APIRouter(prefix="/api/v1", tags=["API v1"])

security = HTTPBearer()


class StockQuote(BaseModel):
    code: str
    name: str
    current_price: float
    change_percent: float
    volume: int
    turnover: float
    update_time: str


class FundNav(BaseModel):
    code: str
    name: str
    nav: float
    accumulated_nav: float
    update_date: str


class PortfolioAnalysis(BaseModel):
    total_assets: float
    total_profit: float
    profit_rate: float
    annual_return: float
    risk_level: str
    update_time: str


class RiskMetrics(BaseModel):
    volatility: float
    max_drawdown: float
    sharpe_ratio: float
    beta: float
    var_95: float


class MonitorReport(BaseModel):
    report_type: str
    timestamp: str
    content: str
    alerts: list[dict[str, Any]]


def _load_api_keys() -> dict[str, dict[str, Any]]:
    api_keys_str = os.getenv("API_KEYS", "")
    if api_keys_str:
        import json

        try:
            result: dict[str, dict[str, Any]] = json.loads(api_keys_str)
            return result
        except json.JSONDecodeError:
            pass
    return {"demo_key": {"user": "demo", "rate_limit": 100}}


API_KEYS = _load_api_keys()

import time
from collections import defaultdict
from threading import Lock

_request_counts_lock = Lock()
_request_counts: dict[str, int] = defaultdict(int)
_request_counts_reset_time: float = time.time()
_REQUEST_COUNTS_RESET_INTERVAL = 3600


def _get_request_count(user: str) -> int:
    global _request_counts_reset_time
    with _request_counts_lock:
        now = time.time()
        if now - _request_counts_reset_time > _REQUEST_COUNTS_RESET_INTERVAL:
            _request_counts.clear()
            _request_counts_reset_time = now
        return _request_counts[user]


def _increment_request_count(user: str) -> None:
    with _request_counts_lock:
        _request_counts[user] += 1


async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    if token not in API_KEYS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return API_KEYS[token]


async def check_rate_limit(api_info: dict = Depends(verify_api_key)):
    user = api_info["user"]
    rate_limit = api_info["rate_limit"]

    if _get_request_count(user) >= rate_limit:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")

    _increment_request_count(user)
    return api_info


@router.get("/stocks/{code}", response_model=StockQuote)
async def get_stock_quote(code: str, api_info: dict = Depends(check_rate_limit)):
    try:
        from asset_lens.data.stock_fetcher import StockDataFetcher

        fetcher = StockDataFetcher()
        quote = fetcher.fetch_stock_quote_akshare(code)
        if quote:
            return StockQuote(
                code=code,
                name=quote.get("name", ""),
                current_price=float(quote.get("current_price", 0)),
                change_percent=float(quote.get("change_percent", 0)),
                volume=int(quote.get("volume", 0)),
                turnover=float(quote.get("amount", 0)),
                update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Stock not found: {code}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get("/funds/{code}", response_model=FundNav)
async def get_fund_nav(code: str, api_info: dict = Depends(check_rate_limit)):
    try:
        from asset_lens.data.fund_fetcher import FundDataFetcher

        fetcher = FundDataFetcher()
        nav_data = fetcher.fetch_fund_info(code)
        if nav_data:
            return FundNav(
                code=code,
                name=nav_data.get("name", ""),
                nav=float(nav_data.get("nav", 0)),
                accumulated_nav=float(nav_data.get("accumulated_nav", 0)),
                update_date=nav_data.get("date", ""),
            )
        return FundNav(code=code, name="", nav=0.0, accumulated_nav=0.0, update_date="")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get("/portfolio/analysis", response_model=PortfolioAnalysis)
async def get_portfolio_analysis(api_info: dict = Depends(check_rate_limit)):
    try:
        from asset_lens.config import config
        from asset_lens.core.analyzer import PortfolioAnalyzer

        analyzer = PortfolioAnalyzer(config)
        summary = analyzer.get_summary()
        return PortfolioAnalysis(
            total_assets=summary.get("total_assets", 0),
            total_profit=summary.get("total_profit", 0),
            profit_rate=summary.get("profit_rate", 0),
            annual_return=summary.get("annual_return", 0),
            risk_level=summary.get("risk_level", "未知"),
            update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get("/risk/metrics", response_model=RiskMetrics)
async def get_risk_metrics(api_info: dict = Depends(check_rate_limit)):
    try:
        return RiskMetrics(volatility=0.0, max_drawdown=0.0, sharpe_ratio=0.0, beta=0.0, var_95=0.0)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get("/monitor/report", response_model=MonitorReport)
async def get_monitor_report(
    report_type: str = Query("daily", description="报告类型: daily, weekly, monthly"),
    api_info: dict = Depends(check_rate_limit),
):
    try:
        return MonitorReport(
            report_type=report_type,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            content="",
            alerts=[],
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.post("/stocks/screen")
async def screen_stocks(
    strategy: str = Query("momentum", description="策略类型"),
    limit: int = Query(10, description="返回数量"),
    api_info: dict = Depends(check_rate_limit),
):
    try:
        return create_success_response(
            {"strategy": strategy, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "stocks": []}
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get("/market/indices")
async def get_market_indices(api_info: dict = Depends(check_rate_limit)):
    try:
        return create_success_response({"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "indices": []})
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get("/")
async def api_root():
    return create_success_response({"message": "Asset-Lens API v1", "docs": "/docs"})


def register_exception_handlers(app):
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        error_code = "INTERNAL_ERROR"
        for code, info in ERROR_CODES.items():
            if info["status_code"] == exc.status_code:
                error_code = code
                break
        return JSONResponse(
            status_code=exc.status_code,
            content=create_error_response(error_code, exc.detail),
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=create_error_response("INTERNAL_ERROR", str(exc)),
        )
