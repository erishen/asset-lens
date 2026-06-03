"""
Enhanced Feature Builder.
增强特征构建器 - 整合基本面和资金流向特征
"""

import logging

import numpy as np

logger = logging.getLogger(__name__)


class EnhancedFeatureBuilder:
    """增强特征构建器 - 整合基本面和资金流向特征"""

    def __init__(self):
        from .fundamental_fetcher import FundamentalData, FundamentalFetcher
        from .money_flow_fetcher import MoneyFlowData, MoneyFlowFetcher

        self.fundamental_fetcher = FundamentalFetcher()
        self.money_flow_fetcher = MoneyFlowFetcher()
        self._fundamental_cache: dict[str, FundamentalData] = {}
        self._money_flow_cache: dict[str, list[MoneyFlowData]] = {}

    def preload_fundamentals(self, codes: list[str]):
        logger.info(f"预加载 {len(codes)} 只股票基本面数据...")
        self._fundamental_cache = self.fundamental_fetcher.batch_get_fundamentals(codes)
        logger.info(f"基本面数据加载完成: {len(self._fundamental_cache)} 只")

    def build_fundamental_features(self, code: str) -> dict[str, float]:
        if code not in self._fundamental_cache:
            self._fundamental_cache[code] = self.fundamental_fetcher.get_fundamental(code)

        data = self._fundamental_cache[code]

        return {
            "pe_ratio": data.pe_ratio,
            "pb_ratio": data.pb_ratio,
            "roe": data.roe,
            "revenue_growth": data.revenue_growth,
            "profit_growth": data.profit_growth,
            "debt_ratio": data.debt_ratio,
            "gross_margin": data.gross_margin,
            "net_margin": data.net_margin,
            "log_market_value": np.log1p(data.total_market_value),
            "log_circulating_mv": np.log1p(data.circulating_market_value),
        }

    def build_money_flow_features(self, code: str, lookback: int = 5) -> dict[str, float]:
        if code not in self._money_flow_cache:
            self._money_flow_cache[code] = self.money_flow_fetcher.get_money_flow(code, days=lookback + 10)

        flows = self._money_flow_cache[code]

        if not flows:
            return {
                "main_net_inflow_mean": 0,
                "main_net_inflow_std": 0,
                "main_net_inflow_ratio_mean": 0,
                "super_net_inflow_mean": 0,
                "big_net_inflow_mean": 0,
                "small_net_inflow_mean": 0,
                "main_inflow_trend": 0,
            }

        recent_flows = flows[-lookback:] if len(flows) >= lookback else flows

        main_inflows = [f.main_net_inflow for f in recent_flows]
        main_ratios = [f.main_net_inflow_ratio for f in recent_flows]
        super_inflows = [f.super_net_inflow for f in recent_flows]
        big_inflows = [f.big_net_inflow for f in recent_flows]
        small_inflows = [f.small_net_inflow for f in recent_flows]

        trend = 0.0
        if len(main_inflows) >= 2:
            trend = float((main_inflows[-1] - main_inflows[0]) / (abs(main_inflows[0]) + 1))

        return {
            "main_net_inflow_mean": float(np.mean(main_inflows)) if main_inflows else 0.0,
            "main_net_inflow_std": float(np.std(main_inflows)) if main_inflows else 0.0,
            "main_net_inflow_ratio_mean": float(np.mean(main_ratios)) if main_ratios else 0.0,
            "super_net_inflow_mean": float(np.mean(super_inflows)) if super_inflows else 0.0,
            "big_net_inflow_mean": float(np.mean(big_inflows)) if big_inflows else 0.0,
            "small_net_inflow_mean": float(np.mean(small_inflows)) if small_inflows else 0.0,
            "main_inflow_trend": trend,
        }

    def build_all_enhanced_features(self, code: str) -> dict[str, float]:
        features = {}
        features.update(self.build_fundamental_features(code))
        features.update(self.build_money_flow_features(code))
        return features
