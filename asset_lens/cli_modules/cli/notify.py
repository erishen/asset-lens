"""
Notification CLI commands for asset-lens.
通知命令
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


@click.group()
def notify():
    """通知管理命令"""
    pass


@notify.command()
def status():
    """显示通知服务状态"""
    from asset_lens.notification.enhanced_notification import enhanced_notification_service

    config = enhanced_notification_service.config

    console.print(
        Panel.fit("[bold cyan]通知服务状态[/bold cyan]", subtitle=f"启用: {'✅' if config.enabled else '❌'}")
    )

    channels_table = Table(title="通知渠道配置")
    channels_table.add_column("渠道", style="cyan")
    channels_table.add_column("状态", style="green")
    channels_table.add_column("配置", style="yellow")

    channels = [
        (
            "钉钉",
            bool(config.dingtalk_webhook),
            "Webhook + Secret" if config.dingtalk_secret else "Webhook" if config.dingtalk_webhook else "未配置",
        ),
        ("企业微信", bool(config.wecom_webhook), "Webhook" if config.wecom_webhook else "未配置"),
        (
            "Telegram",
            bool(config.telegram_bot_token and config.telegram_chat_id),
            "Bot Token + Chat ID" if config.telegram_bot_token else "未配置",
        ),
        (
            "飞书",
            bool(config.feishu_webhook),
            "Webhook + Secret" if config.feishu_secret else "Webhook" if config.feishu_webhook else "未配置",
        ),
        ("Server酱", bool(config.serverchan_key), "Key 已配置" if config.serverchan_key else "未配置"),
        ("邮件", bool(config.email_username), f"{config.email_username}" if config.email_username else "未配置"),
    ]

    for name, enabled, config_info in channels:
        status = "✅ 已配置" if enabled else "❌ 未配置"
        channels_table.add_row(name, status, config_info)

    console.print(channels_table)

    console.print(f"\n[dim]默认渠道: {', '.join(config.default_channels)}[/dim]")
    console.print(f"[dim]冷却时间: {config.cooldown_minutes} 分钟[/dim]")


@notify.command()
@click.argument("title")
@click.argument("content")
@click.option("--channel", "-c", multiple=True, help="通知渠道 (可多次指定)")
def send(title, content, channel):
    """发送通知

    示例:
        asset-lens notify send "测试标题" "测试内容"
        asset-lens notify send "预警" "价格异常" -c dingtalk -c telegram
    """
    from asset_lens.notification.enhanced_notification import EnhancedNotificationMessage, enhanced_notification_service

    channels = list(channel) if channel else None

    message = EnhancedNotificationMessage(
        title=title,
        content=content,
        level="info",
    )

    console.print("[bold blue]📤 发送通知...[/bold blue]")

    results = enhanced_notification_service.send(message, channels, skip_cooldown=True)

    if results:
        result_table = Table(title="发送结果")
        result_table.add_column("渠道", style="cyan")
        result_table.add_column("状态", style="green")

        for ch, success in results.items():
            status = "✅ 成功" if success else "❌ 失败"
            result_table.add_row(ch, status)

        console.print(result_table)
    else:
        console.print("[yellow]没有发送任何通知[/yellow]")


@notify.command()
@click.argument("channel")
def test(channel):
    """测试通知渠道

    示例:
        asset-lens notify test dingtalk
        asset-lens notify test telegram
    """
    from asset_lens.notification.enhanced_notification import enhanced_notification_service

    console.print(f"[bold blue]🧪 测试通知渠道: {channel}[/bold blue]")

    success = enhanced_notification_service.test_channel(channel)

    if success:
        console.print(f"[green]✅ {channel} 通知测试成功！[/green]")
    else:
        console.print(f"[red]❌ {channel} 通知测试失败，请检查配置[/red]")


@notify.command()
@click.option("--hours", default=24, help="显示最近N小时的历史")
def history(hours):
    """显示通知历史"""
    from asset_lens.notification.enhanced_notification import enhanced_notification_service

    records = enhanced_notification_service.get_history(hours)

    if not records:
        console.print(f"[yellow]最近 {hours} 小时内没有通知记录[/yellow]")
        return

    console.print(f"[bold blue]📋 最近 {hours} 小时通知历史[/bold blue]")

    table = Table()
    table.add_column("时间", style="dim")
    table.add_column("标题", style="cyan")
    table.add_column("级别", style="yellow")
    table.add_column("渠道", style="green")
    table.add_column("结果", style="white")

    for record in records[-20:]:
        channels = ", ".join(record.get("channels", []))
        results = record.get("results", {})
        success_count = sum(1 for v in results.values() if v)
        total_count = len(results)
        result_str = f"{success_count}/{total_count} 成功"

        table.add_row(
            record.get("timestamp", ""),
            record.get("title", "")[:30],
            record.get("level", ""),
            channels,
            result_str,
        )

    console.print(table)


@notify.command()
@click.argument("alert_type")
@click.argument("message")
@click.option("--level", default="warning", help="预警级别 (info/warning/danger/critical)")
@click.option("--suggestion", default="", help="建议")
@click.option("--channel", "-c", multiple=True, help="通知渠道")
def alert(alert_type, message, level, suggestion, channel):
    """发送风险预警通知

    示例:
        asset-lens notify alert "止损预警" "股票A触及止损线" --level danger
    """
    from asset_lens.notification.enhanced_notification import enhanced_notification_service

    channels = list(channel) if channel else None

    console.print("[bold yellow]⚠️ 发送风险预警...[/bold yellow]")

    results = enhanced_notification_service.notify_risk_alert(
        alert_type=alert_type,
        level=level,
        message=message,
        suggestion=suggestion,
        channels=channels,
    )

    if results:
        success = all(results.values())
        if success:
            console.print("[green]✅ 预警通知发送成功[/green]")
        else:
            failed = [k for k, v in results.items() if not v]
            console.print(f"[yellow]⚠️ 部分渠道发送失败: {', '.join(failed)}[/yellow]")


def register_notify_commands(cli: click.Group) -> None:
    """注册通知命令到 CLI 组"""
    cli.add_command(notify)
