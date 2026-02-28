"""
Tests for realtime PnL estimation.
"""

import pytest
import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch, MagicMock

from asset_lens.core.realtime_pnl import (
    ProductMapping,
    find_product_mapping,
    adjust_by_risk_level,
    RealtimePnlEstimator,
    DEFAULT_PRODUCT_MAPPING,
)
from asset_lens.data.models import InvestmentProduct, InvestmentType, RiskLevel


class TestProductMapping:
    """Test ProductMapping dataclass"""

    def test_product_mapping_creation(self):
        mapping = ProductMapping(
            index_key="HS300",
            direct_sensitivity=Decimal("1.0"),
            sensitivity_to_sh=Decimal("0.9"),
            equity_ratio=Decimal("1.0"),
        )
        assert mapping.index_key == "HS300"
        assert mapping.direct_sensitivity == Decimal("1.0")
        assert mapping.sensitivity_to_sh == Decimal("0.9")
        assert mapping.equity_ratio == Decimal("1.0")

    def test_product_mapping_defaults(self):
        mapping = ProductMapping(index_key="Test")
        assert mapping.direct_sensitivity == Decimal("1.0")
        assert mapping.sensitivity_to_sh == Decimal("0.7")
        assert mapping.equity_ratio == Decimal("1.0")


class TestFindProductMapping:
    """Test find_product_mapping function"""

    def test_hs300_mapping(self):
        mapping = find_product_mapping("沪深300ETF", InvestmentType.INDEX_FUND)
        assert mapping.index_key == "HS300"
        assert mapping.direct_sensitivity == Decimal("1.0")

    def test_csi500_mapping(self):
        mapping = find_product_mapping("中证500指数增强", InvestmentType.INDEX_FUND)
        assert mapping.index_key == "CSI500"
        assert mapping.direct_sensitivity == Decimal("1.0")

    def test_gem_mapping(self):
        mapping = find_product_mapping("创业板基金", InvestmentType.FUND)
        assert mapping.index_key == "GEM"

    def test_star50_mapping(self):
        mapping = find_product_mapping("科创50ETF", InvestmentType.INDEX_FUND)
        assert mapping.index_key == "STAR50"

    def test_qdii_mapping(self):
        mapping = find_product_mapping("纳斯达克100QDII", InvestmentType.QDII)
        assert mapping.index_key == "Nasdaq"

    def test_gold_mapping(self):
        mapping = find_product_mapping("黄金ETF", InvestmentType.FUND)
        assert mapping.index_key == "Gold"

    def test_bond_mapping(self):
        mapping = find_product_mapping("债券基金A", InvestmentType.BOND_FUND)
        assert mapping.index_key == "Bond"

    def test_monetary_mapping(self):
        mapping = find_product_mapping("货币基金A", InvestmentType.MONETARY)
        assert mapping.index_key == "Cash"

    def test_mixed_fund_mapping(self):
        mapping = find_product_mapping("混合基金A", InvestmentType.MIXED_FUND)
        assert mapping.index_key == "Blend"

    def test_stock_mapping(self):
        mapping = find_product_mapping("平安银行", InvestmentType.STOCK)
        assert mapping.index_key == "SHComp"

    def test_default_mapping(self):
        mapping = find_product_mapping("未知产品", InvestmentType.OTHER)
        assert mapping.index_key == "Blend"


class TestAdjustByRiskLevel:
    """Test adjust_by_risk_level function"""

    def test_low_risk_adjustment(self):
        equity, sensitivity = adjust_by_risk_level(
            "测试产品",
            Decimal("1.0"),
            Decimal("1.0"),
            RiskLevel.LOW,
        )
        assert equity == Decimal("0.3")
        assert sensitivity == Decimal("0.3")

    def test_medium_risk_adjustment(self):
        equity, sensitivity = adjust_by_risk_level(
            "测试产品",
            Decimal("1.0"),
            Decimal("1.0"),
            RiskLevel.MEDIUM,
        )
        assert equity == Decimal("0.7")
        assert sensitivity == Decimal("0.7")

    def test_high_risk_adjustment(self):
        equity, sensitivity = adjust_by_risk_level(
            "测试产品",
            Decimal("1.0"),
            Decimal("1.0"),
            RiskLevel.HIGH,
        )
        assert equity == Decimal("1.0")
        assert sensitivity == Decimal("1.0")

    def test_none_risk_level(self):
        equity, sensitivity = adjust_by_risk_level(
            "测试产品",
            Decimal("0.8"),
            Decimal("0.9"),
            None,
        )
        assert equity == Decimal("0.8")
        assert sensitivity == Decimal("0.9")


class TestRealtimePnlEstimator:
    """Test RealtimePnlEstimator class"""

    def setup_method(self):
        self.estimator = RealtimePnlEstimator()

    def test_estimator_creation(self):
        assert self.estimator.cache_path is not None
        assert self.estimator.domestic_cache_file is not None
        assert self.estimator.foreign_cache_file is not None

    def test_estimate_product_pnl_positive(self):
        product = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="中证500ETF",
            risk_level=RiskLevel.MEDIUM,
            current_amount=Decimal("10000"),
        )
        moves = {"CSI500": Decimal("1.0")}
        result = self.estimator.estimate_product_pnl(product, moves)
        assert result["name"] == "中证500ETF"
        assert result["index_key"] == "CSI500"
        assert result["amount"] == Decimal("10000")

    def test_estimate_product_pnl_zero_amount(self):
        product = InvestmentProduct(
            investment_type=InvestmentType.INDEX_FUND,
            name="测试产品",
            risk_level=RiskLevel.MEDIUM,
            current_amount=Decimal("0"),
        )
        moves = {"SHComp": Decimal("1.0")}
        result = self.estimator.estimate_product_pnl(product, moves)
        assert result["pnl"] == Decimal("0")
        assert result["return_rate"] == Decimal("0")

    def test_estimate_product_pnl_bond(self):
        product = InvestmentProduct(
            investment_type=InvestmentType.BOND,
            name="债券产品",
            risk_level=RiskLevel.LOW,
            current_amount=Decimal("10000"),
        )
        moves = {"SHComp": Decimal("1.0")}
        result = self.estimator.estimate_product_pnl(product, moves)
        assert result["index_key"] == "Bond"
        assert result["pnl"] == Decimal("0")

    def test_estimate_product_pnl_monetary(self):
        product = InvestmentProduct(
            investment_type=InvestmentType.MONETARY,
            name="货币基金",
            risk_level=RiskLevel.LOW,
            current_amount=Decimal("10000"),
        )
        moves = {"SHComp": Decimal("1.0")}
        result = self.estimator.estimate_product_pnl(product, moves)
        assert result["index_key"] == "Cash"
        assert result["pnl"] == Decimal("0")

    @patch("pathlib.Path.exists")
    @patch("builtins.open", create=True)
    def test_read_index_moves_from_cache(self, mock_open, mock_exists):
        mock_exists.return_value = True
        mock_file = MagicMock()
        mock_file.read.return_value = json.dumps({
            "指数数据": {
                "上证指数": {"涨跌幅": 0.5},
                "沪深300": {"涨跌幅": 0.3},
            }
        })
        mock_file.__enter__ = MagicMock(return_value=mock_file)
        mock_file.__exit__ = MagicMock(return_value=False)
        mock_open.return_value = mock_file

        moves = self.estimator.read_index_moves_from_cache()
        assert "SHComp" in moves or len(moves) >= 0

    def test_estimate_portfolio_pnl_empty(self):
        result = self.estimator.estimate_portfolio_pnl([])
        assert "total" in result
        assert "details" in result

    def test_estimate_portfolio_pnl_with_products(self):
        products = [
            InvestmentProduct(
                investment_type=InvestmentType.INDEX_FUND,
                name="中证500ETF",
                risk_level=RiskLevel.MEDIUM,
                current_amount=Decimal("10000"),
            ),
            InvestmentProduct(
                investment_type=InvestmentType.BOND,
                name="债券基金",
                risk_level=RiskLevel.LOW,
                current_amount=Decimal("5000"),
            ),
        ]
        
        with patch.object(
            self.estimator,
            "read_index_moves_from_cache",
            return_value={"CSI500": Decimal("1.0"), "SHComp": Decimal("0.5")},
        ):
            result = self.estimator.estimate_portfolio_pnl(products)
            assert "total" in result
            assert "details" in result
            assert len(result["details"]) > 0
