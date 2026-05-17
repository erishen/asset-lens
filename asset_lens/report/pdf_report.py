"""
PDF report generation module for asset-lens.
PDF 报告生成模块 - 使用 reportlab 生成专业投资报告
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


class PDFReportGenerator:
    """PDF 报告生成器"""

    def __init__(self, output_dir: Path | None = None):
        """
        初始化 PDF 报告生成器

        Args:
            output_dir: 输出目录，默认为 output/reports
        """
        self.output_dir = output_dir or Path("output/reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self._setup_fonts()
        self._setup_styles()

    def _setup_fonts(self):
        """设置中文字体"""
        font_paths = [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/truetype/arphic/uming.ttc",
        ]

        self.chinese_font = "Helvetica"
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont("ChineseFont", font_path))
                    self.chinese_font = "ChineseFont"
                    break
                except Exception:
                    pass

    def _setup_styles(self):
        """设置样式"""
        self.styles = getSampleStyleSheet()

        self.styles.add(
            ParagraphStyle(
                name="ChineseTitle",
                fontName=self.chinese_font,
                fontSize=18,
                leading=24,
                alignment=1,
                spaceAfter=20,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="ChineseHeading",
                fontName=self.chinese_font,
                fontSize=14,
                leading=18,
                spaceBefore=15,
                spaceAfter=10,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="ChineseBody",
                fontName=self.chinese_font,
                fontSize=10,
                leading=14,
                spaceBefore=5,
                spaceAfter=5,
            )
        )

    def generate_investment_report(
        self,
        portfolio_data: dict[str, Any],
        analysis_result: dict[str, Any] | None = None,
        charts: dict[str, Path] | None = None,
        filename: str = "investment_report.pdf",
    ) -> Path:
        """
        生成投资报告 PDF

        Args:
            portfolio_data: 投资组合数据
            analysis_result: 分析结果
            charts: 图表文件路径
            filename: 文件名

        Returns:
            PDF 文件路径
        """
        output_path = self.output_dir / filename
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        story = []

        story.append(
            Paragraph(
                "投资组合分析报告",
                self.styles["ChineseTitle"],
            )
        )

        story.append(
            Paragraph(
                f"生成日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                self.styles["ChineseBody"],
            )
        )

        story.append(Spacer(1, 20))

        story.append(Paragraph("一、投资组合概览", self.styles["ChineseHeading"]))

        overview_data = [
            ["指标", "数值"],
            ["总市值", f"¥{portfolio_data.get('total_value', 0):,.2f}"],
            ["累计收益", f"¥{portfolio_data.get('total_profit', 0):,.2f}"],
            ["整体收益率", f"{portfolio_data.get('overall_return_rate', 0):.2f}%"],
            ["产品数量", f"{portfolio_data.get('total_products', 0)} 个"],
        ]

        overview_table = Table(overview_data, colWidths=[6 * cm, 8 * cm])
        overview_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), self.chinese_font),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ROWHEIGHT", (0, 0), (-1, -1), 25),
                ]
            )
        )
        story.append(overview_table)

        story.append(Spacer(1, 20))

        if "type_distribution" in portfolio_data:
            story.append(Paragraph("二、资产配置分析", self.styles["ChineseHeading"]))

            type_data = [["资产类型", "金额", "占比"]]
            for type_name, stats in portfolio_data["type_distribution"].items():
                total_value = float(stats.get("total_value", 0))
                total = float(portfolio_data.get("total_value", 1))
                percentage = (total_value / total * 100) if total > 0 else 0
                type_data.append(
                    [
                        type_name,
                        f"¥{total_value:,.2f}",
                        f"{percentage:.1f}%",
                    ]
                )

            type_table = Table(type_data, colWidths=[5 * cm, 5 * cm, 4 * cm])
            type_table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (-1, -1), self.chinese_font),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("ROWHEIGHT", (0, 0), (-1, -1), 22),
                    ]
                )
            )
            story.append(type_table)

        story.append(Spacer(1, 20))

        if "risk_distribution" in portfolio_data:
            story.append(Paragraph("三、风险分布分析", self.styles["ChineseHeading"]))

            risk_data = [["风险等级", "金额", "占比"]]
            for risk_name, stats in portfolio_data["risk_distribution"].items():
                total_value = float(stats.get("total_value", 0))
                total = float(portfolio_data.get("total_value", 1))
                percentage = (total_value / total * 100) if total > 0 else 0
                risk_data.append(
                    [
                        f"{risk_name}风险",
                        f"¥{total_value:,.2f}",
                        f"{percentage:.1f}%",
                    ]
                )

            risk_table = Table(risk_data, colWidths=[5 * cm, 5 * cm, 4 * cm])
            risk_table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (-1, -1), self.chinese_font),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("ROWHEIGHT", (0, 0), (-1, -1), 22),
                    ]
                )
            )
            story.append(risk_table)

        if charts:
            story.append(PageBreak())
            story.append(Paragraph("四、图表分析", self.styles["ChineseHeading"]))

            for chart_name, chart_path in charts.items():
                if chart_path.exists():
                    story.append(Paragraph(f"{chart_name}", self.styles["ChineseBody"]))
                    try:
                        img = Image(str(chart_path), width=15 * cm, height=10 * cm)
                        story.append(img)
                        story.append(Spacer(1, 10))
                    except Exception:
                        pass

        if analysis_result:
            story.append(PageBreak())
            story.append(Paragraph("五、AI 分析建议", self.styles["ChineseHeading"]))

            if "summary" in analysis_result:
                story.append(Paragraph("投资摘要", self.styles["ChineseBody"]))
                story.append(Paragraph(analysis_result["summary"], self.styles["ChineseBody"]))
                story.append(Spacer(1, 10))

            if "risk_assessment" in analysis_result:
                story.append(Paragraph("风险评估", self.styles["ChineseBody"]))
                story.append(Paragraph(analysis_result["risk_assessment"], self.styles["ChineseBody"]))
                story.append(Spacer(1, 10))

            if "suggestions" in analysis_result:
                story.append(Paragraph("投资建议", self.styles["ChineseBody"]))
                for i, suggestion in enumerate(analysis_result["suggestions"], 1):
                    story.append(Paragraph(f"{i}. {suggestion}", self.styles["ChineseBody"]))
                story.append(Spacer(1, 10))

            if "warnings" in analysis_result:
                story.append(Paragraph("风险警告", self.styles["ChineseBody"]))
                story.extend(Paragraph(f"⚠️ {warning}", self.styles["ChineseBody"]) for warning in analysis_result["warnings"])

        doc.build(story)

        return output_path


pdf_report_generator = PDFReportGenerator()
