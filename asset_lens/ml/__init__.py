"""
Machine Learning Module for asset-lens.
机器学习模块 - 股票预测、因子分析、风险评估

支持的模型:
- LightGBM: 梯度提升树，快速高效
- XGBoost: 梯度提升树，效果优秀
- RandomForest: 随机森林，可解释性强
"""

from .features import FeatureEngineer
from .predictor import StockPredictor
from .trainer import ModelTrainer

__all__ = ["FeatureEngineer", "StockPredictor", "ModelTrainer"]
