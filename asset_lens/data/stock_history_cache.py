import logging
import time
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class StockHistoryCacheMixin:
    def save_history_cache(self, histories: dict[str, dict[str, Any]]) -> None:
        try:
            cache_data = {
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total": len(histories),
                "data": histories,
            }

            self._cache.save_file("stock_history.json", cache_data, ttl=86400)

            logger.info(f"历史数据缓存已保存: {len(histories)} 只股票")

        except (OSError, json.JSONDecodeError, ValueError) as e:
            logger.error(f"保存历史数据缓存失败: {e}")

    def load_history_cache(self) -> dict[str, dict[str, Any]]:
        data = self._cache.load_file("stock_history.json")
        if data is None:
            return {}
        return data.get("data", {})

    def check_cache_validity(self, max_age_hours: int = 24) -> dict[str, Any]:
        cache = self.load_history_cache()

        if not cache:
            return {
                "is_valid": False,
                "reason": "缓存为空",
                "total_cached": 0,
                "expired_count": 0,
                "valid_count": 0,
            }

        now = datetime.now()
        total = len(cache)
        expired = 0
        valid = 0
        expired_codes = []

        for code, data in cache.items():
            update_time_str = data.get("update_time", "")
            if not update_time_str:
                expired += 1
                expired_codes.append(code)
                continue

            try:
                update_time = datetime.strptime(update_time_str, "%Y-%m-%d %H:%M:%S")
                age_hours = (now - update_time).total_seconds() / 3600

                if age_hours > max_age_hours:
                    expired += 1
                    expired_codes.append(code)
                else:
                    valid += 1
            except ValueError:
                expired += 1
                expired_codes.append(code)

        return {
            "is_valid": expired == 0,
            "total_cached": total,
            "valid_count": valid,
            "expired_count": expired,
            "expired_codes": expired_codes[:20],
            "max_age_hours": max_age_hours,
        }

    def incremental_update(
        self,
        codes: list[str] | None = None,
        max_age_hours: int = 24,
        batch_size: int = 10,
        daily_limit: int = 100,
    ) -> dict[str, Any]:
        cache = self.load_history_cache()
        validity = self.check_cache_validity(max_age_hours)

        if codes is None:
            codes = validity.get("expired_codes", [])

        if not codes:
            return {
                "updated": 0,
                "failed": 0,
                "skipped": 0,
                "total_cached": validity["total_cached"],
            }

        now = datetime.now()
        updated = 0
        failed = 0
        skipped = 0

        for i, code in enumerate(codes[:daily_limit]):
            if i > 0 and i % batch_size == 0:
                logger.info(f"进度: {i}/{len(codes)} (已更新: {updated}, 失败: {failed})")
                time.sleep(1)

            cached_data = cache.get(code)
            if cached_data:
                update_time_str = cached_data.get("update_time", "")
                if update_time_str:
                    try:
                        update_time = datetime.strptime(update_time_str, "%Y-%m-%d %H:%M:%S")
                        age_hours = (now - update_time).total_seconds() / 3600
                        if age_hours < max_age_hours:
                            skipped += 1
                            continue
                    except ValueError as e:
                        logger.debug("股票历史缓存解析失败: %s", e)

            try:
                history = self.fetch_history(code, days=60)
                if history:
                    history["update_time"] = now.strftime("%Y-%m-%d %H:%M:%S")
                    cache[code] = history
                    updated += 1
                else:
                    failed += 1
            except (ValueError, KeyError, ConnectionError) as e:
                logger.debug(f"更新 {code} 失败: {e}")
                failed += 1

        if updated > 0:
            self.save_history_cache(cache)

        return {
            "updated": updated,
            "failed": failed,
            "skipped": skipped,
            "total_cached": len(cache),
        }

    def get_cache_statistics(self) -> dict[str, Any]:
        cache = self.load_history_cache()

        if not cache:
            return {
                "total": 0,
                "with_klines": 0,
                "avg_klines": 0,
                "sources": {},
            }

        total = len(cache)
        with_klines = 0
        total_klines = 0
        sources: dict[str, int] = {}

        for code, data in cache.items():
            klines = data.get("klines", [])
            if klines:
                with_klines += 1
                total_klines += len(klines)

            source = data.get("source", "unknown")
            sources[source] = sources.get(source, 0) + 1

        return {
            "total": total,
            "with_klines": with_klines,
            "avg_klines": round(total_klines / with_klines, 1) if with_klines > 0 else 0,
            "sources": sources,
        }

    def clear_cache(self) -> bool:
        try:
            return self._cache.delete_file("stock_history.json")
        except OSError as e:
            logger.error(f"清除缓存失败: {e}")
            return False
