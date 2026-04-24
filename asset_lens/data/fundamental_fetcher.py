"""
Fundamental and Money Flow Data Fetcher.
基本面数据和资金流向数据获取模块

数据源: AkShare (开源免费)
- PE/PB/ROE等基本面指标
- 北向资金/主力资金流向
"""
import warnings

warnings.filterwarnings("ignore", message="Pandas requires version")
warnings.filterwarnings("ignore", message=".*unclosed.*socket.*")
warnings.filterwarnings("ignore", category=ResourceWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class FundamentalData:
    """基本面数据"""
    code: str
    pe_ratio: float = 0.0
    pb_ratio: float = 0.0
    roe: float = 0.0
    revenue_growth: float = 0.0
    profit_growth: float = 0.0
    debt_ratio: float = 0.0
    gross_margin: float = 0.0
    net_margin: float = 0.0
    total_market_value: float = 0.0
    circulating_market_value: float = 0.0
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'code': self.code,
            'pe_ratio': self.pe_ratio,
            'pb_ratio': self.pb_ratio,
            'roe': self.roe,
            'revenue_growth': self.revenue_growth,
            'profit_growth': self.profit_growth,
            'debt_ratio': self.debt_ratio,
            'gross_margin': self.gross_margin,
            'net_margin': self.net_margin,
            'total_market_value': self.total_market_value,
            'circulating_market_value': self.circulating_market_value,
        }


@dataclass
class MoneyFlowData:
    """资金流向数据"""
    code: str
    date: str = ""
    main_net_inflow: float = 0.0
    main_net_inflow_ratio: float = 0.0
    retail_net_inflow: float = 0.0
    retail_net_inflow_ratio: float = 0.0
    super_net_inflow: float = 0.0
    super_net_inflow_ratio: float = 0.0
    big_net_inflow: float = 0.0
    big_net_inflow_ratio: float = 0.0
    medium_net_inflow: float = 0.0
    medium_net_inflow_ratio: float = 0.0
    small_net_inflow: float = 0.0
    small_net_inflow_ratio: float = 0.0
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'code': self.code,
            'date': self.date,
            'main_net_inflow': self.main_net_inflow,
            'main_net_inflow_ratio': self.main_net_inflow_ratio,
            'retail_net_inflow': self.retail_net_inflow,
            'retail_net_inflow_ratio': self.retail_net_inflow_ratio,
            'super_net_inflow': self.super_net_inflow,
            'super_net_inflow_ratio': self.super_net_inflow_ratio,
            'big_net_inflow': self.big_net_inflow,
            'big_net_inflow_ratio': self.big_net_inflow_ratio,
            'medium_net_inflow': self.medium_net_inflow,
            'medium_net_inflow_ratio': self.medium_net_inflow_ratio,
            'small_net_inflow': self.small_net_inflow,
            'small_net_inflow_ratio': self.small_net_inflow_ratio,
        }


class FundamentalFetcher:
    """基本面数据获取器"""
    
    def __init__(self, cache_path: Path | None = None):
        self.cache_path = cache_path or Path(__file__).parent / "cache"
        self.cache_file = self.cache_path / "fundamental_cache.json"
        self._akshare = None
        self._cache: dict[str, FundamentalData] = {}
        self._load_cache()
    
    @property
    def akshare(self):
        if self._akshare is None:
            try:
                import akshare as ak
                self._akshare = ak
            except ImportError:
                logger.warning("AkShare 未安装")
        return self._akshare
    
    def _load_cache(self):
        if self.cache_file.exists():
            try:
                with open(self.cache_file, encoding='utf-8') as f:
                    data = json.load(f)
                    for code, info in data.get('fundamentals', {}).items():
                        self._cache[code] = FundamentalData(
                            code=code,
                            pe_ratio=info.get('pe_ratio', 0),
                            pb_ratio=info.get('pb_ratio', 0),
                            roe=info.get('roe', 0),
                            revenue_growth=info.get('revenue_growth', 0),
                            profit_growth=info.get('profit_growth', 0),
                            debt_ratio=info.get('debt_ratio', 0),
                            gross_margin=info.get('gross_margin', 0),
                            net_margin=info.get('net_margin', 0),
                            total_market_value=info.get('total_market_value', 0),
                            circulating_market_value=info.get('circulating_market_value', 0),
                        )
            except Exception as e:
                logger.warning(f"加载基本面缓存失败: {e}")
    
    def _save_cache(self):
        self.cache_path.mkdir(parents=True, exist_ok=True)
        data = {
            'updated_at': datetime.now().isoformat(),
            'fundamentals': {code: info.to_dict() for code, info in self._cache.items()},
        }
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_fundamental(self, code: str) -> FundamentalData:
        """获取单只股票基本面数据"""
        if code in self._cache:
            return self._cache[code]
        
        data = FundamentalData(code=code)
        
        if self.akshare:
            try:
                df = self.akshare.stock_a_lg_indicator(symbol=code)  # pylint: disable=no-member
                if df is not None and not df.empty:
                    latest = df.iloc[-1]
                    data.pe_ratio = float(latest.get('pe', 0) or 0)
                    data.pb_ratio = float(latest.get('pb', 0) or 0)
                    data.total_market_value = float(latest.get('total_mv', 0) or 0)
                    data.circulating_market_value = float(latest.get('circ_mv', 0) or 0)
            except Exception as e:
                logger.debug(f"获取 {code} 基本面数据失败: {e}")
        
        self._cache[code] = data
        return data
    
    def get_realtime_pe_pb(self, code: str) -> tuple[float, float]:
        """获取实时PE/PB"""
        if self.akshare:
            try:
                df = self.akshare.stock_a_lg_indicator(symbol=code)  # pylint: disable=no-member
                if df is not None and not df.empty:
                    latest = df.iloc[-1]
                    pe = float(latest.get('pe', 0) or 0)
                    pb = float(latest.get('pb', 0) or 0)
                    return pe, pb
            except Exception:
                pass
        return 0.0, 0.0
    
    def batch_get_fundamentals(self, codes: list[str]) -> dict[str, FundamentalData]:
        """批量获取基本面数据"""
        result = {}
        for i, code in enumerate(codes):
            result[code] = self.get_fundamental(code)
            if (i + 1) % 50 == 0:
                logger.info(f"已获取 {i + 1}/{len(codes)} 只股票基本面数据")
        self._save_cache()
        return result


class MoneyFlowFetcher:
    """资金流向数据获取器"""
    
    def __init__(self, cache_path: Path | None = None):
        self.cache_path = cache_path or Path(__file__).parent / "cache"
        self.cache_file = self.cache_path / "money_flow_cache.json"
        self._akshare = None
        self._cache: dict[str, list[MoneyFlowData]] = {}
        self._load_cache()
    
    @property
    def akshare(self):
        if self._akshare is None:
            try:
                import akshare as ak
                self._akshare = ak
            except ImportError:
                logger.warning("AkShare 未安装")
        return self._akshare
    
    def _load_cache(self):
        if self.cache_file.exists():
            try:
                with open(self.cache_file, encoding='utf-8') as f:
                    data = json.load(f)
                    for code, flows in data.get('money_flows', {}).items():
                        self._cache[code] = [
                            MoneyFlowData(**flow) for flow in flows
                        ]
            except Exception as e:
                logger.warning(f"加载资金流向缓存失败: {e}")
    
    def _save_cache(self):
        self.cache_path.mkdir(parents=True, exist_ok=True)
        data = {
            'updated_at': datetime.now().isoformat(),
            'money_flows': {
                code: [flow.to_dict() for flow in flows]
                for code, flows in self._cache.items()
            },
        }
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_money_flow(self, code: str, days: int = 30) -> list[MoneyFlowData]:
        """获取股票资金流向数据"""
        cache_key = f"{code}_{days}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        flows = []
        
        if self.akshare:
            try:
                df = self.akshare.stock_individual_fund_flow(stock=code, market='sh' if code.startswith('6') else 'sz')
                if df is not None and not df.empty:
                    df = df.tail(days)
                    for _, row in df.iterrows():
                        flow = MoneyFlowData(
                            code=code,
                            date=str(row.get('日期', '')),
                            main_net_inflow=float(row.get('主力净流入-净额', 0) or 0),
                            main_net_inflow_ratio=float(row.get('主力净流入-净占比', 0) or 0),
                            super_net_inflow=float(row.get('超大单净流入-净额', 0) or 0),
                            super_net_inflow_ratio=float(row.get('超大单净流入-净占比', 0) or 0),
                            big_net_inflow=float(row.get('大单净流入-净额', 0) or 0),
                            big_net_inflow_ratio=float(row.get('大单净流入-净占比', 0) or 0),
                            medium_net_inflow=float(row.get('中单净流入-净额', 0) or 0),
                            medium_net_inflow_ratio=float(row.get('中单净流入-净占比', 0) or 0),
                            small_net_inflow=float(row.get('小单净流入-净额', 0) or 0),
                            small_net_inflow_ratio=float(row.get('小单净流入-净占比', 0) or 0),
                        )
                        flows.append(flow)
            except Exception as e:
                logger.debug(f"获取 {code} 资金流向失败: {e}")
        
        self._cache[cache_key] = flows
        return flows
    
    def get_latest_money_flow(self, code: str) -> MoneyFlowData:
        """获取最新资金流向"""
        flows = self.get_money_flow(code, days=1)
        return flows[0] if flows else MoneyFlowData(code=code)
    
    def get_north_money_flow(self, days: int = 30) -> pd.DataFrame:
        """获取北向资金数据"""
        if not self.akshare:
            return pd.DataFrame()
        
        try:
            df = self.akshare.stock_hsgt_north_net_flow_in_em()  # pylint: disable=no-member
            if df is not None and not df.empty:
                return df.tail(days)
        except Exception as e:
            logger.warning(f"获取北向资金数据失败: {e}")
        
        return pd.DataFrame()


class EnhancedFeatureBuilder:
    """增强特征构建器 - 整合基本面和资金流向特征"""
    
    def __init__(self):
        self.fundamental_fetcher = FundamentalFetcher()
        self.money_flow_fetcher = MoneyFlowFetcher()
        self._fundamental_cache: dict[str, FundamentalData] = {}
        self._money_flow_cache: dict[str, list[MoneyFlowData]] = {}
    
    def preload_fundamentals(self, codes: list[str]):
        """预加载基本面数据"""
        logger.info(f"预加载 {len(codes)} 只股票基本面数据...")
        self._fundamental_cache = self.fundamental_fetcher.batch_get_fundamentals(codes)
        logger.info(f"基本面数据加载完成: {len(self._fundamental_cache)} 只")
    
    def build_fundamental_features(self, code: str) -> dict[str, float]:
        """构建基本面特征"""
        if code not in self._fundamental_cache:
            self._fundamental_cache[code] = self.fundamental_fetcher.get_fundamental(code)
        
        data = self._fundamental_cache[code]
        
        return {
            'pe_ratio': data.pe_ratio,
            'pb_ratio': data.pb_ratio,
            'roe': data.roe,
            'revenue_growth': data.revenue_growth,
            'profit_growth': data.profit_growth,
            'debt_ratio': data.debt_ratio,
            'gross_margin': data.gross_margin,
            'net_margin': data.net_margin,
            'log_market_value': np.log1p(data.total_market_value),
            'log_circulating_mv': np.log1p(data.circulating_market_value),
        }
    
    def build_money_flow_features(self, code: str, lookback: int = 5) -> dict[str, float]:
        """构建资金流向特征"""
        if code not in self._money_flow_cache:
            self._money_flow_cache[code] = self.money_flow_fetcher.get_money_flow(code, days=lookback + 10)
        
        flows = self._money_flow_cache[code]
        
        if not flows:
            return {
                'main_net_inflow_mean': 0,
                'main_net_inflow_std': 0,
                'main_net_inflow_ratio_mean': 0,
                'super_net_inflow_mean': 0,
                'big_net_inflow_mean': 0,
                'small_net_inflow_mean': 0,
                'main_inflow_trend': 0,
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
            'main_net_inflow_mean': float(np.mean(main_inflows)) if main_inflows else 0.0,
            'main_net_inflow_std': float(np.std(main_inflows)) if main_inflows else 0.0,
            'main_net_inflow_ratio_mean': float(np.mean(main_ratios)) if main_ratios else 0.0,
            'super_net_inflow_mean': float(np.mean(super_inflows)) if super_inflows else 0.0,
            'big_net_inflow_mean': float(np.mean(big_inflows)) if big_inflows else 0.0,
            'small_net_inflow_mean': float(np.mean(small_inflows)) if small_inflows else 0.0,
            'main_inflow_trend': trend,
        }
    
    def build_all_enhanced_features(self, code: str) -> dict[str, float]:
        """构建所有增强特征"""
        features = {}
        features.update(self.build_fundamental_features(code))
        features.update(self.build_money_flow_features(code))
        return features


fundamental_fetcher = FundamentalFetcher()
money_flow_fetcher = MoneyFlowFetcher()
enhanced_feature_builder = EnhancedFeatureBuilder()
