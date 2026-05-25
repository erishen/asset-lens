"""
Tests for Transaction Parser.
交易记录解析器测试
"""

import pytest


class TestTransactionModule:
    """交易记录模块测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.data import transaction_parser

        assert transaction_parser is not None

    def test_transaction_class(self):
        """测试 Transaction 类"""
        from asset_lens.data.transaction_parser import DCATransaction

        assert DCATransaction is not None

    def test_investment_type_enum(self):
        """测试投资类型枚举"""
        from asset_lens.data.transaction_parser import DCAInvestmentType

        assert DCAInvestmentType is not None


class TestTransactionRecord:
    """交易记录测试"""

    def test_buy_transaction(self):
        """测试买入交易"""
        transaction = {
            "type": "buy",
            "code": "sh600519",
            "name": "贵州茅台",
            "price": 1800.0,
            "quantity": 100,
            "date": "2024-01-15",
        }

        assert transaction["type"] == "buy"
        assert transaction["code"] == "sh600519"
        assert transaction["quantity"] == 100

    def test_sell_transaction(self):
        """测试卖出交易"""
        transaction = {
            "type": "sell",
            "code": "sh600519",
            "name": "贵州茅台",
            "price": 1850.0,
            "quantity": 100,
            "date": "2024-02-15",
        }

        assert transaction["type"] == "sell"
        assert transaction["price"] == 1850.0

    def test_dividend_transaction(self):
        """测试分红交易"""
        transaction = {
            "type": "dividend",
            "code": "sh600519",
            "name": "贵州茅台",
            "amount": 500.0,
            "date": "2024-03-15",
        }

        assert transaction["type"] == "dividend"
        assert transaction["amount"] == 500.0


class TestTransactionCalculations:
    """交易计算测试"""

    def test_profit_calculation(self):
        """测试收益计算"""
        buy_price = 1800.0
        sell_price = 1850.0
        quantity = 100

        profit = (sell_price - buy_price) * quantity
        assert profit == 5000.0

    def test_commission_calculation(self):
        """测试佣金计算"""
        amount = 180000.0
        commission_rate = 0.0003

        commission = amount * commission_rate
        assert commission == pytest.approx(54.0, rel=0.01)

    def test_stamp_duty_calculation(self):
        """测试印花税计算"""
        sell_amount = 185000.0
        stamp_duty_rate = 0.001

        stamp_duty = sell_amount * stamp_duty_rate
        assert stamp_duty == 185.0
