"""
Tests for Announcement Monitor.
公告提醒模块测试
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from asset_lens.analysis.announcement_monitor import (
    AnnouncementMonitor,
    AnnouncementType,
    ImpactLevel,
    Announcement,
    AnnouncementAlert,
    announcement_monitor,
)


class TestAnnouncementType:
    """测试公告类型枚举"""

    def test_announcement_types(self):
        """测试所有公告类型"""
        assert AnnouncementType.EARNINGS.value == "earnings"
        assert AnnouncementType.DIVIDEND.value == "dividend"
        assert AnnouncementType.SHAREHOLDER.value == "shareholder"
        assert AnnouncementType.MAJOR_EVENT.value == "major_event"
        assert AnnouncementType.SUSPENSION.value == "suspension"


class TestImpactLevel:
    """测试影响程度枚举"""

    def test_impact_levels(self):
        """测试所有影响程度"""
        assert ImpactLevel.POSITIVE_HIGH.value == "positive_high"
        assert ImpactLevel.POSITIVE.value == "positive"
        assert ImpactLevel.NEUTRAL.value == "neutral"
        assert ImpactLevel.NEGATIVE.value == "negative"
        assert ImpactLevel.NEGATIVE_HIGH.value == "negative_high"


class TestAnnouncement:
    """测试公告"""

    def test_create_announcement(self):
        """测试创建公告"""
        ann = Announcement(
            code="sh600519",
            name="贵州茅台",
            title="2024年年度业绩预告",
            content="预计净利润同比增长15%",
            ann_type=AnnouncementType.EARNINGS,
            impact=ImpactLevel.POSITIVE,
            publish_date="2024-01-15",
        )

        assert ann.code == "sh600519"
        assert ann.ann_type == AnnouncementType.EARNINGS
        assert ann.impact == ImpactLevel.POSITIVE
        assert ann.action_required is False

    def test_announcement_action_required(self):
        """测试需要行动的公告"""
        ann = Announcement(
            code="sh600519",
            name="贵州茅台",
            title="重大事项公告",
            content="公司涉及重大诉讼",
            ann_type=AnnouncementType.MAJOR_EVENT,
            impact=ImpactLevel.NEGATIVE_HIGH,
            publish_date="2024-01-15",
            action_required=True,
        )

        assert ann.action_required is True


class TestAnnouncementMonitor:
    """测试公告监控器"""

    def test_init(self, tmp_path):
        """测试初始化"""
        monitor = AnnouncementMonitor(cache_path=tmp_path)
        assert monitor.cache_path == tmp_path

    def test_classify_announcement_earnings(self, tmp_path):
        """测试分类业绩公告"""
        monitor = AnnouncementMonitor(cache_path=tmp_path)

        ann_type = monitor._classify_announcement("2024年业绩预告", "")
        assert ann_type == AnnouncementType.EARNINGS

        ann_type = monitor._classify_announcement("盈利预告", "")
        assert ann_type == AnnouncementType.EARNINGS

    def test_classify_announcement_dividend(self, tmp_path):
        """测试分类分红公告"""
        monitor = AnnouncementMonitor(cache_path=tmp_path)

        ann_type = monitor._classify_announcement("2024年分红派息公告", "")
        assert ann_type == AnnouncementType.DIVIDEND

    def test_classify_announcement_shareholder(self, tmp_path):
        """测试分类股东公告"""
        monitor = AnnouncementMonitor(cache_path=tmp_path)

        ann_type = monitor._classify_announcement("股东增持计划", "")
        assert ann_type == AnnouncementType.SHAREHOLDER

    def test_classify_announcement_suspension(self, tmp_path):
        """测试分类停复牌公告"""
        monitor = AnnouncementMonitor(cache_path=tmp_path)

        ann_type = monitor._classify_announcement("停牌公告", "")
        assert ann_type == AnnouncementType.SUSPENSION

    def test_classify_announcement_restructuring(self, tmp_path):
        """测试分类重组公告"""
        monitor = AnnouncementMonitor(cache_path=tmp_path)

        ann_type = monitor._classify_announcement("重大资产重组", "")
        assert ann_type == AnnouncementType.RESTRUCTURING

    def test_assess_impact_positive(self, tmp_path):
        """测试评估正面影响"""
        monitor = AnnouncementMonitor(cache_path=tmp_path)

        impact = monitor._assess_impact(
            "业绩大幅增长",
            "净利润同比增长50%",
            AnnouncementType.EARNINGS,
        )
        assert impact in [ImpactLevel.POSITIVE, ImpactLevel.POSITIVE_HIGH]

    def test_assess_impact_negative(self, tmp_path):
        """测试评估负面影响"""
        monitor = AnnouncementMonitor(cache_path=tmp_path)

        impact = monitor._assess_impact(
            "业绩亏损公告",
            "公司出现重大亏损",
            AnnouncementType.EARNINGS,
        )
        assert impact in [ImpactLevel.NEGATIVE, ImpactLevel.NEGATIVE_HIGH]

    def test_assess_impact_dividend(self, tmp_path):
        """测试评估分红影响"""
        monitor = AnnouncementMonitor(cache_path=tmp_path)

        impact = monitor._assess_impact(
            "分红派息公告",
            "",
            AnnouncementType.DIVIDEND,
        )
        assert impact == ImpactLevel.POSITIVE

    def test_assess_impact_shareholder_increase(self, tmp_path):
        """测试评估股东增持影响"""
        monitor = AnnouncementMonitor(cache_path=tmp_path)

        impact = monitor._assess_impact(
            "股东增持计划",
            "",
            AnnouncementType.SHAREHOLDER,
        )
        assert impact == ImpactLevel.POSITIVE

    def test_assess_impact_shareholder_decrease(self, tmp_path):
        """测试评估股东减持影响"""
        monitor = AnnouncementMonitor(cache_path=tmp_path)

        impact = monitor._assess_impact(
            "股东减持公告",
            "",
            AnnouncementType.SHAREHOLDER,
        )
        assert impact == ImpactLevel.NEGATIVE

    def test_get_action_suggestion_positive_high(self, tmp_path):
        """测试获取重大利好建议"""
        monitor = AnnouncementMonitor(cache_path=tmp_path)

        suggestion = monitor._get_action_suggestion(ImpactLevel.POSITIVE_HIGH, AnnouncementType.EARNINGS)
        assert "重大利好" in suggestion

    def test_get_action_suggestion_negative_high(self, tmp_path):
        """测试获取重大利空建议"""
        monitor = AnnouncementMonitor(cache_path=tmp_path)

        suggestion = monitor._get_action_suggestion(ImpactLevel.NEGATIVE_HIGH, AnnouncementType.EARNINGS)
        assert "重大利空" in suggestion

    def test_get_action_suggestion_neutral(self, tmp_path):
        """测试获取中性建议"""
        monitor = AnnouncementMonitor(cache_path=tmp_path)

        suggestion = monitor._get_action_suggestion(ImpactLevel.NEUTRAL, AnnouncementType.OTHER)
        assert "中性" in suggestion

    def test_check_holdings_empty(self, tmp_path):
        """测试检查空持仓"""
        monitor = AnnouncementMonitor(cache_path=tmp_path)

        alerts = monitor.check_holdings([])
        assert alerts == []

    @patch("asset_lens.analysis.announcement_monitor.AnnouncementMonitor.fetch_announcements")
    def test_check_holdings_with_data(self, mock_fetch, tmp_path):
        """测试检查持仓公告"""
        monitor = AnnouncementMonitor(cache_path=tmp_path)

        mock_fetch.return_value = [
            Announcement(
                code="sh600519",
                name="贵州茅台",
                title="业绩预告",
                content="净利润增长",
                ann_type=AnnouncementType.EARNINGS,
                impact=ImpactLevel.POSITIVE,
                publish_date="2024-01-15",
            )
        ]

        alerts = monitor.check_holdings(["sh600519"])

        assert len(alerts) == 1
        assert alerts[0].code == "sh600519"


class TestAnnouncementMonitorInstance:
    """测试全局实例"""

    def test_global_instance_exists(self):
        """测试全局实例存在"""
        assert announcement_monitor is not None
        assert isinstance(announcement_monitor, AnnouncementMonitor)
