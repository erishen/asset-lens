import logging

logger = logging.getLogger(__name__)


def _get_fund_type_threshold(fund) -> dict:
    inv_type = fund.investment_type.value if fund.investment_type else ""
    name = fund.name.lower() if fund.name else ""

    if "债券" in inv_type or "债" in name:
        return {"excellent": 6, "good": 4, "normal": 2, "type": "债券型"}
    elif "货币" in inv_type or "货币" in name or "钱宝" in name or "朝朝宝" in name:
        return {"excellent": 3, "good": 2, "normal": 1.5, "type": "货币型"}
    elif "qdii" in inv_type.lower() or "qdii" in name or "纳斯达克" in name or "标普" in name:
        return {"excellent": 15, "good": 10, "normal": 5, "type": "QDII"}
    elif "黄金" in name or "gold" in name:
        return {"excellent": 12, "good": 8, "normal": 4, "type": "黄金"}
    elif "指数" in inv_type or "沪深300" in name or "中证500" in name or "增强" in name:
        return {"excellent": 12, "good": 8, "normal": 4, "type": "指数型"}
    elif "混合" in inv_type or "混合" in name:
        return {"excellent": 15, "good": 10, "normal": 5, "type": "混合型"}
    elif "股票" in inv_type or "股票" in name:
        return {"excellent": 18, "good": 12, "normal": 6, "type": "股票型"}
    else:
        return {"excellent": 15, "good": 10, "normal": 5, "type": "其他"}


def _evaluate_fund(fund, north_flow_trend: str = "neutral") -> dict:
    from asset_lens.cli_modules.cli.report import _get_cny_amount

    annual_return = float(fund.annual_return or 0)
    threshold = _get_fund_type_threshold(fund)

    score = 0
    reasons = []

    if annual_return >= threshold["excellent"]:
        score += 40
        reasons.append(f"年化{annual_return:.1f}%超{threshold['type']}优秀线{threshold['excellent']}%")
    elif annual_return >= threshold["good"]:
        score += 25
        reasons.append(f"年化{annual_return:.1f}%达{threshold['type']}良好线{threshold['good']}%")
    elif annual_return >= threshold["normal"]:
        score += 10
        reasons.append(f"年化{annual_return:.1f}%达{threshold['type']}正常线{threshold['normal']}%")
    elif annual_return > 0:
        score += 5
        reasons.append(f"年化{annual_return:.1f}%偏低")
    else:
        score -= 20
        reasons.append(f"年化{annual_return:.1f}%亏损")

    amount = _get_cny_amount(fund)
    if amount < 10000:
        score += 5
        reasons.append("小仓位可加仓")
    elif amount < 30000:
        score += 0
    else:
        score -= 5
        reasons.append("仓位较重")

    if north_flow_trend == "bullish":
        if threshold["type"] in ["股票型", "混合型", "指数型"]:
            score += 10
            reasons.append("北向资金流入利好")
    elif north_flow_trend == "bearish" and threshold["type"] in ["股票型", "混合型", "指数型"]:
        score -= 10
        reasons.append("北向资金流出不利")

    return_rate = float(fund.return_rate or 0)
    if return_rate < -10:
        score -= 20
        reasons.append(f"累计亏损{abs(return_rate):.1f}%")
    elif return_rate < -5:
        score -= 10
        reasons.append(f"累计亏损{abs(return_rate):.1f}%")

    if score >= 50:
        suggestion = "强烈加仓"
        emoji = "🔴🔴"
    elif score >= 30:
        suggestion = "考虑加仓"
        emoji = "🔴"
    elif score >= 10:
        suggestion = "继续持有"
        emoji = "🟡"
    elif score >= 0:
        suggestion = "观察"
        emoji = "🟡"
    elif score >= -20:
        suggestion = "考虑减仓"
        emoji = "🟢"
    else:
        suggestion = "建议赎回"
        emoji = "🟢🟢"

    return {
        "score": score,
        "suggestion": suggestion,
        "emoji": emoji,
        "reasons": reasons,
        "fund_type": threshold["type"],
    }


def _get_fund_category(fund) -> str:
    name = fund.name.lower() if fund.name else ""

    if "沪深300" in name or "300etf" in name:
        return "沪深300"
    elif "中证500" in name or "500etf" in name:
        return "中证500"
    elif "中证1000" in name or "1000etf" in name:
        return "中证1000"
    elif "创业板" in name:
        return "创业板"
    elif "科创50" in name or "科创板" in name:
        return "科创50"
    elif "纳斯达克" in name or "纳指" in name:
        return "纳斯达克"
    elif "标普" in name:
        return "标普500"
    elif "黄金" in name or "gold" in name:
        return "黄金"
    elif "港股" in name or "恒生" in name:
        return "港股"
    elif "债券" in name or "债" in name:
        return "债券"
    elif "军工" in name:
        return "军工"
    elif "医药" in name:
        return "医药"
    elif "消费" in name:
        return "消费"
    elif "新能源" in name:
        return "新能源"
    elif "芯片" in name or "半导体" in name:
        return "芯片"
    elif "油气" in name or "能源" in name:
        return "油气"
    else:
        return "其他"


def _evaluate_fund_with_peers(fund, peer_funds: list, north_flow_trend: str = "neutral") -> dict:
    from asset_lens.cli_modules.cli.report import _get_cny_amount

    annual_return = float(fund.annual_return or 0)
    threshold = _get_fund_type_threshold(fund)
    inv_type = fund.investment_type.value if fund.investment_type else ""

    score = 0
    reasons = []

    is_usd_fund = "美元" in inv_type
    is_money_fund = "货币" in fund.name or "货币" in inv_type or "Money" in fund.name

    if is_money_fund and annual_return == 0:
        annual_return = 3.5
        reasons.append("货币基金约3.5%年化")

    if annual_return >= threshold["excellent"]:
        score += 30
        if not is_money_fund:
            reasons.append(f"年化{annual_return:.1f}%优秀")
    elif annual_return >= threshold["good"]:
        score += 20
        if not is_money_fund:
            reasons.append(f"年化{annual_return:.1f}%良好")
    elif annual_return >= threshold["normal"]:
        score += 10
        if not is_money_fund:
            reasons.append(f"年化{annual_return:.1f}%正常")
    elif annual_return > 0:
        score += 5
    elif annual_return < 0:
        score -= 10
        reasons.append(f"年化{annual_return:.1f}%亏损")

    if peer_funds and len(peer_funds) > 1:
        peer_returns = [float(f.annual_return or 0) for f in peer_funds]
        peer_returns.sort(reverse=True)
        rank = peer_returns.index(annual_return) + 1 if annual_return in peer_returns else len(peer_returns)
        percentile = (1 - (rank - 1) / len(peer_returns)) * 100

        if percentile >= 80:
            score += 20
            reasons.append(f"同类排名前{100 - percentile + 1:.0f}%")
        elif percentile >= 50:
            score += 10
        elif percentile < 30:
            score -= 10
            reasons.append(f"同类排名后{percentile:.0f}%")

    amount = _get_cny_amount(fund)
    if amount < 10000:
        score += 5
    elif amount > 50000:
        score -= 5
        reasons.append("仓位较重")

    if north_flow_trend == "bullish":
        if threshold["type"] in ["股票型", "混合型", "指数型"]:
            score += 10
            reasons.append("北向资金流入利好")
    elif north_flow_trend == "bearish" and threshold["type"] in ["股票型", "混合型", "指数型"]:
        score -= 10
        reasons.append("北向资金流出不利")

    return_rate = float(fund.return_rate or 0)
    if return_rate < -10:
        score -= 15
        reasons.append(f"累计亏损{abs(return_rate):.1f}%")
    elif return_rate < -5:
        score -= 8
        reasons.append(f"累计亏损{abs(return_rate):.1f}%")

    if is_usd_fund:
        reasons.append("美元资产")

    if score >= 45:
        suggestion = "强烈加仓"
        emoji = "🔴🔴"
    elif score >= 25:
        suggestion = "考虑加仓"
        emoji = "🔴"
    elif score >= 10:
        suggestion = "继续持有"
        emoji = "🟡"
    elif score >= 0:
        suggestion = "观察"
        emoji = "🟡"
    elif score >= -15:
        suggestion = "考虑减仓"
        emoji = "🟢"
    else:
        suggestion = "建议赎回"
        emoji = "🟢🟢"

    return {
        "score": score,
        "suggestion": suggestion,
        "emoji": emoji,
        "reasons": reasons,
        "fund_type": threshold["type"],
        "category": _get_fund_category(fund),
    }
