"""
Strategy CLI commands for asset-lens.
策略命令模块 - 包含 strategy, backtest, screen-stocks, filter-stocks, volume-breakout, momentum-screen, optimize-strategy
"""

from pathlib import Path

import click


def register_strategy_commands(cli: click.Group) -> None:
    """注册策略命令到 CLI 组"""

    @cli.command()
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    @click.option("--strategy-name", type=str, help="策略名称")
    def strategy(data_mode: str | None, strategy_name: str | None):
        """运行投资策略"""
        from asset_lens.cli_modules.cli.helpers import setup_data_mode

        setup_data_mode(data_mode)

        click.echo("\n📊 运行投资策略")
        click.echo("=" * 60)

        try:
            from asset_lens.strategy.engine import StrategyEngine

            engine = StrategyEngine()

            if strategy_name:
                strategies = engine.list_strategies()
                click.echo(f"✅ 策略 {strategy_name} 已加载")
                click.echo(f"可用策略: {[s['name'] for s in strategies]}")
            else:
                strategies = engine.list_strategies()
                click.echo("可用策略:")
                for s in strategies:
                    click.echo(f"  - {s.get('name', s)}")

        except Exception as e:
            click.echo(f"❌ 执行失败: {e}", err=True)

    @cli.command()
    @click.option("--strategy", type=str, required=True, help="策略名称")
    @click.option("--start-date", type=str, help="开始日期 (YYYY-MM-DD)")
    @click.option("--end-date", type=str, help="结束日期 (YYYY-MM-DD)")
    def backtest(strategy: str, start_date: str | None, end_date: str | None):
        """运行策略回测"""
        click.echo("\n📊 策略回测")
        click.echo("=" * 60)

        try:
            from asset_lens.strategy.backtester import Backtester

            Backtester()

            click.echo("\n📈 回测配置:")
            click.echo(f"  策略: {strategy}")
            click.echo(f"  开始日期: {start_date or '默认'}")
            click.echo(f"  结束日期: {end_date or '默认'}")

            click.echo("\n💡 请使用 run_backtest() 方法执行回测")

        except Exception as e:
            click.echo(f"❌ 回测失败: {e}", err=True)

    @cli.command()
    @click.option("--strategy", type=str, default="momentum", help="筛选策略")
    @click.option("--limit", type=int, default=20, help="返回数量限制")
    def screen_stocks(strategy: str, limit: int):
        """筛选股票"""
        click.echo("\n📊 股票筛选")
        click.echo("=" * 60)

        try:
            from asset_lens.data.market_stock_fetcher import market_stock_fetcher
            from asset_lens.strategy.engine import StrategyEngine

            click.echo("📡 正在获取股票列表...")
            stocks = market_stock_fetcher.fetch_all_cn_stocks(max_pages=1)

            if not stocks:
                click.echo("❌ 未能获取股票列表", err=True)
                return

            engine = StrategyEngine()
            result = engine.screen_stocks(stocks=stocks, strategy_name=strategy)

            click.echo(f"\n📈 筛选结果 ({len(result) if result else 0} 只股票):")
            if result:
                for stock in result[:limit]:
                    code = stock.get("code", stock.get("symbol", "N/A"))
                    name = stock.get("name", "N/A")
                    score = stock.get("strategy_score", stock.get("score", 0))
                    change_percent = stock.get("change_percent", 0)
                    current_price = stock.get("current_price", 0)
                    click.echo(
                        f"  {code} - {name} (得分: {score:.1f}, 涨幅: {change_percent:+.2f}%, 价格: {current_price:.2f})"
                    )

            click.echo("\n✅ 筛选完成！")

        except Exception as e:
            click.echo(f"❌ 筛选失败: {e}", err=True)

    @cli.command("filter-stocks")
    @click.option("--config-file", type=click.Path(), help="筛选配置文件路径")
    @click.option("--stocks-file", type=click.Path(), help="股票数据文件路径")
    @click.option("--fetch-market", is_flag=True, help="从市场获取股票列表")
    @click.option("--max-pages", type=int, default=5, help="获取市场股票的最大页数")
    def filter_stocks(config_file: str | None, stocks_file: str | None, fetch_market: bool, max_pages: int):
        """筛选股票"""
        click.echo("\n📊 股票筛选")
        click.echo("=" * 60)

        try:
            from asset_lens.strategy.stock_filter import StockFilter

            config_path = Path(config_file) if config_file else None
            stock_filter = StockFilter(config_path)

            click.echo(stock_filter.get_filter_summary())
            click.echo("")

            if fetch_market:
                from asset_lens.data.market_stock_fetcher import market_stock_fetcher

                click.echo("📡 正在从市场获取股票列表...")
                stocks = market_stock_fetcher.fetch_all_cn_stocks(max_pages=max_pages)

                if stocks:
                    market_stock_fetcher.save_market_stocks(stocks)

            click.echo("\n✅ 筛选完成！")

        except Exception as e:
            click.echo(f"❌ 筛选失败: {e}", err=True)

    @cli.command()
    @click.option("--min-volume-ratio", type=float, default=2.0, help="最小成交量比率")
    @click.option("--limit", type=int, default=20, help="返回数量限制")
    def volume_breakout(min_volume_ratio: float, limit: int):
        """成交量突破筛选"""
        click.echo("\n📊 成交量突破筛选")
        click.echo("=" * 60)

        try:
            from asset_lens.strategy.volume_breakout import volume_breakout_filter

            result = volume_breakout_filter.filter()

            click.echo(f"\n📈 筛选结果 ({len(result) if result else 0} 只股票):")
            if result:
                for stock in result[:limit]:
                    code = stock.get("code", "N/A")
                    name = stock.get("name", "N/A")
                    volume_ratio = stock.get("volume_ratio", 0)
                    click.echo(f"  {code} - {name} (成交量比率: {volume_ratio:.2f})")

            click.echo("\n✅ 筛选完成！")

        except Exception as e:
            click.echo(f"❌ 筛选失败: {e}", err=True)

    @cli.command()
    @click.option("--min-momentum", type=float, default=0.05, help="最小动量得分")
    @click.option("--limit", type=int, default=20, help="返回数量限制")
    @click.option("--add-to-pool", is_flag=True, help="将筛选结果添加到股票池")
    def momentum_screen(min_momentum: float, limit: int, add_to_pool: bool):
        """动量选股"""
        click.echo("\n📊 动量选股")
        click.echo("=" * 60)

        try:
            from asset_lens.data.market_stock_fetcher import market_stock_fetcher
            from asset_lens.strategy.engine import StrategyEngine
            from asset_lens.trading.stock_pool import StockPool

            stocks = market_stock_fetcher.get_cached_market_stocks()
            cache_age = market_stock_fetcher.get_cache_age_hours()

            if stocks and cache_age >= 0:
                click.echo(f"📦 使用缓存数据（{cache_age:.1f}小时前更新)")

            if market_stock_fetcher.is_cache_expired(max_age_hours=24):
                click.echo("⚠️ 缓存已过期，正在更新...")
                new_stocks = market_stock_fetcher.fetch_all_cn_stocks(max_pages=1)
                if new_stocks:
                    market_stock_fetcher.save_market_stocks(new_stocks)
                    stocks = new_stocks
                    click.echo(f"✅ 已更新缓存，获取到 {len(stocks)} 只股票")
                else:
                    click.echo("📦 网络获取失败，使用旧缓存数据")

            if not stocks:
                click.echo("❌ 未能获取股票列表", err=True)
                click.echo("💡 提示: 请检查网络连接")
                return

            click.echo(f"✅ 共 {len(stocks)} 只股票")

            engine = StrategyEngine()
            result = engine.screen_stocks(stocks=stocks, strategy_name="momentum", min_score=60.0)

            click.echo(f"\n📈 筛选结果 ({len(result) if result else 0} 只股票):")
            if result:
                for stock in result[:limit]:
                    code = stock.get("code", stock.get("symbol", "N/A"))
                    name = stock.get("name", "N/A")
                    score = stock.get("strategy_score", stock.get("score", 0))
                    click.echo(f"  {code} - {name} (得分: {score:.2f})")

                if add_to_pool:
                    click.echo("\n📦 正在添加到股票池...")
                    pool = StockPool()
                    added = 0
                    skipped = 1
                    for stock in result[:limit]:
                        code = stock.get("code", stock.get("symbol", ""))
                        name = stock.get("name", "")
                        score = stock.get("strategy_score", stock.get("score", 0))
                        if code:
                            success, msg = pool.add_stock(
                                code=code,
                                name=name,
                                price=0.0,
                                status="watching",
                                notes=f"动量策略选入，得分: {score:.2f}",
                            )
                            if success:
                                click.echo(f"✅ {msg}")
                                added += 1
                            else:
                                click.echo(f"⏭️ {msg}")
                                skipped += 1
                    click.echo(f"\n📊 统计: 新增 {added} 只，跳过 {skipped} 只")

            click.echo("\n✅ 筛选完成！")

        except Exception as e:
            click.echo(f"❌ 筛选失败: {e}", err=True)

    @cli.command()
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    def optimize_strategy(data_mode: str | None):
        """优化策略参数"""
        from asset_lens.cli_modules.cli.helpers import setup_data_mode

        setup_data_mode(data_mode)

        click.echo("\n📊 策略优化")
        click.echo("=" * 60)

        try:
            from asset_lens.strategy.engine import StrategyEngine

            StrategyEngine()

            click.echo("\n📈 可用优化方法:")
            click.echo("  - optimize_strategy_params(): 参数优化")
            click.echo("  - combine_strategies(): 策略组合")

            click.echo("\n✅ 策略引擎已加载！")
        except Exception as e:
            click.echo(f"❌ 优化失败: {e}", err=True)

    @cli.command("auto-trade")
    @click.option(
        "--strategy-name", type=click.Choice(["value", "momentum", "reversal"]), default="momentum", help="策略名称"
    )
    @click.option("--max-buy", type=int, default=5, help="单次最大买入数量")
    @click.option("--max-sell", type=int, default=10, help="单次最大卖出数量")
    @click.option("--dry-run", is_flag=True, help="仅显示信号，不执行交易")
    @click.option("--max-daily-buy", type=int, default=5, help="每日最大买入数量")
    @click.option("--max-amount", type=float, default=10000, help="单只股票最大买入金额")
    @click.option("--max-position", type=float, default=100000, help="总持仓金额上限")
    @click.option("--max-industry", type=int, default=2, help="每个行业最大持仓数量")
    @click.option("--auto-screen", is_flag=True, default=True, help="股票池为空时自动选股入池")
    @click.option("--use-ai", is_flag=True, default=False, help="启用 AI 分析辅助决策")
    @click.option("--use-ml", is_flag=True, default=False, help="启用 ML 模型预测辅助决策")
    def auto_trade(
        strategy_name: str,
        max_buy: int,
        max_sell: int,
        dry_run: bool,
        max_daily_buy: int,
        max_amount: float,
        max_position: float,
        max_industry: int,
        auto_screen: bool,
        use_ai: bool,
        use_ml: bool,
    ):
        """自动交易 - 根据策略信号自动买入卖出（增强版，支持 AI/ML 分析）"""
        from datetime import datetime

        from asset_lens.data.market_stock_fetcher import market_stock_fetcher
        from asset_lens.strategy.engine import StrategyEngine
        from asset_lens.trading.stock_pool import StockPool

        click.echo(f"\n🤖 自动交易系统 v4.0 ({strategy_name}策略)")
        if use_ai:
            click.echo("🧠 AI 分析已启用")
        if use_ml:
            click.echo("🔮 ML 预测已启用")
        click.echo("=" * 60)

        try:
            pool = StockPool()
            engine = StrategyEngine()

            ai_advisor = None
            if use_ai:
                try:
                    from asset_lens.strategy.ai_analyzer import ai_trading_advisor

                    ai_advisor = ai_trading_advisor
                    if ai_advisor.analyzer.enabled:
                        click.echo("✅ AI 分析器已加载")
                    else:
                        click.echo("⚠️ AI 分析器未配置 API Key，将仅使用策略信号")
                        ai_advisor = None
                except Exception as e:
                    click.echo(f"⚠️ AI 分析器加载失败: {e}")
                    ai_advisor = None

            ml_predictor = None
            history_fetcher = None
            if use_ml:
                try:
                    from pathlib import Path

                    from asset_lens.data.stock_history_fetcher import StockHistoryFetcher
                    from asset_lens.ml.predictor import StockPredictor

                    model_path = Path("cache/ml/model.pkl")
                    if model_path.exists():
                        ml_predictor = StockPredictor(model_path=model_path)
                        history_fetcher = StockHistoryFetcher()
                        click.echo(f"✅ ML 模型已加载: {model_path}")
                    else:
                        click.echo("⚠️ ML 模型不存在，正在自动训练...")
                        try:
                            from click.testing import CliRunner

                            from asset_lens.cli_modules.cli.ml import train as train_cmd
                            runner = CliRunner()
                            result = runner.invoke(train_cmd, [])
                            if result.exit_code == 0 and model_path.exists():
                                ml_predictor = StockPredictor(model_path=model_path)
                                history_fetcher = StockHistoryFetcher()
                                click.echo("✅ ML 模型自动训练完成")
                            else:
                                click.echo("⚠️ ML 模型自动训练失败，跳过 ML 预测")
                        except Exception as train_error:
                            click.echo(f"⚠️ ML 模型自动训练失败: {train_error}")
                except Exception as e:
                    click.echo(f"⚠️ ML 预测器加载失败: {e}")
                    ml_predictor = None

            click.echo("\n📊 市场环境分析...")
            market_ok, market_msg = _check_market_environment()
            click.echo(f"  {market_msg}")

            market_data = None
            try:
                from asset_lens.data.enhanced_market_data_fetcher import enhanced_market_data_fetcher

                market_result = enhanced_market_data_fetcher.fetch_all_domestic_indexes()
                if market_result and "指数数据" in market_result:
                    for name, data in market_result["指数数据"].items():
                        if "上证" in name:
                            change = data.get("涨跌幅", 0)
                            if isinstance(change, str):
                                change = float(change.replace("%", ""))
                            market_data = {
                                "index_name": name,
                                "index_change": change,
                                "sentiment": "乐观" if change > 1 else ("悲观" if change < -1 else "中性"),
                            }
                            break
            except Exception:
                pass

            click.echo("\n📊 分析股票池持仓...")
            holding_stocks = pool.list_stocks(status="holding")
            watching_stocks = pool.list_stocks(status="watching")

            click.echo(f"  持仓股票: {len(holding_stocks)}")
            click.echo(f"  观察股票: {len(watching_stocks)}")

            if auto_screen and len(watching_stocks) < 10:
                click.echo(f"\n⚠️ 观察股票不足 ({len(watching_stocks)} < 10)，自动执行选股入池...")
                _auto_screen_and_add_to_pool(pool, strategy_name, max_buy * 10)
                watching_stocks = pool.list_stocks(status="watching")
                click.echo(f"  更新后观察股票: {len(watching_stocks)}")

            today = datetime.now().strftime("%Y-%m-%d")
            today_bought = [s for s in holding_stocks if s.get("buy_date") == today]
            click.echo(f"  今日已买入: {len(today_bought)}")

            total_position = sum(s.get("buy_price", 0) * s.get("shares", 100) for s in holding_stocks)
            current_market_value = sum(
                s.get("current_price", s.get("buy_price", 0)) * s.get("shares", 100) for s in holding_stocks
            )
            unrealized_pnl = current_market_value - total_position
            unrealized_pnl_pct = (unrealized_pnl / total_position * 100) if total_position > 0 else 0

            click.echo(f"  总持仓金额: ¥{total_position:,.2f} (买入成本)")
            click.echo(f"  当前市值: ¥{current_market_value:,.2f} (实时估值)")
            pnl_emoji = "🟢" if unrealized_pnl >= 0 else "🔴"
            click.echo(f"  浮盈浮亏: {pnl_emoji} ¥{unrealized_pnl:+,.2f} ({unrealized_pnl_pct:+.2f}%)")

            remaining_buy = max(0, max_daily_buy - len(today_bought))
            remaining_position = max(0, max_position - total_position)
            click.echo(f"  今日剩余可买: {remaining_buy} 只")
            click.echo(f"  剩余仓位: ¥{remaining_position:,.2f}")

            for s in holding_stocks[:5]:
                buy_price = s.get("buy_price", 0)
                current_price = s.get("current_price", buy_price)
                profit_rate = ((current_price - buy_price) / buy_price * 100) if buy_price > 0 else 0
                click.echo(
                    f"  {s['code']} - {s['name']} (买入价: {buy_price:.2f}, 现价: {current_price:.2f}, 收益率: {profit_rate:+.2f}%)"
                )

            if remaining_buy <= 0 and not dry_run:
                click.echo("\n⚠️ 今日买入数量已达上限，跳过买入操作")

            if remaining_position <= 0 and not dry_run:
                click.echo("\n⚠️ 总仓位已达上限，跳过买入操作")

            click.echo("\n📈 分析卖出信号...")
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
                    except Exception:
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

            if sell_signals:
                stop_loss_signals = [s for s in sell_signals if s.get("is_stop_loss")]
                take_profit_signals = [s for s in sell_signals if s.get("is_take_profit") and not s.get("is_stop_loss")]
                other_signals = [s for s in sell_signals if not s.get("is_stop_loss") and not s.get("is_take_profit")]

                click.echo(f"\n📉 卖出信号 ({len(sell_signals)}):")
                for signal in sell_signals:
                    signal_type = (
                        "🔴止损"
                        if signal.get("is_stop_loss")
                        else ("🟢止盈" if signal.get("is_take_profit") else "📊趋势")
                    )
                    click.echo(f"  {signal['code']} - {signal['name']} [{signal_type}]")
                    click.echo(f"    收益率: {signal['profit_rate']:+.2f}%, 持仓: {signal['holding_days']}天")
                    click.echo(f"    理由: {signal['reason']}")
                    if signal.get("ml_down_prob", 0) > 0:
                        click.echo(f"    🔮 ML预测下跌概率: {signal['ml_down_prob']:.1%}")
                    if signal["ai_confidence"] > 0:
                        click.echo(f"    🧠 AI信心: {signal['ai_confidence']:.0f}%")

                if not dry_run:
                    click.echo("\n💰 执行卖出操作...")

                    for signal in stop_loss_signals[:max_sell]:
                        success, msg = pool.sell_stock(
                            code=signal["code"], price=signal["current_price"], notes=f"止损卖出: {signal['reason']}"
                        )
                        if success:
                            click.echo(f"🔴 止损卖出: {msg}")
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
                                    click.echo(f"🟢 止盈卖出: {msg}")
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
            else:
                click.echo("\n📉 无卖出信号")

            click.echo("\n📊 分析买入信号...")
            buy_signals = []

            cache_max_age = 24
            if market_stock_fetcher.is_cache_expired(max_age_hours=cache_max_age):
                click.echo("⚠️ 缓存已过期，正在更新市场数据...")
                try:
                    new_stocks = market_stock_fetcher.fetch_all_cn_stocks(max_pages=2)
                    if new_stocks:
                        market_stock_fetcher.save_market_stocks(new_stocks)
                        click.echo(f"✅ 已更新缓存，获取到 {len(new_stocks)} 只股票")
                    else:
                        click.echo("⚠️ 网络获取失败，尝试使用旧缓存")
                except Exception as e:
                    click.echo(f"⚠️ 更新失败: {e}，使用旧缓存")

            stocks_data = market_stock_fetcher.get_cached_market_stocks()
            if not stocks_data:
                click.echo("⚠️ 无股票数据缓存，正在自动获取...")
                try:
                    stocks_data = market_stock_fetcher.fetch_all_cn_stocks(max_pages=3)
                    if stocks_data:
                        market_stock_fetcher.save_market_stocks(stocks_data)
                        click.echo(f"✅ 已获取 {len(stocks_data)} 只股票数据")
                    else:
                        click.echo("❌ 获取市场数据失败")
                        return
                except Exception as fetch_error:
                    click.echo(f"❌ 获取市场数据失败: {fetch_error}")
                    return

            holding_codes = {s["code"] for s in holding_stocks}

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

                if evaluation["match"] and evaluation["score"] >= 60:
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

            if buy_signals:
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

                if not dry_run and remaining_buy > 0 and remaining_position > 0 and market_ok:
                    click.echo("\n💰 执行买入操作...")
                    bought = 0
                    total_amount = 0

                    for signal in buy_signals:
                        if bought >= remaining_buy:
                            click.echo(f"⏭️ 今日买入数量已达上限 ({max_daily_buy} 只)")
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
                elif not market_ok:
                    click.echo("\n⚠️ 市场环境不佳，跳过买入操作")
            else:
                click.echo("\n📈 无买入信号")

            click.echo("\n📊 交易汇总")
            click.echo(f"  买入信号: {len(buy_signals)}")
            click.echo(f"  卖出信号: {len(sell_signals)}")
            click.echo(f"  今日已买入: {len(today_bought)}")
            click.echo(f"  总持仓金额: ¥{total_position:,.2f} (买入成本)")
            click.echo(f"  当前市值: ¥{current_market_value:,.2f} (实时估值)")
            pnl_emoji = "🟢" if unrealized_pnl >= 0 else "🔴"
            click.echo(f"  浮盈浮亏: {pnl_emoji} ¥{unrealized_pnl:+,.2f} ({unrealized_pnl_pct:+.2f}%)")
            if dry_run:
                click.echo("  模式: 仅显示信号（未执行）")
            if use_ml and ml_predictor:
                click.echo("  🔮 ML 预测: 已启用")
            if use_ai and ai_advisor:
                click.echo("  🧠 AI 分析: 已启用")

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
                click.echo("  🔴 整体亏损较大，建议检查持仓")
                click.echo("     考虑止损或减仓，等待市场好转")
            elif unrealized_pnl_pct > 10:
                click.echo("  🟢 整体盈利良好，可考虑部分止盈")
                click.echo("     建议分批卖出锁定收益")

            if len(holding_stocks) > 10:
                click.echo(f"  ⚠️ 持仓股票较多 ({len(holding_stocks)} 只)")
                click.echo("     建议集中持仓，提高效率")

            if not market_ok:
                click.echo("  ⚠️ 市场环境不佳，建议谨慎操作")
                click.echo("     可降低仓位或观望等待")

        except Exception as e:
            import traceback

            click.echo(f"❌ 自动交易失败: {e}", err=True)
            click.echo(traceback.format_exc(), err=True)

    @cli.command("ai-qa")
    @click.option("--question", "-q", type=str, help="投资问题")
    @click.option("--interactive", "-i", is_flag=True, help="交互模式")
    def ai_qa(question: str | None, interactive: bool):
        """AI 问答 - 投资问题解答和策略咨询"""
        from asset_lens.analysis.ai_qa import ai_qa_engine

        click.echo("\n🤖 AI 投资问答系统")
        click.echo("=" * 60)

        try:
            if interactive or not question:
                click.echo("输入问题进行咨询，输入 'quit' 或 'exit' 退出")
                click.echo("示例: 如何设置止损？当前市场趋势如何？\n")

                while True:
                    try:
                        user_input = click.prompt("你的问题", type=str, default="")
                        if user_input.lower() in ["quit", "exit", "q", "退出"]:
                            click.echo("👋 再见！")
                            break

                        if not user_input.strip():
                            continue

                        response = ai_qa_engine.answer_question(user_input)

                        click.echo(f"\n📝 问题类型: {response.question_type.value}")
                        click.echo("💡 回答:")
                        click.echo(f"   {response.answer}")
                        click.echo(f"\n📊 置信度: {response.confidence:.0%}")

                        if response.sources:
                            click.echo(f"📚 来源: {', '.join(response.sources)}")

                        if response.suggestions:
                            click.echo("💡 建议:")
                            for sug in response.suggestions:
                                click.echo(f"   - {sug}")

                        if response.related_questions:
                            click.echo("❓ 相关问题:")
                            for rq in response.related_questions:
                                click.echo(f"   - {rq}")

                        click.echo()

                    except KeyboardInterrupt:
                        click.echo("\n👋 再见！")
                        break
            else:
                response = ai_qa_engine.answer_question(question)

                click.echo(f"\n📝 问题类型: {response.question_type.value}")
                click.echo("💡 回答:")
                click.echo(f"   {response.answer}")
                click.echo(f"\n📊 置信度: {response.confidence:.0%}")

                if response.sources:
                    click.echo(f"📚 来源: {', '.join(response.sources)}")

                if response.suggestions:
                    click.echo("💡 建议:")
                    for sug in response.suggestions:
                        click.echo(f"   - {sug}")

                if response.related_questions:
                    click.echo("❓ 相关问题:")
                    for rq in response.related_questions:
                        click.echo(f"   - {rq}")

        except Exception as e:
            click.echo(f"❌ 问答失败: {e}", err=True)

    @cli.command("risk-check")
    def risk_check():
        """黑天鹅风险检查 - 系统性风险评估"""
        from asset_lens.analysis.black_swan import black_swan_monitor
        from asset_lens.data.enhanced_market_data_fetcher import enhanced_market_data_fetcher
        from asset_lens.trading.stock_pool import StockPool

        click.echo("\n🦢 黑天鹅风险检查")
        click.echo("=" * 60)

        try:
            result = enhanced_market_data_fetcher.fetch_all_domestic_indexes()
            market_data = None
            if result and "指数数据" in result:
                for name, data in result["指数数据"].items():
                    if "上证" in name:
                        change = data.get("涨跌幅", 0)
                        if isinstance(change, str):
                            change = float(change.replace("%", ""))
                        market_data = {
                            "index_name": name,
                            "index_change": change,
                            "volatility": abs(change),
                            "sentiment": "乐观" if change > 1 else ("悲观" if change < -1 else "中性"),
                            "trend": "上涨" if change > 0 else "下跌",
                        }
                        break

            pool = StockPool()
            holdings = pool.list_stocks(status="holding")

            assessment = black_swan_monitor.check_market_risk(market_data)
            portfolio_alerts = black_swan_monitor.check_portfolio_risk(holdings, market_data)

            click.echo(black_swan_monitor.format_assessment(assessment))

            if portfolio_alerts:
                click.echo("\n⚠️ 持仓风险预警:")
                for alert in portfolio_alerts:
                    level_emoji = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}
                    emoji = level_emoji.get(alert.risk_level.value, "⚪")
                    click.echo(f"  {emoji} {alert.title}")
                    click.echo(f"     {alert.description}")
                    click.echo(f"     建议: {alert.suggested_action}")

            black_swan_monitor.save_alerts(assessment.risk_alerts + portfolio_alerts)

        except Exception as e:
            click.echo(f"❌ 风险检查失败: {e}", err=True)

    @cli.command("rebalance")
    def rebalance():
        """调仓建议 - 持仓优化建议"""
        from asset_lens.analysis.rebalancer import portfolio_rebalancer
        from asset_lens.trading.stock_pool import StockPool

        click.echo("\n📊 持仓调仓分析")
        click.echo("=" * 60)

        try:
            pool = StockPool()
            holdings = pool.list_stocks(status="holding")

            if not holdings:
                click.echo("⚠️ 当前无持仓")
                return

            report = portfolio_rebalancer.generate_report(holdings)
            click.echo(portfolio_rebalancer.format_report(report))

        except Exception as e:
            click.echo(f"❌ 调仓分析失败: {e}", err=True)

    @cli.command("ml-performance")
    @click.option("--days", type=int, default=30, help="统计天数")
    def ml_performance(days: int):
        """ML 模型表现 - 查看预测准确率"""
        from asset_lens.analysis.ml_tracker import ml_prediction_tracker

        click.echo("\n📊 ML 模型表现分析")
        click.echo("=" * 60)

        try:
            performance = ml_prediction_tracker.get_performance(days=days)
            click.echo(ml_prediction_tracker.format_performance_report(performance))

            analysis = ml_prediction_tracker.analyze_predictions(days=days)

            click.echo("\n📈 预测方向分析:")
            for direction, stats in analysis.by_direction.items():
                total = stats["correct"] + stats["wrong"] + stats["pending"]
                if total > 0:
                    click.echo(
                        f"  {direction}: 正确 {stats['correct']}, 错误 {stats['wrong']}, 待验证 {stats['pending']}"
                    )

            click.echo("\n📊 置信度分析:")
            for level, stats in analysis.by_confidence.items():
                total = stats["correct"] + stats["wrong"]
                if total > 0:
                    acc = stats["correct"] / total
                    click.echo(f"  {level}: 准确率 {acc:.1%} ({stats['correct']}/{total})")

            trend_emoji = {"improving": "📈", "declining": "📉", "stable": "➡️"}
            click.echo(f"\n{trend_emoji.get(analysis.trend, '➡️')} 趋势: {analysis.trend}")

        except Exception as e:
            click.echo(f"❌ 分析失败: {e}", err=True)

    register_enhanced_commands(cli)


def _auto_screen_and_add_to_pool(pool, strategy_name: str, max_stocks: int = 50) -> int:
    """自动选股并添加到股票池"""
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
                success, msg = pool.add_stock(
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
    """检查市场环境"""
    try:
        from asset_lens.data.enhanced_market_data_fetcher import enhanced_market_data_fetcher

        result = enhanced_market_data_fetcher.fetch_all_domestic_indexes()
        if not result or "指数数据" not in result:
            return True, "⚠️ 无市场数据，默认允许交易"

        indices = result["指数数据"]
        sh_index = None
        for name, data in indices.items():
            if "上证" in name:
                sh_index = data
                break

        if not sh_index:
            return True, "⚠️ 无上证指数数据，默认允许交易"

        change = sh_index.get("涨跌幅", 0)
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
    """生成买入理由"""
    reasons = []
    for detail in evaluation.get("details", []):
        if detail.get("matched"):
            reasons.append(f"{detail.get('condition', '')}")
    return ", ".join(reasons) if reasons else "策略匹配"


def register_enhanced_commands(cli: click.Group) -> None:
    """注册增强命令"""

    @cli.command("ml-retrain")
    @click.option("--force", is_flag=True, help="强制重训练")
    def ml_retrain(force: bool):
        """ML 模型重训练 - 保持模型新鲜度"""
        from asset_lens.analysis.model_retrainer import model_retrainer

        click.echo("\n🔄 ML 模型重训练")
        click.echo("=" * 60)

        try:
            should, reason = model_retrainer.should_retrain()
            click.echo(f"重训练检查: {reason}")

            if not should and not force:
                click.echo("使用 --force 强制重训练")
                return

            result = model_retrainer.retrain_model(force=force)

            if result.success:
                click.echo("\n✅ 重训练成功!")
                click.echo(f"  旧版本: {result.old_version}")
                click.echo(f"  新版本: {result.new_version}")
                click.echo(f"  准确率变化: {result.old_accuracy:.2%} → {result.new_accuracy:.2%}")
                click.echo(f"  改进: {result.improvement:+.2%}")
                click.echo(f"  训练时间: {result.training_time:.1f}s")
            else:
                click.echo(f"\n❌ 重训练失败: {result.message}")

        except Exception as e:
            click.echo(f"❌ 重训练失败: {e}", err=True)

    @cli.command("trade-stats")
    @click.option("--days", type=int, default=30, help="统计天数")
    def trade_stats(days: int):
        """交易日志统计 - 查看交易记录"""
        from asset_lens.analysis.trade_logger import enhanced_trade_logger

        click.echo("\n📊 交易日志统计")
        click.echo("=" * 60)

        try:
            stats = enhanced_trade_logger.get_statistics(days=days)
            click.echo(enhanced_trade_logger.format_statistics_report(stats))

        except Exception as e:
            click.echo(f"❌ 统计失败: {e}", err=True)

    @cli.command("backtest-report")
    @click.option("--period", type=click.Choice(["daily", "weekly", "monthly"]), default="weekly", help="报告周期")
    def backtest_report(period: str):
        """策略回测报告 - 定期评估"""
        from asset_lens.analysis.backtest_reporter import ReportPeriod, backtest_reporter

        click.echo("\n📊 策略回测报告")
        click.echo("=" * 60)

        try:
            period_enum = ReportPeriod(period)
            report = backtest_reporter.generate_report(period=period_enum)
            click.echo(backtest_reporter.format_report(report))

        except Exception as e:
            click.echo(f"❌ 报告生成失败: {e}", err=True)

    @cli.command("dashboard")
    @click.option("--export", type=click.Choice(["text", "html"]), default="text", help="导出格式")
    def dashboard(export: str):
        """绩效看板 - 可视化展示"""
        from asset_lens.analysis.dashboard import dashboard_generator
        from asset_lens.trading.stock_pool import StockPool

        click.echo("\n📊 绩效看板")
        click.echo("=" * 60)

        try:
            pool = StockPool()
            holdings = pool.list_stocks(status="holding")

            dashboard_obj = dashboard_generator.generate_dashboard(holdings=holdings)

            if export == "html":
                html = dashboard_generator.export_html(dashboard_obj)
                output_file = Path("cache/dashboard.html")
                output_file.parent.mkdir(parents=True, exist_ok=True)
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(html)
                click.echo(f"✅ HTML 看板已导出: {output_file}")
            else:
                click.echo(dashboard_generator.format_dashboard(dashboard_obj))

        except Exception as e:
            click.echo(f"❌ 看板生成失败: {e}", err=True)
