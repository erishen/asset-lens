"""
Report Components - 报告组件模块

提供可复用的报告生成组件，支持渐进式重构。
"""

from .charts import ChartGenerator
from .data_collectors import ReportDataCollector
from .formatters import (
    format_currency,
    format_date,
    format_number,
    format_percentage,
)

__all__ = [
    "format_currency",
    "format_percentage",
    "format_date",
    "format_number",
    "ChartGenerator",
    "ReportDataCollector",
]
