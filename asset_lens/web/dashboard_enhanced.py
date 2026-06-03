import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


class DashboardConfig(BaseModel):
    theme: str = "dark"
    refresh_interval: int = 30
    show_risk_alerts: bool = True
    show_predictions: bool = True
    chart_type: str = "echarts"


class WebSocketManager:
    def __init__(self):
        self.connections: set[WebSocket] = set()
        self._broadcast_task: Any = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.add(websocket)
        logger.info(f"WebSocket 连接建立，当前连接数: {len(self.connections)}")

    def disconnect(self, websocket: WebSocket):
        self.connections.discard(websocket)
        logger.info(f"WebSocket 连接断开，当前连接数: {len(self.connections)}")

    async def broadcast(self, message: dict):
        for connection in list(self.connections):
            try:
                await connection.send_json(message)
            except (OSError, RuntimeError) as e:
                logger.debug(f"忽略异常: {e}")
                self.connections.discard(connection)

    async def start_periodic_broadcast(self, interval: int = 30):
        while True:
            if self.connections:
                try:
                    data = await get_dashboard_data()
                    await self.broadcast(
                        {"type": "update", "data": data, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                    )
                except (ValueError, KeyError, ConnectionError, RuntimeError) as e:
                    logger.error(f"广播数据失败: {e}")
            await asyncio.sleep(interval)


ws_manager = WebSocketManager()


async def get_dashboard_data() -> dict[str, Any]:
    from asset_lens.data.csv_parser import CSVParser
    from asset_lens.monitoring.risk_alert import risk_alert_system

    try:
        parser = CSVParser()
        products = parser.load_data()

        total_assets: float = 0.0
        total_profit: float = 0.0
        total_cost: float = 0.0
        items = []

        for product in products:
            current = float(product.current_amount or product.total_amount or 0)
            cost = float(product.initial_amount or 0)
            profit = current - cost if cost > 0 else 0

            total_assets += current
            total_profit += profit
            total_cost += cost

            items.append(
                {
                    "name": product.name,
                    "code": product.code if hasattr(product, "code") else None,
                    "type": product.investment_type if hasattr(product, "investment_type") else "其他",
                    "current_amount": current,
                    "initial_amount": cost,
                    "profit": profit,
                    "profit_rate": (profit / cost * 100) if cost > 0 else 0,
                }
            )

        risk_summary = risk_alert_system.get_alert_summary()

        return {
            "summary": {
                "total_assets": total_assets,
                "total_profit": total_profit,
                "total_return": (total_profit / total_cost * 100) if total_cost > 0 else 0,
                "position_count": len(items),
            },
            "items": items,
            "risk": {
                "score": 50 + (1 - risk_summary["total_alerts"] / 10) * 50,
                "level": "低"
                if risk_summary["total_alerts"] == 0
                else "中"
                if risk_summary["total_alerts"] < 5
                else "高",
                "alerts_count": risk_summary["total_alerts"],
            },
            "market": await get_market_summary(),
        }

    except (ValueError, KeyError, TypeError, OSError, RuntimeError) as e:
        logger.error(f"获取 Dashboard 数据失败: {e}")
        return {
            "summary": {"total_assets": 0, "total_profit": 0, "total_return": 0, "position_count": 0},
            "items": [],
            "risk": {"score": 50, "level": "中", "alerts_count": 0},
            "market": {},
        }


async def get_market_summary() -> dict[str, Any]:
    from .aiohttp_session import async_get

    indexes = []
    index_codes = [
        ("sh000001", "上证指数"),
        ("sz399001", "深证成指"),
        ("sz399006", "创业板指"),
    ]

    for code, name in index_codes:
        try:
            url = f"http://hq.sinajs.cn/list={code}"
            headers = {
                "Referer": "http://finance.sina.com.cn",
                "User-Agent": "Mozilla/5.0",
            }
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
                            current = float(parts[3]) if parts[3] else 0
                            prev = float(parts[2]) if parts[2] else 0
                            change_pct = ((current - prev) / prev * 100) if prev > 0 else 0

                            indexes.append(
                                {
                                    "code": code,
                                    "name": name,
                                    "price": current,
                                    "change_percent": round(change_pct, 2),
                                }
                            )
        except (ConnectionError, TimeoutError, ValueError, KeyError, OSError) as e:
            logger.debug(f"忽略异常: {e}")

    return {"indexes": indexes}


@router.get("/data")
async def dashboard_data():
    return await get_dashboard_data()


@router.get("/config")
async def get_config():
    return {"theme": "dark", "refresh_interval": 30}


@router.post("/config")
async def update_config(config: DashboardConfig):
    return {"status": "success", "config": config}


@router.websocket("/ws")
async def dashboard_websocket(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            text_data = await websocket.receive_text()
            try:
                message = json.loads(text_data)
                action = message.get("action", "")

                if action == "ping":
                    await websocket.send_json({"type": "pong"})

                elif action == "get_data":
                    dashboard_data = await get_dashboard_data()
                    await websocket.send_json(
                        {
                            "type": "data",
                            "data": dashboard_data,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        }
                    )

                elif action == "set_theme":
                    theme = message.get("theme", "dark")
                    await websocket.send_json(
                        {
                            "type": "theme_changed",
                            "theme": theme,
                        }
                    )

            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


def _load_dashboard_html() -> str:
    template_path = Path(__file__).parent / "dashboard_template.html"
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return "<html><body><h1>Dashboard template not found</h1></body></html>"


@router.get("/enhanced", response_class=HTMLResponse)
async def enhanced_dashboard():
    return _load_dashboard_html()
