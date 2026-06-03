"""
Industry flow data fetching utility.
行业资金流向数据获取工具 - 统一的行业资金流向获取入口

提供便捷函数获取北向资金行业流向数据，避免在多个 CLI 和 Web 模块中
重复创建 MoneyFlowFetcher 实例和错误处理逻辑。
"""

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

_money_flow_fetcher = None


def get_money_flow_fetcher():
    """获取全局 MoneyFlowFetcher 实例（延迟加载）"""
    global _money_flow_fetcher
    if _money_flow_fetcher is None:
        from ..data.fundamental_fetcher import MoneyFlowFetcher

        _money_flow_fetcher = MoneyFlowFetcher()
    return _money_flow_fetcher


def fetch_north_flow_by_industry(use_cache: bool = True, force: bool = False) -> pd.DataFrame:
    """获取北向资金行业流向数据

    Args:
        use_cache: 是否使用缓存
        force: 是否强制获取

    Returns:
        DataFrame 包含行业流向数据，失败时返回空 DataFrame
    """
    fetcher = get_money_flow_fetcher()
    try:
        df = fetcher.get_north_flow_by_industry(use_cache=use_cache, force=force)
        if df is not None and not df.empty:
            return df
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"获取行业资金流向数据解析失败: {e}")
    except (ConnectionError, RuntimeError, OSError) as e:
        logger.error(f"获取行业资金流向数据失败: {e}")

    return pd.DataFrame()


def fetch_north_money_flow(days: int = 30) -> pd.DataFrame:
    """获取北向资金每日净流入数据

    Args:
        days: 获取天数

    Returns:
        DataFrame 包含北向资金数据，失败时返回空 DataFrame
    """
    fetcher = get_money_flow_fetcher()
    try:
        df = fetcher.get_north_money_flow(days=days)
        if df is not None and not df.empty:
            return df
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"获取北向资金数据解析失败: {e}")
    except (ConnectionError, RuntimeError, OSError) as e:
        logger.error(f"获取北向资金数据失败: {e}")

    return pd.DataFrame()


def get_north_flow_summary(days: int = 7) -> dict[str, Any]:
    """获取北向资金摘要信息（用于报告和展示）

    Args:
        days: 统计天数

    Returns:
        包含 total_flow, flows 等字段的字典
    """
    df = fetch_north_money_flow(days=days)
    if df.empty:
        return {"total_flow": 0, "flows": []}

    total_flow = 0.0
    flows = []

    if "north_net_inflow" in df.columns:
        total_flow = float(df["north_net_inflow"].sum())

        for _, row in df.iterrows():
            date = str(row.get("date", ""))
            flow = float(row.get("north_net_inflow", 0))
            if date:
                flows.append({"date": date, "flow": flow})

    return {"total_flow": total_flow, "flows": flows}
