"""
Asset Lens - 投资组合管理系统
==============================

一个功能完整的投资组合管理系统，支持：
- 投资组合分析
- 市场风向分析
- 策略选股
- 周报生成
- Web 界面

主要模块:
---------
- data: 数据获取和处理
- core: 核心功能模块
- report: 报告生成
- web: Web API
- utils: 工具函数

使用示例:
---------
>>> from asset_lens import config
>>> from asset_lens.data.csv_parser import CSVParser
>>> parser = CSVParser()
>>> data = parser.parse()

版本历史:
---------
- 1.0.0: 初始版本
"""

import warnings

warnings.filterwarnings("ignore", message="Pandas requires version")
warnings.filterwarnings("ignore", message=".*unclosed.*socket.*")
warnings.filterwarnings("ignore", category=ResourceWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

__version__ = "1.0.0"
__author__ = "Asset Lens Team"
__all__ = [
    "config",
    "cli",
    "data",
    "core",
    "report",
    "web",
    "utils",
]
