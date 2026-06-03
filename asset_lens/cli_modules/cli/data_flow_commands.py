import click
import pandas as pd


def register_data_flow_commands(cli: click.Group) -> None:
    @cli.command("north-flow")
    @click.option("--days", default=30, type=int, help="查看最近N天的北向资金")
    def north_flow(days: int):
        from rich.console import Console
        from rich.table import Table

        from asset_lens.utils.industry_flow import fetch_north_money_flow

        console = Console()
        console.print("\n📈 北向资金分析")
        console.print("=" * 60)

        try:
            df = fetch_north_money_flow(days=days)

            if df is None or df.empty:
                console.print("[yellow]⚠️ 无法获取北向资金数据[/yellow]")
                return

            data_source = df["data_source"].iloc[0] if "data_source" in df.columns else "历史数据"
            console.print(f"\n📊 最近 {len(df)} 天北向资金流向 (数据来源: {data_source})")

            table = Table()
            table.add_column("日期", style="cyan")
            table.add_column("净流入(亿)", justify="right")
            table.add_column("趋势", justify="center")

            total_inflow = 0
            for _, row in df.iterrows():
                net_inflow = row.get("north_net_inflow", 0)
                if net_inflow:
                    total_inflow += net_inflow
                    trend = "🟢 流出" if net_inflow < 0 else "🔴 流入"
                    table.add_row(
                        str(row.get("date", "")),
                        f"{net_inflow:.2f}",
                        trend,
                    )

            console.print(table)

            console.print("\n📊 汇总:")
            console.print(f"   总净流入: {total_inflow:.2f} 亿")
            if total_inflow > 0:
                console.print("   [red]整体趋势: 北向资金净流入[/red]")
            else:
                console.print("   [green]整体趋势: 北向资金净流出[/green]")

        except Exception as e:
            console.print(f"[red]❌ 获取北向资金数据失败: {e}[/red]")

    @cli.command("north-industry")
    @click.option("--save", is_flag=True, help="保存到数据库")
    @click.option("--history", "show_history", is_flag=True, help="显示历史数据")
    @click.option("--days", default=7, type=int, help="历史天数(默认7天)")
    @click.option("--trend", "industry_name", help="显示指定行业的趋势")
    @click.option("--skip-fetch", is_flag=True, help="跳过数据获取，只显示历史数据")
    @click.option("--force", is_flag=True, help="强制获取数据（即使在开市时间）")
    def north_industry(
        save: bool, show_history: bool, days: int, industry_name: str | None, skip_fetch: bool, force: bool
    ):
        from datetime import datetime, timedelta

        from rich.console import Console

        from asset_lens.db.database import db_manager
        from asset_lens.utils.industry_flow import fetch_north_flow_by_industry

        from .data_display import _display_industry_flow_table, _display_industry_trend

        console = Console()
        console.print("\n🏭 行业资金流向分析")
        console.print("=" * 60)

        try:
            if show_history:
                console.print(f"\n📊 显示最近 {days} 天的历史数据...")
                dates = db_manager.get_north_industry_flow_dates(days=days)

                if not dates:
                    console.print("[yellow]⚠️ 数据库中没有历史数据,请先使用 --save 保存数据[/yellow]")
                    return

                console.print(f"✅ 找到 {len(dates)} 天的历史数据")

                for date in dates[:5]:
                    flow_data = db_manager.get_north_industry_flow(date=date)
                    if flow_data:
                        _display_industry_flow_table(console, flow_data, date)

                if len(dates) > 5:
                    console.print(f"\n... 还有 {len(dates) - 5} 天的数据未显示")

                return

            if industry_name:
                console.print(f"\n📈 {industry_name} 行业流向趋势(最近{days}天)...")
                trend_data = db_manager.get_north_industry_flow_trend(industry=industry_name, days=days)

                if not trend_data:
                    console.print(f"[yellow]⚠️ 数据库中没有 {industry_name} 的历史数据[/yellow]")
                    return

                _display_industry_trend(console, trend_data, industry_name)
                return

            if skip_fetch:
                console.print("\n⏭️ 跳过数据获取，显示最近的历史数据...")
                dates = db_manager.get_north_industry_flow_dates(days=1)
                if dates:
                    flow_data = db_manager.get_north_industry_flow(date=dates[0])
                    if flow_data:
                        _display_industry_flow_table(console, flow_data, dates[0])
                    else:
                        console.print("[yellow]⚠️ 没有找到历史数据[/yellow]")
                else:
                    console.print("[yellow]⚠️ 数据库中没有历史数据[/yellow]")
                return

            df = fetch_north_flow_by_industry(force=force)

            if df.empty:
                console.print("\n[yellow]⚠️ 无法获取行业资金流向数据[/yellow]")
                console.print("\n[cyan]💡 建议使用以下替代方案：[/cyan]")
                console.print("   1. 查看历史数据: make north-industry-history")
                console.print("   2. 稍后重试")
                console.print("   3. 强制获取: make north-industry --force")
                return

            data_source = None
            if "data_source" in df.columns and not df.empty:
                data_source = df["data_source"].iloc[0] if len(df) > 0 else None

            if data_source:
                console.print(f"\n📊 行业资金流向分析 (数据来源: {data_source})")

                if "新浪" in str(data_source):
                    console.print("   [yellow]⚠️ 注意: 此数据为全市场行业涨跌代理，非北向资金数据[/yellow]")
                    console.print("   说明: 正值=行业上涨，负值=行业下跌，单位：亿元")
                elif "5日" in str(data_source):
                    console.print("   说明: 显示北向资金近5日在各行业的净流入变化，单位：亿元")
                    console.print("   计算: 5日净流入 = 今日持仓 - 5日前持仓")
                else:
                    console.print("   说明: 显示北向资金在各行业的持仓市值分布，单位：亿元")
            else:
                console.print("\n📊 行业资金流向分析")

            if save:
                date = datetime.now().strftime("%Y-%m-%d")
                industry_data = df.to_dict("records")
                result = db_manager.save_north_industry_flow(date, industry_data)

                if result["added"] > 0:
                    console.print(f"\n✅ 已保存 {result['added']} 条新数据到数据库")
                elif result["updated"] > 0:
                    console.print(f"\n✅ 已更新 {result['updated']} 条数据到数据库")
                else:
                    console.print("\n✅ 数据已是最新，无需保存")

                yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
                yesterday_data = db_manager.get_north_industry_flow(date=yesterday)

                if yesterday_data:
                    console.print(f"\n📈 行业流向变化分析 (对比 {yesterday}):")

                    yesterday_df = pd.DataFrame(yesterday_data)
                    merged = df.merge(
                        yesterday_df[["industry", "net_inflow"]], on="industry", suffixes=("", "_yesterday")
                    )

                    merged["flow_change"] = merged["net_inflow"] - merged["net_inflow_yesterday"]
                    merged["flow_change_pct"] = (
                        merged["flow_change"] / merged["net_inflow_yesterday"].abs() * 100
                    ).fillna(0)

                    inflow_increase = merged[merged["flow_change"] > 0.01].nlargest(5, "flow_change")
                    if not inflow_increase.empty:
                        console.print("\n   🔴 流入增加TOP5:")
                        for i, (_, row) in enumerate(inflow_increase.iterrows(), 1):
                            console.print(
                                f"      {i}. {row['industry']}: +{row['flow_change']:.2f}亿 ({row['flow_change_pct']:+.1f}%)"
                            )

                    outflow_increase = merged[merged["flow_change"] < -0.01].nsmallest(5, "flow_change")
                    if not outflow_increase.empty:
                        console.print("\n   🟢 流出增加TOP5:")
                        for i, (_, row) in enumerate(outflow_increase.iterrows(), 1):
                            console.print(
                                f"      {i}. {row['industry']}: {row['flow_change']:.2f}亿 ({row['flow_change_pct']:+.1f}%)"
                            )

                    if inflow_increase.empty and outflow_increase.empty:
                        max_change = merged["flow_change"].abs().max()
                        console.print(f"\n   💡 今日持仓变化很小 (最大变化: {max_change:.2f}亿)")
                        console.print("      这说明北向资金持仓相对稳定，没有明显的行业轮动")
                else:
                    console.print(f"\n💡 提示: 没有找到昨天({yesterday})的数据，明天可以看到流向变化")

            _display_industry_flow_table(console, df.to_dict("records"))

        except Exception as e:
            console.print(f"[red]❌ 分析失败: {e}[/red]")
            import traceback

            traceback.print_exc()
