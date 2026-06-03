from pathlib import Path

import click


def register_enhanced_commands(cli: click.Group) -> None:
    @cli.command("ai-qa")
    @click.option("--question", "-q", type=str, help="投资问题")
    @click.option("--interactive", "-i", is_flag=True, help="交互模式")
    def ai_qa(question: str | None, interactive: bool):
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

    @cli.command("ml-retrain")
    @click.option("--force", is_flag=True, help="强制重训练")
    def ml_retrain(force: bool):
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
