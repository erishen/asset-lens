"""
Report Routes - 报告导出相关 API
"""

from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import Response

router = APIRouter(prefix="/api/report", tags=["report"])


@router.get("/export")
async def export_report():
    """导出投资报告 HTML"""
    from ...data.csv_parser import CSVParser

    try:
        products = CSVParser.load_data()

        total_assets = sum(float(p.current_amount or 0) for p in products)
        total_initial = sum(float(p.initial_amount or 0) for p in products)
        total_profit = total_assets - total_initial
        total_return = (total_profit / total_initial * 100) if total_initial > 0 else 0

        rows_html = ""
        for p in products[:50]:
            profit = float(getattr(p, "profit", 0) or 0)
            profit_rate = float(getattr(p, "return_rate", 0) or 0)
            profit_class = "positive" if profit >= 0 else "negative"
            ptype = getattr(p, "investment_type", None)
            ptype_str = ptype.value if ptype else "其他"
            rows_html += f"""
                <tr>
                    <td>{p.name}</td>
                    <td>{ptype_str}</td>
                    <td>{float(p.current_amount or 0):,.2f} CNY</td>
                    <td class="{profit_class}">{profit:,.2f} CNY</td>
                    <td class="{profit_class}">{profit_rate:.2f}%</td>
                </tr>"""

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Investment Report - Asset Lens</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #333; border-bottom: 2px solid #00d2ff; padding-bottom: 10px; }}
                h2 {{ color: #666; margin-top: 30px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background: #f5f5f5; }}
                .positive {{ color: #00c853; }}
                .negative {{ color: #ff5252; }}
                .summary {{ background: #f9f9f9; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .summary-item {{ display: inline-block; margin-right: 40px; }}
                .summary-label {{ color: #888; font-size: 14px; }}
                .summary-value {{ font-size: 24px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>Asset Lens Investment Report</h1>
            <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>

            <div class="summary">
                <div class="summary-item">
                    <div class="summary-label">Total Assets</div>
                    <div class="summary-value">{total_assets:,.2f} CNY</div>
                </div>
                <div class="summary-item">
                    <div class="summary-label">Total Profit</div>
                    <div class="summary-value {"positive" if total_profit >= 0 else "negative"}">
                        {total_profit:,.2f} CNY
                    </div>
                </div>
                <div class="summary-item">
                    <div class="summary-label">Return Rate</div>
                    <div class="summary-value {"positive" if total_return >= 0 else "negative"}">
                        {total_return:.2f}%
                    </div>
                </div>
                <div class="summary-item">
                    <div class="summary-label">Positions</div>
                    <div class="summary-value">{len(products)}</div>
                </div>
            </div>

            <h2>Holdings Detail</h2>
            <table>
                <tr>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Current Value</th>
                    <th>Profit</th>
                    <th>Return Rate</th>
                </tr>
                {rows_html}
            </table>

            <p style="color: #888; margin-top: 40px;">
                Asset Lens - Personal Asset Operating System<br>
                This report is for reference only and does not constitute investment advice.
            </p>
        </body>
        </html>
        """

        return Response(
            content=html_content,
            media_type="text/html; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename=investment_report_{datetime.now().strftime('%Y%m%d')}.html"
            },
        )

    except Exception as e:
        return {"error": str(e)}
