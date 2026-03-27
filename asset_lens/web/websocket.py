"""
WebSocket Manager - WebSocket 连接管理
"""

import asyncio
import json
import logging
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        self.active_connections: set[WebSocket] = set()
        self._last_ping: dict[WebSocket, float] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        self._last_ping[websocket] = datetime.now().timestamp()
        logger.info(f"WebSocket connected, total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        self._last_ping.pop(websocket, None)
        logger.info(f"WebSocket disconnected, total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.debug(f"Failed to send message: {e}")
                disconnected.add(connection)

        for conn in disconnected:
            self.disconnect(conn)

    def update_ping(self, websocket: WebSocket):
        self._last_ping[websocket] = datetime.now().timestamp()

    def check_timeout(self, timeout_seconds: float = 300) -> list[WebSocket]:
        now = datetime.now().timestamp()
        return [
            ws for ws, last_ping in self._last_ping.items()
            if now - last_ping > timeout_seconds
        ]

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
    - 心跳检测
    """
    await manager.connect(websocket)
    heartbeat_task = None

    try:
        async def heartbeat():
            while True:
                await asyncio.sleep(30)
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    break

        heartbeat_task = asyncio.create_task(heartbeat())

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

                elif action == "pong":
                    manager.update_ping(websocket)

                elif action == "ping":
                    await websocket.send_json({"type": "pong"})

                elif action == "get_market_indexes":
                    indexes = await _get_market_indexes_async()
                    await websocket.send_json({
                        "type": "market_indexes",
                        "data": indexes,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })

                elif action == "get_stock_quotes":
                    codes = message.get("codes", [])
                    quotes = await _get_stock_quotes_async(codes)
                    await websocket.send_json({
                        "type": "stock_quotes",
                        "data": quotes,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })

            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if heartbeat_task:
            heartbeat_task.cancel()
        manager.disconnect(websocket)


async def _get_market_indexes_async():
    """获取市场指数数据（异步版本）"""
    import aiohttp

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
    timeout = aiohttp.ClientTimeout(total=5)

    async with aiohttp.ClientSession() as session:
        for code, name in index_codes:
            try:
                url = f"http://hq.sinajs.cn/list={code}"
                async with session.get(url, headers=headers, timeout=timeout) as response:
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
                                try:
                                    current_price = float(parts[3]) if parts[3] else 0
                                    prev_close = float(parts[2]) if parts[2] else 0
                                    change = current_price - prev_close
                                    change_percent = (change / prev_close * 100) if prev_close > 0 else 0

                                    indexes.append({
                                        "code": code,
                                        "name": name,
                                        "price": current_price,
                                        "change": change,
                                        "changePercent": change_percent,
                                    })
                                except (ValueError, ZeroDivisionError) as e:
                                    logger.debug(f"Failed to parse index {code}: {e}")
            except asyncio.TimeoutError:
                logger.debug(f"Timeout fetching index {code}")
            except Exception as e:
                logger.debug(f"Error fetching index {code}: {e}")

    return indexes


async def _get_stock_quotes_async(codes: list[str]):
    """获取股票行情数据（异步版本）"""
    import aiohttp

    quotes = []
    headers = {
        "Referer": "http://finance.sina.com.cn",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    timeout = aiohttp.ClientTimeout(total=5)

    async with aiohttp.ClientSession() as session:
        for code in codes[:10]:
            try:
                url = f"http://hq.sinajs.cn/list={code}"
                async with session.get(url, headers=headers, timeout=timeout) as response:
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
                                try:
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
                                except (ValueError, ZeroDivisionError) as e:
                                    logger.debug(f"Failed to parse quote {code}: {e}")
            except asyncio.TimeoutError:
                logger.debug(f"Timeout fetching quote {code}")
            except Exception as e:
                logger.debug(f"Error fetching quote {code}: {e}")

    return quotes
