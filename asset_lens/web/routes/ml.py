"""
ML Prediction API Routes.
ML 预测信号 API 路由
"""

import logging
import os
import random
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ml", tags=["ml"])

MODEL_PATH = Path(__file__).parent.parent.parent / "models" / "stock_predictor.joblib"

# Demo 模式检测
DEMO_MODE = os.getenv("ASSET_LENS_DEMO_MODE", "").lower() in ("true", "1", "yes")

# Demo 模式模拟 ML 信号数据
DEMO_ML_SIGNALS = [
    {"code": "SH900001", "name": "华夏成长混合", "prediction": "up", "confidence": 0.78, "up_prob": 0.78, "down_prob": 0.22, "expected_return": 3.5},
    {"code": "SH900002", "name": "招商科技先锋", "prediction": "down", "confidence": 0.65, "up_prob": 0.35, "down_prob": 0.65, "expected_return": -1.8},
    {"code": "SZ900003", "name": "中银价值精选", "prediction": "up", "confidence": 0.72, "up_prob": 0.72, "down_prob": 0.28, "expected_return": 2.1},
    {"code": "US900001", "name": "环球科技指数基金", "prediction": "up", "confidence": 0.82, "up_prob": 0.82, "down_prob": 0.18, "expected_return": 4.2},
    {"code": "F900001", "name": "南方稳健成长混合A", "prediction": "up", "confidence": 0.71, "up_prob": 0.71, "down_prob": 0.29, "expected_return": 1.9},
    {"code": "F900004", "name": "广发高端制造股票A", "prediction": "up", "confidence": 0.75, "up_prob": 0.75, "down_prob": 0.25, "expected_return": 3.8},
    {"code": "B900001", "name": "招商国债A", "prediction": "neutral", "confidence": 0.60, "up_prob": 0.55, "down_prob": 0.45, "expected_return": 0.3},
    {"code": "G900001", "name": "华安黄金ETF联接A", "prediction": "up", "confidence": 0.80, "up_prob": 0.80, "down_prob": 0.20, "expected_return": 5.1},
    {"code": "E900001", "name": "中证500ETF先锋", "prediction": "up", "confidence": 0.68, "up_prob": 0.68, "down_prob": 0.32, "expected_return": 2.5},
    {"code": "D900001", "name": "环球股息优势基金A", "prediction": "up", "confidence": 0.73, "up_prob": 0.73, "down_prob": 0.27, "expected_return": 2.8},
]


def _get_model():
    """获取模型实例"""
    try:
        from asset_lens.ml.predictor import StockPredictor

        if MODEL_PATH.exists():
            return StockPredictor(model_path=MODEL_PATH)
        return None
    except (ImportError, OSError, ValueError, RuntimeError) as e:
        logger.error(f"加载模型失败: {e}")
        return None


def _get_stock_features(code: str) -> dict[str, Any]:
    """获取股票特征数据"""
    try:
        import akshare as ak

        df = ak.stock_zh_a_hist(symbol=code.split(".")[-1], period="daily", adjust="qfq")
        if df is None or len(df) == 0:
            return {}

        df = df.tail(60)

        closes = df["收盘"].values
        volumes = df["成交量"].values
        highs = df["最高"].values
        lows = df["最低"].values

        features = {
            "close": float(closes[-1]),
            "volume": float(volumes[-1]),
            "ma5": float(closes[-5:].mean()) if len(closes) >= 5 else float(closes[-1]),
            "ma10": float(closes[-10:].mean()) if len(closes) >= 10 else float(closes[-1]),
            "ma20": float(closes[-20:].mean()) if len(closes) >= 20 else float(closes[-1]),
            "high": float(highs[-1]),
            "low": float(lows[-1]),
            "vol_ma5": float(volumes[-5:].mean()) if len(volumes) >= 5 else float(volumes[-1]),
            "price_change_1d": float((closes[-1] - closes[-2]) / closes[-2] * 100) if len(closes) >= 2 else 0,
            "price_change_5d": float((closes[-1] - closes[-5]) / closes[-5] * 100) if len(closes) >= 5 else 0,
            "price_change_20d": float((closes[-1] - closes[-20]) / closes[-20] * 100) if len(closes) >= 20 else 0,
            "volatility_20d": float(closes[-20:].std() / closes[-20:].mean() * 100) if len(closes) >= 20 else 0,
            "high_low_ratio": float(highs[-1] / lows[-1]) if lows[-1] > 0 else 1,
            "volume_ratio": float(volumes[-1] / volumes[-5:].mean()) if volumes[-5:].mean() > 0 else 1,
        }

        return features
    except (ValueError, KeyError, ConnectionError, RuntimeError) as e:
        logger.error(f"获取股票特征失败 {code}: {e}")
        return {}


@router.get("/signals")
async def get_ml_signals() -> dict[str, Any]:
    """
    获取 ML 预测信号

    Returns:
        预测信号列表
    """
    # Demo 模式下返回模拟信号
    if DEMO_MODE:
        signals = []
        for s in DEMO_ML_SIGNALS:
            signals.append({
                "code": s["code"],
                "name": s["name"],
                "prediction": s["prediction"],
                "confidence": s["confidence"],
                "up_prob": s["up_prob"],
                "down_prob": s["down_prob"],
                "expected_return": s["expected_return"],
                "signal_strength": "strong" if s["confidence"] > 0.7 else "medium" if s["confidence"] > 0.6 else "weak",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
        return {
            "signals": signals,
            "model_status": "demo",
            "total": len(signals),
            "message": "Demo 模式 — 预测结果为模拟数据",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    model = _get_model()
    if model is None:
        return {
            "signals": [],
            "model_status": "not_loaded",
            "message": "模型未加载，请先训练模型",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    try:
        from asset_lens.trading.stock_pool import StockPool

        pool = StockPool()
        stocks = pool.list_stocks()

        if not stocks:
            return {
                "signals": [],
                "model_status": "loaded",
                "message": "股票池为空",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

        signals = []
        for stock in stocks[:20]:
            code = stock.get("code", "")
            name = stock.get("name", "")

            features = _get_stock_features(code)
            if not features:
                continue

            try:
                result = model.predict_stock(features, code, name)
                signal = {
                    "code": code,
                    "name": name,
                    "prediction": result.prediction,
                    "confidence": result.confidence,
                    "up_prob": result.up_prob,
                    "down_prob": result.down_prob,
                    "expected_return": result.expected_return,
                    "signal_strength": "strong"
                    if result.confidence > 0.7
                    else "medium"
                    if result.confidence > 0.6
                    else "weak",
                    "timestamp": result.timestamp,
                }
                signals.append(signal)
            except (ValueError, KeyError, RuntimeError) as e:
                logger.warning(f"预测股票 {code} 失败: {e}")
                continue

        signals.sort(key=lambda x: x["confidence"], reverse=True)

        return {
            "signals": signals,
            "model_status": "loaded",
            "total": len(signals),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    except (ValueError, KeyError, RuntimeError, OSError) as e:
        logger.error(f"获取 ML 信号失败: {e}")
        return {
            "signals": [],
            "model_status": "error",
            "message": str(e),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }


@router.get("/signal/{code}")
async def get_stock_signal(code: str) -> dict[str, Any]:
    """
    获取单只股票的 ML 预测信号

    Args:
        code: 股票代码

    Returns:
        预测信号详情
    """
    # Demo 模式下返回模拟信号
    if DEMO_MODE:
        for s in DEMO_ML_SIGNALS:
            if s["code"].upper() == code.upper():
                return {
                    "code": code,
                    "signal": {
                        "prediction": s["prediction"],
                        "confidence": s["confidence"],
                        "up_prob": s["up_prob"],
                        "down_prob": s["down_prob"],
                        "expected_return": s["expected_return"],
                    },
                    "model_status": "demo",
                    "message": "Demo 模式 — 预测结果为模拟数据",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
        # 未找到匹配的代码，返回随机信号
        return {
            "code": code,
            "signal": {
                "prediction": random.choice(["up", "down", "neutral"]),
                "confidence": round(random.uniform(0.5, 0.85), 2),
                "up_prob": round(random.uniform(0.3, 0.7), 2),
                "down_prob": round(random.uniform(0.3, 0.7), 2),
                "expected_return": round(random.uniform(-3, 5), 2),
            },
            "model_status": "demo",
            "message": "Demo 模式 — 预测结果为模拟数据",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    model = _get_model()
    if model is None:
        return {
            "code": code,
            "signal": None,
            "model_status": "not_loaded",
            "message": "模型未加载",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    features = _get_stock_features(code)
    if not features:
        return {
            "code": code,
            "signal": None,
            "model_status": "loaded",
            "message": "无法获取股票数据",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    try:
        result = model.predict_stock(features, code, "")

        return {
            "code": code,
            "signal": {
                "prediction": result.prediction,
                "confidence": result.confidence,
                "up_prob": result.up_prob,
                "down_prob": result.down_prob,
                "expected_return": result.expected_return,
                "features": result.features,
            },
            "model_status": "loaded",
            "timestamp": result.timestamp,
        }
    except (ValueError, KeyError, RuntimeError) as e:
        logger.error(f"预测股票 {code} 失败: {e}")
        return {
            "code": code,
            "signal": None,
            "model_status": "error",
            "message": str(e),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }


@router.get("/model/status")
async def get_model_status() -> dict[str, Any]:
    """
    获取模型状态

    Returns:
        模型状态信息
    """
    # Demo 模式下返回模拟状态
    if DEMO_MODE:
        return {
            "status": "demo",
            "model_type": "simulated",
            "feature_count": 14,
            "model_path": "demo_mode",
            "message": "Demo 模式 — 使用模拟预测数据",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    model = _get_model()

    if model is None:
        return {
            "status": "not_loaded",
            "model_path": str(MODEL_PATH),
            "exists": MODEL_PATH.exists(),
            "message": "模型未加载",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    return {
        "status": "loaded",
        "model_type": model.model_type,
        "feature_count": len(model.feature_names),
        "model_path": str(MODEL_PATH),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


@router.get("/history")
async def get_signal_history(days: int = 30) -> dict[str, Any]:
    """
    获取历史信号记录

    Args:
        days: 查询天数

    Returns:
        历史信号记录
    """
    try:
        from sqlalchemy import text

        from asset_lens.db.database import db_manager

        with db_manager.session_scope() as db:
            result = db.execute(
                text(
                    """
                    SELECT code, name, prediction, confidence, up_prob, down_prob, timestamp
                    FROM ml_signals
                    WHERE timestamp >= datetime('now', :days_str)
                    ORDER BY timestamp DESC
                    LIMIT 100
                """
                ),
                {"days_str": f"-{days} days"},
            )

            rows = result.fetchall()

            history = [
                {
                    "code": row[0],
                    "name": row[1],
                    "prediction": row[2],
                    "confidence": row[3],
                    "up_prob": row[4],
                    "down_prob": row[5],
                    "timestamp": row[6],
                }
                for row in rows
            ]

            return {
                "history": history,
                "total": len(history),
                "days": days,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

    except (ValueError, KeyError, RuntimeError, OSError) as e:
        logger.error(f"获取历史信号失败: {e}")
        return {
            "history": [],
            "total": 0,
            "days": days,
            "message": str(e),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
