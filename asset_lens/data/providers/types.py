from enum import Enum


class ProviderType(Enum):
    AKSHARE = "akshare"
    EASTMONEY = "eastmoney"
    TUSHARE = "tushare"
    ALPHA_VANTAGE = "alpha_vantage"
    FINNHUB = "finnhub"
    CCXT = "ccxt"
    LOCAL = "local"


class DataType(Enum):
    STOCK_CN = "stock_cn"
    STOCK_HK = "stock_hk"
    STOCK_US = "stock_us"
    FUND_CN = "fund_cn"
    FUND_ETF = "fund_etf"
    FUTURES_CN = "futures_cn"
    FUTURES_INTL = "futures_intl"
    CRYPTO = "crypto"
    MACRO = "macro"
    INDEX = "index"
