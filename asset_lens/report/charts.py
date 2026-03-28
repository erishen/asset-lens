"""
Chart Generator - 图表生成器

提供报告图表生成功能。
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class ChartConfig:
    """图表配置"""
    title: str
    chart_type: str = "bar"
    width: int = 800
    height: int = 400
    show_legend: bool = True
    show_grid: bool = True
    x_label: str = ""
    y_label: str = ""


class ChartGenerator:
    """图表生成器 - 生成报告所需的图表数据"""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path(".")
        if self.output_dir:
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
            图表文件路径字典
        """
        if not portfolio_data:
            return {}

        charts = {}

        # 资产配置图
        if "type_distribution" in portfolio_data:
            path = self.generate_asset_allocation_chart(
                portfolio_data["type_distribution"],
                filename=f"{prefix}asset_allocation.png" if prefix else None,
            )
            charts["asset_allocation"] = path

        # 风险分布图
        if "risk_distribution" in portfolio_data:
            path = self.generate_risk_distribution_chart(
                portfolio_data["risk_distribution"],
                filename=f"{prefix}risk_distribution.png" if prefix else None,
            )
            charts["risk_distribution"] = path

        # 收益分布图
        if "return_distribution" in portfolio_data:
            path = self.generate_return_distribution_chart(
                portfolio_data["return_distribution"],
                filename=f"{prefix}return_distribution.png" if prefix else None,
            )
            charts["return_distribution"] = path

        # 月度收益图
        if "monthly_returns" in portfolio_data:
            path = self.generate_monthly_returns_chart(
                portfolio_data["monthly_returns"],
                filename=f"{prefix}monthly_returns.png" if prefix else None,
            )
            charts["monthly_returns"] = path

        # 累计收益图
        if "cumulative_returns" in portfolio_data:
            path = self.generate_cumulative_returns_chart(
                portfolio_data["cumulative_returns"],
                filename=f"{prefix}cumulative_returns.png" if prefix else None,
            )
            charts["cumulative_returns"] = path

        # 最佳产品图
        if "top_products" in portfolio_data:
            path = self.generate_top_products_chart(
                portfolio_data["top_products"],
                filename=f"{prefix}top_products.png" if prefix else None,
            )
            charts["top_products"] = path

        return charts

    def generate_asset_allocation_chart(
        self,
        type_distribution: Dict[str, Any],
        filename: Optional[str] = None,
    ) -> Path:
        """
        生成资产配置图表

        Args:
            type_distribution: 类型分布数据
            filename: 文件名

        Returns:
            图表文件路径
        """
        if filename is None:
            filename = f"asset_allocation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

        filepath = self.output_dir / filename

        # 生成图表数据（简化版，实际项目中可以使用 matplotlib 或其他库）
        chart_data = {
            "chart_type": "pie",
            "title": "资产配置",
            "data": type_distribution,
        }

        # 保存图表配置
        config_path = filepath.with_suffix(".json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(chart_data, f, ensure_ascii=False, indent=2)

        # 创建空的 PNG 文件（实际项目中应该生成真实图表）
        filepath.touch()

        return filepath

    def generate_risk_distribution_chart(
        self,
        risk_distribution: Dict[str, Any],
        filename: Optional[str] = None,
    ) -> Path:
        """
        生成风险分布图表

        Args:
            risk_distribution: 风险分布数据
            filename: 文件名

        Returns:
            图表文件路径
        """
        if filename is None:
            filename = f"risk_distribution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

        filepath = self.output_dir / filename

        chart_data = {
            "chart_type": "pie",
            "title": "风险分布",
            "data": risk_distribution,
        }

        config_path = filepath.with_suffix(".json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(chart_data, f, ensure_ascii=False, indent=2)

        filepath.touch()

        return filepath

    def generate_return_distribution_chart(
        self,
        return_distribution: Dict[str, Any],
        filename: Optional[str] = None,
    ) -> Path:
        """
        生成收益分布图表

        Args:
            return_distribution: 收益分布数据
            filename: 文件名

        Returns:
            图表文件路径
        """
        if filename is None:
            filename = f"return_distribution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

        filepath = self.output_dir / filename

        chart_data = {
            "chart_type": "bar",
            "title": "收益分布",
            "data": return_distribution,
        }

        config_path = filepath.with_suffix(".json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(chart_data, f, ensure_ascii=False, indent=2)

        filepath.touch()

        return filepath

    def generate_monthly_returns_chart(
        self,
        monthly_returns: List[Dict[str, Any]],
        filename: Optional[str] = None,
    ) -> Path:
        """
        生成月度收益图表

        Args:
            monthly_returns: 月度收益数据
            filename: 文件名

        Returns:
            图表文件路径
        """
        if filename is None:
            filename = f"monthly_returns_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

        filepath = self.output_dir / filename

        chart_data = {
            "chart_type": "bar",
            "title": "月度收益",
            "data": monthly_returns,
        }

        config_path = filepath.with_suffix(".json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(chart_data, f, ensure_ascii=False, indent=2)

        filepath.touch()

        return filepath

    def generate_cumulative_returns_chart(
        self,
        cumulative_returns: List[Dict[str, Any]],
        filename: Optional[str] = None,
    ) -> Path:
        """
        生成累计收益图表

        Args:
            cumulative_returns: 累计收益数据
            filename: 文件名

        Returns:
            图表文件路径
        """
        if filename is None:
            filename = f"cumulative_returns_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

        filepath = self.output_dir / filename

        chart_data = {
            "chart_type": "line",
            "title": "累计收益",
            "data": cumulative_returns,
        }

        config_path = filepath.with_suffix(".json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(chart_data, f, ensure_ascii=False, indent=2)

        filepath.touch()

        return filepath

    def generate_top_products_chart(
        self,
        top_products: List[Dict[str, Any]],
        filename: Optional[str] = None,
    ) -> Path:
        """
        生成最佳产品图表

        Args:
            top_products: 最佳产品数据
            filename: 文件名

        Returns:
            图表文件路径
        """
        if filename is None:
            filename = f"top_products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

        filepath = self.output_dir / filename

        chart_data = {
            "chart_type": "bar",
            "title": "最佳产品",
            "data": top_products,
        }

        config_path = filepath.with_suffix(".json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(chart_data, f, ensure_ascii=False, indent=2)

        filepath.touch()

        return filepath

    def generate_pie_chart_data(
        self,
        data: Dict[str, float],
        title: str = "资产分布",
    ) -> Dict[str, Any]:
        """
        生成饼图数据

        Args:
            data: 数据字典 {标签: 值}
            title: 图表标题

        Returns:
            图表配置数据
        """
        total = sum(data.values())
        chart_data = []

        for label, value in data.items():
            percentage = (value / total * 100) if total > 0 else 0
            chart_data.append({
                "name": label,
                "value": value,
                "percentage": round(percentage, 2),
            })

        return {
            "chart_type": "pie",
            "title": title,
            "data": chart_data,
            "total": total,
        }

    def generate_bar_chart_data(
        self,
        labels: List[str],
        values: List[float],
        title: str = "收益对比",
        colors: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        生成柱状图数据

        Args:
            labels: 标签列表
            values: 值列表
            title: 图表标题
            colors: 颜色列表

        Returns:
            图表配置数据
        """
        default_colors = [
            "#4CAF50" if v >= 0 else "#F44336"
            for v in values
        ]

        return {
            "chart_type": "bar",
            "title": title,
            "labels": labels,
            "datasets": [{
                "data": values,
                "backgroundColor": colors or default_colors,
            }],
        }

    def generate_line_chart_data(
        self,
        labels: List[str],
        datasets: List[Dict[str, Any]],
        title: str = "收益曲线",
    ) -> Dict[str, Any]:
        """
        生成折线图数据

        Args:
            labels: X 轴标签
            datasets: 数据集列表
            title: 图表标题

        Returns:
            图表配置数据
        """
        return {
            "chart_type": "line",
            "title": title,
            "labels": labels,
            "datasets": datasets,
        }

    def save_chart_config(
        self,
        chart_data: Dict[str, Any],
        filename: str,
    ) -> Optional[Path]:
        """
        保存图表配置到文件

        Args:
            chart_data: 图表数据
            filename: 文件名

        Returns:
            文件路径
        """
        if not self.output_dir:
            return None

        self.output_dir.mkdir(parents=True, exist_ok=True)
        filepath = self.output_dir / f"{filename}.json"

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(chart_data, f, ensure_ascii=False, indent=2)

        return filepath
