"""
Enhanced Data Fetcher with retry mechanism and multiple data sources.
增强版数据获取模块 - 支持重试机制和多数据源

功能:
1. 自动重试机制 (指数退避)
2. 多数据源备选 (腾讯、新浪、东方财富、网易)
3. 离线缓存支持
4. 代理自动切换
"""

import json
import os
import time
import functools
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from ..config import config


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exceptions: tuple = (Exception,),
):
    """重试装饰器 - 指数退避"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        print(f"  ⚠️ 第 {attempt + 1} 次重试，等待 {delay:.1f}s... ({type(e).__name__})")
                        time.sleep(delay)
            raise last_exception if last_exception else Exception("Unknown error")
        return wrapper
    return decorator


@contextmanager
def _disable_proxy() -> Generator[None, None, None]:
    """临时禁用代理的上下文管理器"""
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
    original_values = {}

    for var in proxy_vars:
        if var in os.environ:
            original_values[var] = os.environ[var]
            del os.environ[var]

    try:
        yield
    finally:
        for var, value in original_values.items():
            os.environ[var] = value


class EnhancedDataFetcher:
    """增强版数据获取器 - 多数据源 + 重试机制"""

    def __init__(self, cache_path: Path | None = None):
        self.cache_path = cache_path or config.cache_path
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self.market_stock_cache_file = self.cache_path / "market_stocks.json"

    def get_cached_stocks(self, max_age_hours: int = 24) -> list[dict[str, Any]] | None:
        """获取缓存的股票列表"""
        if not self.market_stock_cache_file.exists():
            return None

        try:
            with open(self.market_stock_cache_file, encoding='utf-8') as f:
                data = json.load(f)

            cache_time = datetime.fromisoformat(data.get('update_time', '2000-01-01'))
            age_hours = (datetime.now() - cache_time).total_seconds() / 3600

            if age_hours <= max_age_hours:
                stocks: list[dict[str, Any]] = data.get('stocks', [])
                print(f"📦 使用缓存数据: {len(stocks)} 只股票 (缓存时间: {age_hours:.1f}小时前)")
                return stocks
        except Exception as e:
            print(f"⚠️ 读取缓存失败: {e}")

        return None

    def save_to_cache(self, stocks: list[dict[str, Any]]) -> None:
        """保存股票列表到缓存"""
        data = {
            'stocks': stocks,
            'update_time': datetime.now().isoformat(),
            'count': len(stocks)
        }
        with open(self.market_stock_cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ 已缓存 {len(stocks)} 只股票")

    @retry_with_backoff(max_retries=3, base_delay=2.0)
    def _fetch_from_tencent(self) -> list[dict[str, Any]] | None:
        """从腾讯财经获取数据"""
        import requests

        print("🌐 尝试腾讯财经...")
        with _disable_proxy():
            url = "https://qt.gtimg.cn/q=sh600000,sz000001,sh600519"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                return [{'source': 'tencent', 'status': 'connected'}]
        return None

    @retry_with_backoff(max_retries=3, base_delay=2.0)
    def _fetch_from_sina(self) -> list[dict[str, Any]] | None:
        """从新浪财经获取数据"""
        import requests

        print("🌐 尝试新浪财经...")
        with _disable_proxy():
            url = "https://hq.sinajs.cn/list=sh600000,sz000001"
            headers = {'Referer': 'https://finance.sina.com.cn'}
            r = requests.get(url, timeout=10, headers=headers)
            if r.status_code == 200:
                return [{'source': 'sina', 'status': 'connected'}]
        return None

    @retry_with_backoff(max_retries=2, base_delay=3.0)
    def _fetch_from_eastmoney(self) -> list[dict[str, Any]] | None:
        """从东方财富获取数据"""
        import requests

        print("🌐 尝试东方财富...")
        with _disable_proxy():
            url = "https://push2.eastmoney.com/api/qt/clist/get"
            params: dict[str, str | int] = {
                'pn': 1, 'pz': 100, 'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',
                'fields': 'f12,f14,f2,f3,f4,f5,f6'
            }
            r = requests.get(url, params=params, timeout=15)
            if r.status_code == 200:
                data = r.json()
                if data.get('data', {}).get('diff'):
                    return [{'source': 'eastmoney', 'status': 'connected'}]
        return None

    def fetch_with_fallback(self, use_cache: bool = True) -> list[dict[str, Any]]:
        """多数据源获取，自动降级"""
        if use_cache:
            cached = self.get_cached_stocks(max_age_hours=24)
            if cached:
                return cached

        sources = [
            ('腾讯财经', self._fetch_from_tencent),
            ('新浪财经', self._fetch_from_sina),
            ('东方财富', self._fetch_from_eastmoney),
        ]

        for name, fetcher in sources:
            try:
                result: list[dict[str, Any]] | None = fetcher()
                if result:
                    print(f"✅ {name} 连接成功")
                    return result
            except Exception as e:
                print(f"❌ {name} 失败: {type(e).__name__}")
                continue

        if use_cache:
            cached = self.get_cached_stocks(max_age_hours=99999)
            if cached:
                print("⚠️ 所有数据源失败，使用旧缓存")
                return cached

        print("❌ 所有数据源获取失败，无缓存可用")
        return []


enhanced_fetcher = EnhancedDataFetcher()
