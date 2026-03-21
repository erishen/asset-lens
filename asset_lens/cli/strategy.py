"""
Strategy CLI commands for asset-lens.
策略命令模块 - 包含 strategy, backtest, screen-stocks, filter-stocks, volume-breakout, momentum-screen, optimize-strategy
"""

from pathlib import Path
from typing import Optional

import click


def register_strategy_commands(cli: click.Group) -> None:
    """注册策略命令到 CLI 组"""
    
    @cli.command()
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    @click.option("--strategy-name", type=str, help="策略名称")
    def strategy(data_mode: Optional[str], strategy_name: Optional[str]):
        """运行投资策略"""
        from asset_lens.config import config

        if data_mode:
            config.data_mode = data_mode

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
    def backtest(strategy: str, start_date: Optional[str], end_date: Optional[str]):
        """运行策略回测"""
        click.echo("\n📊 策略回测")
        click.echo("=" * 60)

        try:
            from asset_lens.strategy.backtester import Backtester
            backtester = Backtester()
            
            click.echo(f"\n📈 回测配置:")
            click.echo(f"  策略: {strategy}")
            click.echo(f"  开始日期: {start_date or '默认'}")
            click.echo(f"  结束日期: {end_date or '默认'}")
            
            click.echo(f"\n💡 请使用 run_backtest() 方法执行回测")

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
            from asset_lens.strategy.engine import StrategyEngine
            from asset_lens.data.market_stock_fetcher import market_stock_fetcher
            
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
                    code = stock.get('code', stock.get('symbol', 'N/A'))
                    name = stock.get('name', 'N/A')
                    score = stock.get('score', 0)
                    click.echo(f"  {code} - {name} ({score:.2f})")

            click.echo(f"\n✅ 筛选完成！")

        except Exception as e:
            click.echo(f"❌ 筛选失败: {e}", err=True)

    @cli.command("filter-stocks")
    @click.option("--config-file", type=click.Path(), help="筛选配置文件路径")
    @click.option("--stocks-file", type=click.Path(), help="股票数据文件路径")
    @click.option("--fetch-market", is_flag=True, help="从市场获取股票列表")
    @click.option("--max-pages", type=int, default=5, help="获取市场股票的最大页数")
    def filter_stocks(config_file: Optional[str], stocks_file: Optional[str], fetch_market: bool, max_pages: int):
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

            click.echo(f"\n✅ 筛选完成！")

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
                    code = stock.get('code', 'N/A')
                    name = stock.get('name', 'N/A')
                    volume_ratio = stock.get('volume_ratio', 0)
                    click.echo(f"  {code} - {name} (成交量比率: {volume_ratio:.2f})")

            click.echo(f"\n✅ 筛选完成！")

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
            from asset_lens.strategy.engine import StrategyEngine
            from asset_lens.data.market_stock_fetcher import market_stock_fetcher
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
                    code = stock.get('code', stock.get('symbol', 'N/A'))
                    name = stock.get('name', 'N/A')
                    score = stock.get('strategy_score', stock.get('score', 0))
                    click.echo(f"  {code} - {name} (得分: {score:.2f})")

                if add_to_pool:
                    click.echo("\n📦 正在添加到股票池...")
                    pool = StockPool()
                    added = 0
                    skipped = 1
                    for stock in result[:limit]:
                        code = stock.get('code', stock.get('symbol', ''))
                        name = stock.get('name', '')
                        score = stock.get('strategy_score', stock.get('score', 0))
                        if code:
                            success, msg = pool.add_stock(
                                code=code,
                                name=name,
                                price=0.0,
                                status="watching",
                                notes=f"动量策略选入，得分: {score:.2f}"
                            )
                            if success:
                                click.echo(f"✅ {msg}")
                                added += 1
                            else:
                                click.echo(f"⏭️ {msg}")
                                skipped += 1
                    click.echo(f"\n📊 统计: 新增 {added} 只，跳过 {skipped} 只")

            click.echo(f"\n✅ 筛选完成！")

        except Exception as e:
            click.echo(f"❌ 筛选失败: {e}", err=True)

    @cli.command()
    @click.option("--data-mode", type=click.Choice(["sample", "real"]), help="数据模式")
    def optimize_strategy(data_mode: Optional[str]):
        """优化策略参数"""
        from asset_lens.config import config

        if data_mode:
            config.data_mode = data_mode

        click.echo("\n📊 策略优化")
        click.echo("=" * 60)

        try:
            from asset_lens.strategy.engine import StrategyEngine
            engine = StrategyEngine()
            
            click.echo("\n📈 可用优化方法:")
            click.echo("  - optimize_strategy_params(): 参数优化")
            click.echo("  - combine_strategies(): 策略组合")
            
            click.echo(f"\n✅ 策略引擎已加载！")
        except Exception as e:
            click.echo(f"❌ 优化失败: {e}", err=True)

    
    @cli.command("auto-trade")
    @click.option("--strategy-name", type=click.Choice(["value", "momentum", "reversal"]), default="momentum", help="策略名称")
    @click.option("--max-buy", type=int, default=5, help="单次最大买入数量")
    @click.option("--max-sell", type=int, default=10, help="单次最大卖出数量")
    @click.option("--dry-run", is_flag=True, help="仅显示信号，不执行交易")
    @click.option("--max-daily-buy", type=int, default=5, help="每日最大买入数量")
    @click.option("--max-amount", type=float, default=10000, help="单只股票最大买入金额")
    @click.option("--max-position", type=float, default=100000, help="总持仓金额上限")
    @click.option("--max-industry", type=int, default=2, help="每个行业最大持仓数量")
    @click.option("--auto-screen", is_flag=True, default=True, help="股票池为空时自动选股入池")
    @click.option("--use-ai", is_flag=True, default=False, help="启用 AI 分析辅助决策")
    def auto_trade(strategy_name: str, max_buy: int, max_sell: int, dry_run: bool, 
                   max_daily_buy: int, max_amount: float, max_position: float, max_industry: int,
                   auto_screen: bool, use_ai: bool):
        """自动交易 - 根据策略信号自动买入卖出（增强版，支持 AI 分析）"""
        from rich.console import Console
        from rich.table import Table
        from asset_lens.trading.stock_pool import StockPool
        from asset_lens.data.market_stock_fetcher import market_stock_fetcher
        from asset_lens.strategy.engine import StrategyEngine
        from datetime import datetime
        
        click.echo(f"\n🤖 自动交易系统 v3.0 ({strategy_name}策略)")
        if use_ai:
            click.echo("🧠 AI 分析已启用")
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
            
            click.echo("\n📊 市场环境分析...")
            market_ok, market_msg = _check_market_environment()
            click.echo(f"  {market_msg}")
            
            market_data = None
            try:
                from asset_lens.data.enhanced_market_data_fetcher import enhanced_market_data_fetcher
                result = enhanced_market_data_fetcher.fetch_all_domestic_indexes()
                if result and "指数数据" in result:
                    for name, data in result["指数数据"].items():
                        if "上证" in name:
                            change = data.get("涨跌幅", 0)
                            if isinstance(change, str):
                                change = float(change.replace("%", ""))
                            market_data = {
                                "index_name": name,
                                "index_change": change,
                                "sentiment": "乐观" if change > 1 else ("悲观" if change < -1 else "中性")
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
            today_bought = [s for s in holding_stocks if s.get('buy_date') == today]
            click.echo(f"  今日已买入: {len(today_bought)}")
            
            total_position = sum(s.get('buy_price', 0) * s.get('shares', 100) for s in holding_stocks)
            click.echo(f"  总持仓金额: ¥{total_position:,.2f}")
            
            remaining_buy = max(0, max_daily_buy - len(today_bought))
            remaining_position = max(0, max_position - total_position)
            click.echo(f"  今日剩余可买: {remaining_buy} 只")
            click.echo(f"  剩余仓位: ¥{remaining_position:,.2f}")
            
            for s in holding_stocks[:5]:
                buy_price = s.get('buy_price', 0)
                current_price = s.get('current_price', buy_price)
                profit_rate = ((current_price - buy_price) / buy_price * 100) if buy_price > 0 else 0
                click.echo(f"  {s['code']} - {s['name']} (买入价: {buy_price:.2f}, 收益率: {profit_rate:+.2f}%)")
            
            if remaining_buy <= 0 and not dry_run:
                click.echo("\n⚠️ 今日买入数量已达上限，跳过买入操作")
            
            if remaining_position <= 0 and not dry_run:
                click.echo("\n⚠️ 总仓位已达上限，跳过买入操作")
            
            click.echo("\n📈 分析卖出信号...")
            sell_signals = []
            for stock in holding_stocks:
                buy_price = stock.get('buy_price', 0)
                current_price = stock.get('current_price', buy_price)
                profit_rate = ((current_price - buy_price) / buy_price * 100) if buy_price > 0 else 0
                buy_date = stock.get('buy_date', '')
                holding_days = 0
                if buy_date:
                    try:
                        buy_dt = datetime.strptime(buy_date, "%Y-%m-%d")
                        holding_days = (datetime.now() - buy_dt).days
                    except Exception:
                        pass
                
                strategy_sell = False
                strategy_reason = ""
                
                evaluation = engine.evaluate_stock(
                    {
                        "code": stock["code"],
                        "name": stock["name"],
                        "current_price": current_price,
                        "profit_rate": profit_rate,
                        "change_percent": stock.get("change_percent", 0),
                    },
                    strategy_name
                )
                
                for detail in evaluation.get("details", []):
                    if detail.get("matched") and detail.get("condition") in ["止损", "止盈", "趋势破坏"]:
                        strategy_sell = True
                        strategy_reason = detail.get("condition", "") + ": " + detail.get("expected", "")
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
                
                should_sell = strategy_sell
                final_reason = strategy_reason
                
                if ai_decision:
                    if ai_decision.get("action") == "sell":
                        should_sell = True
                        if strategy_reason:
                            final_reason = f"{strategy_reason} + AI确认卖出"
                        else:
                            final_reason = ai_decision.get("reason", "AI建议卖出")
                    elif ai_decision.get("action") == "hold" and strategy_sell:
                        final_reason = f"{strategy_reason} (AI建议持有观望)"
                
                if should_sell:
                    sell_signals.append({
                        "code": stock["code"],
                        "name": stock["name"],
                        "current_price": current_price,
                        "buy_price": buy_price,
                        "profit_rate": profit_rate,
                        "holding_days": holding_days,
                        "score": evaluation["score"],
                        "reason": final_reason,
                        "ai_confidence": ai_decision.get("ai_confidence", 0) if ai_decision else 0,
                    })
            
            if sell_signals:
                click.echo(f"\n📉 卖出信号 ({len(sell_signals)}):")
                for signal in sell_signals:
                    click.echo(f"  {signal['code']} - {signal['name']}")
                    click.echo(f"    收益率: {signal['profit_rate']:+.2f}%, 持仓: {signal['holding_days']}天")
                    click.echo(f"    理由: {signal['reason']}")
                    if signal['ai_confidence'] > 0:
                        click.echo(f"    AI信心: {signal['ai_confidence']:.0f}%")
                
                if not dry_run:
                    click.echo("\n💰 执行卖出操作...")
                    for signal in sell_signals[:max_sell]:
                        success, msg = pool.sell_stock(
                            code=signal["code"],
                            price=signal["current_price"],
                            notes=f"自动卖出: {signal['reason']}"
                        )
                        if success:
                            click.echo(f"✅ {msg}")
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
                click.echo("⚠️ 无股票数据缓存，请先运行 make momentum-screen-pool")
                return
            
            holding_codes = {s["code"] for s in holding_stocks}
            industry_count = {}
            
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
                    
                    final_action = "buy"
                    final_reason = strategy_reason
                    
                    if ai_decision:
                        if ai_decision.get("action") == "wait":
                            final_action = "wait"
                            final_reason = ai_decision.get("reason", "AI建议观望")
                        elif ai_decision.get("action") == "skip":
                            final_action = "skip"
                            final_reason = ai_decision.get("reason", "AI不建议买入")
                        elif ai_decision.get("action") == "buy":
                            final_reason = f"{strategy_reason} + AI确认"
                    
                    if final_action == "buy":
                        buy_signals.append({
                            "code": stock["code"],
                            "name": stock["name"],
                            "current_price": current_price,
                            "change_percent": stock_data.get("change_percent", 0),
                            "turnover_rate": stock_data.get("turnover_rate", 0),
                            "market_cap": market_cap,
                            "score": evaluation["score"],
                            "reason": final_reason,
                            "ai_confidence": ai_decision.get("ai_confidence", 0) if ai_decision else 0,
                            "risk_level": ai_decision.get("risk_level", "medium") if ai_decision else "medium",
                            "suggested_stop_loss": ai_decision.get("suggested_stop_loss") if ai_decision else None,
                            "suggested_take_profit": ai_decision.get("suggested_take_profit") if ai_decision else None,
                        })
            
            buy_signals.sort(key=lambda x: (x["score"], x["ai_confidence"]), reverse=True)
            
            if buy_signals:
                click.echo(f"\n📈 买入信号 ({len(buy_signals)}):")
                for signal in buy_signals[:max_buy]:
                    click.echo(f"  {signal['code']} - {signal['name']} (得分: {signal['score']:.0f})")
                    click.echo(f"    当前价: {signal['current_price']:.2f}, 涨幅: {signal['change_percent']:+.2f}%, 换手: {signal['turnover_rate']:.2f}%")
                    click.echo(f"    市值: {signal['market_cap']:.1f}亿, 风险: {signal['risk_level']}")
                    click.echo(f"    理由: {signal['reason']}")
                    if signal['ai_confidence'] > 0:
                        click.echo(f"    AI信心: {signal['ai_confidence']:.0f}%")
                    if signal.get('suggested_stop_loss'):
                        click.echo(f"    建议止损: {signal['suggested_stop_loss']:.2f}")
                    if signal.get('suggested_take_profit'):
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
                        if signal.get('suggested_stop_loss'):
                            notes += f", 止损: {signal['suggested_stop_loss']:.2f}"
                        if signal.get('suggested_take_profit'):
                            notes += f", 止盈: {signal['suggested_take_profit']:.2f}"
                        
                        success, msg = pool.buy_stock(
                            code=signal["code"],
                            price=price,
                            shares=shares,
                            notes=notes
                        )
                        if success:
                            click.echo(f"✅ {msg}")
                            bought += 1
                            total_amount += amount
                        else:
                            click.echo(f"⏭️ {msg}")
                    
                    click.echo(f"\n💰 买入统计: {bought} 只股票，总金额: ¥{total_amount:,.2f}")
                elif not market_ok:
                    click.echo(f"\n⚠️ 市场环境不佳，跳过买入操作")
            else:
                click.echo("\n📈 无买入信号")
            
            click.echo(f"\n📊 交易汇总")
            click.echo(f"  买入信号: {len(buy_signals)}")
            click.echo(f"  卖出信号: {len(sell_signals)}")
            click.echo(f"  今日已买入: {len(today_bought)}")
            click.echo(f"  总持仓金额: ¥{total_position:,.2f}")
            if dry_run:
                click.echo(f"  模式: 仅显示信号（未执行）")
            if use_ai and ai_advisor:
                click.echo(f"  AI 分析: 已启用")
            
        except Exception as e:
            import traceback
            click.echo(f"❌ 自动交易失败: {e}", err=True)
            click.echo(traceback.format_exc(), err=True)


def _auto_screen_and_add_to_pool(pool, strategy_name: str, max_stocks: int = 50) -> int:
    """自动选股并添加到股票池"""
    from asset_lens.data.market_stock_fetcher import market_stock_fetcher
    from asset_lens.strategy.engine import StrategyEngine
    
    try:
        click.echo(f"  正在执行 {strategy_name} 策略选股...")
        
        stocks_data = market_stock_fetcher.get_cached_market_stocks()
        if not stocks_data:
            click.echo("  ⚠️ 无股票数据缓存，请先运行 make momentum-screen-pool")
            return 0
        
        engine = StrategyEngine()
        result = engine.screen_stocks(stocks=stocks_data, strategy_name=strategy_name, min_score=60.0)
        
        if not result:
            click.echo("  ⚠️ 未筛选到符合条件的股票")
            return 0
        
        added = 0
        for stock in result[:max_stocks]:
            code = stock.get('code', '')
            name = stock.get('name', '')
            score = stock.get('strategy_score', stock.get('score', 0))
            
            if code:
                success, msg = pool.add_stock(
                    code=code,
                    name=name,
                    price=stock.get('current_price', 0),
                    status="watching",
                    notes=f"自动选股入池，得分: {score:.0f}"
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
