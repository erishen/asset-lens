"""
Report Components - 报告组件模块

提供可复用的报告生成组件，支持渐进式重构。
"""

from .formatters import (
    format_currency,
    format_percentage,
    format_date,
    format_number,
)
from .charts import ChartGenerator
from .data_collectors import ReportDataCollector
from .investment_report import InvestmentReportGenerator, investment_report_generator
from .template_engine import ReportTemplateEngine, template_engine

__all__ = [
    "format_currency",
    "format_percentage",
    "format_date",
    "format_number",
    "ChartGenerator",
    "ReportDataCollector",
    "InvestmentReportGenerator",
    "investment_report_generator",
    "ReportTemplateEngine",
    "template_engine",
]
