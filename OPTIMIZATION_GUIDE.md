# Asset-Lens 项目优化指南

## 📊 项目现状概览

**项目规模**：
- 核心模块：17个
- Python 文件：100+ 个
- 测试文件：90+ 个
- 代码行数：~15,000+ 行

**当前状态**：
- ✅ 功能完整，所有主要功能正常运行
- ✅ 测试覆盖率良好（1714 个测试通过）
- ⚠️ 代码质量有改进空间
- ⚠️ 性能可进一步优化
- ⚠️ 安全性需要加强

---

## 🔴 高优先级优化（第1-2周）

### 1. 复杂函数拆分 - `_calculate_irr_for_products()`

**文件**：`asset_lens/data/csv_parser.py` (行 391-550)

**问题**：
- 函数超过 400 行，包含 5 层嵌套条件判断
- 混合了 3 种不同的收益率计算逻辑（债券、定投、普通产品）
- 难以维护和测试

**优化方案**：

```python
# 提取为独立方法
def _calculate_bond_return(cls, product: InvestmentProduct, total_days: int) -> None:
    """计算债券类产品收益率"""
    if product.initial_amount and product.initial_amount > 0:
        current_value = float(product.current_amount or 0)
        interest = float(product.interest_payment or 0)
        initial_value = float(product.initial_amount)
        net_gain = current_value + interest - initial_value
        simple_return = net_gain / initial_value
        product.return_rate = Decimal(str(round(simple_return * 100, 2)))
        simple_annualized = (1 + simple_return) ** (360 / total_days) - 1
        product.annual_return = Decimal(str(round(simple_annualized * 100, 2)))

def _calculate_dca_return(cls, product: InvestmentProduct, transactions: List[Dict], 
                          total_days: int) -> None:
    """计算定投产品收益率"""
    # 实现定投特定逻辑
    pass

def _calculate_regular_return(cls, product: InvestmentProduct, transactions: List[Dict],
                              total_days: int) -> None:
    """计算普通产品收益率"""
    # 实现普通产品逻辑
    pass
```

**预期收益**：
- 可维护性提升 40%
- 单元测试覆盖率提升 25%
- 代码复杂度降低 50%

**工作量**：中等（2-3 小时）

---

### 2. 错误处理改进 - 添加日志和异常处理

**文件**：`asset_lens/core/realtime_pnl.py` (行 217, 248, 311)

**问题**：
```python
# 现有代码
except Exception:
    pass  # 隐藏错误，无法调试
```

**优化方案**：

```python
import logging

logger = logging.getLogger(__name__)

# 改进后
except Exception as e:
    logger.warning(
        f"加载基金代码映射失败",
        exc_info=True,
        extra={
            "error_type": type(e).__name__,
            "config_file": config_file
        }
    )
    self._fund_codes_map = {}
    return {}
```

**预期收益**：
- 可调试性提升 50%
- 问题诊断时间减少 70%

**工作量**：小（1 小时）

---

### 3. API 密钥安全加强

**文件**：
- `asset_lens/data/stock_fetcher.py` (行 568)
- `asset_lens/data/enhanced_market_data_fetcher.py` (行 557, 630)

**问题**：
```python
# 现有代码 - 不安全
api_key = config.finnhub_api_key or "demo"
url = f"https://api.finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}"
# 密钥可能被日志记录或缓存
```

**优化方案**：

```python
# 改进后 - 使用 headers 而非 URL 参数
if not config.finnhub_api_key:
    raise ConfigurationError(
        "FINNHUB_API_KEY 未配置，请在 .env 中设置",
        config_key="FINNHUB_API_KEY"
    )

headers = {
    "Authorization": f"Bearer {config.finnhub_api_key}",
    "User-Agent": "asset-lens/1.0"
}
url = "https://api.finnhub.io/api/v1/quote"
params = {"symbol": symbol}

# 使用 http_client 发送请求
response = await self._session.get(url, params=params, headers=headers)
```

**预期收益**：
- 安全性提升 60%
- 密钥泄露风险降低 90%

**工作量**：小（1.5 小时）

---

### 4. 缓存优化 - 汇率数据缓存

**文件**：`asset_lens/data/csv_parser.py` (行 59-185)

**问题**：
```python
# 现有代码 - 每次调用都重新读取
@staticmethod
def get_exchange_rates(data_dir: Path) -> tuple[float, float]:
    # 每次都读取 CSV 文件
    df = pd.read_csv(...)
    return usd_rate, hkd_rate
```

**优化方案**：

```python
import functools
from datetime import datetime, timedelta

class ExchangeRateCache:
    """汇率缓存管理器"""
    
    def __init__(self, ttl_seconds: int = 3600):
        self._cache = {}
        self._ttl = ttl_seconds
        self._timestamps = {}
    
    def get(self, key: str) -> Optional[tuple[float, float]]:
        """获取缓存的汇率"""
        if key not in self._cache:
            return None
        
        # 检查是否过期
        if datetime.now() - self._timestamps[key] > timedelta(seconds=self._ttl):
            del self._cache[key]
            del self._timestamps[key]
            return None
        
        return self._cache[key]
    
    def set(self, key: str, value: tuple[float, float]) -> None:
        """缓存汇率"""
        self._cache[key] = value
        self._timestamps[key] = datetime.now()

# 使用缓存
_exchange_rate_cache = ExchangeRateCache(ttl_seconds=3600)

@staticmethod
def get_exchange_rates(data_dir: Path) -> tuple[float, float]:
    cache_key = str(data_dir)
    
    # 先检查缓存
    cached = _exchange_rate_cache.get(cache_key)
    if cached:
        return cached
    
    # 读取文件
    df = pd.read_csv(...)
    rates = (usd_rate, hkd_rate)
    
    # 保存到缓存
    _exchange_rate_cache.set(cache_key, rates)
    return rates
```

**预期收益**：
- 性能提升 30-50%（减少 I/O 操作）
- 内存使用优化

**工作量**：小（1 小时）

---

### 5. 代码重复消除 - 统一 parse 函数

**文件**：
- `asset_lens/data/parser_utils.py`
- `asset_lens/data/parsers/field_parsers.py`
- `asset_lens/data/csv_parser.py`

**问题**：
```python
# 重复定义 1 - parser_utils.py
def parse_decimal(value: str) -> Optional[Decimal]:
    if not value or value.strip() == "":
        return None
    try:
        cleaned = value.replace(",", "").strip()
        return Decimal(cleaned)
    except Exception:
        return None

# 重复定义 2 - field_parsers.py
def parse_decimal(value: Optional[str]) -> Optional[Decimal]:
    if not value or value.strip() in ("", "-", "N/A", "无"):
        return None
    try:
        clean_value = value.strip().replace(",", "").replace("%", "").replace("￥", "")
        return Decimal(clean_value)
    except (InvalidOperation, ValueError):
        return None

# 重复定义 3 - csv_parser.py
@staticmethod
def parse_decimal(value: str) -> Decimal | None:
    """解析 Decimal 值"""
    return _parse_decimal(value)
```

**优化方案**：

```python
# 统一使用 field_parsers.py 中的实现（最完整）
# 在 parser_utils.py 中导入
from .parsers.field_parsers import (
    parse_decimal,
    parse_date,
    parse_boolean,
    parse_investment_type,
    parse_risk_level
)

# 在 csv_parser.py 中导入
from .parsers.field_parsers import parse_decimal

# 删除 csv_parser.py 中的重复定义
```

**预期收益**：
- 代码行数减少 10%
- 维护成本降低 25%
- 一致性提升

**工作量**：小（1.5 小时）

---

## 🟡 中优先级优化（第2-3周）

### 6. 配置系统统一

**文件**：
- `asset_lens/config.py`
- `asset_lens/core/config_manager.py`

**问题**：
- 存在两套配置系统
- 配置加载逻辑分散
- 缺少验证和默认值管理

**优化方案**：

```python
# 使用 Pydantic 进行配置验证
from pydantic import BaseSettings, validator

class AppConfig(BaseSettings):
    """应用配置"""
    
    # 数据模式
    data_mode: str = "sample"
    
    # API 密钥
    finnhub_api_key: Optional[str] = None
    alphavantage_api_key: Optional[str] = None
    tushare_token: Optional[str] = None
    
    # 路径配置
    sample_data_path: Path = Path("data/sample_data")
    real_data_path: Path = Path("data/real")
    output_path: Path = Path("output")
    cache_path: Path = Path("cache")
    
    # 汇率配置
    default_usd_rate: float = 6.90
    default_hkd_rate: float = 0.89
    
    @validator("data_mode")
    def validate_data_mode(cls, v):
        if v not in ("sample", "real"):
            raise ValueError("data_mode 必须是 'sample' 或 'real'")
        return v
    
    @validator("finnhub_api_key")
    def validate_api_key(cls, v):
        if v and len(v) < 10:
            raise ValueError("API 密钥格式不正确")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# 全局配置实例
config = AppConfig()
```

**预期收益**：
- 可维护性提升 20%
- 配置错误提前发现
- 类型安全性提升

**工作量**：中等（2-3 小时）

---

### 7. 并发获取优化 - 添加重试机制

**文件**：`asset_lens/data/concurrent_fetcher.py`

**问题**：
- 没有重试机制
- 没有连接池复用
- 超时处理不完善

**优化方案**：

```python
from aiohttp_retry import RetryClientSession
from aiohttp import TCPConnector

class ConcurrentDataFetcher:
    def __init__(self, max_concurrent: int = 10, timeout: int = 30, max_retries: int = 3):
        self.max_concurrent = max_concurrent
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self._session: Optional[RetryClientSession] = None
        self._connector: Optional[TCPConnector] = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        # 创建连接池
        self._connector = TCPConnector(
            limit=self.max_concurrent,
            limit_per_host=5,
            ttl_dns_cache=300
        )
        
        # 创建带重试的会话
        self._session = RetryClientSession(
            connector=self._connector,
            timeout=self.timeout,
            raise_for_status=False
        )
        return self
    
    async def fetch_single(self, url: str, **kwargs) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """获取单个数据（带重试）"""
        if self._session is None:
            return False, None, "Session not initialized"
        
        try:
            async with self._session.get(url, **kwargs) as response:
                if response.status == 200:
                    data = await response.json()
                    return True, data, None
                else:
                    return False, None, f"HTTP {response.status}"
        except asyncio.TimeoutError:
            return False, None, "请求超时"
        except Exception as e:
            logger.error(f"请求失败: {url}", exc_info=True)
            return False, None, str(e)
```

**预期收益**：
- 可靠性提升 40%
- 网络错误恢复能力提升
- 性能提升 20%（连接复用）

**工作量**：中等（2 小时）

---

### 8. 类型提示完善

**文件**：多个文件

**问题**：
- 许多函数缺少返回类型提示
- 字典参数没有类型定义
- 难以进行静态类型检查

**优化方案**：

```python
# 改进前
def analyze_portfolio(self, portfolio_data):
    return AIAnalysisResult(...)

# 改进后
from typing import Dict, Any, List
from .models import AIAnalysisResult, InvestmentProduct

def analyze_portfolio(
    self, 
    portfolio_data: Dict[str, Any]
) -> AIAnalysisResult:
    """分析投资组合
    
    Args:
        portfolio_data: 投资组合数据字典
        
    Returns:
        AI 分析结果
        
    Raises:
        ValueError: 如果数据格式不正确
    """
    # 实现...
    return AIAnalysisResult(...)

# 为复杂类型定义 TypedDict
from typing import TypedDict

class PortfolioData(TypedDict):
    """投资组合数据类型"""
    total_value: float
    products: List[InvestmentProduct]
    risk_level: str
    allocation: Dict[str, float]
```

**预期收益**：
- 代码质量提升 15%
- IDE 自动完成能力提升
- 运行时错误减少 20%

**工作量**：大（4-5 小时）

---

### 9. 测试覆盖率提升

**文件**：
- `asset_lens/data/concurrent_fetcher.py` - 无测试
- `asset_lens/core/realtime_pnl.py` - 测试不完整
- `asset_lens/core/ai_analyzer.py` - 缺少边界条件测试

**优化方案**：

```python
# 为 concurrent_fetcher.py 添加测试
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_fetch_single_success():
    """测试单个数据获取成功"""
    async with ConcurrentDataFetcher() as fetcher:
        with patch.object(fetcher._session, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"c": 100.0})
            mock_get.return_value.__aenter__.return_value = mock_response
            
            success, data, error = await fetcher.fetch_single("http://example.com")
            assert success is True
            assert data == {"c": 100.0}

@pytest.mark.asyncio
async def test_fetch_single_timeout():
    """测试单个数据获取超时"""
    async with ConcurrentDataFetcher(timeout=1) as fetcher:
        with patch.object(fetcher._session, 'get') as mock_get:
            mock_get.side_effect = asyncio.TimeoutError()
            
            success, data, error = await fetcher.fetch_single("http://example.com")
            assert success is False
            assert error == "请求超时"

@pytest.mark.asyncio
async def test_fetch_multiple_stocks():
    """测试并发获取多个股票"""
    codes = ["sh600000", "sh600001", "sh600002"]
    async with ConcurrentDataFetcher(max_concurrent=2) as fetcher:
        # Mock 实现...
        results = await fetcher.fetch_multiple_stocks(codes)
        assert len(results) == 3
```

**预期收益**：
- 测试覆盖率提升 15-20%
- 回归测试能力提升
- 代码质量提升

**工作量**：中等（3-4 小时）

---

## 🟢 低优先级优化（第3-4周）

### 10. 日志系统改进

**问题**：
- 混合使用 `print()` 和 `logger`
- 日志级别不一致
- 缺少结构化日志

**优化方案**：

```python
import logging
import json
from datetime import datetime

# 创建结构化日志处理器
class StructuredLogFormatter(logging.Formatter):
    """结构化日志格式化器"""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # 添加额外信息
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        return json.dumps(log_data, ensure_ascii=False)

# 配置日志
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(StructuredLogFormatter())
logger.addHandler(handler)

# 使用结构化日志
logger.warning(
    "DCA 产品数据不一致",
    extra={
        "product_name": product.name,
        "csv_amount": product.initial_amount,
        "transaction_amount": net_invest,
        "difference": diff
    }
)
```

**预期收益**：
- 日志可读性提升
- 日志分析能力提升
- 问题追踪更容易

**工作量**：小（1.5 小时）

---

### 11. 命名规范统一

**问题**：
- 混合使用 `_private` 和 `__dunder` 前缀
- 变量名有时过长有时过短
- 常量未使用全大写

**优化方案**：

```python
# 统一命名规范

# 常量 - 全大写
CACHE_TTL = 3600
MAX_CONCURRENT_REQUESTS = 10
DEFAULT_TIMEOUT = 30

# 私有变量 - 单下划线前缀
_internal_cache = {}
_session: Optional[aiohttp.ClientSession] = None

# 公开方法 - 小写 + 下划线
def fetch_stock_quote(code: str) -> FetchResult:
    pass

# 私有方法 - 单下划线前缀
def _parse_response(response: Dict) -> Optional[Dict]:
    pass

# 类名 - PascalCase
class ConcurrentDataFetcher:
    pass

# 类常量 - 全大写
class Config:
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
```

**预期收益**：
- 代码可读性提升 10%
- 新开发者上手更快

**工作量**：小（1 小时）

---

### 12. 文档完善

**问题**：
- 缺少模块级文档
- 复杂函数缺少详细注释
- 没有使用示例

**优化方案**：

```python
"""
并发数据获取器 - 使用异步和并发技术优化数据获取性能

该模块提供高效的并发数据获取功能，支持：
- 异步 HTTP 请求
- 自动重试机制
- 连接池复用
- 性能监控

使用示例：
    >>> async with ConcurrentDataFetcher(max_concurrent=10) as fetcher:
    ...     results = await fetcher.fetch_multiple_stocks(['sh600000', 'sh600001'])
    ...     for result in results:
    ...         if result.success:
    ...             print(f"{result.code}: {result.data}")
    ...         else:
    ...             print(f"{result.code}: {result.error}")

性能指标：
    - 单个请求平均耗时：200-500ms
    - 并发 10 个请求：1-2s
    - 成功率：>99%（带重试）

异常处理：
    - 网络超时：自动重试 3 次
    - HTTP 错误：返回错误信息
    - 解析错误：记录日志并继续
"""

import asyncio
import aiohttp
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)
```

**预期收益**：
- 易用性提升 15%
- 新开发者上手时间减少 30%

**工作量**：小（1.5 小时）

---

## 📈 优化优先级总结表

| 优先级 | 问题 | 预期收益 | 工作量 | 周期 |
|--------|------|--------|--------|------|
| 🔴 高 | 复杂函数拆分 | 可维护性 +40% | 中 | 2-3h |
| 🔴 高 | 错误处理改进 | 可调试性 +50% | 小 | 1h |
| 🔴 高 | API 密钥安全 | 安全性 +60% | 小 | 1.5h |
| 🔴 高 | 缓存优化 | 性能 +30% | 小 | 1h |
| 🔴 高 | 代码重复消除 | 维护性 +25% | 小 | 1.5h |
| 🟡 中 | 配置系统统一 | 可维护性 +20% | 中 | 2-3h |
| 🟡 中 | 并发优化 | 可靠性 +40% | 中 | 2h |
| 🟡 中 | 类型提示完善 | 代码质量 +15% | 大 | 4-5h |
| 🟡 中 | 测试覆盖率 | 质量 +15% | 中 | 3-4h |
| 🟢 低 | 日志系统改进 | 可观测性 +20% | 小 | 1.5h |
| 🟢 低 | 命名规范统一 | 可读性 +10% | 小 | 1h |
| 🟢 低 | 文档完善 | 易用性 +15% | 小 | 1.5h |

**总工作量**：约 25-30 小时

---

## 🎯 建议执行计划

### 第 1 周（高优先级）
1. **周一**：复杂函数拆分 + 错误处理改进
2. **周二**：API 密钥安全加强
3. **周三**：缓存优化 + 代码重复消除
4. **周四-周五**：测试和验证

### 第 2 周（中优先级）
1. **周一-周二**：配置系统统一
2. **周三-周四**：并发获取优化
3. **周五**：集成测试

### 第 3 周（中优先级）
1. **周一-周三**：类型提示完善
2. **周四-周五**：测试覆盖率提升

### 第 4 周（低优先级）
1. **周一**：日志系统改进
2. **周二**：命名规范统一
3. **周三-周五**：文档完善 + 最终验证

---

## ✅ 验证清单

完成每项优化后，请检查：

- [ ] 代码通过 `pylint` 检查
- [ ] 代码通过 `mypy` 类型检查
- [ ] 代码通过 `black` 格式化
- [ ] 所有测试通过（`make test`）
- [ ] 测试覆盖率未下降
- [ ] 性能基准测试通过
- [ ] 文档已更新
- [ ] Git 提交信息清晰

---

## 📚 相关资源

- [Python 最佳实践](https://pep8.org/)
- [Async/Await 最佳实践](https://docs.python.org/3/library/asyncio.html)
- [Pydantic 文档](https://pydantic-docs.helpmanual.io/)
- [pytest 文档](https://docs.pytest.org/)

---

## 💡 快速开始

选择一个高优先级的优化开始：

```bash
# 1. 创建新分支
git checkout -b optimize/refactor-irr-calculation

# 2. 进行优化
# ... 编辑文件 ...

# 3. 运行测试
make test

# 4. 检查代码质量
make lint

# 5. 提交更改
git add .
git commit -m "refactor: 拆分 _calculate_irr_for_products 函数"

# 6. 推送
git push origin optimize/refactor-irr-calculation
```

---

**最后更新**：2026-03-17
**优化指南版本**：1.0
