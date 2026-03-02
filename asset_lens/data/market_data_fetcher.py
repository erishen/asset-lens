"""
Market data fetcher for asset-lens.
使用免费的金融数据 API 获取市场指数数据
"""

import json
import time
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..config import config
from ..data.market_index import IndexPerformance, MarketIndex, MarketIndexCache


class MarketDataFetcher:
    """市场数据获取器"""

    def __init__(self):
        self.cache_path = config.cache_path
        self.domestic_cache_file = self.cache_path / "market_index_domestic.json"
        self.foreign_cache_file = self.cache_path / "market_index_foreign.json"

        self.cache_path.mkdir(parents=True, exist_ok=True)

    def fetch_domestic_index_sina(self, index_code: str) -> Optional[Dict[str, Any]]:
        try:
            url = f"http://hq.sinajs.cn/list={index_code}"
            request = Request(url)
            request.add_header("Referer", "http://finance.sina.com.cn")

            with urlopen(request, timeout=10) as response:
                data = response.read().decode("gbk")

                if not data or "hq_str_" not in data:
                    return None

                data_str = data.split('"')[1]
                if not data_str:
                    return None

                parts = data_str.split(",")
                if len(parts) < 32:
                    return None

                name = parts[0]
                open_price = float(parts[1]) if parts[1] else 0
                prev_close = float(parts[2]) if parts[2] else 0
                current_price = float(parts[3]) if parts[3] else 0
                high = float(parts[4]) if parts[4] else 0
                low = float(parts[5]) if parts[5] else 0
                volume = int(parts[8]) if parts[8] else 0
                amount = float(parts[9]) if parts[9] else 0

                change_amount = current_price - prev_close if prev_close > 0 else 0
                change_percent = (change_amount / prev_close * 100) if prev_close > 0 else 0

                return {
                    "name": name,
                    "code": index_code,
                    "current_price": current_price,
                    "open": open_price,
                    "prev_close": prev_close,
                    "high": high,
                    "low": low,
                    "volume": volume,
                    "amount": amount,
                    "change_amount": change_amount,
                    "change_percent": change_percent,
                }

        except (URLError, HTTPError, ValueError, IndexError) as e:
            print(f"获取指数数据失败 {index_code}: {e}")
            return None

    def _load_existing_history(self) -> Dict[str, List[Dict]]:
        try:
            if self.domestic_cache_file.exists():
                with open(self.domestic_cache_file, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)
                    history_map = {}
                    for name, data in cache_data.get("指数数据", {}).items():
                        if "历史走势" in data:
                            history_map[name] = data["历史走势"]
                    return history_map
        except Exception:
            pass
        return {}

    def _update_history(self, existing_history: List[Dict], today_data: Dict) -> List[Dict]:
        today_entry = {
            "日期": today_data["数据日期"],
            "开盘": today_data["今开"],
            "收盘": today_data["最新价"],
            "最高": today_data["最高"],
            "最低": today_data["最低"],
            "成交量": today_data["成交量"],
        }

        if existing_history:
            if existing_history[0]["日期"] == today_entry["日期"]:
                existing_history[0] = today_entry
            else:
                existing_history.insert(0, today_entry)

            return existing_history[:7]
        else:
            return [today_entry]

    def _calculate_domestic_period_performance(self, history: List[Dict]) -> Dict[str, Any]:
        try:
            if not history:
                return {}

            latest_price = history[0]["收盘"]

            weekly_change = 0
            weekly_high = latest_price
            weekly_low = latest_price

            for i, day in enumerate(history[:5]):
                high = day["最高"]
                low = day["最低"]

                weekly_high = max(weekly_high, high)
                weekly_low = min(weekly_low, low)

                if i == 4:
                    price = day["收盘"]
                    weekly_change = ((latest_price - price) / price * 100) if price > 0 else 0

            weekly_amplitude = (
                ((weekly_high - weekly_low) / weekly_low * 100) if weekly_low > 0 else 0
            )

            monthly_change = 0
            if len(history) >= 22:
                price = history[21]["收盘"]
                monthly_change = ((latest_price - price) / price * 100) if price > 0 else 0

            ytd_change = 0
            current_year = datetime.now().year
            for day in history:
                if day["日期"].startswith(str(current_year - 1)):
                    price = day["收盘"]
                    ytd_change = ((latest_price - price) / price * 100) if price > 0 else 0
                    break

            return {
                "周涨跌幅": round(weekly_change, 2),
                "周最高": round(weekly_high, 2),
                "周最低": round(weekly_low, 2),
                "周振幅": round(weekly_amplitude, 2),
                "月涨跌幅": round(monthly_change, 2),
                "年初至今涨跌幅": round(ytd_change, 2),
            }

        except Exception as e:
            print(f"计算周期表现失败: {e}")
            return {}

    def _estimate_domestic_technical_status(
        self, history: List[Dict], current_price: float
    ) -> Dict[str, Any]:
        try:
            if len(history) < 2:
                return {}

            closes = [h["收盘"] for h in history]
            highs = [h["最高"] for h in history]
            lows = [h["最低"] for h in history]

            avg_close = sum(closes) / len(closes)

            if current_price > avg_close * 1.02:
                trend = "强势上涨"
            elif current_price > avg_close:
                trend = "震荡上行"
            elif current_price < avg_close * 0.98:
                trend = "震荡下行"
            else:
                trend = "震荡整理"

            support = min(lows)
            resistance = max(highs)

            rsi = self._calculate_rsi(closes)

            macd_status = "中性"
            if len(closes) >= 5:
                ema5 = sum(closes[:5]) / 5
                ema10 = sum(closes[:10]) / 10 if len(closes) >= 10 else ema5

                if ema5 > ema10 * 1.005:
                    macd_status = "金叉"
                elif ema5 < ema10 * 0.995:
                    macd_status = "死叉"

            return {
                "趋势": trend,
                "支撑位": round(support, 2),
                "阻力位": round(resistance, 2),
                "RSI": round(rsi, 1),
                "MACD": macd_status,
            }

        except Exception as e:
            print(f"估算技术状态失败: {e}")
            return {}

    def fetch_all_domestic_indexes(self) -> Dict[str, Any]:
        index_mapping = {
            "sh000001": "上证指数",
            "sh000300": "沪深300",
            "sh000905": "中证500",
            "sz399006": "创业板指",
            "sh000688": "科创50",
        }

        existing_history_map = self._load_existing_history()

        indexes = {}

        for code, name in index_mapping.items():
            print(f"正在获取 {name} 数据...")
            data = self.fetch_domestic_index_sina(code)

            if data:
                today_data = {
                    "名称": name,
                    "代码": code[2:],
                    "最新价": data["current_price"],
                    "涨跌额": data["change_amount"],
                    "涨跌幅": data["change_percent"],
                    "昨收": data["prev_close"],
                    "今开": data["open"],
                    "最高": data["high"],
                    "最低": data["low"],
                    "成交量": data["volume"],
                    "成交额": data["amount"],
                    "数据日期": datetime.now().strftime("%Y-%m-%d"),
                    "数据来源": "新浪财经（实时数据）",
                }

                existing_history = existing_history_map.get(name, [])
                history = self._update_history(existing_history, today_data)

                period_performance = self._calculate_domestic_period_performance(history)
                technical_status = self._estimate_domestic_technical_status(
                    history, data["current_price"]
                )

                today_data["历史走势"] = history
                today_data["周期表现"] = period_performance
                today_data["技术状态"] = technical_status

                indexes[name] = today_data
                print(f"  ✅ {name}: {data['change_percent']:+.2f}%")
            else:
                print(f"  ❌ {name}: 获取失败")

            time.sleep(0.5)

        cache_data = {
            "更新时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "数据日期": datetime.now().strftime("%Y-%m-%d"),
            "是否交易时间": self._is_trading_time(),
            "是否交易日": self._is_trading_day(),
            "指数数据": indexes,
        }

        return cache_data

    def fetch_foreign_index_timeseries(self, symbol: str, api_key: str) -> Optional[Dict[str, Any]]:
        try:
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={api_key}&outputsize=compact"
            request = Request(url)
            request.add_header("User-Agent", "Mozilla/5.0")

            with urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))

                if "Time Series (Daily)" not in data:
                    print(f"  ⚠️ {symbol}: 无历史数据")
                    return None

                time_series = data["Time Series (Daily)"]

                sorted_dates = sorted(time_series.keys(), reverse=True)

                if not sorted_dates:
                    return None

                latest_date = sorted_dates[0]
                latest_data = time_series[latest_date]

                current_price = float(latest_data.get("4. close", 0))
                open_price = float(latest_data.get("1. open", 0))
                high = float(latest_data.get("2. high", 0))
                low = float(latest_data.get("3. low", 0))
                volume = int(latest_data.get("5. volume", 0))

                prev_close = 0.0
                if len(sorted_dates) > 1:
                    prev_date = sorted_dates[1]
                    prev_close = float(time_series[prev_date].get("4. close", 0.0))

                if current_price == 0:
                    return None

                change_amount = current_price - prev_close if prev_close > 0 else 0
                change_percent = (change_amount / prev_close * 100) if prev_close > 0 else 0

                history = []
                for i, date in enumerate(sorted_dates[:7]):
                    day_data = time_series[date]
                    history.append(
                        {
                            "日期": date,
                            "开盘": float(day_data.get("1. open", 0)),
                            "收盘": float(day_data.get("4. close", 0)),
                            "最高": float(day_data.get("2. high", 0)),
                            "最低": float(day_data.get("3. low", 0)),
                            "成交量": int(day_data.get("5. volume", 0)),
                        }
                    )

                period_performance = self._calculate_period_performance(time_series, sorted_dates)

                technical_status = self._estimate_technical_status(history, current_price)

                return {
                    "symbol": symbol,
                    "name": symbol,
                    "current_price": current_price,
                    "prev_close": prev_close,
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "volume": volume,
                    "change_amount": change_amount,
                    "change_percent": change_percent,
                    "history": history,
                    "period_performance": period_performance,
                    "technical_status": technical_status,
                    "data_date": latest_date,
                }

        except (URLError, HTTPError, ValueError, KeyError) as e:
            print(f"获取海外指数历史数据失败 {symbol}: {e}")
            return None

    def _calculate_period_performance(
        self, time_series: Dict, sorted_dates: List[str]
    ) -> Dict[str, Any]:
        try:
            if not sorted_dates:
                return {}

            latest_price = float(time_series[sorted_dates[0]].get("4. close", 0))

            weekly_change = 0.0
            weekly_high = latest_price
            weekly_low = latest_price

            for i, date in enumerate(sorted_dates[:5]):
                day_data = time_series[date]
                price = float(day_data.get("4. close", 0))
                high = float(day_data.get("2. high", 0))
                low = float(day_data.get("3. low", 0))

                weekly_high = max(weekly_high, high)
                weekly_low = min(weekly_low, low)

                if i == 4:
                    weekly_change = ((latest_price - price) / price * 100) if price > 0 else 0.0

            weekly_amplitude = (
                ((weekly_high - weekly_low) / weekly_low * 100) if weekly_low > 0 else 0.0
            )

            monthly_change = 0.0
            for i, date in enumerate(sorted_dates[:22]):
                if i == 21:
                    price = float(time_series[date].get("4. close", 0.0))
                    monthly_change = ((latest_price - price) / price * 100) if price > 0 else 0.0

            ytd_change = 0.0
            current_year = datetime.now().year
            for date in sorted_dates:
                if date.startswith(str(current_year - 1)):
                    price = float(time_series[date].get("4. close", 0.0))
                    ytd_change = ((latest_price - price) / price * 100) if price > 0 else 0.0
                    break

            return {
                "周涨跌幅": round(weekly_change, 2),
                "周最高": round(weekly_high, 2),
                "周最低": round(weekly_low, 2),
                "周振幅": round(weekly_amplitude, 2),
                "月涨跌幅": round(monthly_change, 2),
                "年初至今涨跌幅": round(ytd_change, 2),
            }

        except Exception as e:
            print(f"计算周期表现失败: {e}")
            return {}

    def _estimate_technical_status(
        self, history: List[Dict], current_price: float
    ) -> Dict[str, Any]:
        try:
            if len(history) < 5:
                return {}

            closes = [h["收盘"] for h in history]
            highs = [h["最高"] for h in history]
            lows = [h["最低"] for h in history]

            avg_close = sum(closes) / len(closes)

            if current_price > avg_close * 1.02:
                trend = "强势上涨"
            elif current_price > avg_close:
                trend = "震荡上行"
            elif current_price < avg_close * 0.98:
                trend = "震荡下行"
            else:
                trend = "震荡整理"

            support = min(lows)
            resistance = max(highs)

            rsi = self._calculate_rsi(closes)

            macd_status = "中性"
            if len(closes) >= 5:
                ema5 = sum(closes[:5]) / 5
                ema10 = sum(closes[:10]) / 10 if len(closes) >= 10 else ema5

                if ema5 > ema10 * 1.005:
                    macd_status = "金叉"
                elif ema5 < ema10 * 0.995:
                    macd_status = "死叉"

            return {
                "趋势": trend,
                "支撑位": round(support, 0),
                "阻力位": round(resistance, 0),
                "RSI": round(rsi, 1),
                "MACD": macd_status,
            }

        except Exception as e:
            print(f"估算技术状态失败: {e}")
            return {}

    def _calculate_rsi(self, closes: List[float], period: int = 14) -> float:
        try:
            if len(closes) < period + 1:
                period = len(closes) - 1

            if period < 2:
                return 50.0

            gains: List[float] = []
            losses: List[float] = []

            for i in range(1, min(period + 1, len(closes))):
                change = closes[i - 1] - closes[i]
                if change > 0:
                    gains.append(change)
                    losses.append(0.0)
                else:
                    gains.append(0.0)
                    losses.append(abs(change))

            if not gains and not losses:
                return 50.0

            avg_gain = sum(gains) / len(gains) if gains else 0
            avg_loss = sum(losses) / len(losses) if losses else 0

            if avg_loss == 0:
                return 100.0

            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

            return rsi

        except Exception:
            return 50.0

    def fetch_foreign_index_alphavantage(
        self, symbol: str, api_key: str
    ) -> Optional[Dict[str, Any]]:
        try:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
            request = Request(url)
            request.add_header("User-Agent", "Mozilla/5.0")

            with urlopen(request, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))

                if "Global Quote" not in data:
                    return None

                quote = data["Global Quote"]

                current_price = float(quote.get("05. price", 0))
                prev_close = float(quote.get("08. previous close", 0))

                if current_price == 0 or prev_close == 0:
                    return None

                change_amount = current_price - prev_close
                change_percent = (change_amount / prev_close * 100) if prev_close > 0 else 0

                return {
                    "symbol": symbol,
                    "name": symbol,
                    "current_price": current_price,
                    "prev_close": prev_close,
                    "change_amount": change_amount,
                    "change_percent": change_percent,
                }

        except (URLError, HTTPError, ValueError, KeyError) as e:
            print(f"获取海外指数数据失败 {symbol}: {e}")
            return None

    def fetch_all_foreign_indexes(self, api_key: Optional[str] = None) -> Dict[str, Any]:
        if not api_key:
            api_key = config.alphavantage_api_key or "demo"

        index_mapping = {
            "QQQ": "Invesco QQQ Trust",
            "SPY": "SPDR S&P 500 ETF",
            "GLD": "SPDR Gold Shares",
        }

        indexes = {}

        for symbol, name in index_mapping.items():
            print(f"正在获取 {symbol} 数据...")

            data = self.fetch_foreign_index_timeseries(symbol, api_key)

            if data:
                indexes[f"{symbol}-{name}"] = {
                    "名称": f"{symbol}-{name}",
                    "代码": symbol,
                    "最新价": data["current_price"],
                    "涨跌额": data["change_amount"],
                    "涨跌幅": data["change_percent"],
                    "昨收": data["prev_close"],
                    "今开": data["open"],
                    "最高": data["high"],
                    "最低": data["low"],
                    "成交量": data["volume"],
                    "成交额": data["volume"] * data["current_price"],
                    "数据日期": data["data_date"],
                    "数据来源": "alphavantage（实时数据 + 完整历史）",
                    "周期表现": data["period_performance"],
                    "历史走势": data["history"],
                    "技术状态": data["technical_status"],
                }
                print(f"  ✅ {symbol}: {data['change_percent']:+.2f}%")
            else:
                print(f"  ❌ {symbol}: 获取失败")

            time.sleep(12)

        cache_data = {
            "更新时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "数据日期": datetime.now().strftime("%Y-%m-%d"),
            "是否交易时间": False,
            "是否交易日": True,
            "指数数据": indexes,
        }

        return cache_data

    def fetch_foreign_index_finnhub(self, symbol: str, api_key: str) -> Optional[Dict[str, Any]]:
        try:
            url = f"https://api.finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}"
            request = Request(url)
            request.add_header("User-Agent", "Mozilla/5.0")

            with urlopen(request, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))

                current_price = float(data.get("c", 0))
                prev_close = float(data.get("pc", 0))
                high = float(data.get("h", 0))
                low = float(data.get("l", 0))
                open_price = float(data.get("o", 0))

                if current_price == 0 or prev_close == 0:
                    return None

                change_amount = current_price - prev_close
                change_percent = (change_amount / prev_close * 100) if prev_close > 0 else 0

                return {
                    "symbol": symbol,
                    "name": symbol,
                    "current_price": current_price,
                    "prev_close": prev_close,
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "change_amount": change_amount,
                    "change_percent": change_percent,
                }

        except (URLError, HTTPError, ValueError, KeyError) as e:
            print(f"获取海外指数数据失败 {symbol}: {e}")
            return None

    def update_domestic_cache(self) -> bool:
        print("\n📊 更新国内市场指数数据...")

        data = self.fetch_all_domestic_indexes()

        if not data.get("指数数据"):
            print("❌ 没有获取到任何国内指数数据")
            return False

        with open(self.domestic_cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ 国内市场指数数据已保存到: {self.domestic_cache_file}")
        return True

    def update_foreign_cache_alphavantage(self) -> bool:
        print("\n📊 更新海外市场指数数据 (Alpha Vantage API)...")

        data = self.fetch_all_foreign_indexes()

        if not data.get("指数数据"):
            print("❌ 没有获取到任何海外指数数据")
            return False

        with open(self.foreign_cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ 海外市场指数数据已保存到: {self.foreign_cache_file}")
        return True

    def update_foreign_cache_finnhub(self) -> bool:
        print("\n📊 更新海外市场指数数据 (Finnhub API)...")

        api_key = config.finnhub_api_key or "demo"

        index_mapping = {
            "QQQ": "纳斯达克100 ETF",
            "SPY": "标普500 ETF",
            "GLD": "黄金 ETF",
        }

        indexes = {}

        for symbol, name in index_mapping.items():
            print(f"正在获取 {name} 数据...")
            data = self.fetch_foreign_index_finnhub(symbol, api_key)

            if data:
                indexes[f"{symbol}-{name}"] = {
                    "名称": f"{symbol}-{name}",
                    "代码": symbol,
                    "最新价": data["current_price"],
                    "涨跌额": data["change_amount"],
                    "涨跌幅": data["change_percent"],
                    "昨收": data["prev_close"],
                    "今开": data["open"],
                    "最高": data["high"],
                    "最低": data["low"],
                    "数据日期": datetime.now().strftime("%Y-%m-%d"),
                    "数据来源": "finnhub（实时数据）",
                }
                print(f"  ✅ {name}: {data['change_percent']:+.2f}%")
            else:
                print(f"  ❌ {name}: 获取失败")

            time.sleep(1)

        if not indexes:
            print("❌ 没有获取到任何海外指数数据")
            return False

        cache_data = {
            "更新时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "数据日期": datetime.now().strftime("%Y-%m-%d"),
            "是否交易时间": False,
            "是否交易日": True,
            "指数数据": indexes,
        }

        with open(self.foreign_cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

        print(f"✅ 海外市场指数数据已保存到: {self.foreign_cache_file}")
        return True

    def update_all_cache(self, api: str = "finnhub") -> bool:
        print("\n🚀 开始更新市场指数数据...")

        if api == "finnhub":
            domestic_success = self.update_domestic_cache()
            foreign_success = self.update_foreign_cache_finnhub()
        elif api == "alphavantage":
            domestic_success = self.update_domestic_cache()
            foreign_success = self.update_foreign_cache_alphavantage()
        else:
            domestic_success = self.update_domestic_cache()
            foreign_success = self.update_foreign_cache_alphavantage()

        if domestic_success or foreign_success:
            print("\n✅ 市场指数数据更新完成！")
            return True
        else:
            print("\n❌ 市场指数数据更新失败！")
            return False

    def _is_trading_time(self) -> bool:
        now = datetime.now()
        if now.weekday() >= 5:
            return False

        hour = now.hour
        minute = now.minute

        if hour == 9 and minute >= 30:
            return True
        if hour == 10:
            return True
        if hour == 11 and minute <= 30:
            return True

        if hour == 13:
            return True
        if hour == 14:
            return True
        if hour == 15 and minute == 0:
            return True

        return False

    def _is_trading_day(self) -> bool:
        now = datetime.now()
        return now.weekday() < 5
