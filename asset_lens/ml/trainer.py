"""
Model Trainer for Machine Learning.
模型训练器 - 训练、评估、优化机器学习模型

功能:
- 数据准备: 生成训练标签
- 模型训练: 支持多种模型
- 模型评估: 准确率、精确率、召回率、F1
- 回测验证: 验证模型历史表现
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

try:
    from sklearn.metrics import (
        accuracy_score,
        f1_score,
        precision_score,
        recall_score,
        roc_auc_score,
    )
    from sklearn.model_selection import TimeSeriesSplit, cross_val_score, train_test_split

    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    logger.warning("sklearn 未安装")

from .features import FeatureEngineer
from .predictor import StockPredictor


@dataclass
class TrainingConfig:
    """训练配置"""

    prediction_days: int = 5
    positive_threshold: float = 0.02
    negative_threshold: float = -0.02
    test_size: float = 0.2
    cv_folds: int = 5
    random_state: int = 42


@dataclass
class TrainingResult:
    """训练结果"""

    model_type: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    auc: float
    cv_scores: list[float]
    feature_importance: pd.DataFrame
    training_samples: int
    test_samples: int
    training_time: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_type": self.model_type,
            "accuracy": round(self.accuracy, 4),
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1_score": round(self.f1_score, 4),
            "auc": round(self.auc, 4),
            "cv_scores": [round(s, 4) for s in self.cv_scores],
            "feature_importance": self.feature_importance.head(10).to_dict("records"),
            "training_samples": self.training_samples,
            "test_samples": self.test_samples,
            "training_time": round(self.training_time, 2),
            "timestamp": self.timestamp,
        }


class ModelTrainer:
    """模型训练器"""

    def __init__(
        self,
        model_type: str = "lightgbm",
        config: TrainingConfig | None = None,
    ):
        self.model_type = model_type
        self.config = config or TrainingConfig()
        self.feature_engineer = FeatureEngineer()
        self.predictor = StockPredictor(model_type=model_type)

    def prepare_training_data(
        self,
        price_data: pd.DataFrame,
        code: str = "",
    ) -> tuple[pd.DataFrame, pd.Series]:
        """
        准备训练数据

        Args:
            price_data: 价格数据，需包含 close, high, low, volume 等列
            code: 股票代码

        Returns:
            X: 特征数据
            y: 标签数据
        """
        df = self.feature_engineer.calculate_all_features(price_data)

        future_return = df["close"].shift(-self.config.prediction_days) / df["close"] - 1

        def label_return(r):
            if pd.isna(r):
                return -1
            if r >= self.config.positive_threshold:
                return 1
            elif r <= self.config.negative_threshold:
                return 0
            else:
                return -1

        y = future_return.apply(label_return)

        valid_mask = y != -1
        X = df[valid_mask].copy()
        y = y[valid_mask].copy()

        feature_cols = self.feature_engineer.feature_names
        X = X[feature_cols].fillna(0)
        X = X.replace([np.inf, -np.inf], 0)

        logger.info(f"准备训练数据: {len(X)} 样本, {len(feature_cols)} 特征")

        return X, y

    def prepare_multi_stock_data(
        self,
        stocks_data: dict[str, pd.DataFrame],
    ) -> tuple[pd.DataFrame, pd.Series]:
        """
        准备多股票训练数据

        Args:
            stocks_data: 多只股票的价格数据 {code: DataFrame}

        Returns:
            X: 特征数据
            y: 标签数据
        """
        all_X = []
        all_y = []

        for code, df in stocks_data.items():
            try:
                X, y = self.prepare_training_data(df, code)
                all_X.append(X)
                all_y.append(y)
            except (ValueError, KeyError, RuntimeError) as e:
                logger.warning(f"处理股票 {code} 失败: {e}")
                continue

        if not all_X:
            raise ValueError("没有有效的训练数据")

        X = pd.concat(all_X, ignore_index=True)
        y = pd.concat(all_y, ignore_index=True)

        logger.info(f"多股票训练数据: {len(X)} 样本, 来自 {len(stocks_data)} 只股票")

        return X, y

    def train(self, X: pd.DataFrame, y: pd.Series, **kwargs) -> TrainingResult:
        """
        训练模型

        Args:
            X: 特征数据
            y: 标签数据

        Returns:
            训练结果
        """
        import time

        start_time = time.time()

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=self.config.test_size, random_state=self.config.random_state, stratify=y
        )

        self.predictor.fit(X_train, y_train, **kwargs)  # type: ignore[call-arg]

        y_pred = self.predictor.predict(X_test)
        y_proba = self.predictor.predict_proba(X_test)[:, 1]

        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)

        try:
            auc = roc_auc_score(y_test, y_proba)
        except ValueError:
            auc = 0.5

        if self.model_type == "ensemble":
            cv_scores = [accuracy]
        else:
            tscv = TimeSeriesSplit(n_splits=self.config.cv_folds)
            cv_scores = cross_val_score(self.predictor.model, X, y, cv=tscv, scoring="accuracy")

        feature_importance = self.predictor.get_feature_importance()

        training_time = time.time() - start_time

        result = TrainingResult(
            model_type=self.model_type,
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            auc=auc,
            cv_scores=list(cv_scores),
            feature_importance=feature_importance,
            training_samples=len(X_train),
            test_samples=len(X_test),
            training_time=training_time,
        )

        logger.info(f"训练完成: Accuracy={accuracy:.4f}, F1={f1:.4f}, AUC={auc:.4f}")

        return result

    def train_with_market_data(self, stocks_data: dict[str, pd.DataFrame], **kwargs) -> TrainingResult:
        """
        使用市场数据训练模型

        Args:
            stocks_data: 多只股票的价格数据

        Returns:
            训练结果
        """
        X, y = self.prepare_multi_stock_data(stocks_data)
        return self.train(X, y, **kwargs)

    def backtest(
        self,
        price_data: pd.DataFrame,
        initial_capital: float = 100000,
        position_size: float = 0.1,
    ) -> dict[str, Any]:
        """
        回测模型表现

        Args:
            price_data: 价格数据
            initial_capital: 初始资金
            position_size: 仓位比例

        Returns:
            回测结果
        """
        df = self.feature_engineer.calculate_all_features(price_data)

        X = df[self.feature_engineer.feature_names].fillna(0)
        X = X.replace([np.inf, -np.inf], 0)

        predictions = self.predictor.predict(X)
        probas = self.predictor.predict_proba(X)[:, 1]

        df["prediction"] = predictions
        df["up_prob"] = probas
        df["position"] = 0

        df.loc[(df["prediction"] == 1) & (df["up_prob"] > 0.6), "position"] = 1

        df["returns"] = df["close"].pct_change()
        df["strategy_returns"] = df["position"].shift(1) * df["returns"]

        df["capital"] = initial_capital * (1 + df["strategy_returns"]).cumprod()

        total_return = (df["capital"].iloc[-1] / initial_capital - 1) * 100
        max_drawdown = (df["capital"] / df["capital"].cummax() - 1).min() * 100
        sharpe_ratio = df["strategy_returns"].mean() / df["strategy_returns"].std() * np.sqrt(252)

        win_trades = (df["strategy_returns"] > 0).sum()
        total_trades = (df["position"] == 1).sum()
        win_rate = win_trades / total_trades * 100 if total_trades > 0 else 0

        return {
            "total_return": round(total_return, 2),
            "max_drawdown": round(max_drawdown, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "win_rate": round(win_rate, 2),
            "total_trades": total_trades,
            "final_capital": round(df["capital"].iloc[-1], 2),
        }

    def save_model(self, path: Path) -> None:
        """保存模型"""
        self.predictor.save_model(path)

    def load_model(self, path: Path) -> None:
        """加载模型"""
        self.predictor.load_model(path)
        self.feature_engineer.feature_names = self.predictor.feature_names  # type: ignore[attr-defined]

    def save_training_result(self, result: Any, path: Path) -> None:
        """保存训练结果"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

        logger.info(f"训练结果已保存: {path}")

    def train_from_database(self, codes: list[str] | None = None, days: int = 250, **kwargs) -> TrainingResult:
        """
        从数据库读取数据并训练模型

        Args:
            codes: 股票代码列表，为空则使用所有可用数据
            days: 历史天数

        Returns:
            训练结果
        """
        from ..db.database import db_manager

        logger.info(f"从数据库获取训练数据: {len(codes) if codes else '所有'} 只股票, {days} 天")

        klines_data = db_manager.get_klines_for_ml(codes=codes, days=days)

        if not klines_data:
            raise ValueError("数据库中没有足够的K线数据，请先运行 'asset-lens db fetch' 获取数据")

        stocks_data = {}
        for code, klines in klines_data.items():
            if len(klines) < 30:
                continue

            df = pd.DataFrame(klines)
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").reset_index(drop=True)

            for col in ["open", "close", "high", "low", "volume", "amount"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

            stocks_data[code] = df

        if not stocks_data:
            raise ValueError("没有足够的数据用于训练")

        logger.info(f"成功加载 {len(stocks_data)} 只股票的数据")

        result = self.train_with_market_data(stocks_data, **kwargs)

        try:
            from ..db.database import db_manager

            fi_df = result.feature_importance.head(20)
            feature_importance_dict = dict(zip(fi_df["feature"], fi_df["importance"], strict=False))

            model_id = db_manager.save_ml_model(
                name="stock_predictor",
                model_type=self.model_type,
                params=self.predictor.model.get_params() if hasattr(self.predictor.model, "get_params") else {},
                feature_importance=feature_importance_dict,
                metrics={
                    "accuracy": result.accuracy,
                    "precision": result.precision,
                    "recall": result.recall,
                    "f1_score": result.f1_score,
                    "auc": result.auc,
                },
                train_samples=result.training_samples,
                train_features=len(self.feature_engineer.feature_names),
            )
            logger.info(f"模型记录已保存到数据库: ID={model_id}")
        except (ValueError, KeyError, OSError, RuntimeError) as e:
            logger.warning(f"保存模型记录到数据库失败: {e}")

        return result

    def predict_and_save(
        self,
        code: str,
        save_to_db: bool = True,
    ) -> dict[str, Any]:
        """
        预测单只股票并保存结果

        Args:
            code: 股票代码
            save_to_db: 是否保存到数据库

        Returns:
            预测结果
        """
        from ..db.database import db_manager

        klines = db_manager.get_klines(code, limit=250)

        if len(klines) < 30:
            return {"error": "数据不足", "code": code}

        df = pd.DataFrame(klines)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)

        for col in ["open", "close", "high", "low", "volume", "amount"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        result = self.predictor.predict_stock(df.to_dict("records")[0] if not df.empty else {}, code=code)

        if save_to_db:
            try:
                model_info = db_manager.get_latest_model("stock_predictor")
                if model_info:
                    db_manager.save_prediction(
                        model_id=model_info["id"],
                        code=code,
                        prediction=1 if result.prediction == "up" else 0,
                        confidence=result.confidence,
                        features={"latest_close": float(df["close"].iloc[-1])},
                    )
            except (ValueError, KeyError, OSError, RuntimeError) as e:
                logger.warning(f"保存预测记录失败: {e}")

        return {
            "code": result.code,
            "name": result.name,
            "prediction": result.prediction,
            "confidence": result.confidence,
            "up_prob": result.up_prob,
            "down_prob": result.down_prob,
            "expected_return": result.expected_return,
        }
