"""
资产汇总数据解析器
解析备份-表格 1.csv 文件
"""

import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List

from ..data.models import AssetSummary


class AssetSummaryParser:
    """资产汇总数据解析器"""
    
    @staticmethod
    def parse_decimal(value: str) -> Decimal | None:
        """解析 Decimal 值"""
        if not value or value.strip() == "":
            return None
        try:
            cleaned = value.replace(",", "").strip()
            return Decimal(cleaned)
        except:
            return None
    
    @staticmethod
    def parse_date(value: str) -> datetime | None:
        """解析日期值"""
        if not value or value.strip() == "":
            return None
        
        date_formats = [
            "%Y/%m/%d",
            "%Y-%m-%d",
            "%Y/%m/%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y.%m.%d",
            "%Y.%m.%d %H:%M:%S",
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(value.strip(), fmt)
            except ValueError:
                continue
        
        return None
    
    @classmethod
    def parse_row(cls, row: dict) -> AssetSummary | None:
        """解析单行数据"""
        try:
            summary_date = cls.parse_date(row.get("日期", ""))
            if not summary_date:
                return None
            
            return AssetSummary(
                summary_date=summary_date,
                wechat_amount=cls.parse_decimal(row.get("微信", "")),
                zhongjin_amount=cls.parse_decimal(row.get("中金财富", "")),
                alipay_amount=cls.parse_decimal(row.get("支付宝", "")),
                futu_amount=cls.parse_decimal(row.get("富途", "")),
                zhaoshang_amount=cls.parse_decimal(row.get("招商", "")),
                gangzhao_amount=cls.parse_decimal(row.get("港招", "")),
                jiaotong_amount=cls.parse_decimal(row.get("交通", "")),
                pufa_amount=cls.parse_decimal(row.get("浦发", "")),
                jianshe_amount=cls.parse_decimal(row.get("建设", "")),
                zhongxin_amount=cls.parse_decimal(row.get("中信", "")),
                minsheng_amount=cls.parse_decimal(row.get("民生", "")),
                gongshang_amount=cls.parse_decimal(row.get("工商", "")),
                zhongyin_amount=cls.parse_decimal(row.get("中银", "")),
                credit_card_amount=cls.parse_decimal(row.get("信用卡", "")),
                jingdong_white_amount=cls.parse_decimal(row.get("京东白条", "")),
                douyin_monthly_amount=cls.parse_decimal(row.get("抖音月付", "")),
                duoduo_later_amount=cls.parse_decimal(row.get("多多后付", "")),
                total_amount=cls.parse_decimal(row.get("总金额", "")),
                usd_rate=cls.parse_decimal(row.get("美元汇率", "")),
                hkd_rate=cls.parse_decimal(row.get("港元汇率", "")),
                gold_amount=cls.parse_decimal(row.get("黄金", "")),
                exchange_usd_amount=cls.parse_decimal(row.get("兑换美元", "")),
                exchange_hkd_amount=cls.parse_decimal(row.get("兑换港元", "")),
                exchange_gold_amount=cls.parse_decimal(row.get("兑换黄金", "")),
                shanghai_index=cls.parse_decimal(row.get("上证指数", "")),
                csi300_index=cls.parse_decimal(row.get("沪深300", "")),
                csi500_index=cls.parse_decimal(row.get("中证500", "")),
                nasdaq100_index=cls.parse_decimal(row.get("纳指100", "")),
                sp500_index=cls.parse_decimal(row.get("标普500", "")),
                vix_index=cls.parse_decimal(row.get("恐慌VXX", "")),
                us_treasury_rate=cls.parse_decimal(row.get("美联基利率", "")),
                property_value=cls.parse_decimal(row.get("房产总价", "")),
                return_rate=cls.parse_decimal(row.get("收益率", "")),
            )
        except Exception as e:
            print(f"解析资产汇总行数据时出错: {e}, 行数据: {row}")
            return None
    
    @classmethod
    def parse_csv_file(cls, csv_path: Path) -> List[AssetSummary]:
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
            with open(csv_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                
                for row_num, row in enumerate(reader, start=2):
                    summary = cls.parse_row(row)
                    if summary:
                        summaries.append(summary)
                    else:
                        print(f"警告: 第 {row_num} 行资产汇总数据解析失败")
        
        except Exception as e:
            raise Exception(f"读取资产汇总 CSV 文件失败: {e}")
        
        return summaries
