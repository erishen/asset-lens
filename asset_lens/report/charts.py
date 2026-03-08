"""
Chart generation module for asset-lens.
图表生成模块 - 使用 matplotlib 生成投资分析图表
"""

import os
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["font.sans-serif"] = ["Arial Unicode MS", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


class ChartGenerator:
    """图表生成器"""

    def __init__(self, output_dir: Optional[Path] = None):
        """
        初始化图表生成器

        Args:
            output_dir: 输出目录，默认为 output/charts
        """
        self.output_dir = output_dir or Path("output/charts")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_all_charts(
        self,
        portfolio_data: Dict[str, Any],
        prefix: str = "",
    ) -> Dict[str, Path]:
        """
        生成所有图表

        Args:
            portfolio_data: 投资组合数据
            prefix: 文件名前缀

        Returns:
            生成的图表文件路径
        """
        charts = {}

        if "type_distribution" in portfolio_data:
            charts["asset_allocation"] = self.generate_asset_allocation_chart(
                portfolio_data["type_distribution"],
                filename=f"{prefix}asset_allocation.png" if prefix else "asset_allocation.png",
            )

        if "risk_distribution" in portfolio_data:
            charts["risk_distribution"] = self.generate_risk_distribution_chart(
                portfolio_data["risk_distribution"],
                filename=f"{prefix}risk_distribution.png" if prefix else "risk_distribution.png",
            )

        if "return_distribution" in portfolio_data:
            charts["return_distribution"] = self.generate_return_distribution_chart(
                portfolio_data["return_distribution"],
                filename=f"{prefix}return_distribution.png"
                if prefix
                else "return_distribution.png",
            )

        if "monthly_returns" in portfolio_data:
            charts["monthly_returns"] = self.generate_monthly_returns_chart(
                portfolio_data["monthly_returns"],
                filename=f"{prefix}monthly_returns.png" if prefix else "monthly_returns.png",
            )

        if "cumulative_returns" in portfolio_data:
            charts["cumulative_returns"] = self.generate_cumulative_returns_chart(
                portfolio_data["cumulative_returns"],
                filename=f"{prefix}cumulative_returns.png" if prefix else "cumulative_returns.png",
            )

        if "top_products" in portfolio_data:
            charts["top_products"] = self.generate_top_products_chart(
                portfolio_data["top_products"],
                filename=f"{prefix}top_products.png" if prefix else "top_products.png",
            )

        return charts

    def generate_asset_allocation_chart(
        self,
        type_distribution: Dict[str, Any],
        filename: str = "asset_allocation.png",
        title: str = "资产配置分布",
    ) -> Path:
        """
        生成资产配置饼图

        Args:
            type_distribution: 类型分布数据
            filename: 文件名
            title: 图表标题

        Returns:
            图表文件路径
        """
        fig, ax = plt.subplots(figsize=(10, 8))

        labels = []
        values = []
        for type_name, stats in type_distribution.items():
            labels.append(type_name)
            values.append(float(stats.get("total_value", 0)))

        total = sum(values)
        percentages = [v / total * 100 if total > 0 else 0 for v in values]

        colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))  # type: ignore

        wedges, texts, autotexts = ax.pie(
            values,
            labels=None,
            autopct=lambda pct: f"{pct:.1f}%" if pct > 3 else "",
            colors=colors,
            startangle=90,
            explode=[0.02] * len(values),
        )

        legend_labels = [
            f"{label}: ¥{value/10000:.1f}万 ({pct:.1f}%)"
            for label, value, pct in zip(labels, values, percentages)
        ]
        ax.legend(
            wedges,
            legend_labels,
            title="资产类型",
            loc="center left",
            bbox_to_anchor=(1, 0, 0.5, 1),
        )

        ax.set_title(title, fontsize=14, fontweight="bold")

        plt.tight_layout()

        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()

        return output_path

    def generate_risk_distribution_chart(
        self,
        risk_distribution: Dict[str, Any],
        filename: str = "risk_distribution.png",
        title: str = "风险等级分布",
    ) -> Path:
        """
        生成风险分布饼图

        Args:
            risk_distribution: 风险分布数据
            filename: 文件名
            title: 图表标题

        Returns:
            图表文件路径
        """
        fig, ax = plt.subplots(figsize=(10, 8))

        labels = []
        values = []
        for risk_name, stats in risk_distribution.items():
            labels.append(f"{risk_name}风险")
            values.append(float(stats.get("total_value", 0)))

        colors = ["#2ecc71", "#f39c12", "#e74c3c"][: len(labels)]

        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            autopct="%1.1f%%",
            colors=colors,
            startangle=90,
            explode=[0.02] * len(values),
        )

        ax.set_title(title, fontsize=14, fontweight="bold")

        plt.tight_layout()

        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()

        return output_path

    def generate_return_distribution_chart(
        self,
        return_distribution: Dict[str, int],
        filename: str = "return_distribution.png",
        title: str = "收益率分布",
    ) -> Path:
        """
        生成收益率分布柱状图

        Args:
            return_distribution: 收益率分布数据
            filename: 文件名
            title: 图表标题

        Returns:
            图表文件路径
        """
        fig, ax = plt.subplots(figsize=(12, 6))

        labels = list(return_distribution.keys())
        values = list(return_distribution.values())

        colors = []
        for label in labels:
            if "亏损" in label or "负" in label:
                colors.append("#e74c3c")
            elif "盈利" in label or "正" in label:
                colors.append("#2ecc71")
            else:
                colors.append("#3498db")

        bars = ax.bar(labels, values, color=colors, edgecolor="white", linewidth=1.2)

        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.annotate(
                f"{value}",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=10,
            )

        ax.set_xlabel("收益率区间", fontsize=12)
        ax.set_ylabel("产品数量", fontsize=12)
        ax.set_title(title, fontsize=14, fontweight="bold")

        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()

        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()

        return output_path

    def generate_monthly_returns_chart(
        self,
        monthly_returns: List[Dict[str, Any]],
        filename: str = "monthly_returns.png",
        title: str = "月度收益走势",
    ) -> Path:
        """
        生成月度收益走势图

        Args:
            monthly_returns: 月度收益数据
            filename: 文件名
            title: 图表标题

        Returns:
            图表文件路径
        """
        fig, ax = plt.subplots(figsize=(14, 6))

        dates = [datetime.strptime(m["month"], "%Y-%m") for m in monthly_returns]
        returns = [float(m.get("return_rate", 0)) for m in monthly_returns]

        colors = ["#2ecc71" if r >= 0 else "#e74c3c" for r in returns]

        ax.bar(dates, returns, color=colors, width=20, edgecolor="white", linewidth=0.5)

        ax.axhline(y=0, color="gray", linestyle="-", linewidth=0.5)

        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))

        ax.set_xlabel("月份", fontsize=12)
        ax.set_ylabel("收益率 (%)", fontsize=12)
        ax.set_title(title, fontsize=14, fontweight="bold")

        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()

        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()

        return output_path

    def generate_cumulative_returns_chart(
        self,
        cumulative_returns: List[Dict[str, Any]],
        benchmark_returns: Optional[List[Dict[str, Any]]] = None,
        filename: str = "cumulative_returns.png",
        title: str = "累计收益曲线",
    ) -> Path:
        """
        生成累计收益曲线图

        Args:
            cumulative_returns: 累计收益数据
            benchmark_returns: 基准收益数据（可选）
            filename: 文件名
            title: 图表标题

        Returns:
            图表文件路径
        """
        fig, ax = plt.subplots(figsize=(14, 6))

        dates = [datetime.strptime(c["date"], "%Y-%m-%d") for c in cumulative_returns]
        values = [float(c.get("cumulative_return", 0)) for c in cumulative_returns]

        ax.plot(dates, values, label="投资组合", linewidth=2, color="#3498db")

        if benchmark_returns:
            bench_dates = [datetime.strptime(c["date"], "%Y-%m-%d") for c in benchmark_returns]
            bench_values = [float(c.get("cumulative_return", 0)) for c in benchmark_returns]
            ax.plot(
                bench_dates,
                bench_values,
                label="基准指数",
                linewidth=2,
                color="#95a5a6",
                linestyle="--",
            )

        ax.axhline(y=0, color="gray", linestyle="-", linewidth=0.5)

        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))

        ax.set_xlabel("日期", fontsize=12)
        ax.set_ylabel("累计收益率 (%)", fontsize=12)
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.legend()

        ax.fill_between(dates, values, 0, alpha=0.3, color="#3498db")

        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()

        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()

        return output_path

    def generate_top_products_chart(
        self,
        top_products: List[Dict[str, Any]],
        filename: str = "top_products.png",
        title: str = "持仓TOP10产品",
    ) -> Path:
        """
        生成持仓TOP10产品柱状图

        Args:
            top_products: TOP产品数据
            filename: 文件名
            title: 图表标题

        Returns:
            图表文件路径
        """
        fig, ax = plt.subplots(figsize=(12, 8))

        names = [p.get("name", "未知")[:15] for p in top_products[:10]]
        values = [float(p.get("current_amount", 0)) / 10000 for p in top_products[:10]]

        colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(names)))[::-1]  # type: ignore

        bars = ax.barh(names, values, color=colors, edgecolor="white", linewidth=1.2)

        for bar, value in zip(bars, values):
            width = bar.get_width()
            ax.annotate(
                f"¥{value:.1f}万",
                xy=(width, bar.get_y() + bar.get_height() / 2),
                xytext=(3, 0),
                textcoords="offset points",
                ha="left",
                va="center",
                fontsize=10,
            )

        ax.set_xlabel("持仓金额（万元）", fontsize=12)
        ax.set_title(title, fontsize=14, fontweight="bold")

        ax.invert_yaxis()

        plt.tight_layout()

        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()

        return output_path

    def generate_drawdown_chart(
        self,
        drawdown_data: List[Dict[str, Any]],
        filename: str = "drawdown.png",
        title: str = "最大回撤分析",
    ) -> Path:
        """
        生成最大回撤分析图

        Args:
            drawdown_data: 回撤数据
            filename: 文件名
            title: 图表标题

        Returns:
            图表文件路径
        """
        fig, (ax1, ax2) = plt.subplots(
            2, 1, figsize=(14, 10), gridspec_kw={"height_ratios": [2, 1]}
        )

        dates = [datetime.strptime(d["date"], "%Y-%m-%d") for d in drawdown_data]
        values = [float(d.get("portfolio_value", 0)) for d in drawdown_data]
        drawdowns = [float(d.get("drawdown", 0)) for d in drawdown_data]

        ax1.plot(dates, values, linewidth=2, color="#3498db")
        ax1.fill_between(dates, values, min(values), alpha=0.3, color="#3498db")
        ax1.set_ylabel("组合价值（元）", fontsize=12)
        ax1.set_title(title, fontsize=14, fontweight="bold")
        ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=2))

        ax2.fill_between(dates, drawdowns, 0, color="#e74c3c", alpha=0.5)
        ax2.plot(dates, drawdowns, linewidth=1, color="#e74c3c")
        ax2.set_xlabel("日期", fontsize=12)
        ax2.set_ylabel("回撤 (%)", fontsize=12)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=2))

        max_drawdown = min(drawdowns)
        max_drawdown_idx = drawdowns.index(max_drawdown)
        ax2.annotate(
            f"最大回撤: {max_drawdown:.2f}%",
            xy=(dates[max_drawdown_idx], max_drawdown),
            xytext=(10, 10),
            textcoords="offset points",
            fontsize=10,
            arrowprops=dict(arrowstyle="->", color="red"),
        )

        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()

        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()

        return output_path


chart_generator = ChartGenerator()
