"""
Announcement Alert Module.
公告提醒模块 - 监控持仓个股公告

功能:
1. 业绩预告/公告提醒
2. 分红派息提醒
3. 股东增减持提醒
4. 重大事项公告
5. 停复牌提醒
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from ..config import config
from .signal_pusher import Priority, Signal, SignalPusher, SignalType

logger = logging.getLogger(__name__)


class AnnouncementType(Enum):
    """公告类型"""

    EARNINGS = "earnings"  # 业绩公告
    DIVIDEND = "dividend"  # 分红派息
    SHAREHOLDER = "shareholder"  # 股东增减持
    MAJOR_EVENT = "major_event"  # 重大事项
    SUSPENSION = "suspension"  # 停复牌
    IPO = "ipo"  # 新股相关
    RESTRUCTURING = "restructuring"  # 重组
    OTHER = "other"  # 其他


class ImpactLevel(Enum):
    """影响程度"""

    POSITIVE_HIGH = "positive_high"  # 重大利好
    POSITIVE = "positive"  # 利好
    NEUTRAL = "neutral"  # 中性
    NEGATIVE = "negative"  # 利空
    NEGATIVE_HIGH = "negative_high"  # 重大利空


@dataclass
class Announcement:
    """公告"""

    code: str
    name: str
    title: str
    content: str
    ann_type: AnnouncementType
    impact: ImpactLevel
    publish_date: str
    source: str = ""
    url: str = ""
    summary: str = ""
    action_required: bool = False
    action_suggestion: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


@dataclass
class AnnouncementAlert:
    """公告预警"""

    code: str
    name: str
    announcements: list[Announcement]
    has_important: bool
    summary: str
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class AnnouncementMonitor:
    """公告监控器"""

    def __init__(
        self,
        pusher: SignalPusher | None = None,
        cache_path: Path | None = None,
    ):
        self.pusher = pusher or SignalPusher()
        self.cache_path = cache_path or config.cache_path
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self.announcement_cache_file = self.cache_path / "announcements.json"

    def fetch_announcements(self, code: str) -> list[Announcement]:
        """获取股票公告"""
        announcements: list[Announcement] = []

        try:
            import akshare as ak

            with self._disable_proxy():
                df = ak.stock_notice_report(symbol=code)

                if df is not None and not df.empty:
                    for _, row in df.head(10).iterrows():
                        ann = self._parse_announcement(code, row)
                        if ann:
                            announcements.append(ann)

        except ImportError:
            pass
        except (ValueError, KeyError, ConnectionError) as e:
            logger.debug(f"忽略异常: {e}")

        return announcements

    def _parse_announcement(self, code: str, row: Any) -> Announcement | None:
        """解析公告"""
        try:
            title = str(row.get("title", ""))
            content = str(row.get("content", ""))
            publish_date = str(row.get("publish_date", ""))

            ann_type = self._classify_announcement(title, content)
            impact = self._assess_impact(title, content, ann_type)

            return Announcement(
                code=code,
                name="",
                title=title,
                content=content[:500],
                ann_type=ann_type,
                impact=impact,
                publish_date=publish_date,
                action_required=impact in [ImpactLevel.POSITIVE_HIGH, ImpactLevel.NEGATIVE_HIGH],
                action_suggestion=self._get_action_suggestion(impact, ann_type),
            )
        except (ValueError, KeyError, TypeError) as e:
            logger.debug(f"忽略异常: {e}")
            return None

    def _classify_announcement(self, title: str, content: str) -> AnnouncementType:
        """分类公告类型"""
        title.lower()

        if any(k in title for k in ["业绩", "盈利", "亏损", "营收"]):
            return AnnouncementType.EARNINGS
        elif any(k in title for k in ["分红", "派息", "送股"]):
            return AnnouncementType.DIVIDEND
        elif any(k in title for k in ["股东", "增持", "减持"]):
            return AnnouncementType.SHAREHOLDER
        elif any(k in title for k in ["停牌", "复牌"]):
            return AnnouncementType.SUSPENSION
        elif any(k in title for k in ["重组", "并购", "收购"]):
            return AnnouncementType.RESTRUCTURING
        else:
            return AnnouncementType.OTHER

    def _assess_impact(self, title: str, content: str, ann_type: AnnouncementType) -> ImpactLevel:
        """评估影响程度"""
        positive_keywords = ["增长", "盈利", "增持", "分红", "利好", "突破", "创新高"]
        negative_keywords = ["亏损", "减持", "下降", "风险", "诉讼", "处罚", "利空"]

        positive_count = sum(1 for k in positive_keywords if k in title + content)
        negative_count = sum(1 for k in negative_keywords if k in title + content)

        if ann_type == AnnouncementType.EARNINGS:
            if positive_count > negative_count:
                return ImpactLevel.POSITIVE_HIGH if positive_count >= 2 else ImpactLevel.POSITIVE
            elif negative_count > positive_count:
                return ImpactLevel.NEGATIVE_HIGH if negative_count >= 2 else ImpactLevel.NEGATIVE

        if ann_type == AnnouncementType.DIVIDEND:
            return ImpactLevel.POSITIVE

        if ann_type == AnnouncementType.SHAREHOLDER:
            if "增持" in title:
                return ImpactLevel.POSITIVE
            elif "减持" in title:
                return ImpactLevel.NEGATIVE

        if positive_count > negative_count:
            return ImpactLevel.POSITIVE
        elif negative_count > positive_count:
            return ImpactLevel.NEGATIVE

        return ImpactLevel.NEUTRAL

    def _get_action_suggestion(self, impact: ImpactLevel, ann_type: AnnouncementType) -> str:
        """获取行动建议"""
        if impact == ImpactLevel.POSITIVE_HIGH:
            return "重大利好，关注股价表现，考虑是否加仓"
        elif impact == ImpactLevel.POSITIVE:
            return "利好消息，持续关注"
        elif impact == ImpactLevel.NEGATIVE_HIGH:
            return "重大利空，评估风险，考虑止损"
        elif impact == ImpactLevel.NEGATIVE:
            return "利空消息，注意风险"
        else:
            return "中性消息，无需特别操作"

    def check_holdings(self, holdings: list[str]) -> list[AnnouncementAlert]:
        """检查持仓公告"""
        alerts: list[AnnouncementAlert] = []

        for code in holdings:
            announcements = self.fetch_announcements(code)

            if announcements:
                important = [a for a in announcements if a.action_required]
                summary = f"发现 {len(announcements)} 条公告"
                if important:
                    summary += f"，其中 {len(important)} 条需要关注"

                alerts.append(
                    AnnouncementAlert(
                        code=code,
                        name="",
                        announcements=announcements,
                        has_important=len(important) > 0,
                        summary=summary,
                    )
                )

                for ann in important:
                    self._push_announcement(code, ann)

        return alerts

    def _push_announcement(self, code: str, ann: Announcement) -> None:
        """推送公告提醒"""
        signal = Signal(
            code=code,
            name=ann.name,
            signal_type=SignalType.NEWS_ALERT,
            price=0.0,
            change_percent=0.0,
            confidence=1.0,
            reason=ann.title,
            suggestion=ann.action_suggestion,
            priority=Priority.HIGH if ann.action_required else Priority.MEDIUM,
        )

        self.pusher.push(signal)

    def _disable_proxy(self):
        """禁用代理"""
        import os
        from contextlib import contextmanager

        @contextmanager
        def _proxy_context():
            proxy_vars = ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]
            original = {}
            for var in proxy_vars:
                if var in os.environ:
                    original[var] = os.environ[var]
                    del os.environ[var]
            try:
                yield
            finally:
                for var, val in original.items():
                    os.environ[var] = val

        return _proxy_context()


announcement_monitor = AnnouncementMonitor()
