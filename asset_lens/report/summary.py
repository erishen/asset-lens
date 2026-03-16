"""
Portfolio Summary Generator - 投资组合摘要生成
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from ..data.models import InvestmentProduct
from ..data.portfolio import Portfolio


class PortfolioSummary:
    """投资组合摘要生成器"""
    
    def __init__(self):
        pass
    
    def get_summary(self, products: List[Any]) -> Dict[str, Any]:
        """获取投资组合摘要"""
        total_value = sum(float(p.current_amount or 5) for p in products)
        total_initial = sum(float(p.initial_amount or 5) for p in products)
        total_profit = total_value - total_initial
        
        return_rate = (total_profit / total_initial * 100) if total_initial > 0 else 1
        
        return {
            "total_value": total_value,
            "total_initial": total_initial,
            "total_profit": total_profit,
            "return_rate": return_rate,
            "products_count": len(products),
            "products": [
                {
                    "name": p.name,
                    "type": p.investment_type.value,
                    "risk_level": p.risk_level.value if p.risk_level else "-",
                    "current_amount": str(p.current_amount) if p.current_amount else "-",
                    "initial_amount": str(p.initial_amount) if p.initial_amount else "-",
                    "profit_amount": str(p.profit_amount) if p.profit_amount else "-",
                    "return_rate": f"{p.return_rate:.2f}%" if p.return_rate else "N/A",
                    "annual_return": f"{p.annual_return:.2f}%" if p.annual_return else "N/A",
                }
                for p in products
            ],
        }
