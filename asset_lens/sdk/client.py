"""
Asset-Lens Python SDK.
方便的 Python 调用接口
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AssetLensClient:
    """Asset-Lens 客户端"""

    def __init__(self, config_path: Path | None = None):
        """
        初始化客户端

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path or Path("config/asset_lens.yaml")
        self._cache: dict[str, Any] = {}

    def get_stock_quote(self, code: str) -> dict[str, Any]:
        """
        获取股票实时行情

        Args:
            code: 股票代码（如 sh600519, sz000001）

        Returns:
            股票行情数据
        """
        try:
            from asset_lens.data.stock_fetcher import StockDataFetcher

            fetcher = StockDataFetcher()
            data = fetcher.fetch_stock_quote_akshare(code)
            return {
                "success": True,
                "data": data,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        except (ValueError, KeyError, ConnectionError, RuntimeError) as e:
            logger.error(f"获取股票行情失败: {code}, {e}")
            return {"success": False, "error": str(e), "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    def get_fund_nav(self, code: str) -> dict[str, Any]:
        """
        获取基金净值

        Args:
            code: 基金代码

        Returns:
            基金净值数据
        """
        try:
            from asset_lens.data.fund_fetcher import FundDataFetcher

            fetcher = FundDataFetcher()
            data = fetcher.fetch_fund_info(code)
            return {
                "success": True,
                "data": data,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        except (ValueError, KeyError, ConnectionError, RuntimeError) as e:
            logger.error(f"获取基金净值失败: {code}, {e}")
            return {"success": False, "error": str(e), "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    def analyze_portfolio(self) -> dict[str, Any]:
        """
        分析投资组合

        Returns:
            投资组合分析数据
        """
        try:
            from asset_lens.analysis.portfolio_analyzer import PortfolioAnalyzer

            analyzer = PortfolioAnalyzer()
            data = analyzer.analyze_portfolio_health([])
            return {
                "success": True,
                "data": {
                    "health_score": data.health_score if hasattr(data, "health_score") else None,
                    "status": data.status if hasattr(data, "status") else None,
                },
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        except (ValueError, KeyError, TypeError, RuntimeError) as e:
            logger.error(f"分析投资组合失败: {e}")
            return {"success": False, "error": str(e), "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    def screen_stocks(self, strategy: str = "momentum", limit: int = 10) -> dict[str, Any]:
        """
        股票筛选

        Args:
            strategy: 策略类型（fundamental, technical, comprehensive）
            limit: 返回数量

        Returns:
            筛选结果
        """
        try:
            from asset_lens.strategy.screener import StockScreener

            screener = StockScreener()
            data = screener.screen(filter_type=strategy)
            if isinstance(data, list) and limit:
                data = data[:limit]
            return {
                "success": True,
                "data": data,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        except (ValueError, KeyError, RuntimeError) as e:
            logger.error(f"股票筛选失败: {strategy}, {e}")
            return {"success": False, "error": str(e), "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    def get_market_indices(self) -> dict[str, Any]:
        """
        获取市场指数

        Returns:
            市场指数数据
        """
        try:
            indices = {"sh000300": "沪深300", "sh000016": "上证50", "sz399006": "创业板指", "sh000688": "科创50"}

            results = {}
            for code, name in indices.items():
                result = self.get_stock_quote(code)
                if result["success"]:
                    results[name] = result

            return {"success": True, "data": results, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        except (ValueError, KeyError, ConnectionError, RuntimeError) as e:
            logger.error(f"获取市场指数失败: {e}")
            return {"success": False, "error": str(e), "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    def calculate_risk_metrics(self, returns: list[float]) -> dict[str, Any]:
        """
        计算风险指标

        Args:
            returns: 收益率序列

        Returns:
            风险指标数据
        """
        try:
            from asset_lens.risk import risk_service

            metrics = risk_service.calculate_metrics(returns)

            return {
                "success": True,
                "data": {
                    "volatility": metrics.volatility,
                    "max_drawdown": metrics.max_drawdown,
                    "sharpe_ratio": metrics.sharpe_ratio,
                    "var_95": metrics.var_95,
                },
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        except (ValueError, KeyError, TypeError, RuntimeError) as e:
            logger.error(f"计算风险指标失败: {e}")
            return {"success": False, "error": str(e), "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    def generate_report(self, report_type: str = "daily") -> dict[str, Any]:
        """
        生成报告

        Args:
            report_type: 报告类型（daily, weekly, monthly）

        Returns:
            报告数据
        """
        try:
            from asset_lens.monitoring.investment_monitor import InvestmentMonitor

            monitor = InvestmentMonitor()

            if report_type == "daily":
                report = monitor.generate_daily_report()
            elif report_type == "weekly":
                report = monitor.generate_weekly_report()
            else:
                report = monitor.generate_daily_report()

            return {"success": True, "data": report, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        except (ValueError, KeyError, TypeError, OSError, RuntimeError) as e:
            logger.error(f"生成报告失败: {report_type}, {e}")
            return {"success": False, "error": str(e), "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    def add_to_stock_pool(self, code: str, name: str, price: float) -> dict[str, Any]:
        """
        添加股票到股票池

        Args:
            code: 股票代码
            name: 股票名称
            price: 买入价格

        Returns:
            操作结果
        """
        try:
            from asset_lens.db.database import db_manager

            db_manager.save_stock_info({"code": code, "name": name, "current_price": price})
            return {
                "success": True,
                "message": f"股票 {code} 已添加到股票池",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        except (ValueError, KeyError, RuntimeError) as e:
            logger.error(f"添加股票到股票池失败: {code}, {e}")
            return {"success": False, "error": str(e), "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    def get_stock_pool_status(self) -> dict[str, Any]:
        """
        获取股票池状态

        Returns:
            股票池状态数据
        """
        try:
            from asset_lens.db.database import db_manager

            codes = db_manager.get_stock_codes()
            stats = db_manager.get_statistics()
            return {
                "success": True,
                "data": {"codes": codes, "statistics": stats},
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        except (ValueError, KeyError, RuntimeError) as e:
            logger.error(f"获取股票池状态失败: {e}")
            return {"success": False, "error": str(e), "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}


def create_client(config_path: Path | None = None) -> AssetLensClient:
    """创建客户端实例"""
    return AssetLensClient(config_path)
