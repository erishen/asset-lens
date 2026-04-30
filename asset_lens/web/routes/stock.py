"""
Stock Routes - 股票相关 API
"""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api/stock", tags=["stock"])


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


@router.get("/quote/{code}", response_model=StockQuote)
async def get_stock_quote(code: str):
    """
    获取股票行情 - 使用新浪财经接口

    Args:
        code: 股票代码（如 sh600519）
    """
    try:
        from ...utils.http_client import safe_get

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


@router.get("/search")
async def search_stocks(keyword: str = Query(..., description="搜索关键词")):
    """
    搜索股票

    Args:
        keyword: 搜索关键词
    """
    from ...strategy.screener import stock_screener

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


@router.get("/kline/{code}")
async def get_stock_kline(
    code: str,
    ktype: str = Query("day", description="K线类型: day/week/month"),
    count: int = Query(100, description="返回数据条数"),
):
    """
    获取股票 K 线数据

    Args:
        code: 股票代码
        ktype: K线类型 (day/week/month)
        count: 返回数据条数
    """
    try:
        kline_data = await _get_kline_tencent(code, ktype, count)
        return {"code": code, "ktype": ktype, "count": len(kline_data), "data": kline_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取K线数据失败: {str(e)}")


async def _get_kline_tencent(code: str, ktype: str, count: int) -> list[dict]:
    """从腾讯获取 K 线数据"""
    import requests

    ktype_map = {"day": "day", "week": "week", "month": "month"}
    ktype_param = ktype_map.get(ktype, "day")

    url = "http://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
    params = {
        "_var": f"fqkline_{code}",
        "param": f"{code},{ktype_param},,{count},,",
        "r": str(int(datetime.now().timestamp() * 1000)),
    }
    headers = {
        "Referer": "http://gu.qq.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    response = requests.get(url, params=params, headers=headers, timeout=10)

    if response.status_code == 200:
        import json

        text = response.text
        json_start = text.find("{")
        if json_start != -1:
            data = json.loads(text[json_start:])

            if data.get("code") == 0:
                stock_data = data.get("data", {}).get(code, {})
                kline_data = stock_data.get(ktype_param, [])

                result = []
                for item in kline_data:
                    result.append(
                        {
                            "date": item[0],
                            "open": float(item[1]),
                            "close": float(item[2]),
                            "high": float(item[3]),
                            "low": float(item[4]),
                            "volume": float(item[5]),
                        }
                    )

                return result

    return []
