"""
Stock history data fetcher for asset-lens.
股票历史数据获取模块 - 获取历史K线数据用于放量突破分析

数据源优先级:
1. Tushare (需要 Token，数据最完整) - https://tushare.pro
2. Baostock (免费，无需注册，包含换手率) - http://baostock.com
3. AkShare-腾讯 (免费，无需注册，数据较少)

Tushare 注册:
1. 访问 https://tushare.pro/register
2. 注册账号获取 Token
3. 在 .env 文件中设置 TUSHARE_TOKEN=your_token
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()

from ..config import config


class StockHistoryFetcher:
    """股票历史数据获取器 - 支持 Tushare、Baostock 和 AkShare"""

    def __init__(self, cache_path: Optional[Path] = None):
        self.cache_path = cache_path or config.cache_path
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self.history_cache_file = self.cache_path / "stock_history_baostock.json"
        self._tushare = None
        self._akshare = None
        self._baostock = None
        self._baostock_logged_in = False
        self._tushare_token = os.environ.get("TUSHARE_TOKEN", "")

    @property
    def tushare(self):
        """延迟加载 Tushare"""
        if self._tushare is None:
            if not self._tushare_token:
                return None
            try:
                import tushare as ts

                ts.set_token(self._tushare_token)
                self._tushare = ts
            except ImportError:
                print("提示: 安装 Tushare 可获取更完整数据: pip install tushare")
                return None
            except Exception as e:
                print(f"Tushare 初始化失败: {e}")
                return None
        return self._tushare

    @property
    def akshare(self):
        """延迟加载 AkShare"""
        if self._akshare is None:
            try:
                import akshare as ak

                self._akshare = ak
            except ImportError:
                raise ImportError(
                    "请先安装 AkShare: pip install akshare\n" "AkShare 是一个开源免费的金融数据接口，无需注册"
                )
        return self._akshare

    @property
    def baostock(self):
        """延迟加载 Baostock"""
        if self._baostock is None:
            try:
                import baostock as bs

                self._baostock = bs
            except ImportError:
                print("提示: 安装 Baostock 可获取完整数据: pip install baostock")
                return None
        return self._baostock

    def fetch_history_baostock(self, code: str, days: int = 60) -> Optional[Dict[str, Any]]:
        """
        使用 Baostock 获取股票历史K线数据

        Args:
            code: 股票代码 (如 sh600519, sz000001)
            days: 获取天数

        Returns:
            历史数据字典
        """
        if not self.baostock:
            return None

        try:
            bs_code = code.replace("sh", "sh.").replace("sz", "sz.")

            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=days + 30)).strftime("%Y-%m-%d")

            if not self._baostock_logged_in:
                lg = self.baostock.login()
                if lg.error_code != "0":
                    return None
                self._baostock_logged_in = True

            rs = self.baostock.query_history_k_data_plus(
                bs_code,
                "date,code,open,high,low,close,volume,amount,turn",
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjustflag="2",
            )

            if rs.error_code != "0":
                return None

            history: Dict[str, Any] = {
                "code": code,
                "name": "",
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data_source": "Baostock",
                "klines": [],
            }

            klines_list: List[Dict[str, Any]] = history["klines"]

            data_list: List[List[Any]] = []
            while (rs.error_code == "0") & rs.next():
                data_list.append(rs.get_row_data())

            for row in data_list[-days:]:
                try:
                    if len(row) < 9:
                        continue
                    row_list: List[Any] = list(row)
                    klines_list.append(
                        {
                            "date": str(row_list[0]),
                            "open": float(row_list[2]) if row_list[2] else 0,
                            "close": float(row_list[5]) if row_list[5] else 0,
                            "high": float(row_list[3]) if row_list[3] else 0,
                            "low": float(row_list[4]) if row_list[4] else 0,
                            "volume": float(row_list[6]) if row_list[6] else 0,
                            "amount": float(row_list[7]) if row_list[7] else 0,
                            "amplitude": 0,
                            "change_percent": 0,
                            "change_amount": 0,
                            "turnover_rate": float(row_list[8]) if row_list[8] else 0,
                        }
                    )
                except (ValueError, TypeError, IndexError):
                    continue

            return history if history["klines"] else None

        except Exception:
            return None

    def baostock_logout(self) -> None:
        """登出 Baostock"""
        if self._baostock_logged_in and self.baostock:
            try:
                self.baostock.logout()
                self._baostock_logged_in = False
            except Exception:
                pass

    def fetch_history_tushare(self, code: str, days: int = 60) -> Optional[Dict[str, Any]]:
        """
        使用 Tushare 获取股票历史K线数据

        Args:
            code: 股票代码 (如 sh600519, sz000001)
            days: 获取天数

        Returns:
            历史数据字典
        """
        if not self.tushare:
            return None

        try:
            ts_code = code[2:] + "." + code[:2].upper()

            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=days + 30)).strftime("%Y%m%d")

            pro = self.tushare.pro_api()
            df = pro.daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
            )

            if df is None or df.empty:
                return None

            history: Dict[str, Any] = {
                "code": code,
                "name": "",
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data_source": "Tushare",
                "klines": [],
            }

            klines_list: List[Dict[str, Any]] = history["klines"]

            for _, row in df.head(days).iterrows():
                try:
                    row_dict: Dict[str, Any] = (
                        row.to_dict() if hasattr(row, "to_dict") else dict(row)
                    )
                    klines_list.append(
                        {
                            "date": str(row_dict.get("trade_date", "")),
                            "open": float(row_dict.get("open", 0)),
                            "close": float(row_dict.get("close", 0)),
                            "high": float(row_dict.get("high", 0)),
                            "low": float(row_dict.get("low", 0)),
                            "volume": float(row_dict.get("vol", 0)) * 100
                            if row_dict.get("vol")
                            else 0,
                            "amount": float(row_dict.get("amount", 0)) * 1000
                            if row_dict.get("amount")
                            else 0,
                            "amplitude": 0,
                            "change_percent": float(row_dict.get("pct_chg", 0))
                            if row_dict.get("pct_chg")
                            else 0,
                            "change_amount": 0,
                            "turnover_rate": 0,
                        }
                    )
                except (ValueError, TypeError, KeyError):
                    continue

            return history if history["klines"] else None

        except Exception:
            return None

    def fetch_history_akshare(self, code: str, days: int = 60) -> Optional[Dict[str, Any]]:
        """
        使用 AkShare 腾讯数据源获取股票历史K线数据

        Args:
            code: 股票代码 (如 sh600519, sz000001)
            days: 获取天数

        Returns:
            历史数据字典
        """
        try:
            df = self.akshare.stock_zh_a_hist_tx(symbol=code)

            if df is None or df.empty:
                return None

            history: Dict[str, Any] = {
                "code": code,
                "name": "",
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data_source": "AkShare-腾讯",
                "klines": [],
            }

            klines_list: List[Dict[str, Any]] = history["klines"]

            for _, row in df.tail(days).iterrows():
                try:
                    row_dict: Dict[str, Any] = (
                        row.to_dict() if hasattr(row, "to_dict") else dict(row)
                    )
                    klines_list.append(
                        {
                            "date": str(row_dict.get("date", "")),
                            "open": float(row_dict.get("open", 0)),
                            "close": float(row_dict.get("close", 0)),
                            "high": float(row_dict.get("high", 0)),
                            "low": float(row_dict.get("low", 0)),
                            "volume": float(row_dict.get("amount", 0)),
                            "amount": 0,
                            "amplitude": 0,
                            "change_percent": 0,
                            "change_amount": 0,
                            "turnover_rate": 0,
                        }
                    )
                except (ValueError, TypeError, KeyError):
                    continue

            return history if history["klines"] else None

        except Exception as e:
            print(f"AkShare 获取 {code} 历史数据失败: {e}")
            return None

    def fetch_history_akshare_daily(self, code: str, days: int = 60) -> Optional[Dict[str, Any]]:
        """
        使用 AkShare 东方财富数据源获取股票历史K线数据（包含换手率）

        Args:
            code: 股票代码 (如 sh600519, sz000001)
            days: 获取天数

        Returns:
            历史数据字典
        """
        try:
            stock_code = code[2:]

            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=days + 30)).strftime("%Y%m%d")

            df = self.akshare.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq",
            )

            if df is None or df.empty:
                return None

            history: Dict[str, Any] = {
                "code": code,
                "name": "",
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data_source": "AkShare-东方财富",
                "klines": [],
            }

            klines_list: List[Dict[str, Any]] = history["klines"]

            for _, row in df.tail(days).iterrows():
                try:
                    row_dict: Dict[str, Any] = (
                        row.to_dict() if hasattr(row, "to_dict") else dict(row)
                    )
                    klines_list.append(
                        {
                            "date": str(row_dict.get("日期", "")),
                            "open": float(row_dict.get("开盘", 0)),
                            "close": float(row_dict.get("收盘", 0)),
                            "high": float(row_dict.get("最高", 0)),
                            "low": float(row_dict.get("最低", 0)),
                            "volume": float(row_dict.get("成交量", 0)),
                            "amount": float(row_dict.get("成交额", 0)),
                            "amplitude": float(row_dict.get("振幅", 0)),
                            "change_percent": float(row_dict.get("涨跌幅", 0)),
                            "change_amount": float(row_dict.get("涨跌额", 0)),
                            "turnover_rate": float(row_dict.get("换手率", 0)),
                        }
                    )
                except (ValueError, TypeError, KeyError):
                    continue

            return history if history["klines"] else None

        except Exception as e:
            print(f"AkShare-东方财富 获取 {code} 历史数据失败: {e}")
            return None

    def fetch_history(self, code: str, days: int = 60) -> Optional[Dict[str, Any]]:
        """
        获取股票历史K线数据（自动选择数据源）

        优先级: Tushare > Baostock > AkShare-腾讯

        Args:
            code: 股票代码 (如 sh600519, sz000001)
            days: 获取天数

        Returns:
            历史数据字典
        """
        # 优先使用 Tushare（如果有 Token）
        if self._tushare_token:
            try:
                history = self.fetch_history_tushare(code, days)
                if history:
                    return history
            except Exception:
                pass

        # 使用 Baostock（免费，包含换手率）
        history = self.fetch_history_baostock(code, days)
        if history:
            return history

        # 回退到 AkShare-腾讯（稳定可用）
        return self.fetch_history_akshare(code, days)

    def fetch_batch_history(
        self,
        codes: List[str],
        days: int = 60,
        delay: float = 0.1,
        progress: bool = True,
    ) -> Dict[str, Dict[str, Any]]:
        """
        批量获取多只股票历史数据

        Args:
            codes: 股票代码列表
            days: 获取天数
            delay: 请求间隔（秒），避免请求过快
            progress: 是否显示进度

        Returns:
            股票代码到历史数据的映射
        """
        results = {}
        total = len(codes)

        for i, code in enumerate(codes):
            if progress and (i + 1) % 10 == 0:
                print(f"  进度: {i + 1}/{total} ({(i + 1) / total * 100:.1f}%)")

            history = self.fetch_history(code, days)
            if history:
                results[code] = history

            if delay > 0:
                time.sleep(delay)

        self.baostock_logout()

        return results

    def calculate_avg_metrics(self, history: Dict[str, Any], days: int = 60) -> Dict[str, float]:
        """
        计算历史平均指标

        Args:
            history: 历史数据
            days: 计算天数

        Returns:
            平均指标字典
        """
        klines = history.get("klines", [])

        if not klines:
            return {
                "avg_turnover_rate": 0,
                "avg_amount": 0,
                "avg_volume": 0,
            }

        recent_klines = klines[-days:] if len(klines) > days else klines

        if not recent_klines:
            return {
                "avg_turnover_rate": 0,
                "avg_amount": 0,
                "avg_volume": 0,
            }

        total_turnover = sum(k.get("turnover_rate", 0) for k in recent_klines)
        total_amount = sum(k.get("amount", 0) for k in recent_klines)
        total_volume = sum(k.get("volume", 0) for k in recent_klines)

        count = len(recent_klines)

        return {
            "avg_turnover_rate": total_turnover / count if count > 0 else 0,
            "avg_amount": total_amount / count if count > 0 else 0,
            "avg_volume": total_volume / count if count > 0 else 0,
        }

    def save_history_cache(self, histories: Dict[str, Dict[str, Any]]) -> None:
        """保存历史数据缓存"""
        cache_data = {
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data_source": "Tushare/AkShare",
            "total": len(histories),
            "data": histories,
        }

        with open(self.history_cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

        print(f"✅ 历史数据已保存到: {self.history_cache_file}")

    def load_history_cache(self) -> Dict[str, Dict[str, Any]]:
        """加载历史数据缓存"""
        if self.history_cache_file.exists():
            with open(self.history_cache_file, "r", encoding="utf-8") as f:
                data: Dict[str, Any] = json.load(f)
                result: Dict[str, Dict[str, Any]] = data.get("data", {})
                return result
        return {}

    def get_stocks_with_history(
        self,
        stocks: List[Dict[str, Any]],
        days: int = 60,
        use_cache: bool = True,
        delay: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """
        获取带历史数据的股票列表

        Args:
            stocks: 股票列表
            days: 历史天数
            use_cache: 是否使用缓存
            delay: 请求间隔

        Returns:
            带历史平均指标的股票列表
        """
        cached_histories = self.load_history_cache() if use_cache else {}

        need_fetch_codes = []
        for stock in stocks:
            code = stock.get("code", "")
            if code and code not in cached_histories:
                need_fetch_codes.append(code)

        if need_fetch_codes:
            data_source = "Tushare" if self._tushare_token else "AkShare"
            print(f"📡 正在获取 {len(need_fetch_codes)} 只股票的 {days} 日历史数据...")
            print(f"   数据源: {data_source} (优先) / AkShare-腾讯 (备选)")
            new_histories = self.fetch_batch_history(need_fetch_codes, days, delay=delay)
            cached_histories.update(new_histories)
            self.save_history_cache(cached_histories)

        result_stocks = []
        for stock in stocks:
            code = stock.get("code", "")
            history = cached_histories.get(code)

            if history:
                avg_metrics = self.calculate_avg_metrics(history, days)
                stock_with_history = {
                    **stock,
                    "avg_turnover_rate_60d": avg_metrics["avg_turnover_rate"],
                    "avg_amount_60d": avg_metrics["avg_amount"],
                    "avg_volume_60d": avg_metrics["avg_volume"],
                    "data_source": history.get("data_source", "Unknown"),
                }
                result_stocks.append(stock_with_history)
            else:
                result_stocks.append(stock)

        return result_stocks

    def get_stock_realtime_quote(self, code: str) -> Optional[Dict[str, Any]]:
        """
        获取单只股票实时行情

        Args:
            code: 股票代码

        Returns:
            实时行情数据
        """
        try:
            df = self.akshare.stock_zh_a_spot_em()

            if df is None or df.empty:
                return None

            stock_code = code[2:]
            row = df[df["代码"] == stock_code]

            if row.empty:
                return None

            row = row.iloc[0]

            return {
                "code": code,
                "name": row.get("名称", ""),
                "current_price": float(row.get("最新价", 0)),
                "change_percent": float(row.get("涨跌幅", 0)),
                "change_amount": float(row.get("涨跌额", 0)),
                "volume": float(row.get("成交量", 0)),
                "amount": float(row.get("成交额", 0)),
                "amplitude": float(row.get("振幅", 0)),
                "high": float(row.get("最高", 0)),
                "low": float(row.get("最低", 0)),
                "open": float(row.get("今开", 0)),
                "prev_close": float(row.get("昨收", 0)),
                "turnover_rate": float(row.get("换手率", 0)),
                "pe_ratio": float(row.get("市盈率-动态", 0)) if row.get("市盈率-动态") else 0,
                "pb_ratio": float(row.get("市净率", 0)) if row.get("市净率") else 0,
                "market_cap": float(row.get("总市值", 0)) / 100000000 if row.get("总市值") else 0,
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data_source": "AkShare",
            }

        except Exception as e:
            print(f"获取 {code} 实时行情失败: {e}")
            return None

    def check_cache_validity(self, max_age_hours: int = 24) -> Dict[str, Any]:
        """
        检查缓存数据的有效性

        Args:
            max_age_hours: 最大缓存时间（小时）

        Returns:
            检查结果字典
        """
        if not self.history_cache_file.exists():
            return {
                "valid": False,
                "reason": "缓存文件不存在",
                "total_stocks": 0,
                "need_update": [],
            }

        try:
            with open(self.history_cache_file, "r", encoding="utf-8") as f:
                cache_data: Dict[str, Any] = json.load(f)

            update_time_str = cache_data.get("update_time", "")
            if not update_time_str:
                return {
                    "valid": False,
                    "reason": "缓存缺少更新时间",
                    "total_stocks": len(cache_data.get("data", {})),
                    "need_update": [],
                }

            update_time = datetime.strptime(update_time_str, "%Y-%m-%d %H:%M:%S")
            age = datetime.now() - update_time
            age_hours = age.total_seconds() / 3600

            if age_hours > max_age_hours:
                return {
                    "valid": False,
                    "reason": f"缓存已过期 ({age_hours:.1f}小时 > {max_age_hours}小时)",
                    "total_stocks": len(cache_data.get("data", {})),
                    "update_time": update_time_str,
                    "need_update": [],
                }

            data: Dict[str, Dict[str, Any]] = cache_data.get("data", {})
            incomplete_stocks = []

            for code, history in data.items():
                klines: List[Dict[str, Any]] = history.get("klines", [])
                if len(klines) < 30:
                    incomplete_stocks.append(
                        {
                            "code": code,
                            "reason": f"数据不足 ({len(klines)}条 < 30条)",
                        }
                    )

            return {
                "valid": len(incomplete_stocks) == 0,
                "reason": "缓存有效" if not incomplete_stocks else f"{len(incomplete_stocks)}只股票数据不完整",
                "total_stocks": len(data),
                "update_time": update_time_str,
                "age_hours": age_hours,
                "incomplete_stocks": incomplete_stocks,
                "need_update": [s["code"] for s in incomplete_stocks],
            }

        except Exception as e:
            return {
                "valid": False,
                "reason": f"读取缓存失败: {e}",
                "total_stocks": 0,
                "need_update": [],
            }

    def incremental_update(
        self,
        stocks: List[Dict[str, Any]],
        days: int = 60,
        force_update: bool = False,
        delay: float = 0.3,
    ) -> Dict[str, Any]:
        """
        增量更新历史数据

        Args:
            stocks: 股票列表
            days: 历史天数
            force_update: 是否强制更新所有数据
            delay: 请求间隔

        Returns:
            更新结果
        """
        result: Dict[str, Any] = {
            "total": len(stocks),
            "cached": 0,
            "updated": 0,
            "failed": 0,
            "skipped": 0,
            "details": [],
        }

        if force_update:
            cached_histories = {}
            need_fetch_codes = [s.get("code", "") for s in stocks if s.get("code")]
        else:
            cached_histories = self.load_history_cache()
            cache_validity = self.check_cache_validity()

            need_fetch_codes = []

            for stock in stocks:
                code = stock.get("code", "")
                if not code:
                    continue

                if code not in cached_histories:
                    need_fetch_codes.append(code)
                    result["details"].append(
                        {
                            "code": code,
                            "status": "missing",
                            "message": "缓存中不存在",
                        }
                    )
                elif code in cache_validity.get("need_update", []):
                    need_fetch_codes.append(code)
                    result["details"].append(
                        {
                            "code": code,
                            "status": "incomplete",
                            "message": "数据不完整",
                        }
                    )
                else:
                    result["cached"] += 1
                    result["details"].append(
                        {
                            "code": code,
                            "status": "cached",
                            "message": "使用缓存数据",
                        }
                    )

        if need_fetch_codes:
            data_source = "Tushare" if self._tushare_token else "Baostock"
            print(f"📡 增量更新: 需要获取 {len(need_fetch_codes)} 只股票的历史数据...")
            print(f"   数据源: {data_source}")

            new_histories = self.fetch_batch_history(need_fetch_codes, days, delay=delay)

            for code in need_fetch_codes:
                if code in new_histories:
                    cached_histories[code] = new_histories[code]
                    result["updated"] += 1
                    for detail in result["details"]:
                        if detail["code"] == code:
                            detail["status"] = "updated"
                            detail["message"] = "更新成功"
                else:
                    result["failed"] += 1
                    for detail in result["details"]:
                        if detail["code"] == code:
                            detail["status"] = "failed"
                            detail["message"] = "获取失败"

            self.save_history_cache(cached_histories)

        result["success_rate"] = (
            (result["cached"] + result["updated"]) / result["total"] * 100
            if result["total"] > 0
            else 0
        )

        return result

    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        if not self.history_cache_file.exists():
            return {
                "exists": False,
                "total_stocks": 0,
                "total_klines": 0,
                "avg_klines_per_stock": 0,
                "data_sources": {},
            }

        try:
            with open(self.history_cache_file, "r", encoding="utf-8") as f:
                cache_data: Dict[str, Any] = json.load(f)

            data: Dict[str, Dict[str, Any]] = cache_data.get("data", {})
            total_stocks = len(data)
            total_klines = 0
            data_sources: Dict[str, int] = {}

            for code, history in data.items():
                klines: List[Dict[str, Any]] = history.get("klines", [])
                total_klines += len(klines)
                source = history.get("data_source", "Unknown")
                data_sources[source] = data_sources.get(source, 0) + 1

            return {
                "exists": True,
                "update_time": cache_data.get("update_time", ""),
                "total_stocks": total_stocks,
                "total_klines": total_klines,
                "avg_klines_per_stock": total_klines / total_stocks if total_stocks > 0 else 0,
                "data_sources": data_sources,
                "file_size_kb": self.history_cache_file.stat().st_size / 1024,
            }

        except Exception as e:
            return {
                "exists": True,
                "error": str(e),
                "total_stocks": 0,
            }

    def clear_cache(self) -> bool:
        """
        清除历史数据缓存

        Returns:
            是否成功
        """
        try:
            if self.history_cache_file.exists():
                self.history_cache_file.unlink()
                print(f"✅ 已清除历史数据缓存: {self.history_cache_file}")
            return True
        except Exception as e:
            print(f"❌ 清除缓存失败: {e}")
            return False


stock_history_fetcher = StockHistoryFetcher()
