"""
Report Templates - 报告模板系统
使用 Jinja2 模板引擎生成统一格式的报告
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, Template

TEMPLATE_DIR = Path(__file__).parent / "templates"


class ReportTemplateEngine:
    """报告模板引擎"""

    def __init__(self, template_dir: Path | None = None):
        self.template_dir = template_dir or TEMPLATE_DIR
        self.template_dir.mkdir(parents=True, exist_ok=True)

        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

        self.env.filters["datetime"] = self._filter_datetime
        self.env.filters["currency"] = self._filter_currency
        self.env.filters["percent"] = self._filter_percent

    @staticmethod
    def _filter_datetime(value: Any, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
        """日期时间过滤器"""
        if isinstance(value, datetime):
            return value.strftime(fmt)
        return str(value)

    @staticmethod
    def _filter_currency(value: Any, symbol: str = "¥") -> str:
        """货币过滤器"""
        try:
            return f"{symbol}{float(value):,.2f}"
        except (TypeError, ValueError):
            return str(value)

    @staticmethod
    def _filter_percent(value: Any, decimals: int = 2) -> str:
        """百分比过滤器"""
        try:
            return f"{float(value) * 100:.{decimals}f}%"
        except (TypeError, ValueError):
            return str(value)

    def render(
        self,
        template_name: str,
        context: dict[str, Any],
    ) -> str:
        """
        渲染报告模板
        
        Args:
            template_name: 模板文件名
            context: 模板上下文数据
            
        Returns:
            渲染后的报告文本
        """
        template = self.env.get_template(template_name)
        return template.render(**context)

    def render_string(
        self,
        template_string: str,
        context: dict[str, Any],
    ) -> str:
        """
        渲染模板字符串
        
        Args:
            template_string: 模板字符串
            context: 模板上下文数据
            
        Returns:
            渲染后的报告文本
        """
        template = Template(template_string)
        return template.render(**context)


template_engine = ReportTemplateEngine()


__all__ = ["ReportTemplateEngine", "template_engine"]
