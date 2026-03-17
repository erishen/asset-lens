"""
Concurrent Data Fetcher - 并发数据获取器
使用异步和并发技术优化数据获取性能

特性:
- 异步 HTTP 请求
- 自动重试机制
- 连接池复用
- 性能监控
"""

import asyncio
import aiohttp
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

DEFAULT_MAX_CONCURRENT = 10
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0


@dataclass
class FetchResult:
    """数据获取结果"""
    code: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration: float = 0.0
    retries: int = 0


class ConcurrentDataFetcher:
    """并发数据获取器"""
    
    def __init__(
        self, 
        max_concurrent: int = DEFAULT_MAX_CONCURRENT, 
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY
    ):
        """
        初始化并发数据获取器
        
        Args:
            max_concurrent: 最大并发数
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
        """
        self.max_concurrent = max_concurrent
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._session: Optional[aiohttp.ClientSession] = None
        self._connector: Optional[aiohttp.TCPConnector] = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self._connector = aiohttp.TCPConnector(
            limit=self.max_concurrent,
            limit_per_host=5,
            ttl_dns_cache=300,
            enable_cleanup_closed=True
        )
        self._session = aiohttp.ClientSession(
            connector=self._connector,
            timeout=self.timeout
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self._session:
            await self._session.close()
        if self._connector:
            await self._connector.close()
    
    async def fetch_single(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        获取单个数据
        
        Args:
            url: 请求 URL
            params: 请求参数
            headers: 请求头
            
        Returns:
            (成功标志, 数据, 错误信息)
        """
        if self._session is None:
            return False, None, "Session not initialized"
        session: aiohttp.ClientSession = self._session
        
        last_error: Optional[str] = None
        
        for attempt in range(self.max_retries):
            try:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return True, data, None
                    else:
                        last_error = f"HTTP {response.status}"
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(self.retry_delay * (attempt + 1))
            except asyncio.TimeoutError:
                last_error = "请求超时"
                if attempt < self.max_retries - 1:
                    logger.warning(f"请求超时，重试 {attempt + 1}/{self.max_retries}: {url}")
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
            except aiohttp.ClientError as e:
                last_error = f"网络错误: {str(e)}"
                if attempt < self.max_retries - 1:
                    logger.warning(f"网络错误，重试 {attempt + 1}/{self.max_retries}: {url}")
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
            except Exception as e:
                last_error = str(e)
                logger.error(f"请求异常: {url}", exc_info=True)
                break
        
        return False, None, last_error
    
    async def fetch_stock_quote(self, code: str) -> FetchResult:
        """
        获取股票行情
        
        Args:
            code: 股票代码
            
        Returns:
            获取结果
        """
        start_time = time.time()
        
        # 根据股票代码确定 URL
        if code.startswith(('sh', 'sz')):
            url = f"http://hq.sinajs.cn/list={code}"
            headers = {
                "Referer": "http://finance.sina.com.cn",
                "User-Agent": "Mozilla/5.0"
            }
        else:
            url = f"https://api.example.com/stock/{code}"
            headers = {}
        
        success, data, error = await self.fetch_single(url, headers=headers)
        
        return FetchResult(
            code=code,
            success=success,
            data=data,
            error=error,
            duration=time.time() - start_time
        )
    
    async def fetch_multiple_stocks(
        self,
        codes: List[str],
        progress_callback: Optional[Callable] = None
    ) -> List[FetchResult]:
        """
        并发获取多个股票行情
        
        Args:
            codes: 股票代码列表
            progress_callback: 进度回调函数
            
        Returns:
            获取结果列表
        """
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def fetch_with_semaphore(code: str) -> FetchResult:
            async with semaphore:
                result = await self.fetch_stock_quote(code)
                if progress_callback:
                    progress_callback(code, result)
                return result
        
        tasks = [fetch_with_semaphore(code) for code in codes]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        final_results: List[FetchResult] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(FetchResult(
                    code=codes[i],
                    success=False,
                    error=str(result)
                ))
            else:
                final_results.append(result)  # type: ignore[arg-type]
        
        return final_results
    
    async def fetch_fund_nav(self, code: str) -> FetchResult:
        """
        获取基金净值
        
        Args:
            code: 基金代码
            
        Returns:
            获取结果
        """
        start_time = time.time()
        
        url = f"http://fundgz.1234567.com.cn/js/{code}.js"
        headers = {
            "Referer": "http://fund.eastmoney.com/",
            "User-Agent": "Mozilla/5.0"
        }
        
        success, data, error = await self.fetch_single(url, headers=headers)
        
        return FetchResult(
            code=code,
            success=success,
            data=data,
            error=error,
            duration=time.time() - start_time
        )
    
    async def fetch_multiple_funds(
        self,
        codes: List[str],
        progress_callback: Optional[Callable] = None
    ) -> List[FetchResult]:
        """
        并发获取多个基金净值
        
        Args:
            codes: 基金代码列表
            progress_callback: 进度回调函数
            
        Returns:
            获取结果列表
        """
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def fetch_with_semaphore(code: str) -> FetchResult:
            async with semaphore:
                result = await self.fetch_fund_nav(code)
                if progress_callback:
                    progress_callback(code, result)
                return result
        
        tasks = [fetch_with_semaphore(code) for code in codes]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        final_results: List[FetchResult] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(FetchResult(
                    code=codes[i],
                    success=False,
                    error=str(result)
                ))
            else:
                final_results.append(result)  # type: ignore[arg-type]
        
        return final_results


def fetch_stocks_concurrently(codes: List[str], max_concurrent: int = 10) -> List[FetchResult]:
    """
    同步接口：并发获取股票行情
    
    Args:
        codes: 股票代码列表
        max_concurrent: 最大并发数
        
    Returns:
        获取结果列表
    """
    async def _fetch():
        async with ConcurrentDataFetcher(max_concurrent=max_concurrent) as fetcher:
            return await fetcher.fetch_multiple_stocks(codes)
    
    return asyncio.run(_fetch())


def fetch_funds_concurrently(codes: List[str], max_concurrent: int = 10) -> List[FetchResult]:
    """
    同步接口：并发获取基金净值
    
    Args:
        codes: 基金代码列表
        max_concurrent: 最大并发数
        
    Returns:
        获取结果列表
    """
    async def _fetch():
        async with ConcurrentDataFetcher(max_concurrent=max_concurrent) as fetcher:
            return await fetcher.fetch_multiple_funds(codes)
    
    return asyncio.run(_fetch())


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
    
    def record(self, operation: str, duration: float):
        """记录性能指标"""
        if operation not in self.metrics:
            self.metrics[operation] = []
        self.metrics[operation].append(duration)
    
    def get_stats(self, operation: str) -> Dict[str, float]:
        """获取统计信息"""
        if operation not in self.metrics:
            return {}
        
        durations = self.metrics[operation]
        return {
            "count": len(durations),
            "total": sum(durations),
            "average": sum(durations) / len(durations),
            "min": min(durations),
            "max": max(durations)
        }
    
    def get_report(self) -> str:
        """生成性能报告"""
        lines = ["=" * 60, "性能监控报告", "=" * 60, ""]
        
        for operation in sorted(self.metrics.keys()):
            stats = self.get_stats(operation)
            lines.append(f"📊 {operation}:")
            lines.append(f"  • 执行次数: {stats['count']}")
            lines.append(f"  • 总耗时: {stats['total']:.2f}秒")
            lines.append(f"  • 平均耗时: {stats['average']:.2f}秒")
            lines.append(f"  • 最小耗时: {stats['min']:.2f}秒")
            lines.append(f"  • 最大耗时: {stats['max']:.2f}秒")
            lines.append("")
        
        lines.append("=" * 60)
        return "\n".join(lines)


performance_monitor = PerformanceMonitor()
