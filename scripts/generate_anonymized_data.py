"""
生成脱敏的投资数据表
只保留占比，不显示具体金额
增加基金代码、股票代码、ETF代码等
"""

import logging
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)

from asset_lens.data.csv_parser import CSVParser
from asset_lens.data.fund_fetcher import auto_match_fund_codes


def extract_code_from_name(name):
    """从名称中提取代码"""
    # 匹配6位数字代码
    match = re.search(r'\b(\d{6})\b', name)
    if match:
        return match.group(1)
    return None


def generate_anonymized_portfolio():
    """生成脱敏的投资组合数据"""

    # 读取最新的投资数据
    real_data_path = Path("data/real")
    latest_dir = sorted(real_data_path.glob("money_csv_*"))[-1]
    csv_file = latest_dir / "投资产品-表格 1.csv"

    logger.info("读取数据: %s", csv_file)

    # 读取 CSV
    df = pd.read_csv(csv_file)

    # 获取汇率（从第一行获取）
    usd_rate = df["美元汇率"].iloc[0] if "美元汇率" in df.columns else 7.0
    hkd_rate = df["港元汇率"].iloc[0] if "港元汇率" in df.columns else 0.9
    logger.info("美元汇率: %s, 港元汇率: %s", usd_rate, hkd_rate)

    # 获取金额列（各平台）
    platform_columns = ["微信", "中金", "支付宝", "富途", "招商", "港招", "交通", "浦发", "建设", "中信", "民生", "工商", "中银"]

    # 计算每个产品的总金额（需要考虑汇率转换）
    def calc_amount(row):
        ptype = row["类型"]
        amount = row[platform_columns].sum(skipna=True)

        # 美元产品转换为人民币
        if ptype in ["美股（美元）", "美元基金（美元）"]:
            amount = amount * usd_rate
        # 港元产品转换为人民币
        elif ptype in ["股息基金（港元）", "现金（港元）"]:
            amount = amount * hkd_rate

        return amount

    df["总金额"] = df.apply(calc_amount, axis=1)

    # 计算总投资金额
    total_amount = df["总金额"].sum()

    # 计算占比
    df["占比"] = (df["总金额"] / total_amount * 100).round(2)

    # 获取基金代码
    logger.info("正在匹配基金代码...")
    try:
        products = CSVParser.load_data()
        fund_products = [p.name for p in products if p.investment_type.value == "基金"]
        logger.info("找到 %d 个基金产品", len(fund_products))

        fund_codes_map = auto_match_fund_codes(fund_products)
        logger.info("匹配到 %d 个基金代码", len(fund_codes_map))
    except Exception as e:
        logger.error("匹配基金代码失败: %s", e)
        fund_codes_map = {}

    # 创建名称到代码的映射
    name_to_code = {name: code for name, code in fund_codes_map.items() if code}

    # 添加代码列
    def get_code(row):
        name = row["名称"]
        ptype = row["类型"]

        # 基金类型 - 使用自动匹配的代码
        if ptype == "基金":
            return name_to_code.get(name, "")

        # ETF类型 - 从名称中提取代码
        elif ptype == "ETF":
            code = extract_code_from_name(name)
            if code:
                return code
            # 常见ETF代码映射
            etf_map = {
                "沪深300ETF中金": "510300",
                "中证500ETF嘉实": "510500",
                "纳指100ETF": "513100",
                "能源指数ETF": "513030",
            }
            for key, val in etf_map.items():
                if key in name:
                    return val
            return ""

        # 债券类型 - 从名称中提取代码
        elif ptype == "债券":
            code = extract_code_from_name(name)
            if code:
                return code
            # 常见债券基金代码映射
            bond_map = {
                "广发中债7-10年国开债指数A": "003376",
                "南方中债7-10年期国开行债券指数A": "006227",
                "季季享-招商稳乐中短债90天持有期C": "013552",
                "景顺长城景泰纯利债券型证券投资基金C": "006782",
                "兴证全球恒盛90天持有债券A": "011526",
                "华夏鼎泓债券型证券投资基金": "010468",
                "景顺长城90天持有期短债债券C": "015376",
                "工银双玺6个月持有期债券C": "010688",
                "富国裕利债券C": "006698",
                "博时中债7-10年政策性金融债指数A": "006972",
                "嘉实稳宁纯债债券C": "009908",
                "博时信用债纯债债券C": "001662",
                "工银四季收益债券C": "164808",
                "工银瑞信双利债券B": "485011",
                "易方达岁丰添利债券A": "161116",
                "易方达增强回报债券A": "110017",
                "富国天利增长债券C": "010711",
                "嘉实稳祥纯债债券C": "008318",
                "工银产业债券A": "000045",
                "天天盈1号": "",
                "天天盈2号": "",
            }
            for key, val in bond_map.items():
                if key in name:
                    return val
            return ""

        # 美股类型 - 常见美股代码
        elif ptype == "美股（美元）":
            us_stock_map = {
                "可口可乐": "KO",
                "纳指100ETF": "QQQ",
                "能源指数ETF": "XLE",
            }
            for key, val in us_stock_map.items():
                if key in name:
                    return val
            return ""

        # 定投基金 - 从名称中提取代码
        elif ptype == "定投基金":
            code = extract_code_from_name(name)
            if code:
                return code
            # 常见定投基金代码映射
            fund_map = {
                "易方达亚洲精选股票（QDII）": "118001",
                "国联安沪深300指数增强A": "020220",
            }
            for key, val in fund_map.items():
                if key in name:
                    return val
            return ""

        # 个人养老金 - 从名称中提取代码
        elif ptype == "个人养老金":
            pension_map = {
                "兴全安泰积极养老五年持有（FOF）Y": "017559",
                "易方达中证红利ETF联接发起式Y": "021219",
                "广发创业板ETF联接Y": "021320",
            }
            for key, val in pension_map.items():
                if key in name:
                    return val
            return ""

        # 股息基金（港元）
        elif ptype == "股息基金（港元）":
            hk_map = {
                "富达基金-环球股息优势基金": "FIDG",
            }
            for key, val in hk_map.items():
                if key in name:
                    return val
            return ""

        # 美元基金（美元）
        elif ptype == "美元基金（美元）":
            usd_map = {
                "高腾微金美元货币基金": "GSUSMM",
            }
            for key, val in usd_map.items():
                if key in name:
                    return val
            return ""

        return ""

    df["代码"] = df.apply(get_code, axis=1)

    # 创建脱敏数据表
    anonymized_df = pd.DataFrame()
    anonymized_df["类型"] = df["类型"]
    anonymized_df["名称"] = df["名称"]
    anonymized_df["代码"] = df["代码"]
    anonymized_df["风险"] = df["风险"]
    anonymized_df["占比(%)"] = df["占比"]

    # 只保留占比 > 0 的产品
    anonymized_df = anonymized_df[anonymized_df["占比(%)"] > 0]

    # 计算没有代码的产品总占比（在筛选之前）
    other_percent = anonymized_df[anonymized_df["代码"] == ""]["占比(%)"].sum()

    # 只保留有代码的产品
    anonymized_df = anonymized_df[anonymized_df["代码"] != ""]

    # 合并相同代码的产品（同一产品在不同平台持有）
    # 按代码分组，合并占比，保留第一条的类型、名称、风险
    agg_dict = {
        "类型": "first",
        "名称": "first",
        "风险": "first",
        "占比(%)": "sum"
    }
    anonymized_df = anonymized_df.groupby("代码", as_index=False).agg(agg_dict)

    # 重新排列列顺序
    anonymized_df = anonymized_df[["类型", "名称", "代码", "风险", "占比(%)"]]

    # 按占比倒序排序
    anonymized_df = anonymized_df.sort_values("占比(%)", ascending=False)

    # 重置索引
    anonymized_df = anonymized_df.reset_index(drop=True)

    # 添加"其他"行（没有代码的产品总占比）
    if other_percent > 0:
        other_row = pd.DataFrame({
            "类型": ["其他"],
            "名称": ["其他（理财/国债/现金等）"],
            "代码": ["-"],
            "风险": ["-"],
            "占比(%)": [round(other_percent, 2)]
        })
        anonymized_df = pd.concat([anonymized_df, other_row], ignore_index=True)

    # 保存到 sample_data 目录
    output_path = Path("data/sample_data")
    output_path.mkdir(parents=True, exist_ok=True)
    output_file = output_path / "投资产品-脱敏.csv"

    anonymized_df.to_csv(output_file, index=True, encoding="utf-8-sig")

    logger.info("脱敏数据已保存到: %s", output_file)
    logger.info("投资组合概览:")
    logger.info("  产品数量: %d", len(anonymized_df))
    logger.info("  总占比: %.2f%%", anonymized_df['占比(%)'].sum())

    # 统计有代码的产品
    has_code = (anonymized_df["代码"] != "").sum()
    logger.info("  有代码的产品: %d", has_code)

    # 按类型统计代码覆盖率
    logger.info("各类型代码覆盖率:")
    for ptype in anonymized_df["类型"].unique():
        if pd.isna(ptype):
            continue
        type_df = anonymized_df[anonymized_df["类型"] == ptype]
        total = len(type_df)
        with_code = (type_df["代码"] != "").sum()
        coverage = (with_code / total * 100) if total > 0 else 0
        logger.info("  %s: %d/%d (%.0f%%)", ptype, with_code, total, coverage)

    logger.info("投资组合明细:")
    logger.info(anonymized_df.to_string())

    # 按类型汇总
    logger.info("按类型汇总:")
    type_summary = anonymized_df.groupby("类型")["占比(%)"].sum().sort_values(ascending=False)
    for type_name, percent in type_summary.items():
        logger.info("  %s: %.2f%%", type_name, percent)

    # 显示所有有代码的产品
    logger.info("所有有代码的产品:")
    for _, row in anonymized_df.iterrows():
        if row["代码"]:
            logger.info("  %s: %s -> %s", row['类型'], row['名称'], row['代码'])

    return anonymized_df


if __name__ == "__main__":
    generate_anonymized_portfolio()
