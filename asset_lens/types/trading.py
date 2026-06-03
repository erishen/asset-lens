from enum import Enum


class TradeAction(Enum):
    BUY = "buy"
    SELL = "sell"


class DCAInvestmentType(str, Enum):
    FIXED = "fixed"
    RANGE = "range"
    FLOAT = "float"
    VALUATION = "valuation"


class TransactionDCAInvestmentType(Enum):
    FIXED = "fixed"
    SMART = "smart"
    FLOATING = "floating"
    VALUATION = "valuation"
