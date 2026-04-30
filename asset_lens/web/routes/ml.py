"""
ML Prediction API Routes.
ML 预测信号 API 路由
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ml", tags=["ml"])

MODEL_PATH = Path(__file__).parent.parent.parent / "models" / "stock_predictor.joblib"


def _get_model():
    """获取模型实例"""
    try:
        from asset_lens.ml.predictor import StockPredictor

        if MODEL_PATH.exists():
            return StockPredictor(model_path=MODEL_PATH)
        return None
    except Exception as e:
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
    except Exception as e:
        logger.error(f"获取股票特征失败 {code}: {e}")
        return {}


@router.get("/signals")
async def get_ml_signals() -> dict[str, Any]:
    """
    获取 ML 预测信号

    Returns:
        预测信号列表
    """
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
            except Exception as e:
                logger.warning(f"预测股票 {code} 失败: {e}")
                continue

        signals.sort(key=lambda x: x["confidence"], reverse=True)

        return {
            "signals": signals,
            "model_status": "loaded",
            "total": len(signals),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    except Exception as e:
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
    except Exception as e:
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

            history = []
            for row in rows:
                history.append(
                    {
                        "code": row[0],
                        "name": row[1],
                        "prediction": row[2],
                        "confidence": row[3],
                        "up_prob": row[4],
                        "down_prob": row[5],
                        "timestamp": row[6],
                    }
                )

            return {
                "history": history,
                "total": len(history),
                "days": days,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

    except Exception as e:
        logger.error(f"获取历史信号失败: {e}")
        return {
            "history": [],
            "total": 0,
            "days": days,
            "message": str(e),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
