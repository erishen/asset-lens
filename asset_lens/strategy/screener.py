"""
Stock screener for asset-lens.
股票筛选模块 - 多维度综合筛选最佳股票

功能:
1. 基本面筛选 - PE/PB/ROE/营收增长等
2. 技术面筛选 - 均线/MACD/RSI等
3. 综合评分系统 - 多因子打分排名
4. 自定义策略 - 可配置筛选条件
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..config import config


@dataclass
class FundamentalConfig:
    """基本面筛选配置"""

    pe_max: float = 30.0
    pe_min: float = 0.0
    pb_max: float = 5.0
    pb_min: float = 0.0
    roe_min: float = 10.0
    revenue_growth_min: float = 0.0
    profit_growth_min: float = 0.0
    debt_ratio_max: float = 70.0
    market_cap_min: float = 20.0
    market_cap_max: float = 1000.0


@dataclass
class TechnicalConfig:
    """技术面筛选配置"""

    ma_trend: bool = True
    macd_golden_cross: bool = False
    rsi_oversold: bool = False
    rsi_overbought: bool = False
    rsi_min: float = 30.0
    rsi_max: float = 70.0
    volume_breakout: bool = False
    volume_ratio_min: float = 2.0
    price_above_ma20: bool = False
    price_above_ma60: bool = False


@dataclass
class ScoringWeights:
    """评分权重配置"""

    fundamental: float = 0.4
    technical: float = 0.3
    capital_flow: float = 0.2
    industry: float = 0.1


@dataclass
class ScreenerConfig:
    """筛选器总配置"""

    fundamental: FundamentalConfig = field(default_factory=FundamentalConfig)
    technical: TechnicalConfig = field(default_factory=TechnicalConfig)
    scoring_weights: ScoringWeights = field(default_factory=ScoringWeights)
    max_results: int = 20
    min_score: float = 60.0


class StockScreener:
    """股票筛选器"""

    def __init__(self, config_path: Path | None = None):
        self.config_path = config_path or config.project_root / "config" / "stock_screener.json"
        self.screener_config = self._load_config()
        self.cache_path = config.cache_path

    def _load_config(self) -> ScreenerConfig:
        """加载配置"""
        if not self.config_path.exists():
            return ScreenerConfig()

        try:
            with open(self.config_path, encoding="utf-8") as f:
                data = json.load(f)

            fundamental_data = data.get("fundamental", {})
            technical_data = data.get("technical", {})
            weights_data = data.get("scoring_weights", {})

            return ScreenerConfig(
                fundamental=FundamentalConfig(
                    pe_max=fundamental_data.get("pe_max", 30.0),
                    pe_min=fundamental_data.get("pe_min", 0.0),
                    pb_max=fundamental_data.get("pb_max", 5.0),
                    pb_min=fundamental_data.get("pb_min", 0.0),
                    roe_min=fundamental_data.get("roe_min", 10.0),
                    revenue_growth_min=fundamental_data.get("revenue_growth_min", 0.0),
                    profit_growth_min=fundamental_data.get("profit_growth_min", 0.0),
                    debt_ratio_max=fundamental_data.get("debt_ratio_max", 70.0),
                    market_cap_min=fundamental_data.get("market_cap_min", 20.0),
                    market_cap_max=fundamental_data.get("market_cap_max", 1000.0),
                ),
                technical=TechnicalConfig(
                    ma_trend=technical_data.get("ma_trend", True),
                    macd_golden_cross=technical_data.get("macd_golden_cross", False),
                    rsi_oversold=technical_data.get("rsi_oversold", False),
                    rsi_overbought=technical_data.get("rsi_overbought", False),
                    rsi_min=technical_data.get("rsi_min", 30.0),
                    rsi_max=technical_data.get("rsi_max", 70.0),
                    volume_breakout=technical_data.get("volume_breakout", False),
                    volume_ratio_min=technical_data.get("volume_ratio_min", 2.0),
                    price_above_ma20=technical_data.get("price_above_ma20", False),
                    price_above_ma60=technical_data.get("price_above_ma60", False),
                ),
                scoring_weights=ScoringWeights(
                    fundamental=weights_data.get("fundamental", 0.4),
                    technical=weights_data.get("technical", 0.3),
                    capital_flow=weights_data.get("capital_flow", 0.2),
                    industry=weights_data.get("industry", 0.1),
                ),
                max_results=data.get("max_results", 20),
                min_score=data.get("min_score", 60.0),
            )
        except Exception:
            return ScreenerConfig()

    def _load_market_stocks(self) -> list[dict[str, Any]]:
        """加载市场股票数据"""
        market_file = self.cache_path / "market_stocks.json"
        if market_file.exists():
            with open(market_file, encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)
                stocks_list: list[dict[str, Any]] = data.get("data", [])
                return stocks_list
        return []

    def _load_stock_history(self, code: str) -> dict[str, Any] | None:
        """加载股票历史数据"""
        history_file = self.cache_path / "stock_history_baostock.json"
        if history_file.exists():
            with open(history_file, encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)
                history_data: dict[str, Any] = data.get("data", {})
                if history_data and isinstance(history_data, dict):
                    history: dict[str, Any] | None = history_data.get(code)
                    return history
        return None

    def filter_by_fundamental(self, stocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        基本面筛选

        Args:
            stocks: 股票列表

        Returns:
            符合条件的股票列表
        """
        cfg = self.screener_config.fundamental
        results = []

        for stock in stocks:
            name = stock.get("name", "")
            if any(kw in name for kw in ["ST", "退", "ETF", "基金", "指数"]):
                continue

            pe = stock.get("pe_ratio", 0)
            if pe <= 0 or pe > cfg.pe_max or pe < cfg.pe_min:
                continue

            market_cap = stock.get("market_cap", 0)
            if market_cap < cfg.market_cap_min or market_cap > cfg.market_cap_max:
                continue

            results.append(
                {
                    **stock,
                    "fundamental_pass": True,
                    "fundamental_score": self._calculate_fundamental_score(stock),
                }
            )

        return results

    def _calculate_fundamental_score(self, stock: dict[str, Any]) -> float:
        """计算基本面得分"""
        score = 0.0

        pe = stock.get("pe_ratio", 0)
        if 0 < pe < 15:
            score += 30
        elif 15 <= pe < 25:
            score += 20
        elif 25 <= pe < 35:
            score += 10

        market_cap = stock.get("market_cap", 0)
        if 50 <= market_cap <= 200:
            score += 20
        elif 20 <= market_cap < 50 or 200 < market_cap <= 500:
            score += 15
        elif market_cap > 500:
            score += 10

        turnover = stock.get("turnover_rate", 0)
        if 3 <= turnover <= 10:
            score += 20
        elif 1 <= turnover < 3 or 10 < turnover <= 15:
            score += 10

        change = stock.get("change_percent", 0)
        if -3 <= change <= 3:
            score += 10
        elif -5 <= change < -3 or 3 < change <= 5:
            score += 5

        if change > 0:
            score += 20
        elif change < -5:
            score -= 10

        return min(100, max(0, score))

    def filter_by_technical(
        self, stocks: list[dict[str, Any]], histories: dict[str, dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        技术面筛选

        Args:
            stocks: 股票列表
            histories: 历史数据字典

        Returns:
            符合条件的股票列表
        """
        cfg = self.screener_config.technical
        results = []

        for stock in stocks:
            code = stock.get("code", "")
            history = histories.get(code)

            if not history:
                continue

            klines = history.get("klines", [])
            if len(klines) < 20:
                continue

            technical_score = self._calculate_technical_score(stock, klines)
            technical_pass = self._check_technical_conditions(stock, klines, cfg)

            if technical_pass:
                results.append(
                    {
                        **stock,
                        "technical_pass": True,
                        "technical_score": technical_score,
                    }
                )

        return results

    def _calculate_technical_score(self, stock: dict[str, Any], klines: list[dict]) -> float:
        """计算技术面得分"""
        score = 0.0

        closes = [k.get("close", 0) for k in klines[-20:] if k.get("close")]
        if len(closes) < 20:
            return 0

        ma5 = sum(closes[:5]) / 5
        ma10 = sum(closes[:10]) / 10
        ma20 = sum(closes) / 20
        current = closes[0]

        if ma5 > ma10 > ma20:
            score += 30
        elif ma5 > ma10:
            score += 15

        if current > ma5:
            score += 15
        if current > ma20:
            score += 10

        volumes = [k.get("volume", 0) for k in klines[-5:] if k.get("volume")]
        if volumes:
            avg_volume = sum(volumes[1:]) / len(volumes[1:]) if len(volumes) > 1 else volumes[0]
            if volumes[0] > avg_volume * 1.5:
                score += 15
            elif volumes[0] > avg_volume:
                score += 8

        change = stock.get("change_percent", 0)
        if 0 < change <= 5:
            score += 15
        elif 5 < change <= 9:
            score += 10
        elif change > 9:
            score += 5

        return min(100, max(0, score))

    def _check_technical_conditions(self, _stock: dict[str, Any], klines: list[dict], cfg: TechnicalConfig) -> bool:
        """检查技术面条件"""
        closes = [k.get("close", 0) for k in klines[-60:] if k.get("close")]
        if len(closes) < 20:
            return False

        ma5 = sum(closes[:5]) / 5
        ma10 = sum(closes[:10]) / 10
        ma20 = sum(closes[:20]) / 20
        ma60 = sum(closes) / len(closes) if len(closes) >= 60 else ma20
        current = closes[0]

        if cfg.ma_trend and not (ma5 > ma10 > ma20):
            return False

        if cfg.price_above_ma20 and current < ma20:
            return False

        return not (cfg.price_above_ma60 and current < ma60)

    def calculate_comprehensive_score(self, stock: dict[str, Any]) -> dict[str, Any]:
        """
        计算综合评分

        Args:
            stock: 股票数据

        Returns:
            包含评分的股票数据
        """
        weights = self.screener_config.scoring_weights

        fundamental_score = stock.get("fundamental_score", 50)
        technical_score = stock.get("technical_score", 50)

        capital_score = 50
        turnover = stock.get("turnover_rate", 0)
        if 3 <= turnover <= 10:
            capital_score = 70
        elif turnover > 10:
            capital_score = 60

        industry_score = 50
        name = stock.get("name", "")
        hot_keywords = ["科技", "新能源", "医药", "半导体", "人工智能", "AI"]
        for kw in hot_keywords:
            if kw in name:
                industry_score = 70
                break

        total_score = (
            fundamental_score * weights.fundamental
            + technical_score * weights.technical
            + capital_score * weights.capital_flow
            + industry_score * weights.industry
        )

        return {
            **stock,
            "fundamental_score": round(fundamental_score, 1),
            "technical_score": round(technical_score, 1),
            "capital_score": round(capital_score, 1),
            "industry_score": round(industry_score, 1),
            "total_score": round(total_score, 1),
        }

    def screen(
        self,
        stocks: list[dict[str, Any]] | None = None,
        filter_type: str = "comprehensive",
    ) -> list[dict[str, Any]]:
        """
        综合筛选

        Args:
            stocks: 股票列表，如果为空则从缓存加载
            filter_type: 筛选类型 (fundamental/technical/comprehensive)

        Returns:
            筛选结果列表
        """
        if stocks is None:
            stocks = self._load_market_stocks()

        if not stocks:
            return []

        print(f"📊 开始筛选 {len(stocks)} 只股票...")
        print(f"   筛选类型: {filter_type}")

        if filter_type == "fundamental":
            results = self.filter_by_fundamental(stocks)
        elif filter_type == "technical":
            histories = {}
            history_file = self.cache_path / "stock_history_baostock.json"
            if history_file.exists():
                with open(history_file, encoding="utf-8") as f:
                    data = json.load(f)
                    histories = data.get("data", {})
            results = self.filter_by_technical(stocks, histories)
        else:
            fundamental_results = self.filter_by_fundamental(stocks)
            histories = {}
            history_file = self.cache_path / "stock_history_baostock.json"
            if history_file.exists():
                with open(history_file, encoding="utf-8") as f:
                    data = json.load(f)
                    histories = data.get("data", {})
            results = self.filter_by_technical(fundamental_results, histories)

        scored_results = []
        for stock in results:
            scored = self.calculate_comprehensive_score(stock)
            if scored.get("total_score", 0) >= self.screener_config.min_score:
                scored_results.append(scored)

        scored_results.sort(key=lambda x: x.get("total_score", 0), reverse=True)

        return scored_results[: self.screener_config.max_results]

    def screen_with_custom_strategy(
        self,
        stocks: list[dict[str, Any]] | None = None,
        strategy: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        自定义策略筛选

        Args:
            stocks: 股票列表
            strategy: 自定义策略配置

        Returns:
            筛选结果列表
        """
        if stocks is None:
            stocks = self._load_market_stocks()

        if not stocks:
            return []

        if strategy is None:
            strategy = {}

        print(f"📊 使用自定义策略筛选 {len(stocks)} 只股票...")

        results = []
        for stock in stocks:
            name = stock.get("name", "")
            if any(kw in name for kw in ["ST", "退", "ETF", "基金", "指数"]):
                continue

            score = 0
            conditions_met = 0
            total_conditions = 0

            pe_max = strategy.get("pe_max", 30)
            pe = stock.get("pe_ratio", 0)
            total_conditions += 1
            if 0 < pe <= pe_max:
                conditions_met += 1
                score += 20

            market_cap_min = strategy.get("market_cap_min", 20)
            market_cap_max = strategy.get("market_cap_max", 500)
            market_cap = stock.get("market_cap", 0)
            total_conditions += 1
            if market_cap_min <= market_cap <= market_cap_max:
                conditions_met += 1
                score += 20

            turnover_min = strategy.get("turnover_min", 1)
            turnover_max = strategy.get("turnover_max", 15)
            turnover = stock.get("turnover_rate", 0)
            total_conditions += 1
            if turnover_min <= turnover <= turnover_max:
                conditions_met += 1
                score += 15

            change_min = strategy.get("change_min", -10)
            change_max = strategy.get("change_max", 10)
            change = stock.get("change_percent", 0)
            total_conditions += 1
            if change_min <= change <= change_max:
                conditions_met += 1
                score += 15

            price_min = strategy.get("price_min", 3)
            price_max = strategy.get("price_max", 100)
            price = stock.get("current_price", 0)
            total_conditions += 1
            if price_min <= price <= price_max:
                conditions_met += 1
                score += 10

            match_rate = conditions_met / total_conditions if total_conditions > 0 else 0
            min_match_rate = strategy.get("min_match_rate", 0.6)

            if match_rate >= min_match_rate:
                results.append(
                    {
                        **stock,
                        "custom_score": score,
                        "match_rate": round(match_rate * 100, 1),
                        "conditions_met": f"{conditions_met}/{total_conditions}",
                    }
                )

        results.sort(key=lambda x: x.get("custom_score", 0), reverse=True)
        return results[: strategy.get("max_results", 20)]


stock_screener = StockScreener()
