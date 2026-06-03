import click

from .auto_trade_helpers import (
    _analyze_buy_signals,
    _analyze_sell_signals,
    _auto_screen_and_add_to_pool,
    _check_market_environment,
    _display_buy_signals,
    _display_position_advice,
    _display_sell_signals,
    _execute_buy_signals,
    _execute_sell_signals,
    _get_market_data,
)


def register_auto_trade_command(cli: click.Group) -> None:
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
        from datetime import datetime
        from pathlib import Path

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
                    from asset_lens.strategy.stock_ai_analyzer import ai_trading_advisor

                    ai_advisor = ai_trading_advisor
                    if ai_advisor.analyzer.enabled:
                        click.echo("✅ AI 分析器已加载")
                    else:
                        click.echo("⚠️ AI 分析器未配置 API Key，将仅使用策略信号")
                        ai_advisor = None
                except (ImportError, AttributeError) as e:
                    click.echo(f"⚠️ AI 分析器加载失败: {e}")
                    ai_advisor = None

            ml_predictor = None
            history_fetcher = None
            if use_ml:
                try:
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
                        except (ImportError, RuntimeError, OSError) as train_error:
                            click.echo(f"⚠️ ML 模型自动训练失败: {train_error}")
                except (ImportError, OSError, RuntimeError) as e:
                    click.echo(f"⚠️ ML 预测器加载失败: {e}")
                    ml_predictor = None

            click.echo("\n📊 市场环境分析...")
            market_ok, market_msg = _check_market_environment()
            click.echo(f"  {market_msg}")

            market_data = _get_market_data()

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
            pnl_emoji = "🔴" if unrealized_pnl >= 0 else "🟢"
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
            sell_signals = _analyze_sell_signals(
                holding_stocks, engine, strategy_name, ai_advisor, ml_predictor, history_fetcher, market_data
            )

            _display_sell_signals(sell_signals)

            if sell_signals and not dry_run:
                _execute_sell_signals(sell_signals, pool, max_sell, market_ok)

            click.echo("\n📊 分析买入信号...")

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
                except (ConnectionError, OSError, RuntimeError) as e:
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
                except (ConnectionError, OSError, RuntimeError) as fetch_error:
                    click.echo(f"❌ 获取市场数据失败: {fetch_error}")
                    return

            holding_codes = {s["code"] for s in holding_stocks}

            buy_signals = _analyze_buy_signals(
                watching_stocks, holding_codes, stocks_data, engine, strategy_name, ai_advisor, ml_predictor, history_fetcher, market_data
            )

            if buy_signals:
                _display_buy_signals(buy_signals, max_buy)

                if not dry_run and remaining_buy > 0 and remaining_position > 0 and market_ok:
                    _execute_buy_signals(buy_signals, pool, remaining_buy, remaining_position, max_amount)
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
            pnl_emoji = "🔴" if unrealized_pnl >= 0 else "🟢"
            click.echo(f"  浮盈浮亏: {pnl_emoji} ¥{unrealized_pnl:+,.2f} ({unrealized_pnl_pct:+.2f}%)")
            if dry_run:
                click.echo("  模式: 仅显示信号（未执行）")
            if use_ml and ml_predictor:
                click.echo("  🔮 ML 预测: 已启用")
            if use_ai and ai_advisor:
                click.echo("  🧠 AI 分析: 已启用")

            _display_position_advice(holding_stocks, total_position, max_position, unrealized_pnl, unrealized_pnl_pct, market_ok)

        except Exception as e:
            import traceback

            click.echo(f"❌ 自动交易失败: {e}", err=True)
            click.echo(traceback.format_exc(), err=True)
