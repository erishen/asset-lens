"""
Database module for asset-lens.
"""

try:
    from .database import DatabaseManager, db_manager
    from .models import Base, DataSyncLog, MLModel, PredictionRecord, StockInfo, StockKline, init_database

    __all__ = [
        "Base",
        "DataSyncLog",
        "DatabaseManager",
        "MLModel",
        "PredictionRecord",
        "StockInfo",
        "StockKline",
        "db_manager",
        "init_database",
    ]
except ImportError:
    pass
