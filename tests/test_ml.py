"""
Tests for ML Module.
ML 模块测试
"""


class TestMLTrainer:
    """ML 训练器测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.ml.trainer import ModelTrainer, TrainingConfig, TrainingResult

        assert ModelTrainer is not None
        assert TrainingConfig is not None
        assert TrainingResult is not None

    def test_training_config(self):
        """测试训练配置"""
        from asset_lens.ml.trainer import TrainingConfig

        config = TrainingConfig()
        assert config is not None


class TestMLPredictor:
    """ML 预测器测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.ml.predictor import PredictionResult, StockPredictor

        assert StockPredictor is not None
        assert PredictionResult is not None

    def test_prediction_result(self):
        """测试预测结果"""
        from asset_lens.ml.predictor import PredictionResult

        result = PredictionResult(
            code="sh600519",
            name="贵州茅台",
            up_prob=0.7,
            down_prob=0.3,
            prediction="up",
            confidence=0.7,
            expected_return=0.05,
        )
        assert result.code == "sh600519"
        assert result.prediction == "up"


class TestMLFeatures:
    """ML 特征工程测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.ml.features import FeatureConfig, FeatureEngineer

        assert FeatureEngineer is not None
        assert FeatureConfig is not None

    def test_feature_config(self):
        """测试特征配置"""
        from asset_lens.ml.features import FeatureConfig

        config = FeatureConfig()
        assert config is not None

    def test_feature_engineer_init(self):
        """测试特征工程初始化"""
        from asset_lens.ml.features import FeatureEngineer

        engineer = FeatureEngineer()
        assert engineer is not None


class TestMLAITrader:
    """AI 交易器测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.ml.ai_trader import AISimulatedTrader, TradeRecord, TradeSignal

        assert AISimulatedTrader is not None
        assert TradeSignal is not None
        assert TradeRecord is not None

    def test_trade_signal(self):
        """测试交易信号"""
        from asset_lens.ml.ai_trader import TradeSignal

        signal = TradeSignal(
            code="sh600519",
            name="贵州茅台",
            action="buy",
            confidence=0.8,
            price=1800.0,
            reason="test",
            market_condition="bull",
            strategy="momentum",
        )
        assert signal.code == "sh600519"
        assert signal.action == "buy"


class TestSectorML:
    """板块 ML 测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.ml.sector_ml import SectorMLPredictor, SectorPrediction

        assert SectorMLPredictor is not None
        assert SectorPrediction is not None


class TestSectorRotation:
    """板块轮动测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.ml.sector_rotation import SectorInfo, SectorRotationAnalyzer, SectorRotationResult

        assert SectorRotationAnalyzer is not None
        assert SectorInfo is not None
        assert SectorRotationResult is not None

    def test_sector_info(self):
        """测试板块信息"""
        from asset_lens.ml.sector_rotation import SectorInfo

        info = SectorInfo(
            name="科技",
            code="tech",
            change_percent=2.5,
            volume_ratio=1.5,
            turnover_rate=3.2,
            strength_score=85.0,
            trend="up",
            recommendation="buy",
        )
        assert info.name == "科技"
        assert info.recommendation == "buy"


class TestAdaptiveTrainer:
    """自适应训练器测试"""

    def test_module_import(self):
        """测试模块导入"""
        from asset_lens.ml.adaptive_trainer import AdaptiveMLTrainer, AIMarketAnalyzer, MarketAnalysis

        assert AIMarketAnalyzer is not None
        assert AdaptiveMLTrainer is not None
        assert MarketAnalysis is not None
