"""
asset-lens: A personal asset operating system built with Python.
一个以 Python 为核心构建的个人资产操作系统
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .config import Config
from .data.models import InvestmentProduct, Portfolio, Transaction

__all__ = [
    "Config",
    "InvestmentProduct",
    "Transaction",
    "Portfolio",
]
