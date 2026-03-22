"""
WebSocket Manager - WebSocket 连接管理
"""

import json
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        self.active_connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

    @property
    def connection_count(self) -> int:
        return len(self.active_connections)


manager = ConnectionManager()


async def handle_market_websocket(websocket: WebSocket):
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
                    await websocket.send_json({
                        "type": "subscribed",
                        "codes": codes,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })

                elif action == "ping":
                    await websocket.send_json({"type": "pong"})

                elif action == "get_market_indexes":
                    indexes = await _get_market_indexes()
                    await websocket.send_json({
                        "type": "market_indexes",
                        "data": indexes,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })

                elif action == "get_stock_quotes":
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


async def _get_stock_quotes(codes: list[str]):
    """获取股票行情数据"""
    import requests

    quotes = []
    for code in codes[:10]:
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
