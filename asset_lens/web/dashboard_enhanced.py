"""
Enhanced Web Dashboard for asset-lens.
增强版 Web Dashboard - 支持深色/浅色模式、实时数据推送、交互式图表
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


class DashboardConfig(BaseModel):
    """Dashboard 配置"""

    theme: str = "dark"
    refresh_interval: int = 30
    show_risk_alerts: bool = True
    show_predictions: bool = True
    chart_type: str = "echarts"


class WebSocketManager:
    """WebSocket 连接管理器"""

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
            except Exception:
                self.connections.discard(connection)

    async def start_periodic_broadcast(self, interval: int = 30):
        """启动定期广播"""
        while True:
            if self.connections:
                try:
                    data = await get_dashboard_data()
                    await self.broadcast(
                        {"type": "update", "data": data, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                    )
                except Exception as e:
                    logger.error(f"广播数据失败: {e}")
            await asyncio.sleep(interval)


ws_manager = WebSocketManager()


async def get_dashboard_data() -> dict[str, Any]:
    """获取 Dashboard 数据"""
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

    except Exception as e:
        logger.error(f"获取 Dashboard 数据失败: {e}")
        return {
            "summary": {"total_assets": 0, "total_profit": 0, "total_return": 0, "position_count": 0},
            "items": [],
            "risk": {"score": 50, "level": "中", "alerts_count": 0},
            "market": {},
        }


async def get_market_summary() -> dict[str, Any]:
    """获取市场摘要"""
    import requests

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
            response = requests.get(url, headers=headers, timeout=3)

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
        except Exception:
            pass

    return {"indexes": indexes}


@router.get("/data")
async def dashboard_data():
    """获取 Dashboard 数据"""
    return await get_dashboard_data()


@router.get("/config")
async def get_config():
    """获取 Dashboard 配置"""
    return {"theme": "dark", "refresh_interval": 30}


@router.post("/config")
async def update_config(config: DashboardConfig):
    """更新 Dashboard 配置"""
    return {"status": "success", "config": config}


@router.websocket("/ws")
async def dashboard_websocket(websocket: WebSocket):
    """Dashboard WebSocket 连接"""
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


ENHANCED_DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Asset Lens - 个人资产运营系统</title>
    <script src="https://cdn.jsdelivr.net/npm/vue@3/dist/vue.global.prod.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
    <style>
        :root {
            --bg-primary: #1a1a2e;
            --bg-secondary: #16213e;
            --bg-card: rgba(255,255,255,0.05);
            --text-primary: #fff;
            --text-secondary: #888;
            --border-color: rgba(255,255,255,0.1);
            --accent-gradient: linear-gradient(90deg, #00d2ff, #3a7bd5);
            --positive: #ff5252;
            --negative: #00c853;
        }

        [data-theme="light"] {
            --bg-primary: #f5f7fa;
            --bg-secondary: #ffffff;
            --bg-card: rgba(0,0,0,0.02);
            --text-primary: #1a1a2e;
            --text-secondary: #666;
            --border-color: rgba(0,0,0,0.1);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
            min-height: 100vh;
            color: var(--text-primary);
            transition: background 0.3s, color 0.3s;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 0;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 30px;
        }

        .header h1 {
            font-size: 2rem;
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .header-actions {
            display: flex;
            gap: 15px;
            align-items: center;
        }

        .theme-toggle {
            padding: 10px 20px;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            background: var(--bg-card);
            color: var(--text-primary);
            cursor: pointer;
            transition: all 0.3s;
        }

        .theme-toggle:hover {
            background: var(--accent-gradient);
            color: #fff;
        }

        .live-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            border-radius: 20px;
            background: rgba(0, 200, 83, 0.2);
            color: var(--positive);
            font-size: 0.9rem;
        }

        .live-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--positive);
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .nav {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }

        .nav-btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            background: var(--bg-card);
            color: var(--text-primary);
            cursor: pointer;
            transition: all 0.3s;
            font-size: 1rem;
        }

        .nav-btn:hover, .nav-btn.active {
            background: var(--accent-gradient);
            color: #fff;
        }

        .cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .card {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 24px;
            backdrop-filter: blur(10px);
            border: 1px solid var(--border-color);
            transition: transform 0.3s, box-shadow 0.3s;
        }

        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }

        .card-title {
            font-size: 0.9rem;
            color: var(--text-secondary);
            margin-bottom: 10px;
        }

        .card-value {
            font-size: 1.8rem;
            font-weight: bold;
            margin-bottom: 5px;
        }

        .card-change {
            font-size: 0.9rem;
        }

        .positive { color: var(--positive); }
        .negative { color: var(--negative); }

        .chart-container {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 30px;
            border: 1px solid var(--border-color);
        }

        .chart-title {
            font-size: 1.2rem;
            margin-bottom: 20px;
        }

        .chart {
            height: 350px;
            width: 100%;
        }

        .alert-panel {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 30px;
            border: 1px solid var(--border-color);
        }

        .alert-item {
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
            background: rgba(255, 82, 82, 0.1);
            border-left: 4px solid var(--negative);
        }

        .alert-item.warning {
            background: rgba(255, 152, 0, 0.1);
            border-left-color: #ff9800;
        }

        .alert-item.info {
            background: rgba(33, 150, 243, 0.1);
            border-left-color: #2196f3;
        }

        .table-container {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 30px;
            border: 1px solid var(--border-color);
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th, td {
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }

        th {
            color: var(--text-secondary);
            font-weight: 500;
        }

        tr:hover {
            background: rgba(255, 255, 255, 0.05);
        }

        .footer {
            text-align: center;
            padding: 30px;
            color: var(--text-secondary);
        }

        @media screen and (max-width: 768px) {
            .header {
                flex-direction: column;
                gap: 15px;
            }
            .header h1 {
                font-size: 1.5rem;
            }
            .cards {
                grid-template-columns: 1fr;
            }
            .chart {
                height: 280px;
            }
        }
    </style>
</head>
<body>
    <div id="app" :data-theme="theme">
        <div class="container">
            <div class="header">
                <h1>Asset Lens</h1>
                <div class="header-actions">
                    <div class="live-indicator" v-if="wsConnected">
                        <span class="live-dot"></span>
                        实时更新
                    </div>
                    <button class="theme-toggle" @click="toggleTheme">
                        {{ theme === 'dark' ? '☀️ 浅色' : '🌙 深色' }}
                    </button>
                </div>
            </div>

            <div class="nav">
                <button class="nav-btn" :class="{ active: currentTab === 'overview' }" @click="currentTab = 'overview'">概览</button>
                <button class="nav-btn" :class="{ active: currentTab === 'portfolio' }" @click="currentTab = 'portfolio'">投资组合</button>
                <button class="nav-btn" :class="{ active: currentTab === 'signals' }" @click="currentTab = 'signals'">ML信号</button>
                <button class="nav-btn" :class="{ active: currentTab === 'risk' }" @click="currentTab = 'risk'">风险预警</button>
                <button class="nav-btn" :class="{ active: currentTab === 'market' }" @click="currentTab = 'market'">市场行情</button>
            </div>

            <div v-show="currentTab === 'overview'">
                <div class="cards">
                    <div class="card">
                        <div class="card-title">总资产</div>
                        <div class="card-value">{{ formatMoney(summary.total_assets) }}</div>
                        <div class="card-change">持仓数量: {{ summary.position_count }}</div>
                    </div>
                    <div class="card">
                        <div class="card-title">总收益</div>
                        <div class="card-value" :class="summary.total_profit >= 0 ? 'positive' : 'negative'">
                            {{ formatMoney(summary.total_profit) }}
                        </div>
                        <div class="card-change" :class="summary.total_return >= 0 ? 'positive' : 'negative'">
                            收益率: {{ summary.total_return.toFixed(2) }}%
                        </div>
                    </div>
                    <div class="card">
                        <div class="card-title">风险评分</div>
                        <div class="card-value">{{ risk.score.toFixed(0) }}</div>
                        <div class="card-change">风险等级: {{ risk.level }}</div>
                    </div>
                    <div class="card">
                        <div class="card-title">预警数量</div>
                        <div class="card-value" :class="risk.alerts_count > 0 ? 'negative' : 'positive'">
                            {{ risk.alerts_count }}
                        </div>
                        <div class="card-change">需要关注</div>
                    </div>
                </div>

                <div class="chart-container">
                    <div class="chart-title">资产配置</div>
                    <div id="allocationChart" class="chart"></div>
                </div>
            </div>

            <div v-show="currentTab === 'portfolio'">
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>名称</th>
                                <th>类型</th>
                                <th>当前金额</th>
                                <th>收益</th>
                                <th>收益率</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="item in items" :key="item.name">
                                <td>{{ item.name }}</td>
                                <td>{{ item.type }}</td>
                                <td>{{ formatMoney(item.current_amount) }}</td>
                                <td :class="item.profit >= 0 ? 'positive' : 'negative'">{{ formatMoney(item.profit) }}</td>
                                <td :class="item.profit_rate >= 0 ? 'positive' : 'negative'">{{ item.profit_rate.toFixed(2) }}%</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div class="chart-container">
                    <div class="chart-title">收益分布</div>
                    <div id="profitChart" class="chart"></div>
                </div>
            </div>

            <div v-show="currentTab === 'signals'">
                <div class="cards">
                    <div class="card">
                        <div class="card-title">模型状态</div>
                        <div class="card-value" :class="mlSignals.model_status === 'loaded' ? 'positive' : 'negative'">
                            {{ mlSignals.model_status === 'loaded' ? '已加载' : '未加载' }}
                        </div>
                        <div class="card-change">{{ mlSignals.total || 0 }} 个信号</div>
                    </div>
                    <div class="card">
                        <div class="card-title">看涨信号</div>
                        <div class="card-value positive">{{ bullishSignals }}</div>
                        <div class="card-change">置信度 > 60%</div>
                    </div>
                    <div class="card">
                        <div class="card-title">看跌信号</div>
                        <div class="card-value negative">{{ bearishSignals }}</div>
                        <div class="card-change">置信度 > 60%</div>
                    </div>
                    <div class="card">
                        <div class="card-title">强信号</div>
                        <div class="card-value">{{ strongSignals }}</div>
                        <div class="card-change">置信度 > 70%</div>
                    </div>
                </div>

                <div class="table-container">
                    <div class="chart-title">ML 预测信号</div>
                    <div v-if="mlSignals.signals.length === 0" style="text-align: center; padding: 40px; color: var(--text-secondary);">
                        <span v-if="mlSignals.model_status !== 'loaded'">⚠️ {{ mlSignals.message || '模型未加载，请先训练模型' }}</span>
                        <span v-else>📊 暂无预测信号</span>
                    </div>
                    <table v-else>
                        <thead>
                            <tr>
                                <th>代码</th>
                                <th>名称</th>
                                <th>预测</th>
                                <th>置信度</th>
                                <th>上涨概率</th>
                                <th>下跌概率</th>
                                <th>信号强度</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="signal in mlSignals.signals" :key="signal.code">
                                <td>{{ signal.code }}</td>
                                <td>{{ signal.name }}</td>
                                <td :class="signal.prediction === 'up' ? 'positive' : 'negative'">
                                    {{ signal.prediction === 'up' ? '📈 看涨' : '📉 看跌' }}
                                </td>
                                <td>{{ (signal.confidence * 100).toFixed(1) }}%</td>
                                <td class="positive">{{ (signal.up_prob * 100).toFixed(1) }}%</td>
                                <td class="negative">{{ (signal.down_prob * 100).toFixed(1) }}%</td>
                                <td>
                                    <span class="tag" :class="signal.signal_strength === 'strong' ? 'tag-stock' : signal.signal_strength === 'medium' ? 'tag-fund' : 'tag-cash'">
                                        {{ signal.signal_strength === 'strong' ? '强' : signal.signal_strength === 'medium' ? '中' : '弱' }}
                                    </span>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div class="chart-container">
                    <div class="chart-title">信号置信度分布</div>
                    <div id="signalChart" class="chart"></div>
                </div>
            </div>

            <div v-show="currentTab === 'risk'">
                <div class="alert-panel">
                    <div class="chart-title">风险预警</div>
                    <div v-if="risk.alerts_count === 0" style="text-align: center; padding: 40px; color: var(--text-secondary);">
                        ✅ 暂无风险预警
                    </div>
                    <div v-else>
                        <div class="alert-item" v-for="alert in alerts" :key="alert.id">
                            <span>{{ alert.level === 'danger' ? '🔴' : alert.level === 'warning' ? '🟡' : '🔵' }}</span>
                            <div>
                                <strong>{{ alert.title }}</strong>
                                <p style="font-size: 0.9rem; color: var(--text-secondary);">{{ alert.message }}</p>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="chart-container">
                    <div class="chart-title">风险指标</div>
                    <div id="riskChart" class="chart"></div>
                </div>
            </div>

            <div v-show="currentTab === 'market'">
                <div class="cards">
                    <div class="card" v-for="index in market.indexes" :key="index.code">
                        <div class="card-title">{{ index.name }}</div>
                        <div class="card-value">{{ index.price.toFixed(2) }}</div>
                        <div class="card-change" :class="index.change_percent >= 0 ? 'positive' : 'negative'">
                            {{ index.change_percent >= 0 ? '+' : '' }}{{ index.change_percent.toFixed(2) }}%
                        </div>
                    </div>
                </div>
            </div>

            <div class="footer">
                <p>Asset Lens v2.0.0 - Enhanced Dashboard | 最后更新: {{ lastUpdate }}</p>
            </div>
        </div>
    </div>

    <script>
        const { createApp, ref, onMounted, nextTick, watch, computed } = Vue;

        createApp({
            setup() {
                const theme = ref(localStorage.getItem('theme') || 'dark');
                const currentTab = ref('overview');
                const wsConnected = ref(false);
                const lastUpdate = ref('');

                const summary = ref({ total_assets: 0, total_profit: 0, total_return: 0, position_count: 0 });
                const items = ref([]);
                const risk = ref({ score: 50, level: '中', alerts_count: 0 });
                const market = ref({ indexes: [] });
                const alerts = ref([]);
                const mlSignals = ref({ signals: [], model_status: 'unknown', total: 0 });

                let ws = null;
                let charts = {};

                const toggleTheme = () => {
                    theme.value = theme.value === 'dark' ? 'light' : 'dark';
                    localStorage.setItem('theme', theme.value);
                    updateChartsTheme();
                };

                const updateChartsTheme = () => {
                    const textColor = theme.value === 'dark' ? '#fff' : '#1a1a2e';
                    Object.values(charts).forEach(chart => {
                        if (chart) {
                            chart.dispose();
                        }
                    });
                    initCharts();
                };

                const formatMoney = (value) => {
                    if (!value) return '¥0';
                    const num = parseFloat(value);
                    if (num >= 10000) return '¥' + (num / 10000).toFixed(2) + '万';
                    return '¥' + num.toFixed(2);
                };

                const connectWebSocket = () => {
                    const wsUrl = `ws://${window.location.host}/api/dashboard/ws`;
                    ws = new WebSocket(wsUrl);

                    ws.onopen = () => {
                        wsConnected.value = true;
                        console.log('WebSocket 连接成功');
                    };

                    ws.onmessage = (event) => {
                        const data = JSON.parse(event.data);
                        if (data.type === 'update' || data.type === 'data') {
                            summary.value = data.data.summary;
                            items.value = data.data.items;
                            risk.value = data.data.risk;
                            market.value = data.data.market || { indexes: [] };
                            lastUpdate.value = data.timestamp;
                            nextTick(() => initCharts());
                        }
                    };

                    ws.onclose = () => {
                        wsConnected.value = false;
                        setTimeout(connectWebSocket, 5000);
                    };

                    ws.onerror = () => {
                        wsConnected.value = false;
                    };
                };

                const fetchData = async () => {
                    try {
                        const res = await fetch('/api/dashboard/data');
                        const data = await res.json();
                        summary.value = data.summary;
                        items.value = data.items;
                        risk.value = data.risk;
                        market.value = data.market || { indexes: [] };
                        lastUpdate.value = new Date().toLocaleString('zh-CN');
                        nextTick(() => initCharts());
                    } catch (e) {
                        console.error('获取数据失败:', e);
                    }
                };

                const fetchMLSignals = async () => {
                    try {
                        const res = await fetch('/api/ml/signals');
                        const data = await res.json();
                        mlSignals.value = data;
                        nextTick(() => initSignalChart());
                    } catch (e) {
                        console.error('获取 ML 信号失败:', e);
                        mlSignals.value = { signals: [], model_status: 'error', total: 0, message: e.message };
                    }
                };

                const bullishSignals = computed(() => {
                    return mlSignals.value.signals.filter(s => s.prediction === 'up' && s.confidence > 0.6).length;
                });

                const bearishSignals = computed(() => {
                    return mlSignals.value.signals.filter(s => s.prediction === 'down' && s.confidence > 0.6).length;
                });

                const strongSignals = computed(() => {
                    return mlSignals.value.signals.filter(s => s.confidence > 0.7).length;
                });

                const initCharts = () => {
                    initAllocationChart();
                    initProfitChart();
                    initRiskChart();
                };

                const initAllocationChart = () => {
                    const el = document.getElementById('allocationChart');
                    if (!el) return;

                    if (charts.allocation) charts.allocation.dispose();

                    const typeData = {};
                    items.value.forEach(item => {
                        const type = item.type || '其他';
                        typeData[type] = (typeData[type] || 0) + item.current_amount;
                    });

                    const chartData = Object.entries(typeData).map(([name, value]) => ({ name, value }));
                    const textColor = theme.value === 'dark' ? '#fff' : '#1a1a2e';

                    charts.allocation = echarts.init(el);
                    charts.allocation.setOption({
                        tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
                        legend: { orient: 'vertical', left: 'left', textStyle: { color: textColor } },
                        series: [{
                            type: 'pie',
                            radius: ['40%', '70%'],
                            center: ['60%', '50%'],
                            itemStyle: { borderRadius: 10, borderColor: theme.value === 'dark' ? '#1a1a2e' : '#fff', borderWidth: 2 },
                            label: { show: false },
                            emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
                            data: chartData
                        }]
                    });
                };

                const initProfitChart = () => {
                    const el = document.getElementById('profitChart');
                    if (!el) return;

                    if (charts.profit) charts.profit.dispose();

                    const profitData = items.value.slice(0, 20).map(item => ({
                        name: item.name,
                        value: item.profit
                    }));

                    const textColor = theme.value === 'dark' ? '#fff' : '#1a1a2e';

                    charts.profit = echarts.init(el);
                    charts.profit.setOption({
                        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
                        grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
                        xAxis: { type: 'category', data: profitData.map(d => d.name), axisLabel: { color: textColor, rotate: 30 } },
                        yAxis: { type: 'value', axisLabel: { color: textColor } },
                        series: [{
                            type: 'bar',
                            data: profitData.map(d => ({
                                value: d.value,
                                itemStyle: { color: d.value >= 0 ? '#00c853' : '#ff5252' }
                            }))
                        }]
                    });
                };

                const initRiskChart = () => {
                    const el = document.getElementById('riskChart');
                    if (!el) return;

                    if (charts.risk) charts.risk.dispose();

                    const textColor = theme.value === 'dark' ? '#fff' : '#1a1a2e';

                    charts.risk = echarts.init(el);
                    charts.risk.setOption({
                        tooltip: {},
                        radar: {
                            indicator: [
                                { name: '市场风险', max: 100 },
                                { name: '集中度风险', max: 100 },
                                { name: '流动性风险', max: 100 },
                                { name: '信用风险', max: 100 },
                                { name: '操作风险', max: 100 }
                            ],
                            axisName: { color: textColor }
                        },
                        series: [{
                            type: 'radar',
                            data: [{
                                value: [60, 40, 30, 20, 25],
                                areaStyle: { color: 'rgba(0, 210, 255, 0.3)' },
                                lineStyle: { color: '#00d2ff' }
                            }]
                        }]
                    });
                };

                const initSignalChart = () => {
                    const el = document.getElementById('signalChart');
                    if (!el) return;

                    if (charts.signal) charts.signal.dispose();

                    const textColor = theme.value === 'dark' ? '#fff' : '#1a1a2e';
                    const signals = mlSignals.value.signals || [];

                    const confidenceRanges = [
                        { name: '50-60%', count: signals.filter(s => s.confidence >= 0.5 && s.confidence < 0.6).length },
                        { name: '60-70%', count: signals.filter(s => s.confidence >= 0.6 && s.confidence < 0.7).length },
                        { name: '70-80%', count: signals.filter(s => s.confidence >= 0.7 && s.confidence < 0.8).length },
                        { name: '80-90%', count: signals.filter(s => s.confidence >= 0.8 && s.confidence < 0.9).length },
                        { name: '90-100%', count: signals.filter(s => s.confidence >= 0.9).length },
                    ];

                    charts.signal = echarts.init(el);
                    charts.signal.setOption({
                        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
                        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
                        xAxis: { type: 'category', data: confidenceRanges.map(r => r.name), axisLabel: { color: textColor } },
                        yAxis: { type: 'value', axisLabel: { color: textColor } },
                        series: [{
                            type: 'bar',
                            data: confidenceRanges.map((r, i) => ({
                                value: r.count,
                                itemStyle: { color: i < 2 ? '#888' : i < 4 ? '#00c853' : '#00d2ff' }
                            }))
                        }]
                    });
                };

                onMounted(() => {
                    fetchData();
                    fetchMLSignals();
                    connectWebSocket();
                    window.addEventListener('resize', () => {
                        Object.values(charts).forEach(chart => chart && chart.resize());
                    });
                });

                watch(currentTab, () => {
                    nextTick(() => initCharts());
                });

                return {
                    theme, currentTab, wsConnected, lastUpdate,
                    summary, items, risk, market, alerts, mlSignals,
                    bullishSignals, bearishSignals, strongSignals,
                    toggleTheme, formatMoney
                };
            }
        }).mount('#app');
    </script>
</body>
</html>
"""


@router.get("/enhanced", response_class=HTMLResponse)
async def enhanced_dashboard():
    """增强版 Dashboard 页面"""
    return ENHANCED_DASHBOARD_HTML
