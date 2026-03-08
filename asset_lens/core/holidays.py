"""
中国节假日和工作日判断模块
与 ts-demo 的 holidays.ts 保持一致
"""

from datetime import date, datetime, timedelta
from typing import List, Optional


class HolidayConfig:
    """节假日配置"""

    def __init__(
        self,
        year: int,
        holidays: List[dict],
        working_weekends: Optional[List[str]] = None,
        post_holiday_trading_suspensions: Optional[List[str]] = None,
    ):
        self.year = year
        self.holidays = holidays
        self.working_weekends = working_weekends or []
        self.post_holiday_trading_suspensions = post_holiday_trading_suspensions or []


HOLIDAYS_2025 = HolidayConfig(
    year=2025,
    holidays=[
        {"name": "元旦", "start": "2025-01-01", "end": "2025-01-01"},
        {"name": "春节", "start": "2025-01-28", "end": "2025-02-04"},
        {"name": "清明节", "start": "2025-04-04", "end": "2025-04-06"},
        {"name": "劳动节", "start": "2025-05-01", "end": "2025-05-05"},
        {"name": "端午节", "start": "2025-05-31", "end": "2025-06-02"},
        {"name": "中秋节", "start": "2025-10-06", "end": "2025-10-06"},
        {"name": "国庆节", "start": "2025-10-01", "end": "2025-10-08"},
    ],
    working_weekends=[
        "2025-01-26",
        "2025-02-08",
        "2025-04-27",
        "2025-09-28",
    ],
    post_holiday_trading_suspensions=[
        "2025-01-29",
        "2025-10-09",
    ],
)

HOLIDAYS_2026 = HolidayConfig(
    year=2026,
    holidays=[
        {"name": "元旦", "start": "2026-01-01", "end": "2026-01-03"},
        {"name": "春节", "start": "2026-02-15", "end": "2026-02-23"},
        {"name": "清明节", "start": "2026-04-04", "end": "2026-04-06"},
        {"name": "劳动节", "start": "2026-05-01", "end": "2026-05-05"},
        {"name": "端午节", "start": "2026-05-31", "end": "2026-06-02"},
        {"name": "中秋节", "start": "2026-10-03", "end": "2026-10-03"},
        {"name": "国庆节", "start": "2026-10-01", "end": "2026-10-08"},
    ],
    working_weekends=[
        "2026-02-14",
        "2026-02-28",
    ],
    post_holiday_trading_suspensions=[
        "2026-02-17",
        "2026-10-09",
    ],
)

HOLIDAY_CONFIGS = {2025: HOLIDAYS_2025, 2026: HOLIDAYS_2026}


def _format_date(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def is_holiday(d: date) -> bool:
    year = d.year
    config = HOLIDAY_CONFIGS.get(year)

    if not config:
        return _is_fixed_holiday(d)

    date_str = _format_date(d)

    for holiday in config.holidays:
        if holiday["start"] <= date_str <= holiday["end"]:
            return True

    return False


def _is_fixed_holiday(d: date) -> bool:
    month, day = d.month, d.day
    if month == 1 and day == 1:
        return True
    if month == 5 and day in (1, 2, 3, 4, 5):
        return True
    if month == 10 and day in (1, 2, 3, 4, 5, 6, 7, 8):
        return True
    return False


def is_working_day(d: date) -> bool:
    weekday = d.weekday()
    year = d.year
    config = HOLIDAY_CONFIGS.get(year)
    date_str = _format_date(d)

    if config and date_str in config.working_weekends:
        return True

    if weekday >= 5:
        return False

    if is_holiday(d):
        return False

    return True


def get_last_working_day(d: date) -> date:
    result = d
    while not is_working_day(result):
        result -= timedelta(days=1)
    return result


def get_last_fund_trading_day(d: date) -> date:
    """获取最后一个基金交易日"""
    result = d
    while not is_fund_trading_day(result):
        result -= timedelta(days=1)
    return result


def is_post_holiday_trading_suspension(d: date) -> bool:
    year = d.year
    config = HOLIDAY_CONFIGS.get(year)

    if not config or not config.post_holiday_trading_suspensions:
        return False

    date_str = _format_date(d)
    return date_str in config.post_holiday_trading_suspensions


def is_fund_trading_day(d: date) -> bool:
    """判断指定日期是否为基金交易日

    注意：基金市场在周末不开市，即使是调休上班日也不开市
    """
    weekday = d.weekday()

    # 周末不是交易日（即使是调休上班日，基金市场也不开市）
    if weekday >= 5:
        return False

    if is_holiday(d):
        return False

    if is_post_holiday_trading_suspension(d):
        return False

    return True


def calculate_working_days(
    start: date,
    end: date,
    stop_periods: Optional[List[tuple]] = None,
) -> int:
    if start > end:
        return 0

    count = 0
    current = start

    while current <= end:
        if is_working_day(current):
            if stop_periods:
                in_stop = False
                for stop_start, stop_end in stop_periods:
                    if stop_start <= current <= stop_end:
                        in_stop = True
                        break
                if not in_stop:
                    count += 1
            else:
                count += 1
        current += timedelta(days=1)

    return count


def calculate_fund_trading_days(
    start: date,
    end: date,
    stop_periods: Optional[List[tuple]] = None,
) -> int:
    if start > end:
        return 0

    count = 0
    current = start

    while current <= end:
        if is_fund_trading_day(current):
            if stop_periods:
                in_stop = False
                for stop_start, stop_end in stop_periods:
                    if stop_start <= current <= stop_end:
                        in_stop = True
                        break
                if not in_stop:
                    count += 1
            else:
                count += 1
        current += timedelta(days=1)

    return count


def parse_stop_periods(record_str: str) -> List[tuple]:
    stop_periods: List[tuple] = []

    if not record_str:
        return stop_periods

    parts = record_str.split(";")

    for part in parts:
        part = part.strip()
        if ":stop" not in part:
            continue

        date_range = part.split(":")[0].strip()

        if "-" in date_range:
            range_parts = date_range.split("-")
            if len(range_parts) == 2:
                try:
                    start = _parse_date_string(range_parts[0].strip())
                    end = _parse_date_string(range_parts[1].strip())
                    if start and end:
                        stop_periods.append((start, end))
                except Exception:
                    pass
        else:
            try:
                single_date = _parse_date_string(date_range)
                if single_date:
                    stop_periods.append((single_date, single_date))
            except Exception:
                pass

    return stop_periods


def _parse_date_string(date_str: str) -> Optional[date]:
    date_formats = [
        "%Y/%m/%d",
        "%Y-%m-%d",
    ]

    for fmt in date_formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue

    return None
