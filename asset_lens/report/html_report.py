"""
HTML report generation module for asset-lens.
HTML 报告生成模块 - 使用 Jinja2 生成专业投资报告
"""

import base64
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


class HTMLReportGenerator:
    """HTML 报告生成器"""

    def __init__(self, output_dir: Path | None = None):
        """
        初始化 HTML 报告生成器

        Args:
            output_dir: 输出目录，默认为 output/reports
        """
        self.output_dir = output_dir or Path("output/reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        template_dir = Path(__file__).parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(['html', 'xml']),
        )

    def generate_investment_report(
        self,
        portfolio_data: dict[str, Any],
        analysis_result: dict[str, Any] | None = None,
        charts: dict[str, Path] | None = None,
        filename: str = "investment_report.html",
    ) -> Path:
        """
        生成投资报告 HTML

        Args:
            portfolio_data: 投资组合数据
            analysis_result: 分析结果
            charts: 图表文件路径
            filename: 文件名

        Returns:
            HTML 文件路径
        """
        output_path = self.output_dir / filename

        chart_images = {}
        if charts:
            for chart_name, chart_path in charts.items():
                if chart_path.exists():
                    try:
                        with open(chart_path, "rb") as f:
                            chart_images[chart_name] = base64.b64encode(f.read()).decode("utf-8")
                    except Exception:
                        pass

        html_content = self._generate_html_content(
            portfolio_data, analysis_result, chart_images
        )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return output_path

    def _generate_html_content(
        self,
        portfolio_data: dict[str, Any],
        analysis_result: dict[str, Any] | None = None,
        chart_images: dict[str, str] | None = None,
    ) -> str:
        """使用 Jinja2 模板生成 HTML 内容"""
        template = self.env.get_template("investment_report.html.j2")

        total_value = portfolio_data.get("total_value", 0)
        total_profit = portfolio_data.get("total_profit", 0)
        overall_return_rate = portfolio_data.get("overall_return_rate", 0)
        total_products = portfolio_data.get("total_products", 0)

        type_distribution_html = self._generate_distribution_table(
            portfolio_data.get("type_distribution", {}),
            total_value,
            "资产类型",
        )

        risk_distribution_html = self._generate_distribution_table(
            portfolio_data.get("risk_distribution", {}),
            total_value,
            "风险等级",
        )

        return template.render(
            generated_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_value=total_value,
            total_profit=total_profit,
            overall_return_rate=overall_return_rate,
            total_products=total_products,
            type_distribution_html=type_distribution_html,
            risk_distribution_html=risk_distribution_html,
            chart_images=chart_images or {},
            analysis_result=analysis_result,
        )

    def _generate_distribution_table(
        self,
        distribution: dict[str, Any],
        total_value: float,
        label_name: str,
    ) -> str:
        """生成分布表格 HTML"""
        if not distribution:
            return "<p>暂无数据</p>"

        rows = ""
        for name, stats in distribution.items():
            value = float(stats.get("total_value", 0))
            percentage = (value / total_value * 100) if total_value > 0 else 0
            rows += f"""
            <tr>
                <td>{name}</td>
                <td>¥{value:,.2f}</td>
                <td>{percentage:.1f}%</td>
            </tr>
"""

        return f"""
        <table>
            <thead>
                <tr>
                    <th>{label_name}</th>
                    <th>金额</th>
                    <th>占比</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
"""


html_report_generator = HTMLReportGenerator()
