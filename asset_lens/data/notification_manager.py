"""
Notification system for asset-lens.
通知系统 - 邮件和微信通知

功能:
1. 邮件通知
2. 微信通知（通过 Server酱）
3. 通知模板管理
"""

import json
import smtplib
from dataclasses import dataclass
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from ..config import config


@dataclass
class NotificationConfig:
    """通知配置"""

    email_enabled: bool = False
    email_smtp_server: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_recipients: list[str] | None = None

    wechat_enabled: bool = False
    wechat_server_key: str = ""

    def __post_init__(self):
        if self.email_recipients is None:
            self.email_recipients = []


class NotificationManager:
    """通知管理器"""

    def __init__(self):
        self.config = self._load_config()
        self.template_path = config.cache_path / "notification_templates"
        self.template_path.mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> NotificationConfig:
        """加载通知配置"""
        config_path = config.project_root / "config"
        config_file = config_path / "notification.json"

        if config_file.exists():
            try:
                with open(config_file, encoding="utf-8") as f:
                    data = json.load(f)
                return NotificationConfig(**data)
            except (ValueError, KeyError, TypeError):
                pass

        return NotificationConfig()

    def send_email(
        self,
        subject: str,
        content: str,
        html_content: str | None = None,
        recipients: list[str] | None = None,
    ) -> bool:
        """
        发送邮件通知

        Args:
            subject: 邮件主题
            content: 邮件内容
            html_content: HTML 内容
            recipients: 收件人列表

        Returns:
            是否发送成功
        """
        if not self.config.email_enabled:
            print("邮件通知未启用")
            return False

        if recipients is None:
            recipients = self.config.email_recipients

        if not recipients:
            print("没有配置收件人")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[Asset Lens] {subject}"
            msg["From"] = self.config.email_username
            msg["To"] = ", ".join(recipients)

            msg.attach(MIMEText(content, "plain", "utf-8"))

            if html_content:
                msg.attach(MIMEText(html_content, "html", "utf-8"))

            with smtplib.SMTP(
                self.config.email_smtp_server,
                self.config.email_smtp_port,
            ) as server:
                server.starttls()
                server.login(
                    self.config.email_username,
                    self.config.email_password,
                )
                server.sendmail(
                    self.config.email_username,
                    recipients,
                    msg.as_string(),
                )

            print(f"✅ 邮件发送成功: {subject}")
            return True

        except Exception as e:
            print(f"❌ 邮件发送失败: {e}")
            return False

    def send_wechat(
        self,
        title: str,
        content: str,
    ) -> bool:
        """
        发送微信通知（通过 Server酱）

        Args:
            title: 标题
            content: 内容

        Returns:
            是否发送成功
        """
        if not self.config.wechat_enabled:
            print("微信通知未启用")
            return False

        if not self.config.wechat_server_key:
            print("没有配置 Server酱 Key")
            return False

        try:
            import requests  # type: ignore[import-untyped]

            url = f"https://sctapi.ftqq.com/{self.config.wechat_server_key}.send"
            data = {
                "title": f"[Asset Lens] {title}",
                "desp": content,
            }

            response = requests.post(url, data=data, timeout=10)
            result = response.json()

            if result.get("code") == 0:
                print(f"✅ 微信通知发送成功: {title}")
                return True
            else:
                print(f"❌ 微信通知发送失败: {result.get('message', 'Unknown error')}")
                return False

        except Exception as e:
            print(f"❌ 微信通知发送失败: {e}")
            return False

    def send_notification(
        self,
        title: str,
        content: str,
        html_content: str | None = None,
        channels: list[str] | None = None,
    ) -> dict[str, bool]:
        """
        发送通知（支持多渠道）

        Args:
            title: 标题
            content: 内容
            html_content: HTML 内容
            channels: 通知渠道列表 (email, wechat)

        Returns:
            各渠道发送结果
        """
        if channels is None:
            channels = ["email", "wechat"]

        results = {}

        if "email" in channels:
            results["email"] = self.send_email(title, content, html_content)

        if "wechat" in channels:
            results["wechat"] = self.send_wechat(title, content)

        return results

    def notify_daily_report(self, report_data: dict[str, Any]) -> dict[str, bool]:
        """发送每日报告通知"""
        subject = f"每日投资报告 - {datetime.now().strftime('%Y-%m-%d')}"

        content = self._format_daily_report_text(report_data)
        html_content = self._format_daily_report_html(report_data)

        return self.send_notification(subject, content, html_content)

    def notify_risk_alert(self, alert_data: dict[str, Any]) -> dict[str, bool]:
        """发送风险预警通知"""
        subject = f"⚠️ 风险预警 - {alert_data.get('type', 'Unknown')}"

        content = f"""
风险预警

类型: {alert_data.get("type", "Unknown")}
等级: {alert_data.get("level", "Unknown")}
时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

详情:
{alert_data.get("message", "")}

建议:
{alert_data.get("recommendation", "")}
"""

        return self.send_notification(subject, content)

    def notify_trade_signal(self, signal_data: dict[str, Any]) -> dict[str, bool]:
        """发送交易信号通知"""
        subject = f"📊 交易信号 - {signal_data.get('code', '')}"

        content = f"""
交易信号

股票: {signal_data.get("name", "")} ({signal_data.get("code", "")})
信号类型: {signal_data.get("signal_type", "")}
价格: {signal_data.get("price", 0):.2f}
时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

原因:
{signal_data.get("reason", "")}
"""

        return self.send_notification(subject, content)

    def _format_daily_report_text(self, data: dict[str, Any]) -> str:
        """格式化每日报告文本"""
        lines = [
            "📊 每日投资报告",
            f"日期: {datetime.now().strftime('%Y-%m-%d')}",
            "",
            "=== 概览 ===",
            f"总资产: ¥{data.get('total_assets', 0):,.2f}",
            f"总收益: ¥{data.get('total_profit', 0):,.2f}",
            f"收益率: {data.get('total_return', 0):.2%}",
            "",
            "=== 持仓 ===",
        ]

        lines.extend(
            f"  {position.get('name', '')} ({position.get('code', '')}): {position.get('profit_rate', 0):.2%}"
            for position in data.get("positions", [])[:10]
        )

        return "\n".join(lines)

    def _format_daily_report_html(self, data: dict[str, Any]) -> str:
        """格式化每日报告 HTML"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .header {{ background: #667eea; color: white; padding: 20px; }}
        .content {{ padding: 20px; }}
        .metric {{ display: inline-block; margin: 10px; padding: 15px; background: #f5f5f5; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 10px; border: 1px solid #ddd; text-align: left; }}
        th {{ background: #f5f5f5; }}
        .positive {{ color: green; }}
        .negative {{ color: red; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 每日投资报告</h1>
        <p>日期: {datetime.now().strftime("%Y-%m-%d")}</p>
    </div>
    <div class="content">
        <h2>概览</h2>
        <div class="metric">
            <strong>总资产</strong><br>
            ¥{data.get("total_assets", 0):,.2f}
        </div>
        <div class="metric">
            <strong>总收益</strong><br>
            ¥{data.get("total_profit", 0):,.2f}
        </div>
        <div class="metric">
            <strong>收益率</strong><br>
            {data.get("total_return", 0):.2%}
        </div>
        <h2>持仓</h2>
        <table>
            <tr>
                <th>名称</th>
                <th>代码</th>
                <th>收益率</th>
            </tr>
"""

        for position in data.get("positions", [])[:10]:
            profit_rate = position.get("profit_rate", 0)
            rate_class = "positive" if profit_rate >= 0 else "negative"
            html += f"""
            <tr>
                <td>{position.get("name", "")}</td>
                <td>{position.get("code", "")}</td>
                <td class="{rate_class}">{profit_rate:.2%}</td>
            </tr>
"""

        html += """
        </table>
    </div>
</body>
</html>
"""
        return html


notification_manager = NotificationManager()
