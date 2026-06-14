#!/usr/bin/env python3
import json
import logging
import os
from datetime import datetime

import pandas as pd

logger = logging.getLogger(__name__)


class TradingAnalyzer:
    def __init__(self, data_dir="data/trading_records"):
        self.data_dir = data_dir

    def load_transactions(self):
        transactions = []
        for file in os.listdir(self.data_dir):
            if file.startswith("transaction_"):
                with open(
                    os.path.join(self.data_dir, file), encoding="utf-8"
                ) as f:
                    transactions.append(json.load(f))
        return transactions

    def analyze_strategy_performance(self, transactions):
        if not transactions:
            return {"error": "没有交易记录"}

        df = pd.DataFrame(transactions)

        total_trades = len(df)
        buy_trades = len(df[df["action"] == "buy"])
        sell_trades = len(df[df["action"] == "sell"])

        profitable_trades = len(df[df["profit"] > 0])
        loss_trades = len(df[df["profit"] < 0])

        total_profit = df["profit"].sum()
        avg_profit = df["profit"].mean() if len(df) > 0 else 0

        strategy_stats = (
            df.groupby("strategy")
            .agg({"profit": ["count", "sum", "mean"], "profit_rate": "mean"})
            .round(2)
        )

        return {
            "total_trades": total_trades,
            "buy_trades": buy_trades,
            "sell_trades": sell_trades,
            "profitable_trades": profitable_trades,
            "loss_trades": loss_trades,
            "win_rate": profitable_trades / total_trades * 100 if total_trades > 0 else 0,
            "total_profit": total_profit,
            "avg_profit": avg_profit,
            "strategy_stats": strategy_stats.to_dict(),
        }

    def generate_report(self, analysis):
        report = []
        report.append("=" * 60)
        report.append("交易策略分析报告")
        report.append("=" * 60)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report.append(f"分析时间: {now_str}")
        report.append("")

        report.append("总体表现:")
        report.append(f"   总交易次数: {analysis['total_trades']}")
        report.append(f"   买入交易: {analysis['buy_trades']}次")
        report.append(f"   卖出交易: {analysis['sell_trades']}次")
        report.append(f"   盈利交易: {analysis['profitable_trades']}次")
        report.append(f"   亏损交易: {analysis['loss_trades']}次")
        report.append(f"   胜率: {analysis['win_rate']:.1f}%")
        report.append(f"   总盈利: {analysis['total_profit']:.2f}")
        report.append(f"   平均每笔盈利: {analysis['avg_profit']:.2f}")
        report.append("")

        report.append("策略表现:")
        for strategy, stats in analysis["strategy_stats"].items():
            report.append(f"   {strategy}:")
            report.append(f"     交易次数: {stats['profit']['count']}")
            report.append(f"     总盈利: {stats['profit']['sum']:.2f}")
            report.append(f"     平均盈利: {stats['profit']['mean']:.2f}")
            report.append(f"     平均收益率: {stats['profit_rate']['mean']:.2f}%")

        report.append("")
        report.append("改进建议:")
        if analysis["win_rate"] < 50:
            report.append("   1. 胜率偏低，建议优化买入时机")
        if analysis["avg_profit"] < 0:
            report.append("   2. 平均盈利为负，需要调整止损策略")
        else:
            report.append("   1. 策略表现良好，继续保持")
            report.append("   2. 考虑增加仓位或复制成功策略")

        report.append("=" * 60)
        return "\n".join(report)


if __name__ == "__main__":
    analyzer = TradingAnalyzer()
    transactions = analyzer.load_transactions()
    analysis = analyzer.analyze_strategy_performance(transactions)
    report = analyzer.generate_report(analysis)
    logger.info(report)
