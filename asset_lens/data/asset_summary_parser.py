"""
资产汇总数据解析器
解析备份-表格 1.csv 文件
"""

import csv
from decimal import Decimal
from pathlib import Path

from ..data.models import AssetSummary
from .parser_utils import parse_date, parse_decimal


class AssetSummaryParser:
    """资产汇总数据解析器"""

    @classmethod
    def parse_row(cls, row: dict) -> AssetSummary | None:
        """解析单行数据"""
        try:
            summary_date = parse_date(row.get("日期", ""))
            if not summary_date:
                return None

            # 使用动态配置解析平台金额
            platform_amounts = {}
            from asset_lens.config import config as app_config
            from asset_lens.core.platform_loader import PlatformLoader

            # 确保加载了平台配置（使用正确的数据模式）
            PlatformLoader.reset()
            PlatformLoader.load(data_mode=app_config.data_mode)

            for platform in PlatformLoader.get_all_platforms():
                amount = parse_decimal(row.get(platform.name, ""))
                if amount:
                    platform_amounts[platform.id] = amount

            return AssetSummary(
                summary_date=summary_date,
                platform_amounts=platform_amounts,
                credit_card_amount=parse_decimal(row.get("信用卡", "")) or Decimal("0"),
                jingdong_white_amount=parse_decimal(row.get("京东白条", "")) or Decimal("0"),
                douyin_monthly_amount=parse_decimal(row.get("抖音月付", "")) or Decimal("0"),
                duoduo_later_amount=parse_decimal(row.get("多多后付", "")) or Decimal("0"),
                total_amount=parse_decimal(row.get("总金额", "")) or Decimal("0"),
                usd_rate=parse_decimal(row.get("美元汇率", "")) or Decimal("7.1242"),
                hkd_rate=parse_decimal(row.get("港元汇率", "")) or Decimal("0.9157"),
                gold_amount=parse_decimal(row.get("黄金", "")) or Decimal("0"),
                exchange_usd_amount=parse_decimal(row.get("兑换美元", "")) or Decimal("0"),
                exchange_hkd_amount=parse_decimal(row.get("兑换港元", "")) or Decimal("0"),
                exchange_gold_amount=parse_decimal(row.get("兑换黄金", "")) or Decimal("0"),
                shanghai_index=parse_decimal(row.get("上证指数", "")) or Decimal("0"),
                csi300_index=parse_decimal(row.get("沪深300", "")) or Decimal("0"),
                csi500_index=parse_decimal(row.get("中证500", "")) or Decimal("0"),
                nasdaq100_index=parse_decimal(row.get("纳指100", "")) or Decimal("0"),
                sp500_index=parse_decimal(row.get("标普500", "")) or Decimal("0"),
                vix_index=parse_decimal(row.get("恐慌VXX", "")) or Decimal("0"),
                us_treasury_rate=parse_decimal(row.get("美联基利率", "")) or Decimal("0"),
                property_value=parse_decimal(row.get("房产总价", "")) or Decimal("0"),
                return_rate=parse_decimal(row.get("收益率", "")) or Decimal("0"),
            )
        except Exception as e:
            print(f"解析资产汇总行数据时出错: {e}, 行数据: {row}")
            return None

    @classmethod
    def parse_csv_file(cls, csv_path: Path) -> list[AssetSummary]:
        """
        解析资产汇总 CSV 文件
        Args:
            csv_path: CSV 文件路径
        Returns:
            资产汇总记录列表
        """
        if not csv_path.exists():
            raise FileNotFoundError(f"资产汇总 CSV 文件不存在: {csv_path}")

        summaries = []

        try:
            with open(csv_path, encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)

                for row_num, row in enumerate(reader, start=2):
                    summary = cls.parse_row(row)
                    if summary:
                        summaries.append(summary)
                    else:
                        print(f"警告: 第 {row_num} 行资产汇总数据解析失败")

        except Exception as e:
            raise Exception(f"读取资产汇总 CSV 文件失败: {e}") from e

        return summaries
