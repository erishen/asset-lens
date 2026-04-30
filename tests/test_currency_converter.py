"""
Tests for currency converter module.
"""

import tempfile
from decimal import Decimal

from asset_lens.data.models import Currency
from asset_lens.utils.currency_converter import CurrencyConverter


class TestCurrencyConverter:
    """Test CurrencyConverter class"""

    def test_init(self):
        """Test initialization"""
        converter = CurrencyConverter()
        assert converter is not None
        assert Currency.CNY in converter.rates
        assert converter.rates[Currency.CNY] == Decimal("1.0")

    def test_get_rate_cny(self):
        """Test getting CNY rate"""
        converter = CurrencyConverter()
        rate = converter.get_rate(Currency.CNY)
        assert rate == Decimal("1.0")

    def test_get_rate_usd(self):
        """Test getting USD rate"""
        converter = CurrencyConverter()
        rate = converter.get_rate(Currency.USD)
        assert rate > Decimal("0")

    def test_get_rate_hkd(self):
        """Test getting HKD rate"""
        converter = CurrencyConverter()
        rate = converter.get_rate(Currency.HKD)
        assert rate > Decimal("0")

    def test_set_rate(self):
        """Test setting rate"""
        converter = CurrencyConverter()
        converter.set_rate(Currency.USD, Decimal("7.5"))
        rate = converter.get_rate(Currency.USD)
        assert rate == Decimal("7.5")

    def test_convert_to_cny_same_currency(self):
        """Test converting to CNY from CNY"""
        converter = CurrencyConverter()
        result = converter.convert_to_cny(Decimal("100"), Currency.CNY)
        assert result == Decimal("100")

    def test_convert_to_cny_usd(self):
        """Test converting USD to CNY"""
        converter = CurrencyConverter()
        converter.set_rate(Currency.USD, Decimal("7.0"))
        result = converter.convert_to_cny(Decimal("100"), Currency.USD)
        assert result == Decimal("700")

    def test_convert_to_cny_with_custom_rate(self):
        """Test converting with custom rate"""
        converter = CurrencyConverter()
        result = converter.convert_to_cny(Decimal("100"), Currency.USD, exchange_rate=Decimal("7.5"))
        assert result == Decimal("750")

    def test_convert_from_cny_same_currency(self):
        """Test converting from CNY to CNY"""
        converter = CurrencyConverter()
        result = converter.convert_from_cny(Decimal("100"), Currency.CNY)
        assert result == Decimal("100")

    def test_convert_from_cny_usd(self):
        """Test converting CNY to USD"""
        converter = CurrencyConverter()
        converter.set_rate(Currency.USD, Decimal("7.0"))
        result = converter.convert_from_cny(Decimal("700"), Currency.USD)
        assert result == Decimal("100")

    def test_convert_from_cny_with_custom_rate(self):
        """Test converting from CNY with custom rate"""
        converter = CurrencyConverter()
        result = converter.convert_from_cny(Decimal("750"), Currency.USD, exchange_rate=Decimal("7.5"))
        assert result == Decimal("100")

    def test_convert_same_currency(self):
        """Test converting same currency"""
        converter = CurrencyConverter()
        result = converter.convert(Decimal("100"), Currency.CNY, Currency.CNY)
        assert result == Decimal("100")

    def test_convert_cny_to_usd(self):
        """Test converting CNY to USD"""
        converter = CurrencyConverter()
        converter.set_rate(Currency.USD, Decimal("7.0"))
        result = converter.convert(Decimal("700"), Currency.CNY, Currency.USD)
        assert result == Decimal("100")

    def test_convert_usd_to_cny(self):
        """Test converting USD to CNY"""
        converter = CurrencyConverter()
        converter.set_rate(Currency.USD, Decimal("7.0"))
        result = converter.convert(Decimal("100"), Currency.USD, Currency.CNY)
        assert result == Decimal("700")

    def test_convert_with_custom_rates(self):
        """Test converting with custom rates"""
        converter = CurrencyConverter()
        result = converter.convert(
            Decimal("100"),
            Currency.USD,
            Currency.HKD,
            from_rate=Decimal("7.0"),
            to_rate=Decimal("0.9"),
        )
        # 100 USD * 7.0 = 700 CNY
        # 700 CNY / 0.9 = 777.78 HKD
        assert result == Decimal("700") / Decimal("0.9")

    def test_save_and_load_cached_rates(self):
        """Test saving and loading cached rates"""
        with tempfile.TemporaryDirectory():
            # Create a converter and set rates
            converter = CurrencyConverter()
            converter.set_rate(Currency.USD, Decimal("7.5"))
            converter.set_rate(Currency.HKD, Decimal("0.95"))

            # Save to cache
            converter.save_cached_rates()

            # Create a new converter to load cached rates
            converter2 = CurrencyConverter()

            # Check rates are loaded
            assert converter2.get_rate(Currency.USD) == Decimal("7.5")
            assert converter2.get_rate(Currency.HKD) == Decimal("0.95")


class TestCurrencyConverterEdgeCases:
    """Test edge cases"""

    def test_convert_zero_amount(self):
        """Test converting zero amount"""
        converter = CurrencyConverter()
        result = converter.convert_to_cny(Decimal("0"), Currency.USD)
        assert result == Decimal("0")

    def test_convert_negative_amount(self):
        """Test converting negative amount"""
        converter = CurrencyConverter()
        converter.set_rate(Currency.USD, Decimal("7.0"))
        result = converter.convert_to_cny(Decimal("-100"), Currency.USD)
        assert result == Decimal("-700")

    def test_convert_very_small_amount(self):
        """Test converting very small amount"""
        converter = CurrencyConverter()
        converter.set_rate(Currency.USD, Decimal("7.0"))
        result = converter.convert_to_cny(Decimal("0.01"), Currency.USD)
        assert result == Decimal("0.07")

    def test_convert_very_large_amount(self):
        """Test converting very large amount"""
        converter = CurrencyConverter()
        converter.set_rate(Currency.USD, Decimal("7.0"))
        result = converter.convert_to_cny(Decimal("1000000"), Currency.USD)
        assert result == Decimal("7000000")
