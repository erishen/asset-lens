"""
ML 模型参数优化脚本
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


from asset_lens.ml.trainer import ModelTrainer, TrainingConfig

logger = logging.getLogger(__name__)

configs = [
    {"prediction_days": 3, "positive_threshold": 0.015, "negative_threshold": -0.015},
    {"prediction_days": 5, "positive_threshold": 0.025, "negative_threshold": -0.025},
    {"prediction_days": 10, "positive_threshold": 0.03, "negative_threshold": -0.03},
]

logger.info("📊 开始参数优化测试...")
logger.info("=" * 60)

results = []

for i, cfg in enumerate(configs, 1):
    logger.info("\n测试配置 %s: prediction_days=%s, threshold=%s", i, cfg['prediction_days'], cfg['positive_threshold'])

    config = TrainingConfig(
        prediction_days=cfg["prediction_days"],
        positive_threshold=cfg["positive_threshold"],
        negative_threshold=cfg["negative_threshold"],
    )

    trainer = ModelTrainer(model_type="lightgbm", config=config)

    try:
        result = trainer.train_from_database(days=300)
        logger.info(f"  准确率: {result.accuracy:.2%}")
        logger.info(f"  AUC: {result.auc:.2%}")
        logger.info(f"  F1: {result.f1_score:.2%}")
        logger.info("  训练样本: %s", result.training_samples)
        results.append({
            "config": cfg,
            "accuracy": result.accuracy,
            "auc": result.auc,
            "f1": result.f1_score,
        })
    except Exception as e:
        logger.error("  错误: %s", e)

logger.info("\n" + "=" * 60)
logger.info("📊 参数优化结果汇总:")
logger.info("-" * 60)

if results:
    best = max(results, key=lambda x: x["accuracy"])
    logger.info("最佳配置: prediction_days=%s, threshold=%s", best['config']['prediction_days'], best['config']['positive_threshold'])
    logger.info(f"最佳准确率: {best['accuracy']:.2%}")
    logger.info(f"最佳 AUC: {best['auc']:.2%}")

logger.info("✅ 参数优化测试完成")
