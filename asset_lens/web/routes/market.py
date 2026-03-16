"""
Market Routes - 市场数据相关 API
"""

from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api/market", tags=["market"])


class MarketIndex(BaseModel):
    """市场指数模型"""
    code: str
    name: str
    price: float = 0
    change: float = 0
    change_percent: float = 0


@router.get("/indexes", response_model=List[MarketIndex])
async def get_market_indexes():
    """获取市场主要指数"""
    indexes = await _get_market_indexes()
    return indexes


async def _get_market_indexes() -> List[MarketIndex]:
    """获取市场指数数据"""
    import requests
    
    index_codes = [
        ("sh000001", "上证指数"),
        ("sh000300", "沪深300"),
        ("sh000016", "上证50"),
        ("sh000905", "中证500"),
        ("sz399001", "深证成指"),
        ("sz399006", "创业板指"),
    ]
    
    codes_str = ",".join([code for code, _ in index_codes])
    url = f"http://hq.sinajs.cn/list={codes_str}"
    headers = {
        "Referer": "http://finance.sina.com.cn",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = []
            content = response.text
            
            for code, name in index_codes:
                pattern = f'var hq_str_{code}="'
                start = content.find(pattern)
                
                if start != -1:
                    start += len(pattern)
                    end = content.find('";', start)
                    data_str = content[start:end]
                    
                    if data_str:
                        parts = data_str.split(",")
                        if len(parts) >= 32:
                            current_price = float(parts[3]) if parts[3] else 0
                            prev_close = float(parts[2]) if parts[2] else 0
                            change = current_price - prev_close if prev_close > 0 else 0
                            change_percent = (change / prev_close * 100) if prev_close > 0 else 0
                            
                            result.append(
                                MarketIndex(
                                    code=code,
                                    name=name,
                                    price=current_price,
                                    change=change,
                                    change_percent=change_percent,
                                )
                            )
            
            return result
    
    except Exception:
        pass
    
    return []


@router.get("/hot-stocks")
async def get_hot_stocks(
    market: str = Query("all", description="市场: all/sh/sz"),
    limit: int = Query(10, description="返回数量"),
):
    """
    获取热门股票
    
    Args:
        market: 市场 (all/sh/sz)
        limit: 返回数量
    """
    from ...data.market_stock_fetcher import market_stock_fetcher
    
    try:
        stocks = market_stock_fetcher.fetch_all_cn_stocks(max_pages=1)
        return {"market": market, "count": len(stocks[:limit]), "stocks": stocks[:limit]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/north-flow")
async def get_north_flow():
    """获取北向资金流向"""
    try:
        flow_data = await _get_north_flow_data()
        return flow_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _get_north_flow_data() -> Dict:
    """获取北向资金数据"""
    import requests
    
    url = "http://push2.eastmoney.com/api/qt/stock/fflow/kline/get"
    params = {
        "lmt": "0",
        "klt": "1",
        "secid": "1.000001",
        "fields1": "f1,f2,f3,f7",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63",
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("data") and data["data"].get("klines"):
                klines = data["data"]["klines"]
                
                if klines:
                    latest = klines[-1].split(",")
                    return {
                        "date": latest[0],
                        "main_inflow": float(latest[1]) if len(latest) > 1 else 0,
                        "retail_inflow": float(latest[5]) if len(latest) > 5 else 0,
                        "total_inflow": float(latest[9]) if len(latest) > 9 else 0,
                    }
    
    except Exception:
        pass
    
    return {"date": "", "main_inflow": 0, "retail_inflow": 0, "total_inflow": 0}


@router.get("/sentiment")
async def get_market_sentiment():
    """获取市场情绪指标"""
    from ...core.market_sentiment import MarketSentimentAnalyzer
    
    try:
        analyzer = MarketSentimentAnalyzer()
        sentiment = analyzer.analyze()
        
        return {
            "overall_score": sentiment.overall_score,
            "trend": sentiment.trend,
            "risk_level": sentiment.risk_level,
            "indicators": [
                {
                    "name": i.name,
                    "score": i.value,
                    "level": i.level,
                    "description": i.description,
                }
                for i in sentiment.indicators
            ],
            "suggestions": sentiment.suggestions,
            "analysis_time": sentiment.analysis_time,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
