import click


def _auto_screen_and_add_to_pool(pool, strategy_name: str, max_stocks: int = 50) -> int:
    from asset_lens.data.market_stock_fetcher import market_stock_fetcher
    from asset_lens.strategy.engine import StrategyEngine

    try:
        click.echo(f"  正在执行 {strategy_name} 策略选股...")

        stocks_data = market_stock_fetcher.get_cached_market_stocks()
        if not stocks_data:
            click.echo("  ⚠️ 无股票数据缓存，正在自动获取...")
            try:
                stocks_data = market_stock_fetcher.fetch_all_cn_stocks(max_pages=3)
                if stocks_data:
                    market_stock_fetcher.save_market_stocks(stocks_data)
                    click.echo(f"  ✅ 已获取 {len(stocks_data)} 只股票数据")
                else:
                    click.echo("  ❌ 获取市场数据失败")
                    return 0
            except Exception as fetch_error:
                click.echo(f"  ❌ 获取市场数据失败: {fetch_error}")
                return 0

        engine = StrategyEngine()
        result = engine.screen_stocks(stocks=stocks_data, strategy_name=strategy_name, min_score=60.0)

        if not result:
            click.echo("  ⚠️ 未筛选到符合条件的股票")
            return 0

        added = 0
        for stock in result[:max_stocks]:
            code = stock.get("code", "")
            name = stock.get("name", "")
            score = stock.get("strategy_score", stock.get("score", 0))

            if code:
                success, _msg = pool.add_stock(
                    code=code,
                    name=name,
                    price=stock.get("current_price", 0),
                    status="watching",
                    notes=f"自动选股入池，得分: {score:.0f}",
                )
                if success:
                    added += 1

        click.echo(f"  ✅ 已添加 {added} 只股票到观察列表")
        return added

    except Exception as e:
        click.echo(f"  ❌ 自动选股失败: {e}")
        return 0


def _check_market_environment() -> tuple:
    try:
        from asset_lens.data.enhanced_market_data_fetcher import enhanced_market_data_fetcher

        result = enhanced_market_data_fetcher.fetch_all_domestic_indexes()
        if not result or "指数数据" not in result:
            return True, "⚠️ 无市场数据，默认允许交易"

        indices = result["指数数据"]
        sh_index = None
        for code, data in indices.items():
            if "sh000001" in code or "上证" in data.get("name", ""):
                sh_index = data
                break

        if not sh_index:
            return True, "⚠️ 无上证指数数据，默认允许交易"

        change = sh_index.get("change_percent", 0)
        if isinstance(change, str):
            change = float(change.replace("%", ""))

        if change < -2:
            return False, f"❌ 市场环境不佳: 上证指数跌幅 {change:.2f}%，暂停买入"
        elif change < -1:
            return True, f"⚠️ 市场偏弱: 上证指数跌幅 {change:.2f}%，谨慎交易"
        else:
            return True, f"✅ 市场环境正常: 上证指数 {change:+.2f}%"

    except Exception as e:
        return True, f"⚠️ 市场环境检查失败: {e}，默认允许交易"


def _generate_buy_reason(evaluation: dict) -> str:
    reasons = [f"{detail.get('condition', '')}" for detail in evaluation.get("details", []) if detail.get("matched")]
    return ", ".join(reasons) if reasons else "策略匹配"


def _get_market_data():
    try:
        from asset_lens.data.enhanced_market_data_fetcher import enhanced_market_data_fetcher

        market_result = enhanced_market_data_fetcher.fetch_all_domestic_indexes()
        if market_result and "指数数据" in market_result:
            for name, data in market_result["指数数据"].items():
                if "上证" in name:
                    change = data.get("涨跌幅", 0)
                    if isinstance(change, str):
                        change = float(change.replace("%", ""))
                    return {
                        "index_name": name,
                        "index_change": change,
                        "sentiment": "乐观" if change > 1 else ("悲观" if change < -1 else "中性"),
                    }
    except (ValueError, TypeError):
        pass
    return None


def _analyze_sell_signals(
    holding_stocks, engine, strategy_name, ai_advisor, ml_predictor, history_fetcher, market_data
):
    from datetime import datetime

    sell_signals = []
    for stock in holding_stocks:
        buy_price = stock.get("buy_price", 0)
        current_price = stock.get("current_price", buy_price)
        profit_rate = ((current_price - buy_price) / buy_price * 100) if buy_price > 0 else 0
        buy_date = stock.get("buy_date", "")
        holding_days = 0
        if buy_date:
            try:
                buy_dt = datetime.strptime(buy_date, "%Y-%m-%d")
                holding_days = (datetime.now() - buy_dt).days
            except ValueError:
                pass

        strategy_sell = False
        strategy_reason = ""
        is_stop_loss = False
        is_take_profit = False

        evaluation = engine.evaluate_stock(
            {
                "code": stock["code"],
                "name": stock["name"],
                "current_price": current_price,
                "profit_rate": profit_rate,
                "change_percent": stock.get("change_percent", 0),
            },
            strategy_name,
        )

        for detail in evaluation.get("details", []):
            if detail.get("matched") and detail.get("condition") in ["止损", "止盈", "趋势破坏"]:
                strategy_sell = True
                strategy_reason = detail.get("condition", "") + ": " + detail.get("expected", "")
                if detail.get("condition") == "止损":
                    is_stop_loss = True
                elif detail.get("condition") == "止盈":
                    is_take_profit = True
                break

        ai_decision = None
        if ai_advisor:
            ai_result = ai_advisor.evaluate_sell_signal(
                stock_data={
                    "code": stock["code"],
                    "name": stock["name"],
                    "price": current_price,
                    "change_percent": stock.get("change_percent", 0),
                },
                holding_data={
                    "profit_rate": profit_rate,
                    "holding_days": holding_days,
                    "buy_price": buy_price,
                },
                market_data=market_data,
            )
            ai_decision = ai_result

        ml_sell_prediction = None
        ml_down_prob = 0.0
        if ml_predictor:
            try:
                history_data = None
                if history_fetcher:
                    history = history_fetcher.fetch_history(stock["code"], days=60)
                    if history and "klines" in history:
                        history_data = history["klines"]

                ml_result = ml_predictor.predict_single(
                    code=stock["code"],
                    name=stock["name"],
                    current_price=current_price,
                    change_percent=stock.get("change_percent", 0),
                    turnover_rate=stock.get("turnover_rate", 0),
                    history_data=history_data,
                )
                if ml_result:
                    ml_sell_prediction = ml_result
                    ml_down_prob = ml_result.down_prob
            except Exception:
                pass

        should_sell = strategy_sell
        final_reason = strategy_reason

        if ml_sell_prediction and ml_down_prob > 0.6 and not is_stop_loss:
            should_sell = True
            if strategy_reason:
                final_reason = f"{strategy_reason} + ML预测下跌({ml_down_prob:.0%})"
            else:
                final_reason = f"ML预测下跌概率高({ml_down_prob:.0%})"

        if ai_decision:
            if ai_decision.get("action") == "sell":
                should_sell = True
                if strategy_reason:
                    if ml_sell_prediction:
                        final_reason = f"{strategy_reason} + AI确认 + ML({ml_down_prob:.0%})"
                    else:
                        final_reason = f"{strategy_reason} + AI确认卖出"
                else:
                    final_reason = ai_decision.get("reason", "AI建议卖出")
            elif ai_decision.get("action") == "hold" and strategy_sell:
                final_reason = f"{strategy_reason} (AI建议持有观望)"

        if should_sell:
            sell_signals.append(
                {
                    "code": stock["code"],
                    "name": stock["name"],
                    "current_price": current_price,
                    "buy_price": buy_price,
                    "profit_rate": profit_rate,
                    "holding_days": holding_days,
                    "score": evaluation["score"],
                    "reason": final_reason,
                    "ai_confidence": ai_decision.get("ai_confidence", 0) if ai_decision else 0,
                    "ml_down_prob": ml_down_prob,
                    "is_stop_loss": is_stop_loss,
                    "is_take_profit": is_take_profit,
                }
            )

    return sell_signals


def _display_sell_signals(sell_signals):
    if sell_signals:
        click.echo(f"\n📉 卖出信号 ({len(sell_signals)}):")
        for signal in sell_signals:
            signal_type = (
                "🟢止损"
                if signal.get("is_stop_loss")
                else ("🔴止盈" if signal.get("is_take_profit") else "📊趋势")
            )
            click.echo(f"  {signal['code']} - {signal['name']} [{signal_type}]")
            click.echo(f"    收益率: {signal['profit_rate']:+.2f}%, 持仓: {signal['holding_days']}天")
            click.echo(f"    理由: {signal['reason']}")
            if signal.get("ml_down_prob", 0) > 0:
                click.echo(f"    🔮 ML预测下跌概率: {signal['ml_down_prob']:.1%}")
            if signal["ai_confidence"] > 0:
                click.echo(f"    🧠 AI信心: {signal['ai_confidence']:.0f}%")
    else:
        click.echo("\n📉 无卖出信号")


def _execute_sell_signals(sell_signals, pool, max_sell, market_ok):
    stop_loss_signals = [s for s in sell_signals if s.get("is_stop_loss")]
    take_profit_signals = [s for s in sell_signals if s.get("is_take_profit") and not s.get("is_stop_loss")]
    other_signals = [s for s in sell_signals if not s.get("is_stop_loss") and not s.get("is_take_profit")]

    click.echo("\n💰 执行卖出操作...")

    for signal in stop_loss_signals[:max_sell]:
        success, msg = pool.sell_stock(
            code=signal["code"], price=signal["current_price"], notes=f"止损卖出: {signal['reason']}"
        )
        if success:
            click.echo(f"🟢 止损卖出: {msg}")
        else:
            click.echo(f"⏭️ {msg}")

    if take_profit_signals:
        if market_ok:
            for signal in take_profit_signals[: max_sell - len(stop_loss_signals)]:
                success, msg = pool.sell_stock(
                    code=signal["code"],
                    price=signal["current_price"],
                    notes=f"止盈卖出: {signal['reason']}",
                )
                if success:
                    click.echo(f"🔴 止盈卖出: {msg}")
                else:
                    click.echo(f"⏭️ {msg}")
        else:
            click.echo(f"⚠️ 市场环境不佳，暂缓止盈卖出 ({len(take_profit_signals)} 只)")

    for signal in other_signals[: max_sell - len(stop_loss_signals) - len(take_profit_signals)]:
        success, msg = pool.sell_stock(
            code=signal["code"], price=signal["current_price"], notes=f"自动卖出: {signal['reason']}"
        )
        if success:
            click.echo(f"📊 趋势卖出: {msg}")
        else:
            click.echo(f"⏭️ {msg}")


def _analyze_buy_signals(
    watching_stocks, holding_codes, stocks_data, engine, strategy_name, ai_advisor, ml_predictor, history_fetcher, market_data
):
    buy_signals = []

    for stock in watching_stocks:
        if stock["code"] in holding_codes:
            continue

        stock_data = None
        for s in stocks_data:
            if s.get("code") == stock["code"]:
                stock_data = s
                break

        if not stock_data:
            continue

        evaluation = engine.evaluate_stock(stock_data, strategy_name)

        # evaluate_stock 返回 score 为 0~1 小数，recommendation 为推荐等级
        score_pct = evaluation.get("score", 0) * 100
        is_match = evaluation.get("recommendation", "") in ("强烈推荐", "推荐")

        if is_match and score_pct >= 60:
            current_price = stock_data.get("current_price", 0)
            market_cap = stock_data.get("market_cap", 0)

            strategy_reason = _generate_buy_reason(evaluation)

            ai_decision = None
            if ai_advisor:
                ai_result = ai_advisor.evaluate_buy_signal(
                    stock_data={
                        "code": stock["code"],
                        "name": stock["name"],
                        "price": current_price,
                        "change_percent": stock_data.get("change_percent", 0),
                        "turnover_rate": stock_data.get("turnover_rate", 0),
                        "market_cap": market_cap,
                        "pe_ratio": stock_data.get("pe_ratio", 0),
                        "volume": stock_data.get("volume", 0),
                        "amount": stock_data.get("amount", 0),
                    },
                    strategy_score=evaluation["score"],
                    market_data=market_data,
                )
                ai_decision = ai_result

            ml_prediction = None
            ml_up_prob = 0.0
            if ml_predictor:
                try:
                    history_data = None
                    if history_fetcher:
                        history = history_fetcher.fetch_history(stock["code"], days=60)
                        if history and "klines" in history:
                            history_data = history["klines"]

                    ml_result = ml_predictor.predict_single(
                        code=stock["code"],
                        name=stock["name"],
                        current_price=current_price,
                        change_percent=stock_data.get("change_percent", 0),
                        turnover_rate=stock_data.get("turnover_rate", 0),
                        market_cap=market_cap,
                        pe_ratio=stock_data.get("pe_ratio", 0),
                        volume=stock_data.get("volume", 0),
                        amount=stock_data.get("amount", 0),
                        history_data=history_data,
                    )
                    if ml_result:
                        ml_prediction = ml_result
                        ml_up_prob = ml_result.up_prob
                except Exception:
                    pass

            final_action = "buy"
            final_reason = strategy_reason

            if ml_prediction and ml_up_prob < 0.4:
                final_action = "skip"
                final_reason = f"ML预测下跌概率高 ({ml_prediction.down_prob:.1%})"
            elif ml_prediction and ml_up_prob < 0.5:
                final_action = "wait"
                final_reason = f"ML预测不确定 (上涨概率 {ml_up_prob:.1%})"

            if ai_decision and final_action == "buy":
                if ai_decision.get("action") == "wait":
                    final_action = "wait"
                    final_reason = ai_decision.get("reason", "AI建议观望")
                elif ai_decision.get("action") == "skip":
                    final_action = "skip"
                    final_reason = ai_decision.get("reason", "AI不建议买入")
                elif ai_decision.get("action") == "buy":
                    if ml_prediction:
                        final_reason = f"{strategy_reason} + AI确认 + ML({ml_up_prob:.0%})"
                    else:
                        final_reason = f"{strategy_reason} + AI确认"

            if final_action == "buy":
                buy_signals.append(
                    {
                        "code": stock["code"],
                        "name": stock["name"],
                        "current_price": current_price,
                        "change_percent": stock_data.get("change_percent", 0),
                        "turnover_rate": stock_data.get("turnover_rate", 0),
                        "market_cap": market_cap,
                        "score": evaluation["score"],
                        "reason": final_reason,
                        "ai_confidence": ai_decision.get("ai_confidence", 0) if ai_decision else 0,
                        "ml_up_prob": ml_up_prob,
                        "risk_level": ai_decision.get("risk_level", "medium") if ai_decision else "medium",
                        "suggested_stop_loss": ai_decision.get("suggested_stop_loss") if ai_decision else None,
                        "suggested_take_profit": ai_decision.get("suggested_take_profit")
                        if ai_decision
                        else None,
                    }
                )

    buy_signals.sort(key=lambda x: (x["ml_up_prob"], x["score"], x["ai_confidence"]), reverse=True)
    return buy_signals


def _display_buy_signals(buy_signals, max_buy):
    click.echo(f"\n📈 买入信号 ({len(buy_signals)}):")
    for signal in buy_signals[:max_buy]:
        click.echo(f"  {signal['code']} - {signal['name']} (得分: {signal['score']:.0f})")
        click.echo(
            f"    当前价: {signal['current_price']:.2f}, 涨幅: {signal['change_percent']:+.2f}%, 换手: {signal['turnover_rate']:.2f}%"
        )
        click.echo(f"    市值: {signal['market_cap']:.1f}亿, 风险: {signal['risk_level']}")
        click.echo(f"    理由: {signal['reason']}")
        if signal.get("ml_up_prob", 0) > 0:
            click.echo(f"    🔮 ML预测上涨概率: {signal['ml_up_prob']:.1%}")
        if signal["ai_confidence"] > 0:
            click.echo(f"    🧠 AI信心: {signal['ai_confidence']:.0f}%")
        if signal.get("suggested_stop_loss"):
            click.echo(f"    建议止损: {signal['suggested_stop_loss']:.2f}")
        if signal.get("suggested_take_profit"):
            click.echo(f"    建议止盈: {signal['suggested_take_profit']:.2f}")


def _execute_buy_signals(buy_signals, pool, remaining_buy, remaining_position, max_amount):
    bought = 0
    total_amount = 0

    for signal in buy_signals:
        if bought >= remaining_buy:
            click.echo("⏭️ 今日买入数量已达上限")
            break

        price = signal["current_price"]
        shares = min(100, int(max_amount / price)) if price > 0 else 100
        amount = price * shares

        if amount > remaining_position - total_amount:
            shares = int((remaining_position - total_amount) / price)
            amount = price * shares
            if shares <= 0:
                click.echo(f"⏭️ {signal['name']}({signal['code']}) 剩余仓位不足")
                continue

        notes = f"自动买入: {signal['reason']}"
        if signal.get("suggested_stop_loss"):
            notes += f", 止损: {signal['suggested_stop_loss']:.2f}"
        if signal.get("suggested_take_profit"):
            notes += f", 止盈: {signal['suggested_take_profit']:.2f}"

        success, msg = pool.buy_stock(code=signal["code"], price=price, shares=shares, notes=notes)
        if success:
            click.echo(f"✅ {msg}")
            bought += 1
            total_amount += amount
        else:
            click.echo(f"⏭️ {msg}")

    click.echo(f"\n💰 买入统计: {bought} 只股票，总金额: ¥{total_amount:,.2f}")


def _display_position_advice(holding_stocks, total_position, max_position, unrealized_pnl, unrealized_pnl_pct, market_ok):
    position_usage = total_position / max_position * 100 if max_position > 0 else 0
    click.echo("\n💡 仓位调整建议")
    if position_usage < 30:
        click.echo("  📈 仓位偏低，建议逐步加仓")
        click.echo(f"     当前仓位使用率: {position_usage:.1f}%")
        click.echo("     可用资金充足，可关注买入信号")
    elif position_usage > 80:
        click.echo("  ⚠️ 仓位偏高，建议控制风险")
        click.echo(f"     当前仓位使用率: {position_usage:.1f}%")
        click.echo("     建议设置止损，控制单只股票仓位")
    else:
        click.echo(f"  ✅ 仓位适中 ({position_usage:.1f}%)")
        click.echo("     继续执行策略，保持纪律")

    if unrealized_pnl_pct < -5:
        click.echo("  🟢 整体亏损较大，建议检查持仓")
        click.echo("     考虑止损或减仓，等待市场好转")
    elif unrealized_pnl_pct > 10:
        click.echo("  🔴 整体盈利良好，可考虑部分止盈")
        click.echo("     建议分批卖出锁定收益")

    if len(holding_stocks) > 10:
        click.echo(f"  ⚠️ 持仓股票较多 ({len(holding_stocks)} 只)")
        click.echo("     建议集中持仓，提高效率")

    if not market_ok:
        click.echo("  ⚠️ 市场环境不佳，建议谨慎操作")
        click.echo("     可降低仓位或观望等待")
