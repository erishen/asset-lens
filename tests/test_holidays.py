"""
Tests for holidays module.
节假日模块测试
"""

from datetime import date

from asset_lens.core.holidays import (
    HOLIDAY_CONFIGS,
    calculate_fund_trading_days,
    calculate_working_days,
    get_last_fund_trading_day,
    get_last_working_day,
    is_fund_trading_day,
    is_holiday,
    is_post_holiday_trading_suspension,
    is_working_day,
    parse_stop_periods,
)


class TestHolidayConfig:
    """Test HolidayConfig dataclass"""

    def test_holiday_config_2025_exists(self):
        """Test that 2025 holiday config exists"""
        assert 2025 in HOLIDAY_CONFIGS
        config = HOLIDAY_CONFIGS[2025]
        assert config.year == 2025
        assert len(config.holidays) > 0
        assert len(config.working_weekends) > 0

    def test_holiday_config_2026_exists(self):
        """Test that 2026 holiday config exists"""
        assert 2026 in HOLIDAY_CONFIGS
        config = HOLIDAY_CONFIGS[2026]
        assert config.year == 2026
        assert len(config.holidays) > 0
        assert len(config.working_weekends) > 0

    def test_spring_festival_2025(self):
        """Test 2025 Spring Festival dates"""
        config = HOLIDAY_CONFIGS[2025]
        spring_festival = None
        for h in config.holidays:
            if "春节" in h["name"]:
                spring_festival = h
                break

        assert spring_festival is not None
        assert spring_festival["start"] == "2025-01-28"
        assert spring_festival["end"] == "2025-02-04"

    def test_spring_festival_2026(self):
        """Test 2026 Spring Festival dates"""
        config = HOLIDAY_CONFIGS[2026]
        spring_festival = None
        for h in config.holidays:
            if "春节" in h["name"]:
                spring_festival = h
                break

        assert spring_festival is not None
        assert spring_festival["start"] == "2026-02-15"
        assert spring_festival["end"] == "2026-02-23"


class TestIsHoliday:
    """Test is_holiday function"""

    def test_2025_spring_festival(self):
        """Test 2025 Spring Festival is holiday"""
        assert is_holiday(date(2025, 1, 28)) is True
        assert is_holiday(date(2025, 2, 3)) is True
        assert is_holiday(date(2025, 2, 4)) is True

    def test_2026_spring_festival(self):
        """Test 2026 Spring Festival is holiday"""
        assert is_holiday(date(2026, 2, 15)) is True
        assert is_holiday(date(2026, 2, 23)) is True

    def test_2026_spring_festival_extended(self):
        """Test 2026 Spring Festival extended dates"""
        assert is_holiday(date(2026, 2, 16)) is True
        assert is_holiday(date(2026, 2, 22)) is True

    def test_regular_working_day(self):
        """Test regular working day is not holiday"""
        assert is_holiday(date(2025, 3, 15)) is False
        assert is_holiday(date(2026, 3, 15)) is False

    def test_weekend_not_holiday(self):
        """Test weekend is not marked as holiday by default"""
        assert is_holiday(date(2025, 3, 8)) is False
        assert is_holiday(date(2025, 3, 9)) is False


class TestIsWorkingDay:
    """Test is_working_day function"""

    def test_regular_weekday(self):
        """Test regular weekday is working day"""
        assert is_working_day(date(2025, 3, 17)) is True
        assert is_working_day(date(2025, 3, 18)) is True

    def test_weekend_not_working_day(self):
        """Test weekend is not working day"""
        assert is_working_day(date(2025, 3, 8)) is False
        assert is_working_day(date(2025, 3, 9)) is False

    def test_holiday_not_working_day(self):
        """Test holiday is not working day"""
        assert is_working_day(date(2025, 1, 28)) is False
        assert is_working_day(date(2026, 2, 15)) is False

    def test_working_weekend_2025(self):
        """Test 2025 working weekends"""
        assert is_working_day(date(2025, 1, 26)) is True
        assert is_working_day(date(2025, 2, 8)) is True

    def test_working_weekend_2026(self):
        """Test 2026 working weekends"""
        assert is_working_day(date(2026, 2, 14)) is True
        assert is_working_day(date(2026, 2, 28)) is True


class TestIsFundTradingDay:
    """Test is_fund_trading_day function"""

    def test_regular_weekday(self):
        """Test regular weekday is fund trading day"""
        assert is_fund_trading_day(date(2025, 3, 17)) is True
        assert is_fund_trading_day(date(2025, 3, 18)) is True

    def test_weekend_not_trading_day(self):
        """Test weekend is not fund trading day"""
        assert is_fund_trading_day(date(2025, 3, 8)) is False
        assert is_fund_trading_day(date(2025, 3, 9)) is False

    def test_holiday_not_trading_day(self):
        """Test holiday is not fund trading day"""
        assert is_fund_trading_day(date(2025, 1, 28)) is False
        assert is_fund_trading_day(date(2026, 2, 15)) is False

    def test_working_weekend_not_trading_day(self):
        """Test working weekend is not fund trading day"""
        assert is_fund_trading_day(date(2026, 2, 28)) is False

    def test_post_holiday_suspension(self):
        """Test post holiday trading suspension"""
        assert is_fund_trading_day(date(2025, 1, 29)) is False
        assert is_fund_trading_day(date(2026, 2, 17)) is False


class TestGetLastWorkingDay:
    """Test get_last_working_day function"""

    def test_get_last_working_day_from_weekday(self):
        """Test get last working day from weekday"""
        result = get_last_working_day(date(2025, 3, 17))
        assert result == date(2025, 3, 17)

    def test_get_last_working_day_from_saturday(self):
        """Test get last working day from Saturday"""
        result = get_last_working_day(date(2025, 3, 8))
        assert result == date(2025, 3, 7)

    def test_get_last_working_day_from_sunday(self):
        """Test get last working day from Sunday"""
        result = get_last_working_day(date(2025, 3, 9))
        assert result == date(2025, 3, 7)

    def test_get_last_working_day_from_holiday(self):
        """Test get last working day from holiday"""
        result = get_last_working_day(date(2025, 1, 28))
        assert result < date(2025, 1, 28)


class TestGetLastFundTradingDay:
    """Test get_last_fund_trading_day function"""

    def test_get_last_fund_trading_day_from_weekday(self):
        """Test get last fund trading day from weekday"""
        result = get_last_fund_trading_day(date(2025, 3, 17))
        assert result == date(2025, 3, 17)

    def test_get_last_fund_trading_day_from_weekend(self):
        """Test get last fund trading day from weekend"""
        result = get_last_fund_trading_day(date(2025, 3, 8))
        assert result == date(2025, 3, 7)

    def test_get_last_fund_trading_day_from_working_weekend(self):
        """Test get last fund trading day from working weekend"""
        result = get_last_fund_trading_day(date(2026, 2, 28))
        assert result < date(2026, 2, 28)


class TestCalculateWorkingDays:
    """Test calculate_working_days function"""

    def test_calculate_working_days_simple(self):
        """Test calculate working days for a simple week"""
        start = date(2025, 3, 17)
        end = date(2025, 3, 21)
        result = calculate_working_days(start, end)
        assert result == 5

    def test_calculate_working_days_with_weekend(self):
        """Test calculate working days including weekend"""
        start = date(2025, 3, 17)
        end = date(2025, 3, 23)
        result = calculate_working_days(start, end)
        assert result == 5

    def test_calculate_working_days_with_holiday(self):
        """Test calculate working days including holiday"""
        start = date(2025, 1, 27)
        end = date(2025, 2, 5)
        result = calculate_working_days(start, end)
        assert result < 10

    def test_calculate_working_days_with_stop_periods(self):
        """Test calculate working days with stop periods"""
        start = date(2025, 3, 17)
        end = date(2025, 3, 21)
        stop_periods = [(date(2025, 3, 18), date(2025, 3, 19))]
        result = calculate_working_days(start, end, stop_periods)
        assert result == 3


class TestCalculateFundTradingDays:
    """Test calculate_fund_trading_days function"""

    def test_calculate_fund_trading_days_simple(self):
        """Test calculate fund trading days for a simple week"""
        start = date(2025, 3, 17)
        end = date(2025, 3, 21)
        result = calculate_fund_trading_days(start, end)
        assert result == 5

    def test_calculate_fund_trading_days_with_working_weekend(self):
        """Test calculate fund trading days including working weekend"""
        start = date(2026, 2, 27)
        end = date(2026, 2, 28)
        result = calculate_fund_trading_days(start, end)
        assert result == 1

    def test_calculate_fund_trading_days_with_stop_periods(self):
        """Test calculate fund trading days with stop periods"""
        start = date(2025, 3, 17)
        end = date(2025, 3, 21)
        stop_periods = [(date(2025, 3, 18), date(2025, 3, 19))]
        result = calculate_fund_trading_days(start, end, stop_periods)
        assert result == 3


class TestParseStopPeriods:
    """Test parse_stop_periods function"""

    def test_parse_single_stop(self):
        """Test parse single stop period"""
        result = parse_stop_periods("2025/10/13:stop")
        assert len(result) == 1
        assert result[0] == (date(2025, 10, 13), date(2025, 10, 13))

    def test_parse_range_stop(self):
        """Test parse range stop period"""
        result = parse_stop_periods("2025/10/13-2025/10/15:stop")
        assert len(result) == 1
        assert result[0] == (date(2025, 10, 13), date(2025, 10, 15))

    def test_parse_multiple_stops(self):
        """Test parse multiple stop periods"""
        result = parse_stop_periods("2025/10/13-2025/10/15:stop; 2025/10/29:stop")
        assert len(result) == 2
        assert result[0] == (date(2025, 10, 13), date(2025, 10, 15))
        assert result[1] == (date(2025, 10, 29), date(2025, 10, 29))

    def test_parse_empty_string(self):
        """Test parse empty string"""
        result = parse_stop_periods("")
        assert len(result) == 0

    def test_parse_no_stop_periods(self):
        """Test parse string without stop periods"""
        result = parse_stop_periods("2025/10/13-now:buy:100")
        assert len(result) == 0


class TestEdgeCases:
    """Test edge cases"""

    def test_is_holiday_unknown_year(self):
        """Test is_holiday for unknown year"""
        assert is_holiday(date(2030, 3, 15)) is False

    def test_is_working_day_unknown_year(self):
        """Test is_working_day for unknown year"""
        assert is_working_day(date(2030, 3, 15)) is True

    def test_is_fund_trading_day_unknown_year(self):
        """Test is_fund_trading_day for unknown year"""
        assert is_fund_trading_day(date(2030, 3, 15)) is True

    def test_calculate_working_days_same_day(self):
        """Test calculate working days for same day"""
        start = date(2025, 3, 17)
        end = date(2025, 3, 17)
        result = calculate_working_days(start, end)
        assert result == 1

    def test_calculate_fund_trading_days_same_day(self):
        """Test calculate fund trading days for same day"""
        start = date(2025, 3, 17)
        end = date(2025, 3, 17)
        result = calculate_fund_trading_days(start, end)
        assert result == 1

    def test_calculate_working_days_end_before_start(self):
        """Test calculate working days when end is before start"""
        start = date(2025, 3, 21)
        end = date(2025, 3, 17)
        result = calculate_working_days(start, end)
        assert result == 0

    def test_calculate_fund_trading_days_end_before_start(self):
        """Test calculate fund trading days when end is before start"""
        start = date(2025, 3, 21)
        end = date(2025, 3, 17)
        result = calculate_fund_trading_days(start, end)
        assert result == 0

    def test_is_holiday_fixed_holiday_new_year(self):
        """Test is_holiday for fixed holiday - New Year"""
        assert is_holiday(date(2030, 1, 1)) is True

    def test_is_holiday_fixed_holiday_labor_day(self):
        """Test is_holiday for fixed holiday - Labor Day"""
        assert is_holiday(date(2030, 5, 1)) is True
        assert is_holiday(date(2030, 5, 3)) is True

    def test_is_holiday_fixed_holiday_national_day(self):
        """Test is_holiday for fixed holiday - National Day"""
        assert is_holiday(date(2030, 10, 1)) is True
        assert is_holiday(date(2030, 10, 5)) is True

    def test_parse_stop_periods_with_dash_format(self):
        """Test parse stop periods with YYYY-MM-DD format - not supported for single date"""
        result = parse_stop_periods("2025-10-13:stop")
        assert len(result) == 0

    def test_parse_stop_periods_range_with_dash_format(self):
        """Test parse range stop period with YYYY/MM/DD-YYYY/MM/DD format"""
        result = parse_stop_periods("2025/10/13-2025/10/15:stop")
        assert len(result) == 1
        assert result[0] == (date(2025, 10, 13), date(2025, 10, 15))

    def test_parse_stop_periods_invalid_date_format(self):
        """Test parse stop periods with invalid date format"""
        result = parse_stop_periods("invalid-date:stop")
        assert len(result) == 0

    def test_parse_stop_periods_invalid_range_format(self):
        """Test parse stop periods with invalid range format"""
        result = parse_stop_periods("invalid-start-invalid-end:stop")
        assert len(result) == 0

    def test_is_post_holiday_trading_suspension_unknown_year(self):
        """Test is_post_holiday_trading_suspension for unknown year"""
        assert is_post_holiday_trading_suspension(date(2030, 1, 29)) is False

    def test_is_post_holiday_trading_suspension_2025(self):
        """Test is_post_holiday_trading_suspension for 2025"""
        assert is_post_holiday_trading_suspension(date(2025, 1, 29)) is True
        assert is_post_holiday_trading_suspension(date(2025, 10, 9)) is True
        assert is_post_holiday_trading_suspension(date(2025, 3, 15)) is False

    def test_is_post_holiday_trading_suspension_2026(self):
        """Test is_post_holiday_trading_suspension for 2026"""
        assert is_post_holiday_trading_suspension(date(2026, 2, 17)) is True
        assert is_post_holiday_trading_suspension(date(2026, 10, 9)) is True
        assert is_post_holiday_trading_suspension(date(2026, 3, 15)) is False
