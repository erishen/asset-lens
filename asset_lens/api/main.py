"""
Asset-Lens REST API.
基于 FastAPI 的 REST API 实现
"""

import os
from datetime import datetime
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from asset_lens.api.response import ERROR_CODES, create_error_response, create_success_response

app = FastAPI(
    title="Asset-Lens API",
    description="Personal Asset Operating System API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()


class StockQuote(BaseModel):
    """股票行情模型"""

    code: str
    name: str
    current_price: float
    change_percent: float
    volume: int
    turnover: float
    update_time: str


class FundNav(BaseModel):
    """基金净值模型"""

    code: str
    name: str
    nav: float
    accumulated_nav: float
    update_date: str


class PortfolioAnalysis(BaseModel):
    """投资组合分析模型"""

    total_assets: float
    total_profit: float
    profit_rate: float
    annual_return: float
    risk_level: str
    update_time: str


class RiskMetrics(BaseModel):
    """风险指标模型"""

    volatility: float
    max_drawdown: float
    sharpe_ratio: float
    beta: float
    var_95: float


class MonitorReport(BaseModel):
    """监控报告模型"""

    report_type: str
    timestamp: str
    content: str
    alerts: list[dict[str, Any]]


def _load_api_keys() -> dict[str, dict[str, Any]]:
    """从环境变量加载 API Keys"""
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

request_counts: dict[str, int] = {}


async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证 API Key"""
    token = credentials.credentials
    if token not in API_KEYS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return API_KEYS[token]


async def check_rate_limit(api_info: dict = Depends(verify_api_key)):
    """检查速率限制"""
    user = api_info["user"]
    rate_limit = api_info["rate_limit"]

    if user not in request_counts:
        request_counts[user] = 0

    if request_counts[user] >= rate_limit:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")

    request_counts[user] += 1
    return api_info


@app.get("/")
async def root():
    """根路径"""
    return create_success_response({"message": "Welcome to Asset-Lens API", "version": "1.0.0", "docs": "/docs"})


@app.get("/api/v1/stocks/{code}", response_model=StockQuote)
async def get_stock_quote(code: str, api_info: dict = Depends(check_rate_limit)):
    """
    获取股票实时行情

    Args:
        code: 股票代码（如 sh600519, sz000001）

    Returns:
        股票行情数据
    """
    try:
        import subprocess

        result = subprocess.run(
            ["python", "-m", "asset_lens", "data", "fetch-stock", "--codes", code], capture_output=True, text=True
        )

        if result.returncode != 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Stock not found: {code}")

        return StockQuote(
            code=code,
            name="示例股票",
            current_price=100.0,
            change_percent=1.5,
            volume=1000000,
            turnover=100000000.0,
            update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@app.get("/api/v1/funds/{code}", response_model=FundNav)
async def get_fund_nav(code: str, api_info: dict = Depends(check_rate_limit)):
    """
    获取基金净值

    Args:
        code: 基金代码

    Returns:
        基金净值数据
    """
    try:
        return FundNav(
            code=code, name="示例基金", nav=1.5, accumulated_nav=2.0, update_date=datetime.now().strftime("%Y-%m-%d")
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@app.get("/api/v1/portfolio/analysis", response_model=PortfolioAnalysis)
async def get_portfolio_analysis(api_info: dict = Depends(check_rate_limit)):
    """
    获取投资组合分析

    Returns:
        投资组合分析数据
    """
    try:
        return PortfolioAnalysis(
            total_assets=1000000.0,
            total_profit=50000.0,
            profit_rate=5.0,
            annual_return=10.0,
            risk_level="中等",
            update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@app.get("/api/v1/risk/metrics", response_model=RiskMetrics)
async def get_risk_metrics(api_info: dict = Depends(check_rate_limit)):
    """
    获取风险指标

    Returns:
        风险指标数据
    """
    try:
        return RiskMetrics(volatility=15.0, max_drawdown=8.0, sharpe_ratio=1.2, beta=0.8, var_95=3.5)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@app.get("/api/v1/monitor/report", response_model=MonitorReport)
async def get_monitor_report(
    report_type: str = Query("daily", description="报告类型: daily, weekly, monthly"),
    api_info: dict = Depends(check_rate_limit),
):
    """
    获取监控报告

    Args:
        report_type: 报告类型

    Returns:
        监控报告数据
    """
    try:
        return MonitorReport(
            report_type=report_type,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            content="示例监控报告内容",
            alerts=[{"level": "medium", "type": "price_change", "message": "股票价格变动超过5%"}],
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@app.post("/api/v1/stocks/screen")
async def screen_stocks(
    strategy: str = Query("momentum", description="策略类型"),
    limit: int = Query(10, description="返回数量"),
    api_info: dict = Depends(check_rate_limit),
):
    """
    股票筛选

    Args:
        strategy: 策略类型
        limit: 返回数量

    Returns:
        筛选结果
    """
    try:
        return create_success_response(
            {
                "strategy": strategy,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "stocks": [{"code": "sh600519", "name": "贵州茅台", "score": 95, "rank": 1}],
            }
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@app.get("/api/v1/market/indices")
async def get_market_indices(api_info: dict = Depends(check_rate_limit)):
    """
    获取市场指数

    Returns:
        市场指数数据
    """
    try:
        return create_success_response(
            {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "indices": [
                    {"code": "sh000300", "name": "沪深300", "price": 4000.0, "change_percent": 1.5},
                    {"code": "sz399006", "name": "创业板指", "price": 3000.0, "change_percent": 2.0},
                ],
            }
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 异常处理"""
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
    """通用异常处理"""
    return JSONResponse(
        status_code=500,
        content=create_error_response("INTERNAL_ERROR", str(exc)),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
