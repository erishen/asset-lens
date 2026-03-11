"""
CLI Package.
CLI 包
"""

from .interactive import (
    interactive_analyze,
    interactive_calculate,
    interactive_fetch_stock,
    interactive_fetch_fund,
    interactive_search_fund,
    interactive_update_market,
    interactive_report,
    interactive_settings,
    interactive_menu,
)

from .report import (
    get_data_dir,
    show_asset_summary,
    show_exchange_rate_history,
    show_sell_records,
    export_asset_summary,
    export_sell_records,
)

from .data import (
    fetch_stock_data,
    fetch_fund_data,
    search_fund_data,
    update_market_data,
    update_all_data,
)

from .strategy import (
    list_strategies,
    show_strategy,
    run_backtest,
    show_stock_pool,
    add_to_stock_pool,
    remove_from_stock_pool,
    screen_stocks_with_strategy,
)

from .analysis import (
    analyze_portfolio,
    calculate_returns,
    show_pnl,
    calculate_irr,
    estimate_returns,
    show_market_sentiment,
)

__all__ = [
    # Interactive
    "interactive_analyze",
    "interactive_calculate",
    "interactive_fetch_stock",
    "interactive_fetch_fund",
    "interactive_search_fund",
    "interactive_update_market",
    "interactive_report",
    "interactive_settings",
    "interactive_menu",
    # Report
    "get_data_dir",
    "show_asset_summary",
    "show_exchange_rate_history",
    "show_sell_records",
    "export_asset_summary",
    "export_sell_records",
    # Data
    "fetch_stock_data",
    "fetch_fund_data",
    "search_fund_data",
    "update_market_data",
    "update_all_data",
    # Strategy
    "list_strategies",
    "show_strategy",
    "run_backtest",
    "show_stock_pool",
    "add_to_stock_pool",
    "remove_from_stock_pool",
    "screen_stocks_with_strategy",
    # Analysis
    "analyze_portfolio",
    "calculate_returns",
    "show_pnl",
    "calculate_irr",
    "estimate_returns",
    "show_market_sentiment",
]
