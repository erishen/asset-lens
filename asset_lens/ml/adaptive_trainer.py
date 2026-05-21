"""
Adaptive ML Trainer with AI Market Analysis.
AI驱动的自适应机器学习训练器

流程:
1. AI分析当前市场行情 (牛市/熊市/震荡市)
2. 根据行情调整策略参数
3. 筛选适合当前行情的股票池
4. 针对性训练模型
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class MarketCondition(Enum):
    """市场行情状态"""

    BULL = "bull"  # 牛市
    BEAR = "bear"  # 熊市
    SIDEWAYS = "sideways"  # 震荡市
    VOLATILE = "volatile"  # 高波动


@dataclass
class MarketAnalysis:
    """市场分析结果"""

    condition: MarketCondition
    confidence: float
    indicators: dict[str, Any]
    recommendation: str
    risk_level: str
    suggested_strategy: str


class AIMarketAnalyzer:
    """AI市场分析器"""

    def __init__(self):
        self.market_indicators = {}

    def analyze_market(self, market_data: dict | None = None) -> MarketAnalysis:
        """
        分析市场行情

        Args:
            market_data: 市场数据 (指数、涨跌分布等)

        Returns:
            市场分析结果
        """
        if market_data is None:
            market_data = self._get_default_market_data()

        indicators = self._calculate_market_indicators(market_data)
        condition = self._determine_market_condition(indicators)
        recommendation = self._generate_recommendation(condition, indicators)

        return MarketAnalysis(
            condition=condition,
            confidence=indicators.get("confidence", 0.5),
            indicators=indicators,
            recommendation=recommendation,
            risk_level=self._assess_risk_level(condition, indicators),
            suggested_strategy=self._suggest_strategy(condition),
        )

    def _get_default_market_data(self) -> dict[str, Any]:
        """获取默认市场数据"""
        try:
            from ..data.market_stock_fetcher import MarketStockFetcher

            fetcher = MarketStockFetcher()
            stocks = fetcher.get_cached_market_stocks()

            if not stocks:
                return {"avg_change": 0, "up_ratio": 0.5, "volatility": 0.02}

            changes = [s.get("change_percent", 0) for s in stocks if s.get("change_percent")]
            turnovers = [s.get("turnover_rate", 0) for s in stocks if s.get("turnover_rate")]

            up_stocks = len([c for c in changes if c > 0])
            down_stocks = len([c for c in changes if c < 0])

            return {
                "avg_change": np.mean(changes) if changes else 0,
                "up_ratio": up_stocks / len(changes) if changes else 0.5,
                "volatility": np.std(changes) if changes else 0.02,
                "avg_turnover": np.mean(turnovers) if turnovers else 0,
                "total_stocks": len(stocks),
                "up_stocks": up_stocks,
                "down_stocks": down_stocks,
            }
        except Exception as e:
            logger.warning(f"获取市场数据失败: {e}")
            return {"avg_change": 0, "up_ratio": 0.5, "volatility": 0.02}

    def _calculate_market_indicators(self, data: dict) -> dict[str, Any]:
        """计算市场指标"""
        avg_change = data.get("avg_change", 0)
        up_ratio = data.get("up_ratio", 0.5)
        volatility = data.get("volatility", 0.02)

        trend_score = avg_change * 10 + (up_ratio - 0.5) * 20

        confidence = min(1.0, abs(trend_score) / 5 + 0.3)

        return {
            "avg_change": avg_change,
            "up_ratio": up_ratio,
            "volatility": volatility,
            "trend_score": trend_score,
            "confidence": confidence,
            "breadth": up_ratio,
        }

    def _determine_market_condition(self, indicators: dict) -> MarketCondition:
        """判断市场状态"""
        trend_score = indicators.get("trend_score", 0)
        volatility = indicators.get("volatility", 0.02)
        up_ratio = indicators.get("up_ratio", 0.5)

        if volatility > 0.04:
            return MarketCondition.VOLATILE
        elif trend_score > 2 and up_ratio > 0.6:
            return MarketCondition.BULL
        elif trend_score < -2 and up_ratio < 0.4:
            return MarketCondition.BEAR
        else:
            return MarketCondition.SIDEWAYS

    def _generate_recommendation(self, condition: MarketCondition, indicators: dict) -> str:
        """生成投资建议"""
        recommendations = {
            MarketCondition.BULL: "市场处于上涨趋势，可适当增加仓位，关注强势股",
            MarketCondition.BEAR: "市场处于下跌趋势，建议降低仓位，关注防御性股票",
            MarketCondition.SIDEWAYS: "市场震荡，建议轻仓操作，高抛低吸",
            MarketCondition.VOLATILE: "市场波动剧烈，建议谨慎操作，控制风险",
        }
        return recommendations.get(condition, "建议观望")

    def _assess_risk_level(self, condition: MarketCondition, indicators: dict) -> str:
        """评估风险等级"""
        volatility = indicators.get("volatility", 0.02)

        if condition == MarketCondition.VOLATILE or volatility > 0.05:
            return "高"
        elif condition == MarketCondition.BEAR:
            return "中高"
        elif condition == MarketCondition.SIDEWAYS:
            return "中"
        else:
            return "中低"

    def _suggest_strategy(self, condition: MarketCondition) -> str:
        """建议策略"""
        strategies = {
            MarketCondition.BULL: "momentum",
            MarketCondition.BEAR: "dividend",
            MarketCondition.SIDEWAYS: "value",
            MarketCondition.VOLATILE: "reversal",
        }
        return strategies.get(condition, "value")


class AdaptiveStrategyConfig:
    """自适应策略配置"""

    CONFIGS = {
        MarketCondition.BULL: {
            "prediction_days": 3,
            "positive_threshold": 0.03,
            "negative_threshold": -0.01,
            "min_turnover": 3.0,
            "max_turnover": 15.0,
            "min_market_cap": 50,
            "max_market_cap": 1000,
            "description": "牛市策略：追求短期收益，关注高活跃股票",
        },
        MarketCondition.BEAR: {
            "prediction_days": 10,
            "positive_threshold": 0.02,
            "negative_threshold": -0.03,
            "min_turnover": 0.5,
            "max_turnover": 5.0,
            "min_market_cap": 100,
            "max_market_cap": 5000,
            "description": "熊市策略：保守投资，关注大盘蓝筹",
        },
        MarketCondition.SIDEWAYS: {
            "prediction_days": 5,
            "positive_threshold": 0.02,
            "negative_threshold": -0.02,
            "min_turnover": 1.0,
            "max_turnover": 8.0,
            "min_market_cap": 50,
            "max_market_cap": 1000,
            "description": "震荡市策略：均衡配置，适度交易",
        },
        MarketCondition.VOLATILE: {
            "prediction_days": 3,
            "positive_threshold": 0.05,
            "negative_threshold": -0.02,
            "min_turnover": 2.0,
            "max_turnover": 10.0,
            "min_market_cap": 100,
            "max_market_cap": 2000,
            "description": "高波动策略：快进快出，严格止损",
        },
    }

    @classmethod
    def get_config(cls, condition: MarketCondition) -> dict[str, Any]:
        """获取策略配置"""
        return cls.CONFIGS.get(condition, cls.CONFIGS[MarketCondition.SIDEWAYS])


class AdaptiveMLTrainer:
    """自适应ML训练器"""

    def __init__(self):
        self.market_analyzer = AIMarketAnalyzer()
        self.current_analysis: MarketAnalysis | None = None

    def analyze_and_train(
        self,
        custom_market_data: dict | None = None,
        model_type: str = "lightgbm",
    ) -> dict[str, Any]:
        """
        分析市场并训练模型

        Args:
            custom_market_data: 自定义市场数据
            model_type: 模型类型

        Returns:
            训练结果
        """
        from rich.console import Console
        from rich.table import Table

        console = Console()

        console.print("\n" + "=" * 60)
        console.print("  🤖 AI驱动的自适应ML训练")
        console.print("=" * 60)

        console.print("\n📊 第一步: AI分析市场行情...")
        self.current_analysis = self.market_analyzer.analyze_market(custom_market_data)

        analysis = self.current_analysis
        console.print(f"\n  市场状态: [bold]{analysis.condition.value.upper()}[/bold]")
        console.print(f"  置信度: {analysis.confidence:.1%}")
        console.print(f"  风险等级: {analysis.risk_level}")
        console.print(f"  建议: {analysis.recommendation}")

        strategy_config = AdaptiveStrategyConfig.get_config(analysis.condition)
        console.print("\n📋 第二步: 调整策略参数...")
        console.print(f"  策略: {strategy_config['description']}")
        console.print(f"  预测天数: {strategy_config['prediction_days']}天")
        console.print(
            f"  涨跌阈值: {strategy_config['positive_threshold']:.1%} / {strategy_config['negative_threshold']:.1%}"
        )

        console.print("\n🎯 第三步: 筛选股票池...")
        stock_pool = self._select_stock_pool(strategy_config)
        console.print(f"  符合条件股票: {len(stock_pool)} 只")

        if len(stock_pool) < 10:
            console.print("[yellow]  股票数量不足，使用默认股票池[/yellow]")
            stock_pool = self._get_default_stock_pool()

        console.print("\n🚀 第四步: 训练模型...")
        result = self._train_with_config(stock_pool, strategy_config, model_type)

        console.print("\n📈 训练结果:")
        result_table = Table(show_header=False)
        result_table.add_column("指标", style="cyan")
        result_table.add_column("值", justify="right")

        result_table.add_row("市场状态", analysis.condition.value.upper())
        result_table.add_row("策略类型", strategy_config["description"][:20])
        result_table.add_row("准确率", f"{result.get('accuracy', 0):.2%}")
        result_table.add_row("AUC", f"{result.get('auc', 0):.2%}")
        result_table.add_row("训练样本", str(result.get("train_samples", 0)))

        console.print(result_table)

        return {
            "market_analysis": {
                "condition": analysis.condition.value,
                "confidence": analysis.confidence,
                "risk_level": analysis.risk_level,
                "recommendation": analysis.recommendation,
            },
            "strategy_config": strategy_config,
            "training_result": result,
            "stock_pool_size": len(stock_pool),
        }

    def _select_stock_pool(self, config: dict) -> list[str]:
        """根据策略配置筛选股票池"""
        try:
            from ..data.market_stock_fetcher import MarketStockFetcher

            fetcher = MarketStockFetcher()
            stocks = fetcher.get_cached_market_stocks()

            selected = []
            for stock in stocks:
                code = stock.get("code", "")
                name = stock.get("name", "")
                if not code or not name:
                    continue
                if "ST" in name or "*" in name:
                    continue

                market_cap = stock.get("market_cap", 0)
                turnover = stock.get("turnover_rate", 0)

                if (
                    config["min_market_cap"] <= market_cap <= config["max_market_cap"]
                    and config["min_turnover"] <= turnover <= config["max_turnover"]
                ):
                    selected.append(code)

            return selected[:200]
        except Exception as e:
            logger.warning(f"筛选股票池失败: {e}")
            return self._get_default_stock_pool()

    def _get_default_stock_pool(self) -> list[str]:
        """获取默认股票池"""
        try:
            from ..db.database import db_manager

            return db_manager.get_stock_codes()[:100]
        except Exception as e:
            logger.debug(f"忽略异常: {e}")
            return ["sh600519", "sh601318", "sh600036", "sz000001", "sz000002"]

    def _train_with_config(
        self,
        stock_pool: list[str],
        config: dict,
        model_type: str,
    ) -> dict[str, Any]:
        """使用配置训练模型"""
        from ..db.database import db_manager
        from .trainer import ModelTrainer, TrainingConfig

        klines_data = db_manager.get_klines_for_ml(codes=stock_pool, days=250)

        if not klines_data:
            return {"error": "没有足够的数据"}

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
            return {"error": "没有有效的训练数据"}

        training_config = TrainingConfig(
            prediction_days=config["prediction_days"],
            positive_threshold=config["positive_threshold"],
            negative_threshold=config["negative_threshold"],
        )

        trainer = ModelTrainer(model_type=model_type, config=training_config)

        result = trainer.train_with_market_data(stocks_data)

        output_path = Path("cache/ml/model_adaptive.pkl")
        trainer.save_model(output_path)

        return {
            "accuracy": result.accuracy,
            "precision": result.precision,
            "recall": result.recall,
            "f1_score": result.f1_score,
            "auc": result.auc,
            "train_samples": result.training_samples,
            "test_samples": result.test_samples,
        }


from pathlib import Path

adaptive_trainer = AdaptiveMLTrainer()
