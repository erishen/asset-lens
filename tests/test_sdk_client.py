from unittest.mock import MagicMock, patch

from asset_lens.sdk.client import AssetLensClient, create_client


class TestAssetLensClient:
    def setup_method(self):
        self.client = AssetLensClient()

    def test_init_default(self):
        client = AssetLensClient()
        assert client.config_path.name == "asset_lens.yaml"
        assert client._cache == {}

    def test_init_custom_path(self, tmp_path):
        config = tmp_path / "custom.yaml"
        client = AssetLensClient(config_path=config)
        assert client.config_path == config

    def test_create_client(self):
        client = create_client()
        assert isinstance(client, AssetLensClient)

    def test_create_client_with_path(self, tmp_path):
        config = tmp_path / "custom.yaml"
        client = create_client(config_path=config)
        assert isinstance(client, AssetLensClient)
        assert client.config_path == config

    def test_get_stock_quote_success(self):
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_stock_quote_akshare.return_value = {"name": "贵州茅台", "price": 1800.0}

        with patch("asset_lens.data.stock_fetcher.StockDataFetcher", return_value=mock_fetcher):
            result = self.client.get_stock_quote("sh600519")

        assert result["success"] is True
        assert "data" in result
        assert "timestamp" in result

    def test_get_fund_nav_success(self):
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_fund_info.return_value = {"name": "测试基金", "nav": 1.5}

        with patch("asset_lens.data.fund_fetcher.FundDataFetcher", return_value=mock_fetcher):
            result = self.client.get_fund_nav("000001")

        assert result["success"] is True
        assert "data" in result
        assert "timestamp" in result

    def test_get_fund_nav_error(self):
        with patch("asset_lens.data.fund_fetcher.FundDataFetcher", side_effect=Exception("网络错误")):
            result = self.client.get_fund_nav("000001")

        assert result["success"] is False
        assert "error" in result

    def test_analyze_portfolio_success(self):
        mock_analyzer = MagicMock()
        mock_health = MagicMock()
        mock_health.health_score = 85.0
        mock_health.status = "healthy"
        mock_analyzer.analyze_portfolio_health.return_value = mock_health

        with patch("asset_lens.analysis.portfolio_analyzer.PortfolioAnalyzer", return_value=mock_analyzer):
            result = self.client.analyze_portfolio()

        assert result["success"] is True
        assert result["data"]["health_score"] == 85.0
        assert result["data"]["status"] == "healthy"

    def test_analyze_portfolio_error(self):
        with patch("asset_lens.analysis.portfolio_analyzer.PortfolioAnalyzer", side_effect=Exception("分析失败")):
            result = self.client.analyze_portfolio()

        assert result["success"] is False
        assert "error" in result

    def test_screen_stocks_success(self):
        mock_screener = MagicMock()
        mock_screener.screen.return_value = [{"code": "600519", "name": "贵州茅台"}]

        with patch("asset_lens.strategy.screener.StockScreener", return_value=mock_screener):
            result = self.client.screen_stocks(strategy="comprehensive", limit=5)

        assert result["success"] is True
        assert len(result["data"]) == 1
        mock_screener.screen.assert_called_once_with(filter_type="comprehensive")

    def test_screen_stocks_with_limit(self):
        mock_screener = MagicMock()
        mock_screener.screen.return_value = [
            {"code": f"code_{i}", "name": f"stock_{i}"} for i in range(20)
        ]

        with patch("asset_lens.strategy.screener.StockScreener", return_value=mock_screener):
            result = self.client.screen_stocks(strategy="fundamental", limit=5)

        assert result["success"] is True
        assert len(result["data"]) == 5

    def test_screen_stocks_error(self):
        with patch("asset_lens.strategy.screener.StockScreener", side_effect=Exception("筛选失败")):
            result = self.client.screen_stocks()

        assert result["success"] is False
        assert "error" in result

    def test_get_market_indices_success(self):
        with patch.object(self.client, "get_stock_quote") as mock_quote:
            mock_quote.return_value = {"success": True, "data": {"price": 3000.0}}
            result = self.client.get_market_indices()

        assert result["success"] is True
        assert "data" in result

    def test_calculate_risk_metrics_success(self):
        mock_metrics = MagicMock()
        mock_metrics.volatility = 0.15
        mock_metrics.max_drawdown = -0.08
        mock_metrics.sharpe_ratio = 1.2
        mock_metrics.var_95 = -0.03

        with patch("asset_lens.risk.risk_service.calculate_metrics", return_value=mock_metrics):
            result = self.client.calculate_risk_metrics([0.01, -0.02, 0.03])

        assert result["success"] is True
        assert result["data"]["volatility"] == 0.15
        assert result["data"]["sharpe_ratio"] == 1.2

    def test_calculate_risk_metrics_error(self):
        with patch("asset_lens.risk.risk_service.calculate_metrics", side_effect=Exception("计算失败")):
            result = self.client.calculate_risk_metrics([])

        assert result["success"] is False
        assert "error" in result

    def test_generate_report_daily(self):
        mock_monitor = MagicMock()
        mock_monitor.generate_daily_report.return_value = {"summary": "test"}

        with patch("asset_lens.monitoring.investment_monitor.InvestmentMonitor", return_value=mock_monitor):
            result = self.client.generate_report("daily")

        assert result["success"] is True
        mock_monitor.generate_daily_report.assert_called_once()

    def test_generate_report_weekly(self):
        mock_monitor = MagicMock()
        mock_monitor.generate_weekly_report.return_value = {"summary": "test"}

        with patch("asset_lens.monitoring.investment_monitor.InvestmentMonitor", return_value=mock_monitor):
            result = self.client.generate_report("weekly")

        assert result["success"] is True
        mock_monitor.generate_weekly_report.assert_called_once()

    def test_generate_report_default(self):
        mock_monitor = MagicMock()
        mock_monitor.generate_daily_report.return_value = {"summary": "test"}

        with patch("asset_lens.monitoring.investment_monitor.InvestmentMonitor", return_value=mock_monitor):
            result = self.client.generate_report("monthly")

        assert result["success"] is True
        mock_monitor.generate_daily_report.assert_called_once()

    def test_add_to_stock_pool_success(self):
        with patch("asset_lens.db.database.db_manager") as mock_db:
            mock_db.save_stock_info.return_value = None
            result = self.client.add_to_stock_pool("600519", "贵州茅台", 1800.0)

        assert result["success"] is True
        assert "600519" in result["message"]

    def test_get_stock_pool_status_success(self):
        with patch("asset_lens.db.database.db_manager") as mock_db:
            mock_db.get_stock_codes.return_value = ["600519", "000001"]
            mock_db.get_statistics.return_value = {"total": 2}
            result = self.client.get_stock_pool_status()

        assert result["success"] is True
        assert "data" in result
