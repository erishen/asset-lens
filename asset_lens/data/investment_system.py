"""
Investment strategy system for asset-lens.
完整投资策略系统 - 整合股票池、策略引擎、回测系统

工作流程:
1. 数据采集 → 2. 策略筛选 → 3. 股票池管理 → 4. 模拟交易 → 5. 策略优化
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..config import config
from .backtester import Backtester, BacktestResult
from .stock_pool import StockPool, StockPosition
from .strategy_engine import StrategyConfig, StrategyEngine, strategy_engine


class InvestmentSystem:
    """投资策略系统"""

    def __init__(self, system_name: str = "default"):
        self.system_name = system_name
        self.system_path = config.cache_path / "investment_systems" / system_name
        self.system_path.mkdir(parents=True, exist_ok=True)

        self.stock_pool = StockPool(system_name)
        self.backtester = Backtester()
        self.config_file = self.system_path / "system_config.json"

        self.current_strategy: Optional[str] = None
        self.system_config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """加载系统配置"""
        if self.config_file.exists():
            with open(self.config_file, "r", encoding="utf-8") as f:
                self.system_config = json.load(f)
                self.current_strategy = self.system_config.get("current_strategy")

    def _save_config(self) -> None:
        """保存系统配置"""
        self.system_config["current_strategy"] = self.current_strategy
        self.system_config["update_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.system_config, f, ensure_ascii=False, indent=2)

    def set_strategy(self, strategy_name: str) -> bool:
        """
        设置当前策略

        Args:
            strategy_name: 策略名称

        Returns:
            是否设置成功
        """
        if strategy_name not in strategy_engine.strategies:
            print(f"策略 {strategy_name} 不存在")
            print(f"可用策略: {list(strategy_engine.strategies.keys())}")
            return False

        self.current_strategy = strategy_name
        self._save_config()
        print(f"✅ 已设置策略: {strategy_name}")
        return True

    def screen_and_add_to_pool(
        self,
        stocks: List[Dict[str, Any]],
        min_score: float = 60.0,
        max_add: int = 10,
    ) -> int:
        """
        筛选股票并添加到股票池

        Args:
            stocks: 股票列表
            min_score: 最低得分
            max_add: 最大添加数量

        Returns:
            添加的股票数量
        """
        if not self.current_strategy:
            print("请先设置策略")
            return 0

        results = strategy_engine.screen_stocks(stocks, self.current_strategy, min_score)

        added_count = 0
        for stock in results[:max_add]:
            code = stock.get("code", "")
            name = stock.get("name", "")
            price = stock.get("current_price", 0)

            if self.stock_pool.add_stock(
                code, name, price, "watching", f"策略得分: {stock.get('strategy_score', 0):.1f}"
            ):
                added_count += 1

        print(f"✅ 筛选出 {len(results)} 只股票，添加 {added_count} 只到股票池")
        return added_count

    def simulate_buy(self, code: str, price: Optional[float] = None, shares: int = 100) -> bool:
        """
        模拟买入

        Args:
            code: 股票代码
            price: 买入价格（None则使用当前价格）
            shares: 股数

        Returns:
            是否买入成功
        """
        if code not in self.stock_pool.positions:
            print(f"股票 {code} 不在股票池中")
            return False

        pos = self.stock_pool.positions[code]
        buy_price = price if price else pos.current_price

        return self.stock_pool.buy_stock(code, buy_price, shares)

    def simulate_sell(self, code: str, price: Optional[float] = None) -> bool:
        """
        模拟卖出

        Args:
            code: 股票代码
            price: 卖出价格（None则使用当前价格）

        Returns:
            是否卖出成功
        """
        if code not in self.stock_pool.positions:
            print(f"股票 {code} 不在股票池中")
            return False

        pos = self.stock_pool.positions[code]
        sell_price = price if price else pos.current_price

        return self.stock_pool.sell_stock(code, sell_price)

    def run_backtest(
        self,
        historical_data: Dict[str, List[Dict[str, Any]]],
        strategy_name: Optional[str] = None,
        **kwargs,
    ) -> BacktestResult:
        """
        运行回测

        Args:
            historical_data: 历史数据
            strategy_name: 策略名称（None则使用当前策略）
            **kwargs: 其他参数

        Returns:
            回测结果
        """
        strategy = strategy_name or self.current_strategy
        if not strategy:
            raise ValueError("请指定策略名称")

        return self.backtester.run_backtest(strategy, historical_data, **kwargs)

    def optimize_strategy(
        self,
        historical_data: Dict[str, List[Dict[str, Any]]],
        strategies: Optional[List[str]] = None,
        metric: str = "sharpe_ratio",
    ) -> Tuple[str, BacktestResult]:
        """
        优化策略 - 比较多个策略找出最佳

        Args:
            historical_data: 历史数据
            strategies: 策略列表（None则比较所有策略）
            metric: 评估指标

        Returns:
            (最佳策略名称, 回测结果)
        """
        if strategies is None:
            strategies = list(strategy_engine.strategies.keys())

        best_name, best_result = self.backtester.get_best_strategy(
            strategies, historical_data, metric
        )

        self.set_strategy(best_name)
        print(f"\n✅ 最佳策略: {best_name}")
        print(f"   {metric}: {getattr(best_result, metric, 0):.2f}")

        return best_name, best_result

    def get_system_status(self) -> Dict[str, Any]:
        """
        获取系统状态

        Returns:
            系统状态
        """
        pool_performance = self.stock_pool.get_performance()

        return {
            "system_name": self.system_name,
            "current_strategy": self.current_strategy,
            "stock_pool": {
                "total": pool_performance["total_stocks"],
                "watching": pool_performance["watching_count"],
                "holding": pool_performance["holding_count"],
                "sold": pool_performance["sold_count"],
            },
            "performance": {
                "total_profit": pool_performance["total_profit"],
                "profit_rate": pool_performance["profit_rate"],
                "win_rate": pool_performance["win_rate"],
            },
            "available_strategies": list(strategy_engine.strategies.keys()),
        }

    def generate_report(self) -> str:
        """
        生成投资报告

        Returns:
            报告文本
        """
        status = self.get_system_status()
        performance = self.stock_pool.get_performance()

        report = []
        report.append("=" * 60)
        report.append(f"📊 投资策略系统报告 - {self.system_name}")
        report.append("=" * 60)
        report.append(f"\n当前策略: {self.current_strategy or '未设置'}")
        report.append(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        report.append("\n" + "-" * 60)
        report.append("📈 股票池状态")
        report.append("-" * 60)
        report.append(f"总股票数: {status['stock_pool']['total']}")
        report.append(f"观察中: {status['stock_pool']['watching']}")
        report.append(f"持有中: {status['stock_pool']['holding']}")
        report.append(f"已卖出: {status['stock_pool']['sold']}")

        report.append("\n" + "-" * 60)
        report.append("💰 绩效统计")
        report.append("-" * 60)
        report.append(f"总盈亏: {performance['total_profit']:+.2f} 元")
        report.append(f"收益率: {performance['profit_rate']:+.2f}%")
        report.append(f"胜率: {performance['win_rate']:.1f}%")
        report.append(f"盈利次数: {performance['win_count']}")
        report.append(f"亏损次数: {performance['lose_count']}")

        # 最佳表现股票
        best_performers = self.stock_pool.get_best_performers(3)
        if best_performers:
            report.append("\n" + "-" * 60)
            report.append("🏆 表现最佳股票 TOP 3")
            report.append("-" * 60)
            for i, stock in enumerate(best_performers, 1):
                report.append(
                    f"{i}. {stock['name']}({stock['code']}): {stock['profit_rate']:+.2f}%"
                )

        # 最差表现股票
        worst_performers = self.stock_pool.get_worst_performers(3)
        if worst_performers:
            report.append("\n" + "-" * 60)
            report.append("⚠️ 表现最差股票 TOP 3")
            report.append("-" * 60)
            for i, stock in enumerate(worst_performers, 1):
                report.append(
                    f"{i}. {stock['name']}({stock['code']}): {stock['profit_rate']:+.2f}%"
                )

        # 当前持仓
        holdings = self.stock_pool.list_stocks("holding")
        if holdings:
            report.append("\n" + "-" * 60)
            report.append("📦 当前持仓")
            report.append("-" * 60)
            for stock in holdings:
                report.append(f"  {stock['name']}({stock['code']})")
                report.append(
                    f"    买入价: {stock['buy_price']:.2f}, 现价: {stock['current_price']:.2f}"
                )
                report.append(f"    盈亏: {stock['profit']:+.2f} ({stock['profit_rate']:+.2f}%)")

        report.append("\n" + "=" * 60)
        report.append("⚠️ 免责声明: 以上内容仅供参考，不构成投资建议")
        report.append("=" * 60)

        return "\n".join(report)

    def export_data(self, filepath: Optional[Path] = None) -> Path:
        """
        导出系统数据

        Args:
            filepath: 导出路径

        Returns:
            导出文件路径
        """
        if filepath is None:
            filepath = self.system_path / f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        data = {
            "system_name": self.system_name,
            "export_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "current_strategy": self.current_strategy,
            "stock_pool": {
                "positions": {
                    code: {
                        "code": pos.code,
                        "name": pos.name,
                        "buy_price": pos.buy_price,
                        "buy_date": pos.buy_date,
                        "shares": pos.shares,
                        "current_price": pos.current_price,
                        "sell_price": pos.sell_price,
                        "sell_date": pos.sell_date,
                        "status": pos.status,
                        "notes": pos.notes,
                    }
                    for code, pos in self.stock_pool.positions.items()
                },
                "history": self.stock_pool.history,
            },
            "performance": self.stock_pool.get_performance(),
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ 数据已导出到: {filepath}")
        return filepath


investment_system = InvestmentSystem()
