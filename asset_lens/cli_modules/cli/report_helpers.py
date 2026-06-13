import logging
from typing import Any, cast

from .report_fund_evaluation import (
    _evaluate_fund,
    _evaluate_fund_with_peers,
    _get_fund_category,
    _get_fund_type_threshold,
)

logger = logging.getLogger(__name__)


def _train_model_if_needed(model_path, prediction_days: int, max_age_days: int = 7) -> bool:
    from datetime import datetime, timedelta
    from pathlib import Path

    model_path = Path(model_path)

    if model_path.exists():
        file_mtime = datetime.fromtimestamp(model_path.stat().st_mtime)
        age = datetime.now() - file_mtime

        if age > timedelta(days=max_age_days):
            logger.warning(f"模型已过期 (训练于 {age.days} 天前)，正在重新训练...")
        else:
            logger.info(f"模型有效 (训练于 {age.days} 天前)")
            return True
    else:
        logger.warning(f"模型不存在，正在自动训练 (prediction_days={prediction_days})...")

    try:
        import numpy as np
        import pandas as pd

        from asset_lens.data.market_stock_fetcher import MarketStockFetcher
        from asset_lens.ml.trainer import ModelTrainer, TrainingConfig

        fetcher = MarketStockFetcher()
        stocks_data = fetcher.get_cached_market_stocks()

        if not stocks_data:
            logger.warning("无缓存数据，正在自动获取市场股票数据...")
            try:
                stocks_data = fetcher.fetch_all_cn_stocks(max_pages=3)
                if stocks_data:
                    fetcher.save_market_stocks(stocks_data)
                    logger.info(f"已获取 {len(stocks_data)} 只股票数据")
                else:
                    logger.error("获取市场数据失败")
                    return False
            except (ValueError, KeyError, ConnectionError) as fetch_error:
                logger.error(f"获取市场数据失败: {fetch_error}")
                return False

        logger.info(f"加载 {len(stocks_data)} 只股票数据")

        threshold_pct = max(0.02, prediction_days * 0.0025)

        config = TrainingConfig(
            prediction_days=prediction_days,
            positive_threshold=threshold_pct,
            negative_threshold=-threshold_pct,
        )
        trainer = ModelTrainer(model_type="lightgbm", config=config)

        from asset_lens.data.stock_history_fetcher import StockHistoryFetcher

        history_fetcher = StockHistoryFetcher()

        stocks_price_data = {}
        success_count = 0

        for stock in stocks_data[:100]:
            code = stock.get("code", "")
            if not code:
                continue

            try:
                history = history_fetcher.fetch_history(code, days=120)
                if history and history.get("klines"):
                    df = pd.DataFrame(history["klines"])
                    if len(df) >= 60:
                        df["open"] = pd.to_numeric(df["open"], errors="coerce")
                        df["high"] = pd.to_numeric(df["high"], errors="coerce")
                        df["low"] = pd.to_numeric(df["low"], errors="coerce")
                        df["close"] = pd.to_numeric(df["close"], errors="coerce")
                        df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
                        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
                        df = df.dropna()

                        if len(df) >= 60:
                            stocks_price_data[code] = df
                            success_count += 1
            except (ValueError, KeyError, TypeError) as e:
                logger.debug(f"忽略异常: {e}")
                continue

        if success_count < 10:
            logger.warning(f"真实数据不足({success_count}只)，使用模拟数据补充...")
            np.random.seed(42)
            for stock in stocks_data[:200]:
                code = stock.get("code", "")
                current_price = stock.get("current_price", 10)

                if code in stocks_price_data or not code or current_price <= 0:
                    continue

                n_days = 100
                returns = np.random.randn(n_days) * 0.02
                prices = current_price * np.exp(np.cumsum(returns))

                df = pd.DataFrame(
                    {
                        "open": prices * (1 + np.random.randn(n_days) * 0.01),
                        "high": prices * (1 + np.abs(np.random.randn(n_days) * 0.02)),
                        "low": prices * (1 - np.abs(np.random.randn(n_days) * 0.02)),
                        "close": prices,
                        "volume": np.random.randint(100000, 1000000, n_days),
                        "amount": prices * np.random.randint(100000, 1000000, n_days),
                    }
                )

                stocks_price_data[code] = df

        logger.info(f"使用 {len(stocks_price_data)} 只股票数据训练")

        X, y = trainer.prepare_multi_stock_data(stocks_price_data)
        trainer.train(X, y)
        trainer.save_model(model_path)

        logger.info(f"模型训练完成: {model_path}")
        return True
    except (ValueError, KeyError, RuntimeError, OSError) as e:
        logger.error(f"自动训练失败: {e}")
        return False


def _get_ml_predictions() -> dict:
    return _get_ml_predictions_for_model(
        model_path="cache/ml/model.pkl", prediction_days=5, label="短期", bullish_threshold=0.7, bearish_threshold=0.3
    )


def _get_ml_predictions_monthly() -> dict:
    return _get_ml_predictions_for_model(
        model_path="cache/ml/model_monthly.pkl",
        prediction_days=20,
        label="中期",
        bullish_threshold=0.6,
        bearish_threshold=0.4,
    )


def _get_ml_predictions_for_model(
    model_path: str, prediction_days: int, label: str, bullish_threshold: float = 0.7, bearish_threshold: float = 0.3
) -> dict:
    from pathlib import Path

    from asset_lens.data.stock_history_fetcher import StockHistoryFetcher
    from asset_lens.ml.predictor import StockPredictor
    from asset_lens.trading.stock_pool import StockPool

    model_path_obj = Path(model_path)

    if not model_path_obj.exists() and not _train_model_if_needed(model_path_obj, prediction_days=prediction_days):
        return {"bullish": [], "bearish": [], "prediction_days": prediction_days, "label": label}

    try:
        predictor = StockPredictor(model_path=model_path_obj)
    except (ValueError, OSError, RuntimeError) as exc:
        logger.error(f"ML模型加载失败: {exc}")
        return {"bullish": [], "bearish": [], "prediction_days": prediction_days, "label": label}

    pool = StockPool()
    stocks = pool.list_stocks()[:20]
    fetcher = StockHistoryFetcher()

    bullish = []
    bearish = []

    for stock_info in stocks:
        try:
            code = stock_info.get("code", "") if isinstance(stock_info, dict) else stock_info
            name = stock_info.get("name", code) if isinstance(stock_info, dict) else code

            history = fetcher.fetch_history(code, days=120)
            history_data = None
            if history and history.get("klines"):
                history_data = []
                for kline in history["klines"]:
                    history_data.append(
                        {
                            "open": float(kline.get("open", 0)),
                            "high": float(kline.get("high", 0)),
                            "low": float(kline.get("low", 0)),
                            "close": float(kline.get("close", 0)),
                            "volume": float(kline.get("volume", 0)),
                            "amount": float(kline.get("amount", 0)),
                            "amplitude": float(kline.get("amplitude", 0)),
                            "change_amount": float(kline.get("change_amount", 0)),
                            "change_percent": float(kline.get("change_percent", 0)),
                            "turnover_rate": float(kline.get("turnover_rate", 0)),
                        }
                    )

            result = predictor.predict_single(code=code, name=str(name or ""), history_data=history_data)
            if result:
                prob = result.up_prob
                if prob >= bullish_threshold:
                    bullish.append({"code": code, "name": name, "prob": prob * 100})
                elif prob <= bearish_threshold:
                    bearish.append({"code": code, "name": name, "prob": (1 - prob) * 100})
        except (ValueError, KeyError, TypeError) as e:
            logger.debug(f"忽略异常: {e}")
            continue

    bullish.sort(key=lambda x: x["prob"], reverse=True)
    bearish.sort(key=lambda x: x["prob"], reverse=True)

    return {"bullish": bullish, "bearish": bearish, "prediction_days": prediction_days, "label": label}


def _get_north_flow() -> dict:
    from asset_lens.utils.industry_flow import get_north_flow_summary

    return get_north_flow_summary(days=7)


def _check_risks(products: list) -> list:
    from asset_lens.cli_modules.cli.report import _get_cny_amount

    warnings = []

    loss_products = [p for p in products if p.return_rate and float(p.return_rate) < -10]
    if loss_products:
        warnings.append(f"🔴 {len(loss_products)} 只产品亏损超过10%，建议检查止损")

    high_risk_amount = sum(
        _get_cny_amount(p) for p in products if p.risk_level and p.risk_level.value in ["高", "中高"]
    )
    total_amount = sum(_get_cny_amount(p) for p in products)
    if total_amount > 0 and high_risk_amount / total_amount > 0.5:
        warnings.append(f"⚠️ 高风险产品占比 {high_risk_amount / total_amount * 100:.1f}%，建议分散风险")

    for p in products:
        cny_amount = _get_cny_amount(p)
        if cny_amount > 0 and total_amount > 0 and cny_amount / total_amount > 0.2:
            warnings.append(f"⚠️ {p.name} 占比 {cny_amount / total_amount * 100:.1f}%，集中度较高")

    return warnings


def _get_platform_products(products: list) -> dict[str, dict[str, list | float | str]]:
    from asset_lens.cli_modules.cli.report import _get_cny_amount, _get_global_rates
    from asset_lens.config import config
    from asset_lens.core.platform_loader import PlatformLoader

    PlatformLoader.load(data_mode=config.data_mode)
    platforms = PlatformLoader.get_all_platforms(data_mode=config.data_mode)

    platform_products: dict[str, dict[str, Any]] = {}
    for platform in platforms:
        platform_products[platform.name] = {
            "products": [],
            "amount": 0.0,
            "type": platform.type,
        }

    platform_products["其他"] = {
        "products": [],
        "amount": 0.0,
        "type": "other",
    }

    for p in products:
        if p.platform_amounts:
            for platform_id, amount in p.platform_amounts.items():
                platform_info = PlatformLoader.get_platform(platform_id)
                if platform_info:
                    platform_name = platform_info.name
                    if platform_name not in platform_products:
                        platform_products[platform_name] = {
                            "products": [],
                            "amount": 0.0,
                            "type": platform_info.type,
                        }
                    platform_products[platform_name]["products"].append(p)
                    inv_type = p.investment_type.value if p.investment_type else ""
                    global_usd, global_hkd = _get_global_rates()
                    if inv_type in ["美股", "美元基金（美元）"]:
                        usd_rate = float(p.usd_rate) if p.usd_rate else global_usd
                        cny_amount = float(amount) * usd_rate
                    elif inv_type in ["港股", "现金（港元）", "股息基金（港元）"]:
                        hkd_rate = float(p.hkd_rate) if p.hkd_rate else global_hkd
                        cny_amount = float(amount) * hkd_rate
                    else:
                        cny_amount = float(amount)
                    platform_products[platform_name]["amount"] = (
                        float(platform_products[platform_name]["amount"]) + cny_amount
                    )
        else:
            platform_products["其他"]["products"].append(p)
            platform_products["其他"]["amount"] = float(platform_products["其他"]["amount"]) + _get_cny_amount(p)

    return {k: v for k, v in platform_products.items() if float(v["amount"]) > 0}


def _generate_suggestions(products: list, funds: list) -> list:
    from asset_lens.cli_modules.cli.report import _format_amount

    suggestions: list[str] = []

    north_flow = _get_north_flow()
    north_trend = (
        "bullish"
        if north_flow.get("total_flow", 0) > 100
        else ("bearish" if north_flow.get("total_flow", 0) < -100 else "neutral")
    )

    platform_products = _get_platform_products(products)

    all_funds = [
        p for p in products if p.investment_type and p.investment_type.value in ["基金", "定投基金", "ETF", "QDII"]
    ]

    category_funds_global: dict[str, list] = {}
    for f in all_funds:
        category = _get_fund_category(f)
        if category not in category_funds_global:
            category_funds_global[category] = []
        category_funds_global[category].append(f)

    for platform_name, platform_data in sorted(platform_products.items(), key=lambda x: x[1]["amount"], reverse=True):
        products_list = cast(list, platform_data["products"])
        platform_funds = [
            p
            for p in products_list
            if p.investment_type and p.investment_type.value in ["基金", "定投基金", "ETF", "QDII"]
        ]

        if not platform_funds:
            platform_funds = [p for p in products_list if p.investment_type and "基金" in p.investment_type.value]

        if not platform_funds:
            continue

        fund_evaluations = []
        for f in platform_funds:
            category = _get_fund_category(f)
            peers = category_funds_global.get(category, [])
            eval_result = _evaluate_fund_with_peers(f, peers, north_trend)
            eval_result["fund"] = f
            eval_result["category"] = category
            fund_evaluations.append(eval_result)

        fund_evaluations.sort(key=lambda x: x["score"], reverse=True)

        strong_buy = [e for e in fund_evaluations if e["score"] >= 50]
        consider_buy = [e for e in fund_evaluations if 30 <= e["score"] < 50]
        hold_funds = [e for e in fund_evaluations if 10 <= e["score"] < 30]
        watch_funds = [e for e in fund_evaluations if 0 <= e["score"] < 10]
        reduce_funds = [e for e in fund_evaluations if -20 <= e["score"] < 0]
        sell_funds = [e for e in fund_evaluations if e["score"] < -20]

        suggestions.append(f"\n📱 【{platform_name}】 (¥{platform_data['amount']:,.0f}，{len(platform_funds)}只基金)")

        if strong_buy:
            suggestions.append(f"  🔴🔴 强烈加仓 ({len(strong_buy)}只):")
            for e in strong_buy[:4]:
                name = e["fund"].name[:12]
                reasons = e["reasons"][0] if e["reasons"] else ""
                suggestions.append(f"      • {name} (¥{e['fund'].current_amount:,.0f}): {reasons}")
        if consider_buy:
            suggestions.append(f"  🔴 考虑加仓 ({len(consider_buy)}只):")
            for e in consider_buy[:3]:
                name = e["fund"].name[:12]
                reasons = e["reasons"][0] if e["reasons"] else ""
                suggestions.append(f"      • {name} ({_format_amount(e['fund'])}): {reasons}")

        if hold_funds:
            suggestions.append(f"  🟡 继续持有 ({len(hold_funds)}只):")
            for e in hold_funds[:3]:
                name = e["fund"].name[:12]
                suggestions.append(f"      • {name} ({_format_amount(e['fund'])})")

        if watch_funds:
            suggestions.append(f"  ⚪ 需要观察 ({len(watch_funds)}只):")
            for e in watch_funds[:2]:
                name = e["fund"].name[:12]
                suggestions.append(f"      • {name}")

        if reduce_funds:
            suggestions.append(f"  🟢 考虑减仓 ({len(reduce_funds)}只):")
            for e in reduce_funds[:2]:
                name = e["fund"].name[:12]
                reasons = e["reasons"][0] if e["reasons"] else ""
                suggestions.append(f"      • {name}: {reasons}")

        if sell_funds:
            suggestions.append(f"  🟢🟢 建议赎回 ({len(sell_funds)}只):")
            for e in sell_funds[:2]:
                name = e["fund"].name[:12]
                reasons = e["reasons"][0] if e["reasons"] else ""
                suggestions.append(f"      • {name}: {reasons}")

        if not any([strong_buy, consider_buy, hold_funds, watch_funds, reduce_funds, sell_funds]):
            suggestions.append("  ⚪ 暂无建议")

    loss_products = [p for p in products if p.return_rate and float(p.return_rate) < 0]
    if loss_products:
        suggestions.append(f"\n📉 {len(loss_products)} 只产品亏损，建议检查止损位")

    if north_trend == "bullish":
        suggestions.append(f"\n📈 北向资金净流入+{north_flow['total_flow']:.0f}亿，利好权益类资产")
    elif north_trend == "bearish":
        suggestions.append(f"\n📉 北向资金净流出{north_flow['total_flow']:.0f}亿，注意风险")

    suggestions.append("\n📊 各平台资金独立管理，建议保持股债平衡配置")

    return suggestions


def _generate_monthly_suggestions(products: list, type_stats: dict, total_amount: float) -> list:
    suggestions = []

    suggestions.append(f"📅 本月投资组合共 {len(products)} 只产品，总资产 ¥{total_amount:,.0f}")

    sorted_types = sorted(type_stats.items(), key=lambda x: x[1]["amount"], reverse=True)
    if sorted_types:
        top_type, top_stats = sorted_types[0]
        top_pct = top_stats["amount"] / total_amount * 100 if total_amount > 0 else 0
        suggestions.append(f"📊 资产配置: {top_type} 占比最高 ({top_pct:.1f}%)")

    loss_products = [p for p in products if p.return_rate and float(p.return_rate) < -5]
    if loss_products:
        suggestions.append(f"⚠️ {len(loss_products)} 只产品亏损超过5%，建议检查止损策略")

    high_return = [p for p in products if p.annual_return and float(p.annual_return) > 10]
    if high_return:
        suggestions.append(f"🏆 {len(high_return)} 只产品年化收益超过10%，表现优异")

    bond_amount = sum(stats["amount"] for t, stats in type_stats.items() if "债" in t)
    bond_pct = bond_amount / total_amount * 100 if total_amount > 0 else 0
    if bond_pct < 20:
        suggestions.append(f"💡 债券类资产占比 {bond_pct:.1f}%，建议适当增加以降低波动")

    suggestions.append("📋 建议: 每月检查资产配置，保持分散投资，定期再平衡")

    return suggestions
