#!/usr/bin/env python3
"""
Demo 模式数据生成脚本
生成模拟投资组合数据到 CSV 文件，供 Demo 模式使用

使用方法:
    python scripts/seed_demo.py
"""

import csv
import random
from pathlib import Path


# 模拟投资产品数据（¥10万总资产，虚构产品名）
DEMO_PRODUCTS = [
    {"类型": "A股", "名称": "Demo中国成长", "风险": "高", "初始金额": 20000, "收益率": 12.5, "年化收益": 12.5},
    {"类型": "A股", "名称": "Demo科技先锋", "风险": "高", "初始金额": 12000, "收益率": -5.2, "年化收益": -5.2},
    {"类型": "美股", "名称": "Demo全球科技指数", "风险": "高", "初始金额": 10000, "收益率": 18.7, "年化收益": 18.7},
    {"类型": "基金", "名称": "Demo稳健成长混合", "风险": "中", "初始金额": 15000, "收益率": 9.1, "年化收益": 9.1},
    {"类型": "基金", "名称": "Demo蓝筹精选混合", "风险": "中高", "初始金额": 8000, "收益率": -2.8, "年化收益": -2.8},
    {"类型": "债券", "名称": "Demo国债A", "风险": "低", "初始金额": 10000, "收益率": 3.8, "年化收益": 3.8},
    {"类型": "债券", "名称": "Demo信用债A", "风险": "中低", "初始金额": 8000, "收益率": 4.2, "年化收益": 4.2},
    {"类型": "现金", "名称": "Demo货币基金", "风险": "低", "初始金额": 12000, "收益率": 1.8, "年化收益": 1.8},
    {"类型": "黄金", "名称": "Demo黄金ETF联接", "风险": "中", "初始金额": 3000, "收益率": 22.1, "年化收益": 22.1},
    {"类型": "ETF", "名称": "Demo中证500先锋", "风险": "高", "初始金额": 2000, "收益率": 10.2, "年化收益": 10.2},
]


def generate_demo_csv(output_dir: Path | None = None) -> Path:
    """
    生成模拟投资产品 CSV 文件

    CSV 格式与 CSVParser.COLUMN_MAPPING 兼容：
    - 平台A: wechat_amount（用于计算 current_amount）
    - 初始金额: initial_amount
    - 收益金额: profit_amount
    - 收益率: return_rate
    - 年化收益: annual_return

    Args:
        output_dir: 输出目录，默认为 data/sample_data

    Returns:
        生成的 CSV 文件路径
    """
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "data" / "sample_data"

    output_dir.mkdir(parents=True, exist_ok=True)

    # 生成投资产品.csv（CSVParser 优先匹配此文件名）
    csv_path = output_dir / "投资产品.csv"

    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        # 写入表头（与 CSVParser.COLUMN_MAPPING 兼容）
        writer.writerow([
            "", "类型", "名称", "风险", "平台A",
            "初始金额", "收益金额", "收益率", "年化收益", "投资天数",
        ])

        for i, product in enumerate(DEMO_PRODUCTS):
            initial = product["初始金额"]
            return_rate = product["收益率"]
            annual_return = product["年化收益"]
            profit = round(initial * return_rate / 100, 2)
            current = round(initial + profit, 2)
            # 模拟投资天数（60-365天）
            investment_days = random.randint(60, 365)

            writer.writerow([
                i,
                product["类型"],
                product["名称"],
                product["风险"],
                current,  # 平台A = 当前金额（这样 current_amount = 平台A）
                initial,  # 初始金额
                profit,   # 收益金额
                return_rate,  # 收益率
                annual_return,  # 年化收益
                investment_days,  # 投资天数
            ])

    total_initial = sum(p["初始金额"] for p in DEMO_PRODUCTS)
    print(f"✅ 已生成模拟投资产品数据: {csv_path}")
    print(f"   共 {len(DEMO_PRODUCTS)} 个投资产品，总初始金额: ¥{total_initial:,.0f}")

    # 同时生成资产汇总 CSV
    _generate_asset_summary(output_dir, total_initial)

    return csv_path


def _generate_asset_summary(output_dir: Path, total_initial: float) -> Path:
    """生成模拟资产汇总 CSV"""
    csv_path = output_dir / "资产汇总.csv"

    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["日期", "平台A", "平台B", "券商A", "总金额", "美元汇率", "港元汇率"])

        # 生成最近 4 周的模拟数据
        base_total = total_initial
        for week in range(4):
            total = round(base_total * (1 + random.uniform(-0.02, 0.03) * (week + 1) / 4), 0)
            platform_a = round(total * 0.35, 0)
            platform_b = round(total * 0.25, 0)
            broker_a = round(total * 0.15, 0)
            usd_rate = round(7.10 + random.uniform(-0.1, 0.1), 2)
            hkd_rate = round(0.90 + random.uniform(-0.02, 0.02), 2)

            # 模拟日期（从 2025-05-17 开始，每周）
            month = 5
            day = 17 + week * 7
            if day > 31:
                month = 6
                day -= 31
            date_str = f"2025.{month:02d}.{day:02d}"

            writer.writerow([date_str, platform_a, platform_b, broker_a, total, usd_rate, hkd_rate])

    print(f"✅ 已生成模拟资产汇总数据: {csv_path}")
    return csv_path


if __name__ == "__main__":
    generate_demo_csv()
