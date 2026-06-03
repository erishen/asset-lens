from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from investkit_utils.db.models import (
    Base,
    DataSyncLog,
    MLModel,
    NorthIndustryFlow,
    PredictionRecord,
    StockKline,
    init_database,
)
from investkit_utils.db.models import (
    DBStockInfo as StockInfo,
)

__all__ = [
    "Base",
    "DataSyncLog",
    "MLModel",
    "NorthIndustryFlow",
    "PredictionRecord",
    "StockInfo",
    "StockKline",
    "init_database",
]


def get_session(db_url: str | None = None) -> Session:
    import warnings

    warnings.warn("get_session() is deprecated, use DatabaseManager.session_scope()", DeprecationWarning, stacklevel=2)
    from .database import db_manager

    return db_manager.get_session()
