"""
Stock Pool Routes - 股票池相关 API
"""

from datetime import datetime

from fastapi import APIRouter

router = APIRouter(prefix="/api/stock-pool", tags=["stock-pool"])


@router.get("")
async def get_stock_pool():
    """获取股票池数据"""
    from ...config import config
    from ...trading.stock_pool import StockPool

    try:
        pool_path = config.cache_path / "stock_pools"

        if not pool_path.exists():
            return {"stocks": [], "count": 0, "message": "股票池为空，请先运行策略选股"}

        pool_files = [f for f in pool_path.glob("*_pool.json") if not f.name.startswith("test_")]

        if not pool_files:
            return {"stocks": [], "count": 0, "message": "股票池为空"}

        all_stocks: dict[str, dict] = {}
        pool_info: dict[str, dict] = {}

        for pool_file in pool_files:
            pool = StockPool(pool_file.stem.replace("_pool", ""))

            strategy_name = pool.pool_name
            min_score = 60.0
            update_time = ""

            if hasattr(pool, "config") and pool.config:
                if hasattr(pool.config, "strategy_name"):
                    strategy_name = pool.config.strategy_name
                if hasattr(pool.config, "min_score"):
                    min_score = pool.config.min_score

            if hasattr(pool, "update_time"):
                update_time = pool.update_time

            pool_info[pool.pool_name] = {
                "name": pool.pool_name,
                "strategy_name": strategy_name,
                "min_score": min_score,
                "update_time": update_time,
            }

            for code, position in pool.positions.items():
                if code.startswith("sh92") or code.startswith("bj"):
                    continue

                if position.status in ["watching", "holding"]:
                    if code in all_stocks:
                        all_stocks[code]["selected_count"] += position.selected_count
                        all_stocks[code]["max_profit_rate"] = max(
                            all_stocks[code]["max_profit_rate"], position.max_profit_rate
                        )
                        all_stocks[code]["min_profit_rate"] = min(
                            all_stocks[code]["min_profit_rate"], position.min_profit_rate
                        )
                        all_stocks[code]["strategies"].append(strategy_name)
                    else:
                        all_stocks[code] = {
                            "code": position.code,
                            "name": position.name,
                            "buy_price": position.buy_price,
                            "current_price": position.current_price,
                            "buy_date": position.buy_date,
                            "status": position.status,
                            "profit_rate": ((position.current_price - position.buy_price) / position.buy_price * 100)
                            if position.buy_price > 0
                            else 0,
                            "selected_count": position.selected_count,
                            "max_profit_rate": position.max_profit_rate,
                            "min_profit_rate": position.min_profit_rate,
                            "strategies": [strategy_name],
                        }

        stocks_list = sorted(all_stocks.values(), key=lambda x: x.get("selected_count", 0), reverse=True)

        return {
            "stocks": stocks_list,
            "count": len(stocks_list),
            "pools": pool_info,
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    except Exception as e:
        return {"stocks": [], "count": 0, "error": str(e)}
