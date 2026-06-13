import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


class DomesticIndexFetcherMixin:
    def _fetch_from_akshare_spot(self, index_code: str) -> dict[str, Any] | None:
        try:
            df = self.akshare.stock_zh_index_spot_em()  # type: ignore[attr-defined]
            if df is None or df.empty:
                return None

            code = index_code[2:] if index_code.startswith(("sh", "sz")) else index_code
            row = df[df["代码"] == code]

            if row.empty:
                return None

            row = row.iloc[0]
            current_price = float(row.get("最新价", 0))
            prev_close = float(row.get("昨收", 0))

            if current_price == 0:
                return None

            return {
                "name": row.get("名称", ""),
                "code": index_code,
                "current_price": current_price,
                "open": float(row.get("今开", 0)),
                "prev_close": prev_close,
                "high": float(row.get("最高", 0)),
                "low": float(row.get("最低", 0)),
                "volume": int(float(row.get("成交量", 0) or 0)),
                "amount": float(row.get("成交额", 0) or 0),
                "change_amount": current_price - prev_close,
                "change_percent": ((current_price - prev_close) / prev_close * 100) if prev_close > 0 else 0,
                "source": "akshare_spot",
            }
        except (ValueError, KeyError, TypeError) as e:
            logger.debug(f"AkShare spot 数据解析失败 {index_code}: {e}")
            return None
        except (ConnectionError, RuntimeError, OSError) as e:
            logger.debug(f"AkShare spot 获取失败 {index_code}: {e}")
            return None

    def _fetch_from_akshare_hist(self, index_code: str) -> dict[str, Any] | None:
        try:
            code = index_code[2:] if index_code.startswith(("sh", "sz")) else index_code
            df = self.akshare.index_zh_a_hist(  # type: ignore[attr-defined]
                symbol=code,
                period="daily",
                start_date=(datetime.now() - timedelta(days=7)).strftime("%Y%m%d"),
                end_date=datetime.now().strftime("%Y%m%d"),
            )

            if df is None or df.empty:
                return None

            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest

            current_price = float(latest.get("收盘", 0))
            prev_close = float(prev.get("收盘", 0))

            if current_price == 0:
                return None

            return {
                "name": self.DOMESTIC_INDEXES.get(index_code, index_code),  # type: ignore[attr-defined]
                "code": index_code,
                "current_price": current_price,
                "open": float(latest.get("开盘", 0)),
                "prev_close": prev_close,
                "high": float(latest.get("最高", 0)),
                "low": float(latest.get("最低", 0)),
                "volume": int(float(latest.get("成交量", 0) or 0)),
                "amount": 0,
                "change_amount": current_price - prev_close,
                "change_percent": ((current_price - prev_close) / prev_close * 100) if prev_close > 0 else 0,
                "source": "akshare_hist",
            }
        except (ValueError, KeyError, TypeError) as e:
            logger.debug(f"AkShare hist 数据解析失败 {index_code}: {e}")
            return None
        except (ConnectionError, RuntimeError, OSError) as e:
            logger.debug(f"AkShare hist 获取失败 {index_code}: {e}")
            return None

    def _fetch_from_sina(self, index_code: str) -> dict[str, Any] | None:
        try:
            sina_codes = {
                "sh000001": "s_sh000001",
                "sh000300": "s_sh000300",
                "sh000905": "s_sh000905",
                "sz399006": "s_sz399006",
                "sh000688": "s_sh000688",
            }

            sina_code = sina_codes.get(index_code)
            if not sina_code:
                return None

            url = f"http://hq.sinajs.cn/list={sina_code}"
            headers = {"Referer": "http://finance.sina.com.cn"}
            response = self._http_client.get(url, headers=headers, timeout=10)  # type: ignore[attr-defined]

            if response is None:
                return None

            text = response.text
            if not text or "var hq_str_" not in text:
                return None

            parts = text.split('"')[1].split(",")
            if len(parts) < 4:
                return None

            name = parts[0]
            current_price = float(parts[1])
            change_amount = float(parts[2])
            change_percent = float(parts[3])
            prev_close = current_price - change_amount if change_amount else current_price

            return {
                "name": name,
                "code": index_code,
                "current_price": current_price,
                "open": 0,
                "prev_close": prev_close,
                "high": 0,
                "low": 0,
                "volume": 0,
                "amount": 0,
                "change_amount": change_amount,
                "change_percent": change_percent,
                "source": "sina",
            }
        except (ConnectionError, TimeoutError) as e:
            logger.debug(f"新浪财经网络错误 {index_code}: {e}")
            return None
        except (ValueError, IndexError) as e:
            logger.debug(f"新浪财经数据解析失败 {index_code}: {e}")
            return None
        except (OSError, RuntimeError) as e:
            logger.debug(f"新浪财经获取失败 {index_code}: {e}")
            return None

    def _fetch_from_tencent(self, index_code: str) -> dict[str, Any] | None:
        try:
            tencent_codes = {
                "sh000001": "sh000001",
                "sh000300": "sh000300",
                "sh000905": "sh000905",
                "sz399006": "sz399006",
                "sh000688": "sh000688",
                "sh518880": "sh518880",
            }

            tencent_code = tencent_codes.get(index_code)
            if not tencent_code:
                return None

            url = f"http://qt.gtimg.cn/q={tencent_code}"
            response = self._http_client.get(url, timeout=10)  # type: ignore[attr-defined]

            if response is None:
                return None

            text = response.text
            if not text or "~" not in text:
                return None

            parts = text.split("~")
            if len(parts) < 40:
                return None

            current_price = float(parts[3]) if parts[3] else 0
            prev_close = float(parts[4]) if parts[4] else 0

            if current_price == 0:
                return None

            return {
                "name": parts[1] if len(parts) > 1 else "",
                "code": index_code,
                "current_price": current_price,
                "open": float(parts[5]) if len(parts) > 5 and parts[5] else 0,
                "prev_close": prev_close,
                "high": float(parts[33]) if len(parts) > 33 and parts[33] else 0,
                "low": float(parts[34]) if len(parts) > 34 and parts[34] else 0,
                "volume": int(float(parts[6]) if len(parts) > 6 and parts[6] else 0),
                "amount": float(parts[37]) if len(parts) > 37 and parts[37] else 0,
                "change_amount": current_price - prev_close,
                "change_percent": float(parts[32]) if len(parts) > 32 and parts[32] else 0,
                "source": "tencent",
            }
        except (ConnectionError, TimeoutError) as e:
            logger.debug(f"腾讯财经网络错误 {index_code}: {e}")
            return None
        except (ValueError, IndexError) as e:
            logger.debug(f"腾讯财经数据解析失败 {index_code}: {e}")
            return None
        except (OSError, RuntimeError) as e:
            logger.debug(f"腾讯财经获取失败 {index_code}: {e}")
            return None

    def fetch_domestic_index(self, index_code: str) -> dict[str, Any] | None:
        cached = self._get_from_cache(f"domestic_{index_code}")  # type: ignore[attr-defined]
        if cached:
            return cached  # type: ignore[no-any-return]

        sources = self._sources.get(index_code, [])  # type: ignore[attr-defined]
        for source in sources:
            if not source.enabled:
                continue

            try:
                result = None
                if source.name == "akshare_spot":
                    result = self._fetch_from_akshare_spot(index_code)
                elif source.name == "akshare_hist":
                    result = self._fetch_from_akshare_hist(index_code)
                elif source.name == "sina":
                    result = self._fetch_from_sina(index_code)
                elif source.name == "tencent":
                    result = self._fetch_from_tencent(index_code)

                if result:
                    source.mark_success()
                    self._set_cache(f"domestic_{index_code}", result)  # type: ignore[attr-defined]
                    return result
                else:
                    source.mark_failure()
            except (ValueError, KeyError, ConnectionError, RuntimeError) as e:
                logger.debug(f"数据源 {source.name} 获取 {index_code} 失败: {e}")
                source.mark_failure()

        return None

    def fetch_all_domestic_indexes(self) -> dict[str, Any]:
        results = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:  # type: ignore[attr-defined]
            futures = {executor.submit(self.fetch_domestic_index, code): code for code in self.DOMESTIC_INDEXES}  # type: ignore[attr-defined]

            for future in as_completed(futures):
                code = futures[future]
                try:
                    result = future.result()
                    if result:
                        results[code] = result
                except (ValueError, KeyError, RuntimeError) as e:
                    logger.debug(f"获取 {code} 失败: {e}")

        return {
            "指数数据": results,
            "total": len(results),
            "更新时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def fetch_domestic_indexes_fast(self, key_indexes: list[str] | None = None) -> dict[str, Any]:
        if key_indexes is None:
            key_indexes = ["sh000001", "sz399006", "sh000300"]

        results = {}
        for code in key_indexes:
            result = self.fetch_domestic_index(code)
            if result:
                results[code] = result

        return {
            "指数数据": results,
            "total": len(results),
            "更新时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
