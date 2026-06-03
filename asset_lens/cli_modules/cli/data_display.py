import pandas as pd
from rich.table import Table


def _display_industry_flow_table(console, flow_data: list, date: str | None = None):
    df = pd.DataFrame(flow_data) if not isinstance(flow_data, pd.DataFrame) else flow_data

    if date:
        console.print(f"\n📅 {date}")

    inflow_df = df[df["net_inflow"] > 0].head(10)
    outflow_df = df[df["net_inflow"] < 0].head(10)

    data_source = df["data_source"].iloc[0] if "data_source" in df.columns else ""
    is_flow_change = "5日" in data_source
    is_sina = "新浪" in data_source

    if not inflow_df.empty:
        if is_sina:
            title = "\n🔴 行业上涨TOP10（成交额·亿）"
            col_name = "成交额(亿)"
        elif is_flow_change:
            title = "\n🔴 5日净流入TOP10"
            col_name = "净流入(亿)"
        else:
            title = "\n🔴 持仓市值TOP10"
            col_name = "持仓市值(亿)"

        inflow_table = Table(title=title, show_header=True, header_style="bold red")
        inflow_table.add_column("排名", style="cyan", width=6)
        inflow_table.add_column("行业", style="white", width=20)
        inflow_table.add_column(col_name, justify="right", style="red", width=12)
        inflow_table.add_column("变化率", justify="right", style="yellow", width=10)

        for i, (_, row) in enumerate(inflow_df.iterrows(), 1):
            change_rate = row["change_rate"]
            if abs(change_rate) >= 1000:
                change_rate_str = f"{change_rate:+.0f}%"
            elif abs(change_rate) >= 100:
                change_rate_str = f"{change_rate:+.1f}%"
            else:
                change_rate_str = f"{change_rate:+.2f}%"

            inflow_table.add_row(str(i), row["industry"], f"+{row['net_inflow']:.2f}", change_rate_str)

        console.print(inflow_table)

    if not outflow_df.empty:
        if is_sina:
            title = "\n🟢 行业下跌TOP10（成交额·亿）"
            col_name = "成交额(亿)"
        elif is_flow_change:
            title = "\n🟢 5日净流出TOP10"
            col_name = "净流出(亿)"
        else:
            title = "\n🟢 持仓较少行业"
            col_name = "持仓市值(亿)"

        outflow_table = Table(title=title, show_header=True, header_style="bold green")
        outflow_table.add_column("排名", style="cyan", width=6)
        outflow_table.add_column("行业", style="white", width=20)
        outflow_table.add_column(col_name, justify="right", style="green", width=12)
        outflow_table.add_column("变化率", justify="right", style="yellow", width=10)

        for i, (_, row) in enumerate(outflow_df.iterrows(), 1):
            change_rate = row["change_rate"]
            if abs(change_rate) >= 1000:
                change_rate_str = f"{change_rate:+.0f}%"
            elif abs(change_rate) >= 100:
                change_rate_str = f"{change_rate:+.1f}%"
            else:
                change_rate_str = f"{change_rate:+.2f}%"

            outflow_table.add_row(str(i), row["industry"], f"{row['net_inflow']:.2f}", change_rate_str)

        console.print(outflow_table)

    total_inflow = df[df["net_inflow"] > 0]["net_inflow"].sum()
    total_outflow = df[df["net_inflow"] < 0]["net_inflow"].sum()
    net_total = total_inflow + total_outflow

    console.print("\n📊 汇总统计:")

    if is_sina:
        console.print(f"   行业数量: {len(df)} 个")
        console.print(f"   上涨行业: {len(inflow_df)} 个")
        console.print(f"   下跌行业: {len(outflow_df)} 个")
        console.print(f"   上涨成交额: {total_inflow:.2f} 亿")
        console.print(f"   下跌成交额: {abs(total_outflow):.2f} 亿")
    elif is_flow_change:
        console.print(f"   净流入行业数: {len(inflow_df)} 个")
        console.print(f"   净流出行业数: {len(outflow_df)} 个")
        console.print(f"   总净流入: {total_inflow:.2f} 亿")
        console.print(f"   总净流出: {total_outflow:.2f} 亿")
        console.print(f"   净流入合计: {net_total:.2f} 亿")
    else:
        console.print(f"   行业数量: {len(df)} 个")
        console.print(f"   总持仓市值: {net_total:.2f} 亿")

        if len(inflow_df) > 0:
            top1 = inflow_df.iloc[0]
            top1_ratio = (top1["net_inflow"] / net_total * 100) if net_total > 0 else 0
            console.print(f"   第一大行业: {top1['industry']} ({top1_ratio:.1f}%)")

    console.print("\n💡 分析建议:")
    if not inflow_df.empty:
        top_inflow = inflow_df.iloc[0]
        if is_sina:
            console.print(
                f"   🔴 今日最强行业: {top_inflow['industry']} (成交额 {top_inflow['net_inflow']:.2f} 亿, 涨幅 {top_inflow['change_rate']:+.2f}%)"
            )
        elif is_flow_change:
            console.print(f"   🔴 5日净流入最多: {top_inflow['industry']} (净流入 {top_inflow['net_inflow']:.2f} 亿)")
        else:
            console.print(f"   🔴 北向资金重仓: {top_inflow['industry']} (持仓 {top_inflow['net_inflow']:.2f} 亿)")

        if not is_flow_change and not is_sina and len(inflow_df) >= 3:
            console.print("\n   📈 北向资金持仓TOP3:")
            for i, (_, row) in enumerate(inflow_df.head(3).iterrows(), 1):
                ratio = (row["net_inflow"] / net_total * 100) if net_total > 0 else 0
                console.print(f"      {i}. {row['industry']}: {row['net_inflow']:.2f}亿 ({ratio:.1f}%)")

    if is_flow_change and not outflow_df.empty:
        top_outflow = outflow_df.iloc[0]
        console.print(
            f"   🟢 5日净流出最多: {top_outflow['industry']} (净流出 {abs(top_outflow['net_inflow']):.2f} 亿)"
        )

    if is_sina and not outflow_df.empty:
        top_outflow = outflow_df.iloc[0]
        console.print(
            f"   🟢 今日最弱行业: {top_outflow['industry']} (成交额 {abs(top_outflow['net_inflow']):.2f} 亿, 跌幅 {top_outflow['change_rate']:+.2f}%)"
        )


def _display_industry_trend(console, trend_data: list, industry_name: str):
    if not trend_data:
        return

    table = Table(title=f"\n📈 {industry_name} 行业流向趋势", show_header=True, header_style="bold magenta")
    table.add_column("日期", style="cyan", width=12)
    table.add_column("净流入(亿)", justify="right", width=12)
    table.add_column("变化率", justify="right", width=10)
    table.add_column("趋势", justify="center", width=8)

    prev_inflow = None
    for data in trend_data:
        net_inflow = data["net_inflow"]
        change_rate = data["change_rate"]

        if prev_inflow is not None:
            if net_inflow > prev_inflow:
                trend = "📈 上升"
            elif net_inflow < prev_inflow:
                trend = "📉 下降"
            else:
                trend = "➡️ 持平"
        else:
            trend = "-"

        table.add_row(data["date"], f"{net_inflow:+.2f}", f"{change_rate:+.2f}%", trend)
        prev_inflow = net_inflow

    console.print(table)

    avg_inflow = sum(d["net_inflow"] for d in trend_data) / len(trend_data)
    console.print("\n📊 统计:")
    console.print(f"   平均净流入: {avg_inflow:+.2f} 亿")
    console.print(f"   数据天数: {len(trend_data)} 天")

    if avg_inflow > 0:
        console.print(f"   💡 结论: 北向资金整体看好 {industry_name} 行业")
    else:
        console.print(f"   💡 结论: 北向资金整体看空 {industry_name} 行业")
