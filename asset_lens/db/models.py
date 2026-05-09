from investkit_utils.db.models import (
    Base,
    DataSyncLog,
    MLModel,
    PredictionRecord,
    StockInfo,
    StockKline,
    init_database,
)

__all__ = [
    "Base",
    "DataSyncLog",
    "MLModel",
    "PredictionRecord",
    "StockInfo",
    "StockKline",
    "init_database",
]


def get_session(db_url: str | None = None):
    import warnings
    warnings.warn("get_session() is deprecated, use DatabaseManager.session_scope()", DeprecationWarning, stacklevel=2)
    from .database import db_manager
    return db_manager.get_session()
