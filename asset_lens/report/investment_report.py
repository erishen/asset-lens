"""
Investment report generator for asset-lens.
投资报告生成模块 - 生成各类投资分析报告

功能:
1. 投资策略报告 - 策略表现、持仓分析
2. 股票池跟踪报告 - 收益曲线、表现分析
3. 策略对比报告 - 多策略对比分析
4. 风险评估报告 - 风险指标、预警信息
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..config import config
from ..trading.stock_pool import StockPool


@dataclass
class ReportConfig:
    """报告配置"""

    output_dir: str = "reports"
    formats: list[str] = field(default_factory=lambda: ["json"])
    include_charts: bool = True


class InvestmentReportGenerator:
    """投资报告生成器"""

    def __init__(self):
        self.cache_path = config.cache_path
        self.report_path = self.cache_path / "reports"
        self.report_path.mkdir(parents=True, exist_ok=True)
        self.config = ReportConfig()

    def generate_strategy_report(
        self,
        strategy_name: str,
        pool_name: str = "default",
    ) -> dict[str, Any]:
        """
        生成策略报告

        Args:
            strategy_name: 策略名称
            pool_name: 股票池名称

        Returns:
            报告数据
        """
        from ..data.stock_tracker import StockTracker
        from ..strategy.engine import strategy_engine
        from ..trading.stock_pool import StockPool

        report: dict[str, Any] = {
            "report_type": "strategy_report",
            "strategy_name": strategy_name,
            "pool_name": pool_name,
            "generate_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "strategy_info": {},
            "pool_status": {},
            "performance": {},
            "recommendations": [],
        }

        strategy = strategy_engine.get_strategy(strategy_name)
        if strategy:
            report["strategy_info"] = {
                "name": strategy.name,
                "description": strategy.description,
                "buy_conditions": [
                    {
                        "name": c.name,
                        "weight": c.weight,
                        "value": c.value,
                    }
                    for c in strategy.buy_conditions
                ],
                "sell_conditions": [
                    {
                        "name": c.name,
                        "weight": c.weight,
                        "value": c.value,
                    }
                    for c in strategy.sell_conditions
                ],
                "risk_control": {
                    "stop_loss": strategy.stop_loss,
                    "take_profit": strategy.take_profit,
                    "max_positions": strategy.max_positions,
                },
            }

        pool = StockPool(pool_name)
        pool_status = pool.get_performance()
        report["pool_status"] = {
            "total_stocks": pool_status.get("total_stocks", 0),
            "watching_count": pool_status.get("watching_count", 0),
            "holding_count": pool_status.get("holding_count", 0),
            "sold_count": pool_status.get("sold_count", 0),
        }

        report["performance"] = {
            "total_profit": pool_status.get("total_profit", 0),
            "total_profit_rate": pool_status.get("total_profit_rate", 0),
            "win_rate": pool_status.get("win_rate", 0),
            "avg_profit_rate": pool_status.get("avg_profit_rate", 0),
        }

        tracker = StockTracker(pool_name)
        tracking_report = tracker.get_tracking_report()
        report["monster_signals"] = tracking_report.get("recent_monsters", [])

        recommendations_list: list[dict[str, Any]] = self._generate_strategy_recommendations(
            strategy_name, pool_status, tracking_report
        )
        report["recommendations"] = recommendations_list

        filename = f"strategy_{strategy_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.report_path / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        report["report_file"] = str(filepath)
        return report

    def generate_pool_report(self, pool_name: str = "default") -> dict[str, Any]:
        """
        生成股票池报告

        Args:
            pool_name: 股票池名称

        Returns:
            报告数据
        """
        from ..data.stock_tracker import StockTracker
        from ..trading.stock_pool import StockPool

        report: dict[str, Any] = {
            "report_type": "pool_report",
            "pool_name": pool_name,
            "generate_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {},
            "positions": [],
            "performance": {},
            "risk_analysis": {},
        }

        pool = StockPool(pool_name)
        pool_status = pool.get_performance()

        report["summary"] = {
            "total_stocks": pool_status.get("total_stocks", 0),
            "watching_count": pool_status.get("watching_count", 0),
            "holding_count": pool_status.get("holding_count", 0),
            "sold_count": pool_status.get("sold_count", 0),
            "total_profit": pool_status.get("total_profit", 0),
            "total_profit_rate": pool_status.get("total_profit_rate", 0),
        }

        positions_dict = pool.positions
        positions_list: list[dict[str, Any]] = report["positions"]
        if positions_dict:
            for code, pos in positions_dict.items():
                positions_list.append(
                    {
                        "code": pos.code,
                        "name": pos.name,
                        "status": pos.status,
                        "buy_price": pos.buy_price,
                        "current_price": pos.current_price,
                        "sell_price": pos.sell_price,
                        "shares": pos.shares,
                        "selected_count": pos.selected_count,
                        "first_selected_date": pos.first_selected_date,
                    }
                )

        report["performance"] = {
            "win_rate": pool_status.get("win_rate", 0),
            "avg_profit_rate": pool_status.get("avg_profit_rate", 0),
            "max_profit": pool_status.get("max_profit", 0),
            "max_loss": pool_status.get("max_loss", 0),
        }

        report["risk_analysis"] = self._analyze_pool_risk(pool)

        tracker = StockTracker(pool_name)
        tracking_report = tracker.get_tracking_report()
        report["monster_signals"] = tracking_report.get("recent_monsters", [])
        report["best_performers"] = tracking_report.get("best_performers", [])
        report["worst_performers"] = tracking_report.get("worst_performers", [])

        filename = f"pool_{pool_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.report_path / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        report["report_file"] = str(filepath)
        return report

    def generate_comparison_report(
        self,
        strategies: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        生成策略对比报告

        Args:
            strategies: 要对比的策略列表

        Returns:
            报告数据
        """
        from ..strategy.engine import strategy_engine

        if not strategies:
            strategies = ["value", "momentum", "reversal", "dividend"]

        report: dict[str, Any] = {
            "report_type": "comparison_report",
            "strategies": strategies,
            "generate_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "comparison": [],
            "recommendations": [],
        }

        comparison_list: list[dict[str, Any]] = report["comparison"]

        for strategy_name in strategies:
            strategy = strategy_engine.get_strategy(strategy_name)
            if not strategy:
                continue

            pool = StockPool(strategy_name)
            pool_status = pool.get_performance()

            comparison_list.append(
                {
                    "name": strategy_name,
                    "description": strategy.description,
                    "total_stocks": pool_status.get("total_stocks", 0),
                    "holding_count": pool_status.get("holding_count", 0),
                    "win_rate": pool_status.get("win_rate", 0),
                    "total_profit_rate": pool_status.get("total_profit_rate", 0),
                    "risk_level": self._calculate_risk_level(strategy),
                }
            )

        comparison_list.sort(key=lambda x: x.get("total_profit_rate", 0), reverse=True)

        if comparison_list:
            best = comparison_list[0]
            recommendations_list: list[dict[str, Any]] = report["recommendations"]
            recommendations_list.append(
                {
                    "type": "best_strategy",
                    "strategy": best["name"],
                    "reason": f"收益率最高 ({best['total_profit_rate']:.2f}%)",
                }
            )

        filename = f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.report_path / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        report["report_file"] = str(filepath)
        return report

    def generate_risk_report(self, pool_name: str = "default") -> dict[str, Any]:
        """
        生成风险评估报告

        Args:
            pool_name: 股票池名称

        Returns:
            报告数据
        """
        from ..data.market_environment import market_environment_analyzer
        from ..trading.stock_pool import StockPool

        report: dict[str, Any] = {
            "report_type": "risk_report",
            "pool_name": pool_name,
            "generate_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "risk_metrics": {},
            "warnings": [],
            "recommendations": [],
        }

        pool = StockPool(pool_name)
        pool_status = pool.get_performance()

        holding_count = pool_status.get("holding_count", 0)
        total_stocks = pool_status.get("total_stocks", 0)

        if total_stocks > 0:
            concentration = holding_count / total_stocks
        else:
            concentration = 0

        report["risk_metrics"] = {
            "concentration": concentration,
            "win_rate": pool_status.get("win_rate", 0),
            "avg_profit_rate": pool_status.get("avg_profit_rate", 0),
            "max_loss": pool_status.get("max_loss", 0),
        }

        warnings_list: list[dict[str, Any]] = report["warnings"]
        if concentration > 0.7:
            warnings_list.append(
                {
                    "level": "high",
                    "type": "concentration",
                    "message": f"持仓集中度过高 ({concentration:.1%})，建议分散投资",
                }
            )

        if pool_status.get("win_rate", 0) < 0.4:
            warnings_list.append(
                {
                    "level": "medium",
                    "type": "win_rate",
                    "message": f"胜率较低 ({pool_status.get('win_rate', 0):.1%})，建议优化策略",
                }
            )

        if pool_status.get("max_loss", 0) < -0.1:
            warnings_list.append(
                {
                    "level": "high",
                    "type": "max_loss",
                    "message": f"最大亏损较大 ({pool_status.get('max_loss', 0):.2%})，建议加强止损",
                }
            )

        environment = market_environment_analyzer.analyze_environment()
        report["market_environment"] = {
            "type": environment.market_type,
            "risk_level": environment.risk_level,
            "sentiment": environment.sentiment,
        }

        if environment.risk_level == "high":
            warnings_list.append(
                {
                    "level": "high",
                    "type": "market_risk",
                    "message": f"市场风险较高 ({environment.market_type})，建议降低仓位",
                }
            )

        report["recommendations"] = self._generate_risk_recommendations(report)

        filename = f"risk_{pool_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.report_path / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        report["report_file"] = str(filepath)
        return report

    def _generate_strategy_recommendations(
        self,
        strategy_name: str,
        pool_status: dict[str, Any],
        tracking_report: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """生成策略建议"""
        recommendations = []

        win_rate = pool_status.get("win_rate", 0)
        if win_rate < 0.5:
            recommendations.append(
                {
                    "type": "strategy_optimization",
                    "priority": "high",
                    "message": f"胜率 {win_rate:.1%} 偏低，建议调整策略参数或更换策略",
                }
            )

        holding_count = pool_status.get("holding_count", 0)
        if holding_count == 0:
            recommendations.append(
                {
                    "type": "action",
                    "priority": "medium",
                    "message": "当前无持仓，建议筛选股票后模拟买入",
                }
            )

        monster_signals = tracking_report.get("recent_monsters", [])
        if monster_signals:
            recommendations.append(
                {
                    "type": "opportunity",
                    "priority": "medium",
                    "message": f"检测到 {len(monster_signals)} 个妖股信号，建议关注",
                }
            )

        return recommendations

    def _analyze_pool_risk(self, pool: Any) -> dict[str, Any]:
        """分析股票池风险"""
        positions = list(pool.positions.values())

        if not positions:
            return {"risk_level": "unknown", "message": "无持仓数据"}

        holding_positions = [p for p in positions if p.status == "holding"]

        if not holding_positions:
            return {"risk_level": "low", "message": "无持仓，风险较低"}

        total_value = sum(p.buy_price * p.shares for p in holding_positions)

        if total_value == 0:
            return {"risk_level": "unknown", "message": "无法计算持仓价值"}

        position_weights = [
            (p.code, (p.buy_price * p.shares) / total_value) for p in holding_positions
        ]

        max_weight = max(w for _, w in position_weights) if position_weights else 0

        if max_weight > 0.3:
            risk_level = "high"
            message = f"单一持仓占比过高 ({max_weight:.1%})"
        elif max_weight > 0.2:
            risk_level = "medium"
            message = f"持仓较为集中 ({max_weight:.1%})"
        else:
            risk_level = "low"
            message = "持仓分散度良好"

        return {
            "risk_level": risk_level,
            "message": message,
            "max_position_weight": max_weight,
            "position_count": len(holding_positions),
        }

    def _calculate_risk_level(self, strategy: Any) -> str:
        """计算策略风险等级"""
        risk_score = 0

        if strategy.stop_loss and strategy.stop_loss < -0.1:
            risk_score += 1
        elif not strategy.stop_loss:
            risk_score += 2

        if strategy.take_profit and strategy.take_profit > 0.2:
            risk_score += 1

        if strategy.max_position and strategy.max_position > 10:
            risk_score += 1

        if risk_score >= 3:
            return "high"
        elif risk_score >= 2:
            return "medium"
        else:
            return "low"

    def _generate_risk_recommendations(self, report: dict[str, Any]) -> list[dict[str, Any]]:
        """生成风险建议"""
        recommendations = []

        warnings = report.get("warnings", [])
        high_warnings = [w for w in warnings if w.get("level") == "high"]

        if high_warnings:
            recommendations.append(
                {
                    "type": "urgent",
                    "priority": "high",
                    "message": f"存在 {len(high_warnings)} 个高风险警告，请立即处理",
                }
            )

        concentration = report.get("risk_metrics", {}).get("concentration", 0)
        if concentration > 0.5:
            recommendations.append(
                {
                    "type": "diversification",
                    "priority": "medium",
                    "message": "建议分散持仓，降低单一股票风险",
                }
            )

        market_risk = report.get("market_environment", {}).get("risk_level", "low")
        if market_risk == "high":
            recommendations.append(
                {
                    "type": "position_control",
                    "priority": "high",
                    "message": "市场风险较高，建议降低整体仓位至 50% 以下",
                }
            )

        return recommendations

    def print_report(self, report: dict[str, Any]) -> None:
        """打印报告"""
        report_type = report.get("report_type", "unknown")

        print("\n" + "=" * 60)
        print(f"📊 {self._get_report_title(report_type)}")
        print("=" * 60)
        print(f"生成时间: {report.get('generate_time', 'N/A')}")

        if report_type == "strategy_report":
            self._print_strategy_report(report)
        elif report_type == "pool_report":
            self._print_pool_report(report)
        elif report_type == "comparison_report":
            self._print_comparison_report(report)
        elif report_type == "risk_report":
            self._print_risk_report(report)

        print(f"\n📁 报告已保存: {report.get('report_file', 'N/A')}")
        print("=" * 60)

    def _get_report_title(self, report_type: str) -> str:
        """获取报告标题"""
        titles = {
            "strategy_report": "策略报告",
            "pool_report": "股票池报告",
            "comparison_report": "策略对比报告",
            "risk_report": "风险评估报告",
        }
        return titles.get(report_type, "投资报告")

    def _print_strategy_report(self, report: dict[str, Any]) -> None:
        """打印策略报告"""
        strategy_info = report.get("strategy_info", {})
        print(f"\n策略: {strategy_info.get('name', 'N/A')}")
        print(f"描述: {strategy_info.get('description', 'N/A')}")

        print("\n股票池状态:")
        pool_status = report.get("pool_status", {})
        print(f"  总股票数: {pool_status.get('total_stocks', 0)}")
        print(f"  持有中: {pool_status.get('holding_count', 0)}")

        print("\n绩效表现:")
        performance = report.get("performance", {})
        print(f"  总收益: {performance.get('total_profit', 0):.2f}")
        print(f"  收益率: {performance.get('total_profit_rate', 0):.2%}")
        print(f"  胜率: {performance.get('win_rate', 0):.2%}")

        if report.get("recommendations"):
            print("\n建议:")
            for r in report["recommendations"]:
                print(f"  • {r.get('message', '')}")

    def _print_pool_report(self, report: dict[str, Any]) -> None:
        """打印股票池报告"""
        print(f"\n股票池: {report.get('pool_name', 'N/A')}")

        print("\n概览:")
        summary = report.get("summary", {})
        print(f"  总股票数: {summary.get('total_stocks', 0)}")
        print(f"  总收益: {summary.get('total_profit', 0):.2f}")
        print(f"  收益率: {summary.get('total_profit_rate', 0):.2%}")

        print("\n风险分析:")
        risk = report.get("risk_analysis", {})
        print(f"  风险等级: {risk.get('risk_level', 'N/A')}")
        print(f"  {risk.get('message', '')}")

    def _print_comparison_report(self, report: dict[str, Any]) -> None:
        """打印对比报告"""
        print("\n策略对比:")
        print("-" * 60)
        print(f"{'策略':<12} {'股票数':>8} {'胜率':>10} {'收益率':>10} {'风险':>8}")
        print("-" * 60)

        for item in report.get("comparison", []):
            print(
                f"{item.get('name', ''):<12} "
                f"{item.get('total_stocks', 0):>8} "
                f"{item.get('win_rate', 0):>10.1%} "
                f"{item.get('total_profit_rate', 0):>10.2%} "
                f"{item.get('risk_level', ''):>8}"
            )

        print("-" * 60)

    def _print_risk_report(self, report: dict[str, Any]) -> None:
        """打印风险报告"""
        print(f"\n股票池: {report.get('pool_name', 'N/A')}")

        print("\n风险指标:")
        metrics = report.get("risk_metrics", {})
        print(f"  持仓集中度: {metrics.get('concentration', 0):.1%}")
        print(f"  胜率: {metrics.get('win_rate', 0):.1%}")
        print(f"  最大亏损: {metrics.get('max_loss', 0):.2%}")

        warnings = report.get("warnings", [])
        if warnings:
            print(f"\n⚠️ 警告 ({len(warnings)} 个):")
            for w in warnings:
                level_icon = "🔴" if w.get("level") == "high" else "🟡"
                print(f"  {level_icon} {w.get('message', '')}")

    def export_html_report(
        self,
        report: dict[str, Any],
        output_file: str | None = None,
        include_charts: bool = True,
    ) -> str:
        """
        导出 HTML 报告

        Args:
            report: 报告数据
            output_file: 输出文件路径
            include_charts: 是否包含图表

        Returns:
            HTML 文件路径
        """
        if output_file is None:
            report_type = report.get("report_type", "report")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"{report_type}_{timestamp}.html"

        filepath = self.report_path / output_file

        html_content = self._generate_html(report, include_charts)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        return str(filepath)

    def _generate_html(self, report: dict[str, Any], include_charts: bool) -> str:
        """生成 HTML 内容"""
        report_type = report.get("report_type", "unknown")
        title = self._get_report_title(report_type)

        html_parts = [
            "<!DOCTYPE html>",
            "<html lang='zh-CN'>",
            "<head>",
            "    <meta charset='UTF-8'>",
            "    <meta name='viewport' content='width=device-width, initial-scale=1.0'>",
            f"    <title>{title} - Asset Lens</title>",
            "    <style>",
            "        * { margin: 0; padding: 0; box-sizing: border-box; }",
            "        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; background: #f5f5f5; }",
            "        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }",
            "        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }",
            "        .header h1 { font-size: 28px; margin-bottom: 10px; }",
            "        .header .meta { font-size: 14px; opacity: 0.9; }",
            "        .card { background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }",
            "        .card h2 { font-size: 20px; margin-bottom: 15px; color: #667eea; border-bottom: 2px solid #667eea; padding-bottom: 10px; }",
            "        .card h3 { font-size: 16px; margin: 15px 0 10px 0; color: #333; }",
            "        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }",
            "        .metric { background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }",
            "        .metric .value { font-size: 24px; font-weight: bold; color: #667eea; }",
            "        .metric .label { font-size: 12px; color: #666; margin-top: 5px; }",
            "        .warning { background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 10px 0; border-radius: 4px; }",
            "        .warning.high { background: #f8d7da; border-left-color: #dc3545; }",
            "        .recommendation { background: #d1ecf1; border-left: 4px solid #17a2b8; padding: 15px; margin: 10px 0; border-radius: 4px; }",
            "        table { width: 100%; border-collapse: collapse; margin: 15px 0; }",
            "        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }",
            "        th { background: #f8f9fa; font-weight: 600; }",
            "        tr:hover { background: #f8f9fa; }",
            "        .positive { color: #28a745; }",
            "        .negative { color: #dc3545; }",
            "        .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }",
            "    </style>",
            "</head>",
            "<body>",
            "    <div class='container'>",
            "        <div class='header'>",
            f"            <h1>📊 {title}</h1>",
            f"            <div class='meta'>生成时间: {report.get('generate_time', 'N/A')}</div>",
            "        </div>",
        ]

        if report_type == "strategy_report":
            html_parts.extend(self._generate_strategy_html(report))
        elif report_type == "pool_report":
            html_parts.extend(self._generate_pool_html(report))
        elif report_type == "comparison_report":
            html_parts.extend(self._generate_comparison_html(report))
        elif report_type == "risk_report":
            html_parts.extend(self._generate_risk_html(report))

        html_parts.extend(
            [
                "        <div class='footer'>",
                "            <p>Generated by Asset Lens - Personal Asset Operating System</p>",
                "        </div>",
                "    </div>",
                "</body>",
                "</html>",
            ]
        )

        return "\n".join(html_parts)

    def _generate_strategy_html(self, report: dict[str, Any]) -> list[str]:
        """生成策略报告 HTML"""
        parts = []
        strategy_info = report.get("strategy_info", {})
        pool_status = report.get("pool_status", {})
        performance = report.get("performance", {})

        parts.extend(
            [
                "        <div class='card'>",
                "            <h2>策略信息</h2>",
                f"            <p><strong>名称:</strong> {strategy_info.get('name', 'N/A')}</p>",
                f"            <p><strong>描述:</strong> {strategy_info.get('description', 'N/A')}</p>",
                "        </div>",
                "        <div class='card'>",
                "            <h2>股票池状态</h2>",
                "            <div class='metrics'>",
                "                <div class='metric'>",
                f"                    <div class='value'>{pool_status.get('total_stocks', 0)}</div>",
                "                    <div class='label'>总股票数</div>",
                "                </div>",
                "                <div class='metric'>",
                f"                    <div class='value'>{pool_status.get('holding_count', 0)}</div>",
                "                    <div class='label'>持有中</div>",
                "                </div>",
                "            </div>",
                "        </div>",
                "        <div class='card'>",
                "            <h2>绩效表现</h2>",
                "            <div class='metrics'>",
                "                <div class='metric'>",
                f"                    <div class='value'>¥{performance.get('total_profit', 0):,.2f}</div>",
                "                    <div class='label'>总收益</div>",
                "                </div>",
                "                <div class='metric'>",
                f"                    <div class='value'>{performance.get('total_profit_rate', 0):.1%}</div>",
                "                    <div class='label'>收益率</div>",
                "                </div>",
                "                <div class='metric'>",
                f"                    <div class='value'>{performance.get('win_rate', 0):.1%}</div>",
                "                    <div class='label'>胜率</div>",
                "                </div>",
                "            </div>",
                "        </div>",
            ]
        )

        recommendations = report.get("recommendations", [])
        if recommendations:
            parts.append("        <div class='card'><h2>建议</h2>")
            for r in recommendations:
                parts.append(
                    f"            <div class='recommendation'>{r.get('message', '')}</div>"
                )
            parts.append("        </div>")

        return parts

    def _generate_pool_html(self, report: dict[str, Any]) -> list[str]:
        """生成股票池报告 HTML"""
        parts = []
        summary = report.get("summary", {})
        risk = report.get("risk_analysis", {})

        parts.extend(
            [
                "        <div class='card'>",
                "            <h2>概览</h2>",
                "            <div class='metrics'>",
                "                <div class='metric'>",
                f"                    <div class='value'>{summary.get('total_stocks', 0)}</div>",
                "                    <div class='label'>总股票数</div>",
                "                </div>",
                "                <div class='metric'>",
                f"                    <div class='value'>¥{summary.get('total_profit', 0):,.2f}</div>",
                "                    <div class='label'>总收益</div>",
                "                </div>",
                "                <div class='metric'>",
                f"                    <div class='value'>{summary.get('total_profit_rate', 0):.1%}</div>",
                "                    <div class='label'>收益率</div>",
                "                </div>",
                "            </div>",
                "        </div>",
                "        <div class='card'>",
                "            <h2>风险分析</h2>",
                f"            <p><strong>风险等级:</strong> {risk.get('risk_level', 'N/A')}</p>",
                f"            <p>{risk.get('message', '')}</p>",
                "        </div>",
            ]
        )

        return parts

    def _generate_comparison_html(self, report: dict[str, Any]) -> list[str]:
        """生成对比报告 HTML"""
        parts = []

        parts.extend(
            [
                "        <div class='card'>",
                "            <h2>策略对比</h2>",
                "            <table>",
                "                <thead>",
                "                    <tr>",
                "                        <th>策略</th>",
                "                        <th>股票数</th>",
                "                        <th>胜率</th>",
                "                        <th>收益率</th>",
                "                        <th>风险</th>",
                "                    </tr>",
                "                </thead>",
                "                <tbody>",
            ]
        )

        for item in report.get("comparison", []):
            profit_rate = item.get("total_profit_rate", 0)
            rate_class = "positive" if profit_rate >= 0 else "negative"
            parts.extend(
                [
                    "                    <tr>",
                    f"                        <td>{item.get('name', '')}</td>",
                    f"                        <td>{item.get('total_stocks', 0)}</td>",
                    f"                        <td>{item.get('win_rate', 0):.1%}</td>",
                    f"                        <td class='{rate_class}'>{profit_rate:.2%}</td>",
                    f"                        <td>{item.get('risk_level', '')}</td>",
                    "                    </tr>",
                ]
            )

        parts.extend(
            [
                "                </tbody>",
                "            </table>",
                "        </div>",
            ]
        )

        recommendations = report.get("recommendations", [])
        if recommendations:
            parts.append("        <div class='card'><h2>建议</h2>")
            for r in recommendations:
                parts.append(
                    f"            <div class='recommendation'>{r.get('message', '')}</div>"
                )
            parts.append("        </div>")

        return parts

    def _generate_risk_html(self, report: dict[str, Any]) -> list[str]:
        """生成风险报告 HTML"""
        parts = []
        metrics = report.get("risk_metrics", {})
        warnings = report.get("warnings", [])

        parts.extend(
            [
                "        <div class='card'>",
                "            <h2>风险指标</h2>",
                "            <div class='metrics'>",
                "                <div class='metric'>",
                f"                    <div class='value'>{metrics.get('concentration', 0):.1%}</div>",
                "                    <div class='label'>持仓集中度</div>",
                "                </div>",
                "                <div class='metric'>",
                f"                    <div class='value'>{metrics.get('win_rate', 0):.1%}</div>",
                "                    <div class='label'>胜率</div>",
                "                </div>",
                "                <div class='metric'>",
                f"                    <div class='value'>{metrics.get('max_loss', 0):.2%}</div>",
                "                    <div class='label'>最大亏损</div>",
                "                </div>",
                "            </div>",
                "        </div>",
            ]
        )

        if warnings:
            parts.append("        <div class='card'><h2>⚠️ 警告</h2>")
            for w in warnings:
                level_class = "high" if w.get("level") == "high" else ""
                parts.append(
                    f"            <div class='warning {level_class}'>{w.get('message', '')}</div>"
                )
            parts.append("        </div>")

        recommendations = report.get("recommendations", [])
        if recommendations:
            parts.append("        <div class='card'><h2>建议</h2>")
            for r in recommendations:
                parts.append(
                    f"            <div class='recommendation'>{r.get('message', '')}</div>"
                )
            parts.append("        </div>")

        return parts


investment_report_generator = InvestmentReportGenerator()
