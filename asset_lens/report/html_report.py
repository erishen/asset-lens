"""
HTML report generation module for asset-lens.
HTML 报告生成模块 - 使用 Jinja2 生成专业投资报告
"""

import base64
from datetime import datetime
from pathlib import Path
from typing import Any


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

        html_content = self._generate_html_content(portfolio_data, analysis_result, chart_images)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return output_path

    def _generate_html_content(
        self,
        portfolio_data: dict[str, Any],
        analysis_result: dict[str, Any] | None = None,
        chart_images: dict[str, str] | None = None,
    ) -> str:
        """生成 HTML 内容"""
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

        charts_html = ""
        if chart_images:
            for chart_name, image_data in chart_images.items():
                charts_html += f"""
        <div class="chart-section">
            <h3>{chart_name}</h3>
            <img src="data:image/png;base64,{image_data}" alt="{chart_name}" class="chart-image">
        </div>
"""

        analysis_html = ""
        if analysis_result:
            summary = analysis_result.get("summary", "")
            risk_assessment = analysis_result.get("risk_assessment", "")
            suggestions = analysis_result.get("suggestions", [])
            warnings = analysis_result.get("warnings", [])

            suggestions_html = ""
            for i, suggestion in enumerate(suggestions, 1):
                suggestions_html += f"<li>{suggestion}</li>\n"

            warnings_html = ""
            for warning in warnings:
                warnings_html += f'<li class="warning">⚠️ {warning}</li>\n'

            analysis_html = f"""
        <section class="analysis-section">
            <h2>五、AI 分析建议</h2>

            <div class="analysis-block">
                <h3>投资摘要</h3>
                <p>{summary}</p>
            </div>

            <div class="analysis-block">
                <h3>风险评估</h3>
                <p>{risk_assessment}</p>
            </div>

            <div class="analysis-block">
                <h3>投资建议</h3>
                <ol>
                    {suggestions_html}
                </ol>
            </div>

            <div class="analysis-block">
                <h3>风险警告</h3>
                <ul>
                    {warnings_html}
                </ul>
            </div>
        </section>
"""

        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>投资组合分析报告</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}

        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
            margin-bottom: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}

        header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        section {{
            background: white;
            padding: 30px;
            margin-bottom: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}

        h2 {{
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}

        h3 {{
            color: #333;
            margin-bottom: 15px;
        }}

        .overview-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .card {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }}

        .card h3 {{
            font-size: 0.9em;
            color: #666;
            margin-bottom: 10px;
        }}

        .card p {{
            font-size: 1.5em;
            font-weight: bold;
            color: #333;
        }}

        .card.profit p {{
            color: #2ecc71;
        }}

        .card.loss p {{
            color: #e74c3c;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}

        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}

        th {{
            background-color: #667eea;
            color: white;
            font-weight: 600;
        }}

        tr:hover {{
            background-color: #f5f5f5;
        }}

        .chart-section {{
            margin-bottom: 30px;
        }}

        .chart-image {{
            width: 100%;
            max-width: 800px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}

        .analysis-section {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        }}

        .analysis-block {{
            background: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}

        .analysis-block h3 {{
            color: #667eea;
            margin-bottom: 15px;
        }}

        .analysis-block p {{
            line-height: 1.8;
        }}

        .analysis-block ol, .analysis-block ul {{
            margin-left: 20px;
        }}

        .analysis-block li {{
            margin-bottom: 10px;
            line-height: 1.6;
        }}

        .warning {{
            color: #e74c3c;
        }}

        footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }}

        @media (max-width: 768px) {{
            .container {{
                padding: 10px;
            }}

            header {{
                padding: 20px 10px;
            }}

            header h1 {{
                font-size: 1.8em;
            }}

            section {{
                padding: 20px;
            }}

            .overview-cards {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>投资组合分析报告</h1>
            <p>生成日期: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </header>

        <section>
            <h2>一、投资组合概览</h2>

            <div class="overview-cards">
                <div class="card">
                    <h3>总市值</h3>
                    <p>¥{total_value:,.2f}</p>
                </div>
                <div class="card {"profit" if total_profit >= 0 else "loss"}">
                    <h3>累计收益</h3>
                    <p>¥{total_profit:,.2f}</p>
                </div>
                <div class="card {"profit" if overall_return_rate >= 0 else "loss"}">
                    <h3>整体收益率</h3>
                    <p>{overall_return_rate:.2f}%</p>
                </div>
                <div class="card">
                    <h3>产品数量</h3>
                    <p>{total_products} 个</p>
                </div>
            </div>
        </section>

        <section>
            <h2>二、资产配置分析</h2>
            {type_distribution_html}
        </section>

        <section>
            <h2>三、风险分布分析</h2>
            {risk_distribution_html}
        </section>

        {charts_html}

        {analysis_html}

        <footer>
            <p>本报告由 asset-lens 自动生成</p>
        </footer>
    </div>
</body>
</html>
"""

        return html

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
