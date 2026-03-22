"""
Chart generator for asset-lens.
图表生成模块 - 生成各类投资分析图表

功能:
1. 股票池收益曲线图
2. 策略回测曲线图
3. 市场环境仪表盘
4. 妖股信号可视化
"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class ChartConfig:
    """图表配置"""

    width: int = 800
    height: int = 400
    title: str = ""
    x_label: str = ""
    y_label: str = ""
    show_legend: bool = True
    show_grid: bool = True


class ChartGenerator:
    """图表生成器"""

    def __init__(self):
        from ..config import config

        self.cache_path = config.cache_path
        self.chart_path = self.cache_path / "charts"
        self.chart_path.mkdir(parents=True, exist_ok=True)

    def generate_profit_curve(
        self,
        pool_name: str = "default",
        days: int = 30,
    ) -> dict[str, Any]:
        """
        生成收益曲线图数据

        Args:
            pool_name: 股票池名称
            days: 天数

        Returns:
            图表数据
        """
        from ..trading.stock_pool import StockPool
        from .stock_tracker import StockTracker

        pool = StockPool(pool_name)
        tracker = StockTracker(pool_name)

        chart_data = {
            "chart_type": "profit_curve",
            "pool_name": pool_name,
            "generate_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "config": {
                "title": f"{pool_name} 股票池收益曲线",
                "x_label": "日期",
                "y_label": "收益率 (%)",
                "width": 800,
                "height": 400,
            },
            "data": {
                "dates": [],
                "profit_rates": [],
                "benchmark": [],
            },
            "statistics": {},
        }

        daily_records = tracker.daily_records
        if not daily_records:
            return chart_data

        all_dates = set()
        for records in daily_records.values():
            for r in records:
                all_dates.add(r.date)

        sorted_dates = sorted(list(all_dates))[-days:]

        profit_rates: list[float] = []
        for date in sorted_dates:
            total_profit = 0.0
            count = 0

            for code, records in daily_records.items():
                pos = pool.positions.get(code)
                if not pos or pos.status != "holding":
                    continue

                for r in records:
                    if r.date == date:
                        if pos.buy_price > 0:
                            profit_rate = ((r.close_price - pos.buy_price) / pos.buy_price) * 100
                            total_profit += profit_rate
                            count += 1
                        break

            if count > 0:
                profit_rates.append(total_profit / count)
            else:
                profit_rates.append(0.0)

        data_dict: dict[str, Any] = chart_data["data"]  # type: ignore
        data_dict["dates"] = sorted_dates
        data_dict["profit_rates"] = profit_rates

        benchmark: list[float] = [0.0] * len(sorted_dates)
        data_dict["benchmark"] = benchmark

        if profit_rates:
            chart_data["statistics"] = {
                "total_return": profit_rates[-1] if profit_rates else 0,
                "max_return": max(profit_rates) if profit_rates else 0,
                "min_return": min(profit_rates) if profit_rates else 0,
                "avg_return": sum(profit_rates) / len(profit_rates) if profit_rates else 0,
            }

        filename = f"profit_curve_{pool_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.chart_path / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(chart_data, f, ensure_ascii=False, indent=2)

        chart_data["chart_file"] = str(filepath)
        return chart_data

    def generate_strategy_comparison_chart(
        self,
        strategies: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        生成策略对比图数据

        Args:
            strategies: 策略列表

        Returns:
            图表数据
        """
        from ..trading.stock_pool import StockPool

        if not strategies:
            strategies = ["value", "momentum", "reversal", "dividend"]

        chart_data: dict[str, Any] = {
            "chart_type": "strategy_comparison",
            "generate_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "config": {
                "title": "策略收益对比",
                "x_label": "策略",
                "y_label": "收益率 (%)",
                "width": 600,
                "height": 400,
            },
            "data": {
                "strategies": [],
                "profit_rates": [],
                "win_rates": [],
            },
        }

        data_dict: dict[str, Any] = chart_data["data"]
        strategies_list: list[str] = data_dict["strategies"]
        profit_rates_list: list[float] = data_dict["profit_rates"]
        win_rates_list: list[float] = data_dict["win_rates"]

        for strategy_name in strategies:
            pool = StockPool(strategy_name)
            status = pool.get_performance()

            strategies_list.append(strategy_name)
            profit_rates_list.append(float(status.get("total_profit_rate", 0) * 100))
            win_rates_list.append(float(status.get("win_rate", 0) * 100))

        filename = f"strategy_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.chart_path / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(chart_data, f, ensure_ascii=False, indent=2)

        chart_data["chart_file"] = str(filepath)
        return chart_data

    def generate_monster_signal_chart(
        self,
        pool_name: str = "default",
        days: int = 30,
    ) -> dict[str, Any]:
        """
        生成妖股信号图表数据

        Args:
            pool_name: 股票池名称
            days: 天数

        Returns:
            图表数据
        """
        from .stock_tracker import StockTracker

        tracker = StockTracker(pool_name)

        chart_data = {
            "chart_type": "monster_signal",
            "pool_name": pool_name,
            "generate_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "config": {
                "title": "妖股信号分布",
                "x_label": "日期",
                "y_label": "信号数量",
                "width": 800,
                "height": 300,
            },
            "data": {
                "dates": [],
                "signal_counts": [],
                "signal_types": {},
            },
        }

        signals = tracker.monster_signals
        if not signals:
            return chart_data

        date_counts: dict[str, int] = {}
        type_counts: dict[str, int] = {}

        for signal in signals:
            date = signal.signal_date
            date_counts[date] = date_counts.get(date, 0) + 1

            for signal_type in signal.signal_type.split("|"):
                type_counts[signal_type] = type_counts.get(signal_type, 0) + 1

        sorted_dates = sorted(date_counts.keys())[-days:]

        data_dict: dict[str, Any] = chart_data["data"]  # type: ignore
        data_dict["dates"] = sorted_dates
        data_dict["signal_counts"] = [date_counts.get(d, 0) for d in sorted_dates]
        data_dict["signal_types"] = dict(
            sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        )

        filename = f"monster_signal_{pool_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.chart_path / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(chart_data, f, ensure_ascii=False, indent=2)

        chart_data["chart_file"] = str(filepath)
        return chart_data

    def generate_risk_dashboard(
        self,
        pool_name: str = "default",
    ) -> dict[str, Any]:
        """
        生成风险仪表盘数据

        Args:
            pool_name: 股票池名称

        Returns:
            图表数据
        """
        from ..trading.stock_pool import StockPool
        from .market_environment import market_environment_analyzer

        pool = StockPool(pool_name)
        status = pool.get_performance()
        environment = market_environment_analyzer.analyze_environment()

        chart_data: dict[str, Any] = {
            "chart_type": "risk_dashboard",
            "pool_name": pool_name,
            "generate_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "config": {
                "title": "风险仪表盘",
                "width": 600,
                "height": 400,
            },
            "data": {
                "metrics": {
                    "concentration": 0,
                    "win_rate": status.get("win_rate", 0),
                    "profit_rate": status.get("total_profit_rate", 0),
                    "holding_count": status.get("holding_count", 0),
                },
                "market": {
                    "type": environment.market_type,
                    "risk_level": environment.risk_level,
                    "sentiment": environment.sentiment,
                },
                "risk_score": 0,
            },
            "warnings": [],
        }

        risk_score = 0
        warnings: list[str] = []

        holding_count = status.get("holding_count", 0)
        total_stocks = status.get("total_stocks", 0)

        data_dict: dict[str, Any] = chart_data["data"]
        metrics_dict: dict[str, Any] = data_dict["metrics"]

        if total_stocks > 0:
            concentration = holding_count / total_stocks
            metrics_dict["concentration"] = concentration

            if concentration > 0.7:
                risk_score += 30
                warnings.append("持仓集中度过高")
            elif concentration > 0.5:
                risk_score += 15
                warnings.append("持仓集中度偏高")

        win_rate = status.get("win_rate", 0)
        if win_rate < 0.4:
            risk_score += 25
            warnings.append("胜率较低")
        elif win_rate < 0.5:
            risk_score += 10
            warnings.append("胜率偏低")

        if environment.risk_level == "high":
            risk_score += 20
            warnings.append("市场风险较高")
        elif environment.risk_level == "medium":
            risk_score += 10
            warnings.append("市场风险中等")

        data_dict["risk_score"] = min(risk_score, 100)
        chart_data["warnings"] = warnings

        filename = f"risk_dashboard_{pool_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.chart_path / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(chart_data, f, ensure_ascii=False, indent=2)

        chart_data["chart_file"] = str(filepath)
        return chart_data

    def print_chart_summary(self, chart_data: dict[str, Any]) -> None:
        """打印图表摘要"""
        chart_type = chart_data.get("chart_type", "unknown")

        print("\n" + "=" * 60)
        print(f"📊 {self._get_chart_title(chart_type)}")
        print("=" * 60)
        print(f"生成时间: {chart_data.get('generate_time', 'N/A')}")

        if chart_type == "profit_curve":
            self._print_profit_curve(chart_data)
        elif chart_type == "strategy_comparison":
            self._print_strategy_comparison(chart_data)
        elif chart_type == "monster_signal":
            self._print_monster_signal(chart_data)
        elif chart_type == "risk_dashboard":
            self._print_risk_dashboard(chart_data)

        print(f"\n📁 图表数据已保存: {chart_data.get('chart_file', 'N/A')}")
        print("=" * 60)

    def _get_chart_title(self, chart_type: str) -> str:
        """获取图表标题"""
        titles = {
            "profit_curve": "收益曲线图",
            "strategy_comparison": "策略对比图",
            "monster_signal": "妖股信号图",
            "risk_dashboard": "风险仪表盘",
        }
        return titles.get(chart_type, "投资图表")

    def _print_profit_curve(self, chart_data: dict[str, Any]) -> None:
        """打印收益曲线"""
        stats = chart_data.get("statistics", {})
        print(f"\n股票池: {chart_data.get('pool_name', 'N/A')}")
        print("\n统计数据:")
        print(f"  总收益: {stats.get('total_return', 0):.2f}%")
        print(f"  最大收益: {stats.get('max_return', 0):.2f}%")
        print(f"  最小收益: {stats.get('min_return', 0):.2f}%")
        print(f"  平均收益: {stats.get('avg_return', 0):.2f}%")

    def _print_strategy_comparison(self, chart_data: dict[str, Any]) -> None:
        """打印策略对比"""
        data = chart_data.get("data", {})
        print("\n策略对比:")
        print("-" * 40)
        print(f"{'策略':<12} {'收益率':>10} {'胜率':>10}")
        print("-" * 40)

        for i, strategy in enumerate(data.get("strategies", [])):
            profit = data.get("profit_rates", [])[i] if i < len(data.get("profit_rates", [])) else 0
            win_rate = data.get("win_rates", [])[i] if i < len(data.get("win_rates", [])) else 0
            print(f"{strategy:<12} {profit:>10.2f}% {win_rate:>10.1f}%")

        print("-" * 40)

    def _print_monster_signal(self, chart_data: dict[str, Any]) -> None:
        """打印妖股信号"""
        data = chart_data.get("data", {})
        print(f"\n股票池: {chart_data.get('pool_name', 'N/A')}")

        signal_types = data.get("signal_types", {})
        if signal_types:
            print("\n信号类型分布:")
            for signal_type, count in list(signal_types.items())[:5]:
                print(f"  {signal_type}: {count} 次")

    def _print_risk_dashboard(self, chart_data: dict[str, Any]) -> None:
        """打印风险仪表盘"""
        data = chart_data.get("data", {})
        print(f"\n股票池: {chart_data.get('pool_name', 'N/A')}")

        metrics = data.get("metrics", {})
        print("\n风险指标:")
        print(f"  持仓集中度: {metrics.get('concentration', 0):.1%}")
        print(f"  胜率: {metrics.get('win_rate', 0):.1%}")
        print(f"  收益率: {metrics.get('profit_rate', 0):.2%}")

        market = data.get("market", {})
        print("\n市场环境:")
        print(f"  类型: {market.get('type', 'N/A')}")
        print(f"  风险等级: {market.get('risk_level', 'N/A')}")
        print(f"  情绪: {market.get('sentiment', 'N/A')}")

        print(f"\n综合风险评分: {data.get('risk_score', 0)}/100")

        warnings = chart_data.get("warnings", [])
        if warnings:
            print("\n⚠️ 风险警告:")
            for w in warnings:
                print(f"  • {w}")


chart_generator = ChartGenerator()
