"""
Database models for asset-lens.
数据库模型定义 - 使用 SQLAlchemy ORM
"""

# mypy: ignore-errors

import warnings
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker

warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlalchemy")

Base = declarative_base()


class StockKline(Base):
    """股票K线数据表"""

    __tablename__ = "stock_klines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), nullable=False, comment="股票代码")
    date = Column(String(10), nullable=False, comment="交易日期")
    open = Column(Float, default=0, comment="开盘价")
    close = Column(Float, default=0, comment="收盘价")
    high = Column(Float, default=0, comment="最高价")
    low = Column(Float, default=0, comment="最低价")
    volume = Column(Float, default=0, comment="成交量")
    amount = Column(Float, default=0, comment="成交额")
    amplitude = Column(Float, default=0, comment="振幅%")
    change_percent = Column(Float, default=0, comment="涨跌幅%")
    change_amount = Column(Float, default=0, comment="涨跌额")
    turnover_rate = Column(Float, default=0, comment="换手率%")
    data_source = Column(String(50), default="", comment="数据来源")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    __table_args__ = (
        Index("idx_kline_code_date", "code", "date", unique=True),
        Index("idx_kline_date", "date"),
        Index("idx_kline_code", "code"),
    )

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "open": self.open,
            "close": self.close,
            "high": self.high,
            "low": self.low,
            "volume": self.volume,
            "amount": self.amount,
            "amplitude": self.amplitude,
            "change_percent": self.change_percent,
            "change_amount": self.change_amount,
            "turnover_rate": self.turnover_rate,
        }


class StockInfo(Base):
    """股票基本信息表"""

    __tablename__ = "stock_info"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False, comment="股票代码")
    name = Column(String(50), default="", comment="股票名称")
    industry = Column(String(50), default="", comment="所属行业")
    sector = Column(String(50), default="", comment="所属板块")
    market = Column(String(20), default="", comment="市场(SH/SZ/BJ)")
    list_date = Column(String(10), default="", comment="上市日期")
    total_shares = Column(Float, default=0, comment="总股本(万股)")
    float_shares = Column(Float, default=0, comment="流通股本(万股)")
    total_market_cap = Column(Float, default=0, comment="总市值(万元)")
    is_active = Column(Boolean, default=True, comment="是否活跃")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    __table_args__ = (Index("idx_stock_code", "code"),)


class MLModel(Base):
    """机器学习模型存储表"""

    __tablename__ = "ml_models"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="模型名称")
    model_type = Column(String(50), default="lightgbm", comment="模型类型")
    version = Column(String(20), default="1.0.0", comment="模型版本")
    params = Column(Text, default="{}", comment="模型参数JSON")
    feature_importance = Column(Text, default="{}", comment="特征重要性JSON")
    metrics = Column(Text, default="{}", comment="评估指标JSON")
    train_samples = Column(Integer, default=0, comment="训练样本数")
    train_features = Column(Integer, default=0, comment="特征数量")
    train_date_start = Column(String(10), default="", comment="训练数据起始日期")
    train_date_end = Column(String(10), default="", comment="训练数据结束日期")
    is_active = Column(Boolean, default=True, comment="是否激活")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    __table_args__ = (Index("idx_model_name_version", "name", "version"),)


class PredictionRecord(Base):
    """预测记录表"""

    __tablename__ = "prediction_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(Integer, default=0, comment="模型ID")
    code = Column(String(20), nullable=False, comment="股票代码")
    predict_date = Column(String(10), nullable=False, comment="预测日期")
    prediction = Column(Integer, default=0, comment="预测结果(0跌/1涨)")
    confidence = Column(Float, default=0, comment="置信度")
    features = Column(Text, default="{}", comment="特征值JSON")
    actual_result = Column(Integer, default=None, comment="实际结果(用于验证)")
    is_correct = Column(Boolean, default=None, comment="预测是否正确")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")

    __table_args__ = (
        Index("idx_pred_code_date", "code", "predict_date"),
        Index("idx_pred_model", "model_id"),
    )


class DataSyncLog(Base):
    """数据同步日志表"""

    __tablename__ = "data_sync_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    data_type = Column(String(50), nullable=False, comment="数据类型(kline/stock_info/etc)")
    data_source = Column(String(50), default="", comment="数据来源")
    sync_start = Column(DateTime, nullable=False, comment="同步开始时间")
    sync_end = Column(DateTime, default=None, comment="同步结束时间")
    records_total = Column(Integer, default=0, comment="总记录数")
    records_success = Column(Integer, default=0, comment="成功记录数")
    records_failed = Column(Integer, default=0, comment="失败记录数")
    status = Column(String(20), default="running", comment="状态(running/success/failed)")
    error_message = Column(Text, default="", comment="错误信息")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")

    __table_args__ = (Index("idx_sync_type_date", "data_type", "sync_start"),)


def init_database(db_url: str = "sqlite:///./data/asset_lens.db"):
    """
    初始化数据库

    Args:
        db_url: 数据库连接URL

    Returns:
        engine, Session
    """
    engine = create_engine(
        db_url,
        echo=False,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
        pool_timeout=30,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return engine, Session


def get_session(db_url: str = "sqlite:///./data/asset_lens.db"):
    """
    获取数据库会话

    Args:
        db_url: 数据库连接URL

    Returns:
        Session实例
    """
    engine, Session = init_database(db_url)
    return Session()
