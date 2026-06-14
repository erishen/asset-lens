"""
ML 模型优化训练脚本
筛选流动性好的股票，优化模型参数
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import and_, func

from asset_lens.db.database import db_manager
from asset_lens.db.models import StockKline
from asset_lens.ml.trainer import ModelTrainer, TrainingConfig

logger = logging.getLogger(__name__)

logger.info("📊 ML 模型优化训练")
logger.info("=" * 60)

session = db_manager.get_session()

logger.info("1️⃣ 筛选流动性好的股票...")

subquery = session.query(
    StockKline.code,
    func.count(StockKline.id).label('count'),
    func.avg(StockKline.volume).label('avg_volume'),
    func.avg(StockKline.amount).label('avg_amount'),
).group_by(StockKline.code).subquery()

good_stocks = session.query(subquery).filter(
    and_(
        subquery.c.count >= 200,
        subquery.c.avg_volume >= 100000,
        subquery.c.avg_amount >= 1000000,
    )
).order_by(subquery.c.avg_amount.desc()).limit(500).all()

codes = [s.code for s in good_stocks]
logger.info("   筛选出 %s 只流动性好的股票", len(codes))

session.close()

logger.info("2️⃣ 测试不同参数组合...")

configs = [
    {"name": "短期预测(3天)", "prediction_days": 3, "positive_threshold": 0.015, "negative_threshold": -0.015},
    {"name": "中期预测(5天)", "prediction_days": 5, "positive_threshold": 0.02, "negative_threshold": -0.02},
    {"name": "长期预测(10天)", "prediction_days": 10, "positive_threshold": 0.03, "negative_threshold": -0.03},
]

results = []

for cfg in configs:
    logger.info("\n   测试: %s", cfg['name'])

    config = TrainingConfig(
        prediction_days=cfg["prediction_days"],
        positive_threshold=cfg["positive_threshold"],
        negative_threshold=cfg["negative_threshold"],
    )

    trainer = ModelTrainer(model_type="lightgbm", config=config)

    try:
        result = trainer.train_from_database(days=300, codes=codes)
        logger.info(f"   准确率: {result.accuracy:.2%}")
        logger.info(f"   AUC: {result.auc:.2%}")
        logger.info(f"   F1: {result.f1_score:.2%}")
        logger.info("   训练样本: %s", result.training_samples)
        results.append({
            "name": cfg["name"],
            "config": cfg,
            "accuracy": result.accuracy,
            "auc": result.auc,
            "f1": result.f1_score,
        })
    except Exception as e:
        logger.error("   错误: %s", e)

logger.info("\n" + "=" * 60)
logger.info("📊 优化结果汇总:")
logger.info("-" * 60)

if results:
    best = max(results, key=lambda x: x["accuracy"])
    logger.info("\n🏆 最佳配置: %s", best['name'])
    logger.info(f"   准确率: {best['accuracy']:.2%}")
    logger.info(f"   AUC: {best['auc']:.2%}")
    logger.info(f"   F1: {best['f1']:.2%}")

logger.info("✅ 优化训练完成")
