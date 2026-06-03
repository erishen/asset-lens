from ..utils.warnings_config import suppress_common_warnings

suppress_common_warnings()

import logging
from datetime import datetime
from pathlib import Path

from .fetchers.base import FetcherCacheMixin
from .industry_flow import IndustryFlowMixin
from .industry_flow_web_sources import IndustryFlowWebSourcesMixin
from .money_flow_data import MoneyFlowData
from .north_money_flow import NorthMoneyFlowMixin

logger = logging.getLogger(__name__)

__all__ = ["MoneyFlowData", "MoneyFlowFetcher"]


class MoneyFlowFetcher(
    FetcherCacheMixin,
    IndustryFlowWebSourcesMixin,
    IndustryFlowMixin,
    NorthMoneyFlowMixin,
):
    _akshare_raise_on_missing = False

    def __init__(self, cache_path: Path | None = None):
        self._init_cache(
            cache_path or Path(__file__).parent / "cache",
            default_ttl=86400,
        )
        self._money_flow_cache: dict[str, list[MoneyFlowData]] = {}
        self._load_money_flow_cache()

    @property
    def cache_file(self) -> Path:
        return self.cache_path / "money_flow_cache.json"

    def _load_money_flow_cache(self):
        data = self._cache.load_file("money_flow_cache.json")
        if data is None:
            return
        try:
            for code, flows in data.get("money_flows", {}).items():
                self._money_flow_cache[code] = [MoneyFlowData(**flow) for flow in flows]
        except (ValueError, KeyError, TypeError) as e:
            logger.warning(f"加载资金流向缓存数据解析失败: {e}")
        except (OSError, RuntimeError) as e:
            logger.warning(f"加载资金流向缓存失败: {e}")

    def _save_money_flow_cache(self):
        data = {
            "updated_at": datetime.now().isoformat(),
            "money_flows": {code: [flow.to_dict() for flow in flows] for code, flows in self._money_flow_cache.items()},
        }
        self._cache.save_file("money_flow_cache.json", data, ttl=0)

    def get_money_flow(self, code: str, days: int = 30) -> list[MoneyFlowData]:
        cache_key = f"{code}_{days}"
        if cache_key in self._money_flow_cache:
            return self._money_flow_cache[cache_key]

        flows = []

        if self.akshare:
            try:
                df = self.akshare.stock_individual_fund_flow(stock=code, market="sh" if code.startswith("6") else "sz")
                if df is not None and not df.empty:
                    df = df.tail(days)
                    for _, row in df.iterrows():
                        flow = MoneyFlowData(
                            code=code,
                            date=str(row.get("日期", "")),
                            main_net_inflow=float(row.get("主力净流入-净额", 0) or 0),
                            main_net_inflow_ratio=float(row.get("主力净流入-净占比", 0) or 0),
                            super_net_inflow=float(row.get("超大单净流入-净额", 0) or 0),
                            super_net_inflow_ratio=float(row.get("超大单净流入-净占比", 0) or 0),
                            big_net_inflow=float(row.get("大单净流入-净额", 0) or 0),
                            big_net_inflow_ratio=float(row.get("大单净流入-净占比", 0) or 0),
                            medium_net_inflow=float(row.get("中单净流入-净额", 0) or 0),
                            medium_net_inflow_ratio=float(row.get("中单净流入-净占比", 0) or 0),
                            small_net_inflow=float(row.get("小单净流入-净额", 0) or 0),
                            small_net_inflow_ratio=float(row.get("小单净流入-净占比", 0) or 0),
                        )
                        flows.append(flow)
            except (ValueError, KeyError, TypeError) as e:
                logger.debug(f"获取 {code} 资金流向数据解析失败: {e}")
            except (ConnectionError, RuntimeError, OSError) as e:
                logger.debug(f"获取 {code} 资金流向失败: {e}")

        self._money_flow_cache[cache_key] = flows
        return flows

    def get_latest_money_flow(self, code: str) -> MoneyFlowData:
        flows = self.get_money_flow(code, days=1)
        return flows[0] if flows else MoneyFlowData(code=code)
