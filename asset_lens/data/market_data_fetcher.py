"""
Market data fetcher for asset-lens.
市场指数数据获取模块 - 获取国内外市场指数数据

数据源: AkShare (开源免费，无需注册)
- GitHub: https://github.com/akfamily/akshare
- 文档: https://akshare.akfamily.xyz
"""

import json
import time
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import config
from ..data.market_index import IndexPerformance, MarketIndex, MarketIndexCache


class MarketDataFetcher:
    """市场数据获取器 - 使用 AkShare 开源库"""

    def __init__(self):
        self.cache_path = config.cache_path
        self.domestic_cache_file = self.cache_path / "market_index_domestic.json"
        self.foreign_cache_file = self.cache_path / "market_index_foreign.json"
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self._akshare = None

    @property
    def akshare(self):
        """延迟加载 AkShare"""
        if self._akshare is None:
            try:
                import akshare as ak

                self._akshare = ak
            except ImportError:
                raise ImportError(
                    "请先安装 AkShare: pip install akshare\n"
                    "AkShare 是一个开源免费的金融数据接口，无需注册\n"
                    "GitHub: https://github.com/akfamily/akshare"
                )
        return self._akshare

    def fetch_domestic_index_akshare(self, index_code: str) -> Optional[Dict[str, Any]]:
        """
        获取国内指数数据（AkShare）

        Args:
            index_code: 指数代码（如 sh000001, sz399006）

        Returns:
            指数数据
        """
        try:
            # 使用 AkShare 获取A股指数实时行情
            df = self.akshare.stock_zh_index_spot_em()

            if df is None or df.empty:
                return None

            # 提取代码（去掉前缀）
            code = index_code[2:]

            # 查找对应指数
            row = df[df["代码"] == code]

            if row.empty:
                return None

            row = row.iloc[0]

            current_price = float(row.get("最新价", 0))
            prev_close = float(row.get("昨收", 0))
            open_price = float(row.get("今开", 0))
            high = float(row.get("最高", 0))
            low = float(row.get("最低", 0))
            volume = float(row.get("成交量", 0)) if row.get("成交量") else 0
            amount = float(row.get("成交额", 0)) if row.get("成交额") else 0

            change_amount = current_price - prev_close if prev_close > 0 else 0
            change_percent = (change_amount / prev_close * 100) if prev_close > 0 else 0

            return {
                "name": row.get("名称", ""),
                "code": index_code,
                "current_price": current_price,
                "open": open_price,
                "prev_close": prev_close,
                "high": high,
                "low": low,
                "volume": int(volume),
                "amount": amount,
                "change_amount": change_amount,
                "change_percent": change_percent,
            }

        except Exception as e:
            print(f"获取指数数据失败 {index_code}: {e}")
            return None

    def _load_existing_history(self) -> Dict[str, List[Dict]]:
        """加载历史数据"""
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
        """更新历史数据"""
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
        """计算周期表现"""
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
        """估算技术状态"""
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

    def _calculate_rsi(self, closes: List[float], period: int = 14) -> float:
        """计算 RSI"""
        try:
            if len(closes) < period + 1:
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

            avg_gain = sum(gains) / period if gains else 0
            avg_loss = sum(losses) / period if losses else 0

            if avg_loss == 0:
                return 100.0

            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            return rsi

        except Exception:
            return 50.0

    def fetch_all_domestic_indexes(self) -> Dict[str, Any]:
        """获取所有国内指数"""
        index_mapping = {
            "sh000001": "上证指数",
            "sh000300": "沪深300",
            "sh000905": "中证500",
            "sz399006": "创业板指",
            "sh000688": "科创50",
        }

        gold_mapping = {
            "sh518880": "黄金ETF",
        }

        existing_history_map = self._load_existing_history()
        indexes = {}

        for code, name in index_mapping.items():
            print(f"正在获取 {name} 数据...")
            data = self.fetch_domestic_index_akshare(code)

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
                    "数据来源": "AkShare（开源数据）",
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

            time.sleep(0.1)

        for code, name in gold_mapping.items():
            print(f"正在获取 {name} 数据...")
            data = self.fetch_domestic_index_akshare(code)

            if data:
                today_data = {
                    "名称": name,
                    "代码": code,
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
                    "数据来源": "AkShare（开源数据）",
                }
                indexes[name] = today_data
                print(f"  ✅ {name}: {data['change_percent']:+.2f}%")
            else:
                print(f"  ❌ {name}: 获取失败")

            time.sleep(0.1)

        cache_data = {
            "更新时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "指数数据": indexes,
        }

        with open(self.domestic_cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

        return cache_data

    def fetch_foreign_index(self, symbol: str, api_key: str) -> Optional[Dict[str, Any]]:
        """获取国外指数数据（Finnhub 正规 API）"""
        import requests  # type: ignore

        try:
            url = f"https://api.finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}"
            response = requests.get(url, timeout=10)
            data = response.json()

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
                "current_price": current_price,
                "open": open_price,
                "prev_close": prev_close,
                "high": high,
                "low": low,
                "change_amount": change_amount,
                "change_percent": change_percent,
            }

        except Exception as e:
            print(f"获取国外指数失败 {symbol}: {e}")
            return None

    def fetch_all_foreign_indexes(self) -> Dict[str, Any]:
        """获取所有国外指数"""
        api_key = config.finnhub_api_key or "demo"

        index_mapping = {
            "^DJI": "道琼斯",
            "^GSPC": "标普500",
            "^IXIC": "纳斯达克",
            "^N225": "日经225",
            "^HSI": "恒生指数",
        }

        indexes = {}

        for symbol, name in index_mapping.items():
            print(f"正在获取 {name} 数据...")
            data = self.fetch_foreign_index(symbol, api_key)

            if data:
                indexes[name] = {
                    "名称": name,
                    "代码": symbol,
                    "最新价": data["current_price"],
                    "涨跌额": data["change_amount"],
                    "涨跌幅": data["change_percent"],
                    "昨收": data["prev_close"],
                    "今开": data["open"],
                    "最高": data["high"],
                    "最低": data["low"],
                    "数据日期": datetime.now().strftime("%Y-%m-%d"),
                    "数据来源": "Finnhub（正规API）",
                }
                print(f"  ✅ {name}: {data['change_percent']:+.2f}%")
            else:
                print(f"  ❌ {name}: 获取失败")

            time.sleep(0.5)

        cache_data = {
            "更新时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "指数数据": indexes,
        }

        with open(self.foreign_cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

        return cache_data


market_data_fetcher = MarketDataFetcher()
