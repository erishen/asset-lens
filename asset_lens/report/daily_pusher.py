"""
Daily Report Pusher - 日报自动推送
整合报告模板和通知模块，实现定时推送日报
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from ..notification import NotificationChannel, NotificationMessage, NotificationService
from .template_engine import template_engine


class DailyReportPusher:
    """日报推送器"""

    def __init__(
        self,
        notification_service: NotificationService | None = None,
        config_path: Path | None = None,
    ):
        self.notification_service = notification_service or NotificationService()
        self.config_path = config_path or Path.home() / ".asset_lens" / "push_config.json"
        self._load_config()

    def _load_config(self) -> None:
        """加载推送配置"""
        import json

        self._config = {
            "enabled": True,
            "push_time": "18:00",
            "channels": ["console"],
            "include_sections": [
                "asset_summary",
                "risk_alerts",
                "suggestions",
            ],
        }

        if self.config_path.exists():
            try:
                with open(self.config_path, encoding="utf-8") as f:
                    loaded = json.load(f)
                    self._config.update(loaded)
            except (ValueError, KeyError, TypeError):
                pass

    def generate_daily_report(
        self,
        portfolio_data: dict[str, Any],
        risk_alerts: list[dict[str, Any]] | None = None,
        suggestions: list[str] | None = None,
    ) -> str:
        """
        生成日报

        Args:
            portfolio_data: 投资组合数据
            risk_alerts: 风险预警列表
            suggestions: 建议列表

        Returns:
            日报文本
        """
        context = {
            "title": "资产日报",
            "timestamp": datetime.now(),
            "summary": {
                "total_assets": portfolio_data.get("total_assets", 0),
                "total_profit": portfolio_data.get("total_profit", 0),
                "return_rate": portfolio_data.get("return_rate", 0),
                "position_count": portfolio_data.get("position_count", 0),
            },
            "positions": portfolio_data.get("positions", []),
            "risk_alerts": risk_alerts or [],
            "suggestions": suggestions
            or [
                "定期检查持仓风险",
                "保持资产配置多元化",
                "关注市场动态",
            ],
        }

        return template_engine.render("daily_report.md.j2", context)

    def push_daily_report(
        self,
        portfolio_data: dict[str, Any],
        risk_alerts: list[dict[str, Any]] | None = None,
        suggestions: list[str] | None = None,
        channels: list[str] | None = None,
    ) -> dict[str, bool]:
        """
        推送日报

        Args:
            portfolio_data: 投资组合数据
            risk_alerts: 风险预警列表
            suggestions: 建议列表
            channels: 推送渠道列表

        Returns:
            各渠道推送结果
        """

        report_content = self.generate_daily_report(
            portfolio_data,
            risk_alerts,
            suggestions,
        )

        message = NotificationMessage(
            title="📊 资产日报",
            content=report_content,
            level="info",
        )

        if channels is None:
            channel_names = self._config.get("channels", ["console"])
            channels = channel_names if isinstance(channel_names, list) else ["console"]

        channel_enums: list[Any] = []
        for ch in channels:
            if isinstance(ch, str):
                try:
                    channel_enums.append(NotificationChannel(ch))
                except ValueError:
                    continue
            else:
                channel_enums.append(ch)

        return self.notification_service.notify(message, channel_enums)

    def push_risk_alert(
        self,
        alert_type: str,
        level: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> dict[str, bool]:
        """
        推送风险预警

        Args:
            alert_type: 预警类型
            level: 预警级别
            message: 预警消息
            details: 详细信息

        Returns:
            各渠道推送结果
        """
        return self.notification_service.notify_risk_alert(
            alert_type=alert_type,
            level=level,
            message=message,
            details=details,
        )

    def push_weekly_report(
        self,
        portfolio_data: dict[str, Any],
        weekly_summary: dict[str, Any],
        market_regime: dict[str, Any] | None = None,
        top_performers: list[dict[str, Any]] | None = None,
        bottom_performers: list[dict[str, Any]] | None = None,
        risk_alerts: list[dict[str, Any]] | None = None,
        suggestions: list[str] | None = None,
        next_week_tasks: list[str] | None = None,
    ) -> dict[str, bool]:
        """
        推送周报

        Args:
            portfolio_data: 投资组合数据
            weekly_summary: 周度摘要
            market_regime: 市场环境
            top_performers: 表现最佳
            bottom_performers: 表现最差
            risk_alerts: 风险预警
            suggestions: 建议
            next_week_tasks: 下周计划

        Returns:
            各渠道推送结果
        """

        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        context = {
            "title": "资产周报",
            "start_date": start_of_week.strftime("%Y-%m-%d"),
            "end_date": end_of_week.strftime("%Y-%m-%d"),
            "timestamp": today,
            "summary": weekly_summary,
            "market_regime": market_regime
            or {
                "description": "未知",
                "volatility": 0,
                "position_limit": 0.6,
            },
            "top_performers": top_performers or [],
            "bottom_performers": bottom_performers or [],
            "risk_alerts": risk_alerts or [],
            "suggestions": suggestions
            or [
                "保持资产配置多元化",
                "定期检查持仓风险",
            ],
            "next_week_tasks": next_week_tasks
            or [
                "检查持仓风险",
                "关注市场动态",
            ],
        }

        report_content = template_engine.render("weekly_report.md.j2", context)

        message = NotificationMessage(
            title="📊 资产周报",
            content=report_content,
            level="info",
        )

        channel_names_raw = self._config.get("channels", ["console"])
        channel_names_list: list[str] = channel_names_raw if isinstance(channel_names_raw, list) else ["console"]
        channel_enums: list[Any] = []
        for ch in channel_names_list:
            try:
                channel_enums.append(NotificationChannel(str(ch)))
            except ValueError:
                continue

        return self.notification_service.notify(message, channel_enums)


daily_report_pusher = DailyReportPusher()


__all__ = [
    "DailyReportPusher",
    "daily_report_pusher",
]
