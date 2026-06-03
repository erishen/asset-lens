"""
Analysis Module.
分析模块 - 提供盘前分析、实时信号推送、异动监控、持仓分析、公告提醒、复盘总结、AI问答、黑天鹅预警、调仓建议、ML追踪、模型重训练、交易日志、回测报告等功能

推荐使用子模块直接导入:
    from asset_lens.analysis.portfolio_analyzer import PortfolioAnalyzer
    from asset_lens.analysis.black_swan import black_swan_monitor
    from asset_lens.analysis.rebalancer import portfolio_rebalancer
"""

__all__ = [
    "AIQAEngine",
    "AlertMonitor",
    "AnnouncementMonitor",
    "BacktestReporter",
    "BlackSwanMonitor",
    "DashboardGenerator",
    "EnhancedTradeLogger",
    "MLPredictionTracker",
    "ModelRetrainer",
    "PortfolioAnalyzer",
    "PortfolioRebalancer",
    "PreMarketAnalyzer",
    "SignalGenerator",
    "SignalPusher",
    "TradingReview",
    "ai_qa_engine",
    "alert_monitor",
    "announcement_monitor",
    "backtest_reporter",
    "black_swan_monitor",
    "dashboard_generator",
    "enhanced_trade_logger",
    "ml_prediction_tracker",
    "model_retrainer",
    "portfolio_analyzer",
    "portfolio_rebalancer",
    "premarket_analyzer",
    "signal_generator",
    "signal_pusher",
    "trading_review",
]


def __getattr__(name: str):
    if name in __all__:
        if name in ("AIQAEngine", "ai_qa_engine"):
            from .ai_qa import AIQAEngine, ai_qa_engine

            return AIQAEngine if name == "AIQAEngine" else ai_qa_engine
        if name in ("AlertMonitor", "alert_monitor"):
            from .alert_monitor import AlertMonitor, alert_monitor

            return AlertMonitor if name == "AlertMonitor" else alert_monitor
        if name in ("AnnouncementMonitor", "announcement_monitor"):
            from .announcement_monitor import AnnouncementMonitor, announcement_monitor

            return AnnouncementMonitor if name == "AnnouncementMonitor" else announcement_monitor
        if name in ("BacktestReporter", "backtest_reporter"):
            from .backtest_reporter import BacktestReporter, backtest_reporter

            return BacktestReporter if name == "BacktestReporter" else backtest_reporter
        if name in ("BlackSwanMonitor", "black_swan_monitor"):
            from .black_swan import BlackSwanMonitor, black_swan_monitor

            return BlackSwanMonitor if name == "BlackSwanMonitor" else black_swan_monitor
        if name in ("DashboardGenerator", "dashboard_generator"):
            from .dashboard import DashboardGenerator, dashboard_generator

            return DashboardGenerator if name == "DashboardGenerator" else dashboard_generator
        if name in ("EnhancedTradeLogger", "enhanced_trade_logger"):
            from .trade_logger import EnhancedTradeLogger, enhanced_trade_logger

            return EnhancedTradeLogger if name == "EnhancedTradeLogger" else enhanced_trade_logger
        if name in ("MLPredictionTracker", "ml_prediction_tracker"):
            from .ml_tracker import MLPredictionTracker, ml_prediction_tracker

            return MLPredictionTracker if name == "MLPredictionTracker" else ml_prediction_tracker
        if name in ("ModelRetrainer", "model_retrainer"):
            from .model_retrainer import ModelRetrainer, model_retrainer

            return ModelRetrainer if name == "ModelRetrainer" else model_retrainer
        if name in ("PortfolioAnalyzer", "portfolio_analyzer"):
            from .portfolio_analyzer import PortfolioAnalyzer, portfolio_analyzer

            return PortfolioAnalyzer if name == "PortfolioAnalyzer" else portfolio_analyzer
        if name in ("PortfolioRebalancer", "portfolio_rebalancer"):
            from .rebalancer import PortfolioRebalancer, portfolio_rebalancer

            return PortfolioRebalancer if name == "PortfolioRebalancer" else portfolio_rebalancer
        if name in ("PreMarketAnalyzer", "premarket_analyzer"):
            from .premarket_analyzer import PreMarketAnalyzer, premarket_analyzer

            return PreMarketAnalyzer if name == "PreMarketAnalyzer" else premarket_analyzer
        if name in ("SignalGenerator", "signal_generator"):
            from .signal_pusher import SignalGenerator, signal_generator

            return SignalGenerator if name == "SignalGenerator" else signal_generator
        if name in ("SignalPusher", "signal_pusher"):
            from .signal_pusher import SignalPusher, signal_pusher

            return SignalPusher if name == "SignalPusher" else signal_pusher
        if name in ("TradingReview", "trading_review"):
            from .trading_review import TradingReview, trading_review

            return TradingReview if name == "TradingReview" else trading_review
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
