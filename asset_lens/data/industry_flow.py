import contextlib
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


class IndustryFlowMixin:
    def get_north_flow_by_industry(self, use_cache: bool = True, force: bool = False) -> pd.DataFrame:
        cache_file = self.cache_path / "north_industry_flow_cache.json"  # type: ignore[attr-defined]

        if use_cache:
            cached_df = self._load_industry_cache(cache_file)
            if cached_df is not None and not cached_df.empty:
                cache_time = None
                if "cache_time" in cached_df.columns and len(cached_df) > 0:
                    cache_time = cached_df["cache_time"].iloc[0]

                if cache_time:
                    logger.info(f"使用缓存的行业流向数据(缓存时间: {cache_time})")
                else:
                    logger.info("使用缓存的行业流向数据")

                return cached_df.drop(columns=["cache_time"], errors="ignore")

        try:
            logger.info("获取行业资金流向数据...")
            df = self._fetch_industry_flow_from_akshare()

            if df is not None and not df.empty:
                if self._validate_industry_data(df):
                    self._save_industry_cache(cache_file, df)
                    logger.info(f"✅ 成功获取并缓存 {len(df)} 个行业的资金流向数据")
                    return df
                else:
                    logger.warning("数据验证失败")
                    return pd.DataFrame()
            else:
                logger.warning("未获取到数据")
                return pd.DataFrame()

        except (ValueError, KeyError, ConnectionError, OSError, RuntimeError) as e:
            logger.error(f"获取行业资金流向数据失败: {e}")
            import traceback

            traceback.print_exc()
            return pd.DataFrame()

    def _fetch_industry_flow_from_akshare(self) -> pd.DataFrame | None:
        if self.akshare:  # type: ignore[attr-defined]
            logger.info("尝试从AkShare获取北向持股行业数据（真正的北向资金）...")
            try:
                df = self._fetch_north_holding_from_akshare()
                if df is not None and not df.empty:
                    logger.info(f"✅ 成功从AkShare北向持股获取 {len(df)} 个行业数据")
                    return df
            except (ValueError, KeyError, ConnectionError, RuntimeError) as e:
                logger.warning(f"AkShare北向持股获取失败: {e}")

        logger.info("AkShare北向持股获取失败，尝试东方财富push2接口...")
        df = self._fetch_industry_flow_from_push2()  # type: ignore[attr-defined]
        if df is not None and not df.empty:
            logger.info(f"✅ 成功从东方财富push2接口获取 {len(df)} 个行业数据")
            return df

        logger.info("尝试使用Playwright从东方财富获取行业资金流向数据...")
        df = self._fetch_industry_flow_from_eastmoney_playwright()  # type: ignore[attr-defined]
        if df is not None and not df.empty:
            logger.info(f"✅ 成功从东方财富Playwright获取 {len(df)} 个行业数据")
            return df

        logger.warning("以上数据源均失败，尝试新浪行业板块（全市场代理数据，非北向）...")
        df = self._fetch_industry_flow_from_sina()  # type: ignore[attr-defined]
        if df is not None and not df.empty:
            logger.info(f"✅ 成功从新浪行业板块获取 {len(df)} 个行业数据（注意：非北向数据，为全市场代理）")
            return df

        return None

    def _fetch_north_holding_from_akshare(self) -> pd.DataFrame | None:
        max_retries = 2
        for attempt in range(max_retries):
            try:
                import signal

                start_time = time.time()

                if attempt > 0:
                    wait_time = attempt * 3
                    logger.info(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)

                now = datetime.now()
                current_hour = now.hour
                current_minute = now.minute
                is_trading_time = (9 <= current_hour < 15) or (current_hour == 9 and current_minute >= 30)

                timeout = 60

                if is_trading_time:
                    logger.info(f"⏳ 正在获取北向资金持股数据(开市时间，超时{timeout}秒)...")
                else:
                    logger.info(f"⏳ 正在获取北向资金持股数据(非开市时间，超时{timeout}秒)...")

                def timeout_handler(signum, frame):
                    raise TimeoutError("数据获取超时")

                try:
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(timeout)
                except (AttributeError, ValueError) as e:
                    logger.debug("行业资金流数据解析失败: %s", e)

                try:
                    df = self.akshare.stock_hsgt_hold_stock_em(market="北向")  # type: ignore[attr-defined]

                    if df is None:
                        logger.warning("AkShare接口返回None")
                        if attempt < max_retries - 1:
                            continue
                        return None
                except (ValueError, KeyError, ConnectionError, RuntimeError) as e:
                    logger.warning(f"数据解析错误: {e}")
                    logger.warning("AkShare接口返回数据格式异常，可能是数据源问题")
                    if attempt < max_retries - 1:
                        continue
                    return None
                finally:
                    with contextlib.suppress(AttributeError, ValueError):
                        signal.alarm(0)

                fetch_time = time.time() - start_time
                logger.info(f"✅ 数据获取完成，耗时 {fetch_time:.2f} 秒")

                if df is None:
                    logger.warning("AkShare接口返回None")
                    logger.warning("可能原因：数据源暂时不可用、接口维护或数据格式变化")
                    if attempt < max_retries - 1:
                        continue
                    return None

                if df.empty:
                    logger.warning("未获取到北向资金持股数据（返回空数据）")
                    logger.warning("可能原因：数据源暂时不可用、接口维护或数据格式变化")
                    if attempt < max_retries - 1:
                        continue
                    return None

                logger.info(f"获取到 {len(df)} 条持股数据")

                try:
                    columns = df.columns.tolist()
                    logger.debug(f"数据列名: {columns}")
                except (ValueError, AttributeError) as e:
                    logger.warning(f"获取列名失败: {e}")
                    if attempt < max_retries - 1:
                        continue
                    return None

                industry_col = None
                for col in df.columns:
                    if "板块" in col or "行业" in col:
                        industry_col = col
                        break

                if not industry_col:
                    logger.warning("数据中没有行业/板块相关列")
                    return None

                logger.debug(f"使用行业列: {industry_col}")

                value_cols = [col for col in df.columns if "市值" in col or "增持" in col]

                if not value_cols:
                    logger.warning("数据中没有市值相关列")
                    return None

                logger.debug(f"找到市值列: {value_cols}")

                today_col = None
                for col in value_cols:
                    if "今日" in col:
                        today_col = col
                        break

                if not today_col:
                    today_col = value_cols[0]

                logger.info(f"使用市值列: {today_col}")

                five_day_col = None
                for col in df.columns:
                    if "5日" in col and "市值" in col:
                        five_day_col = col
                        break

                if five_day_col:
                    logger.info(f"找到5日增持列: {five_day_col}")

                logger.info("正在按行业聚合数据...")
                agg_start = time.time()

                if five_day_col:
                    industry_flow = df.groupby(industry_col).agg({today_col: "sum", five_day_col: "sum"}).reset_index()

                    industry_flow.columns = ["industry", "today_holding", "five_day_holding"]

                    industry_flow["net_inflow"] = industry_flow["today_holding"] - industry_flow["five_day_holding"]

                    max_val = abs(industry_flow["today_holding"].max())
                    if max_val > 1e9:
                        logger.info("检测到数据单位为'元',正在转换为'亿'...")
                        industry_flow["today_holding"] = industry_flow["today_holding"] / 1e8
                        industry_flow["five_day_holding"] = industry_flow["five_day_holding"] / 1e8
                        industry_flow["net_inflow"] = industry_flow["net_inflow"] / 1e8
                    elif max_val > 1e6:
                        logger.info("检测到数据单位为'万元',正在转换为'亿'...")
                        industry_flow["today_holding"] = industry_flow["today_holding"] / 1e4
                        industry_flow["five_day_holding"] = industry_flow["five_day_holding"] / 1e4
                        industry_flow["net_inflow"] = industry_flow["net_inflow"] / 1e4

                    def calc_change_rate(row):
                        if abs(row["five_day_holding"]) < 1:
                            return 0.0
                        rate = row["net_inflow"] / abs(row["five_day_holding"]) * 100
                        return max(-100, min(1000, rate))

                    industry_flow["change_rate"] = industry_flow.apply(calc_change_rate, axis=1)
                else:
                    industry_flow = df.groupby(industry_col).agg({today_col: "sum"}).reset_index()

                    industry_flow.columns = ["industry", "net_inflow"]

                    max_val = abs(industry_flow["net_inflow"].max())
                    if max_val > 1e9:
                        logger.info("检测到数据单位为'元',正在转换为'亿'...")
                        industry_flow["net_inflow"] = industry_flow["net_inflow"] / 1e8
                    elif max_val > 1e6:
                        logger.info("检测到数据单位为'万元',正在转换为'亿'...")
                        industry_flow["net_inflow"] = industry_flow["net_inflow"] / 1e4

                    industry_flow["change_rate"] = 0.0

                agg_time = time.time() - agg_start
                logger.info(f"✅ 聚合完成,耗时 {agg_time:.2f} 秒")

                if five_day_col:
                    industry_flow["data_source"] = "AkShare(5日流向变化)"
                else:
                    industry_flow["data_source"] = "AkShare(北向持股分布)"

                industry_flow = industry_flow.sort_values("net_inflow", ascending=False)

                total_time = time.time() - start_time
                logger.info(f"✅ 成功聚合 {len(industry_flow)} 个行业数据,总耗时 {total_time:.2f} 秒")

                return industry_flow

            except (ConnectionError, TimeoutError) as e:
                logger.warning(f"第{attempt + 1}次尝试网络错误: {e}")
                logger.warning("网络连接问题,将重试...")
            except (ValueError, KeyError, TypeError) as e:
                logger.error(f"数据解析错误,停止重试: {e}")
                import traceback

                traceback.print_exc()
                return None
            except (RuntimeError, OSError) as e:
                error_msg = str(e)
                logger.warning(f"第{attempt + 1}次尝试失败: {error_msg}")

                if "Connection" in error_msg or "RemoteDisconnected" in error_msg:
                    logger.warning("网络连接问题,将重试...")
                elif "timeout" in error_msg.lower():
                    logger.warning("请求超时,将重试...")
                else:
                    logger.error(f"非网络错误,停止重试: {e}")
                    import traceback

                    traceback.print_exc()
                    return None

                if attempt == max_retries - 1:
                    logger.error(f"所有{max_retries}次尝试均失败")
                    logger.info("💡 北向资金行业数据获取失败是常见问题，建议：")
                    logger.info("   1. 使用缓存数据（如果有）")
                    logger.info("   2. 查看历史数据: make north-industry-history")
                    logger.info("   3. 稍后重试（非开市时间成功率更高）")
                    import traceback

                    traceback.print_exc()
                    return None

        return None

    def _validate_industry_data(self, df: pd.DataFrame) -> bool:
        if df.empty:
            logger.warning("数据为空")
            return False

        if len(df) < 10:
            logger.warning(f"行业数量过少: {len(df)}")
            return False

        if df["net_inflow"].isna().any():
            logger.warning("存在缺失的净流入数据")
            return False

        if df["change_rate"].isna().any():
            logger.warning("存在缺失的变化率数据")
            return False

        total_inflow = df[df["net_inflow"] > 0]["net_inflow"].sum()
        total_outflow = df[df["net_inflow"] < 0]["net_inflow"].sum()

        data_source = df["data_source"].iloc[0] if "data_source" in df.columns else ""
        if "新浪" in data_source:
            threshold = 200000
            unit_desc = "20万亿"
        else:
            threshold = 50000
            unit_desc = "5万亿"

        if abs(total_inflow) > threshold or abs(total_outflow) > threshold:
            logger.warning(f"数据异常: 总流入{total_inflow:.2f}亿, 总流出{total_outflow:.2f}亿 (超过{unit_desc})")
            return False

        logger.info(f"数据验证通过: {len(df)}个行业, 总流入{total_inflow:.2f}亿, 总流出{total_outflow:.2f}亿")
        return True

    def _load_industry_cache(self, cache_file: Path) -> pd.DataFrame | None:
        filename = cache_file.name
        data = self._cache.load_file(filename)  # type: ignore[attr-defined]
        if data is None:
            return None

        try:
            if not data or "cache_time" not in data or "industries" not in data:
                logger.warning("缓存数据格式无效")
                return None

            cache_time_str = data.get("cache_time")
            if not cache_time_str:
                logger.warning("缓存时间缺失")
                return None

            try:
                cache_time = datetime.fromisoformat(cache_time_str)
            except (ValueError, TypeError) as e:
                logger.warning(f"缓存时间格式错误: {e}")
                return None

            now = datetime.now()
            current_hour = now.hour

            if 9 <= current_hour < 15:
                cache_hours = 0.5
                cache_desc = "30分钟(开市时间)"
            else:
                cache_hours = 4
                cache_desc = "4小时(非开市时间)"

            if now - cache_time > timedelta(hours=cache_hours):
                logger.info(f"缓存已过期(超过{cache_desc})")
                return None

            df = pd.DataFrame(data["industries"])
            df["cache_time"] = data["cache_time"]
            return df

        except (ValueError, KeyError, TypeError, OSError) as e:
            logger.warning(f"加载缓存失败: {e}")
            return None

    def _save_industry_cache(self, cache_file: Path, df: pd.DataFrame):
        try:
            filename = cache_file.name
            data = {"cache_time": datetime.now().isoformat(), "industries": df.to_dict("records")}

            self._cache.save_file(filename, data, ttl=0)  # type: ignore[attr-defined]

            logger.info(f"缓存已保存: {cache_file}")

        except (OSError, ValueError, TypeError) as e:
            logger.warning(f"保存缓存失败: {e}")
