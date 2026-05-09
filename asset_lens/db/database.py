"""
Database manager for asset-lens.
数据库管理器 - 提供数据存储和查询接口
"""

# pylint: disable=not-callable
# mypy: ignore-errors

import json
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any

from investkit_utils.db.paths import ensure_data_dir, get_asset_lens_db_path
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from .models import DataSyncLog, MLModel, PredictionRecord, StockInfo, StockKline, init_database


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_path: str | None = None):
        if db_path is None:
            ensure_data_dir()
            db_path = f"sqlite:///{get_asset_lens_db_path()}"

        self.db_url = db_path
        self.engine, self.SessionLocal = init_database(db_path)

    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """提供事务范围的会话上下文管理器"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def close(self):
        """关闭数据库连接"""
        self.engine.dispose()

    def save_klines(
        self,
        code: str,
        klines: list[dict[str, Any]],
        data_source: str = "Unknown",
    ) -> int:
        """
        保存K线数据（批量优化版本）

        Args:
            code: 股票代码
            klines: K线数据列表
            data_source: 数据来源

        Returns:
            保存的记录数
        """
        with self.session_scope() as session:
            valid_klines = [k for k in klines if k.get("date")]
            if not valid_klines:
                return 0

            dates = [k["date"] for k in valid_klines]
            existing_map = {}
            for row in session.query(StockKline).filter(
                StockKline.code == code, StockKline.date.in_(dates)
            ).all():
                existing_map[row.date] = row

            saved_count = 0
            now = datetime.now()
            for kline in valid_klines:
                date = kline["date"]
                existing = existing_map.get(date)

                if existing:
                    existing.open = kline.get("open", 0)
                    existing.close = kline.get("close", 0)
                    existing.high = kline.get("high", 0)
                    existing.low = kline.get("low", 0)
                    existing.volume = kline.get("volume", 0)
                    existing.amount = kline.get("amount", 0)
                    existing.amplitude = kline.get("amplitude", 0)
                    existing.change_percent = kline.get("change_percent", 0)
                    existing.change_amount = kline.get("change_amount", 0)
                    existing.turnover_rate = kline.get("turnover_rate", 0)
                    existing.data_source = data_source
                    existing.updated_at = now
                else:
                    record = StockKline(
                        code=code,
                        date=date,
                        open=kline.get("open", 0),
                        close=kline.get("close", 0),
                        high=kline.get("high", 0),
                        low=kline.get("low", 0),
                        volume=kline.get("volume", 0),
                        amount=kline.get("amount", 0),
                        amplitude=kline.get("amplitude", 0),
                        change_percent=kline.get("change_percent", 0),
                        change_amount=kline.get("change_amount", 0),
                        turnover_rate=kline.get("turnover_rate", 0),
                        data_source=data_source,
                    )
                    session.add(record)
                    saved_count += 1

            return saved_count

    def get_stock_codes_with_klines(self) -> set[str]:
        """
        获取已有K线数据的股票代码集合

        Returns:
            股票代码集合
        """
        with self.session_scope() as session:
            from sqlalchemy import distinct

            results = session.query(distinct(StockKline.code)).all()
            return {r[0] for r in results}

    def get_klines(
        self,
        code: str,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        """
        获取K线数据

        Args:
            code: 股票代码
            start_date: 起始日期
            end_date: 结束日期
            limit: 最大返回数量

        Returns:
            K线数据列表
        """
        with self.session_scope() as session:
            query = session.query(StockKline).filter(StockKline.code == code)

            if start_date:
                query = query.filter(StockKline.date >= start_date)
            if end_date:
                query = query.filter(StockKline.date <= end_date)

            query = query.order_by(desc(StockKline.date)).limit(limit)

            results = query.all()
            klines = [r.to_dict() for r in reversed(results)]
            return klines

    def get_klines_for_ml(
        self,
        codes: list[str] | None = None,
        days: int = 250,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        获取用于机器学习的K线数据

        Args:
            codes: 股票代码列表，为空则获取所有
            days: 历史天数

        Returns:
            股票代码到K线数据的映射
        """
        with self.session_scope() as session:
            start_date = (datetime.now() - timedelta(days=days + 30)).strftime("%Y-%m-%d")

            query = session.query(StockKline).filter(StockKline.date >= start_date)

            if codes:
                query = query.filter(StockKline.code.in_(codes))

            query = query.order_by(StockKline.code, StockKline.date)

            results = query.all()

            data: dict[str, list[dict[str, Any]]] = {}
            for record in results:
                if record.code not in data:
                    data[record.code] = []
                data[record.code].append(record.to_dict())

            return data

    def get_stock_codes(self) -> list[str]:
        """获取所有有K线数据的股票代码"""
        with self.session_scope() as session:
            results = session.query(StockKline.code).distinct().all()
            return [r[0] for r in results]

    def get_kline_count(self, code: str | None = None) -> int:
        """获取K线数据数量"""
        with self.session_scope() as session:
            query = session.query(func.count(StockKline.id))
            if code:
                query = query.filter(StockKline.code == code)
            return query.scalar() or 0

    def save_stock_info(self, info: dict[str, Any]) -> bool:
        """保存股票基本信息"""
        with self.session_scope() as session:
            code = info.get("code", "")
            if not code:
                return False

            existing = session.query(StockInfo).filter(StockInfo.code == code).first()

            if existing:
                for key, value in info.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                existing.updated_at = datetime.now()
            else:
                record = StockInfo(**info)
                session.add(record)

            return True

    def get_stock_info(self, code: str) -> dict[str, Any] | None:
        """获取股票基本信息"""
        with self.session_scope() as session:
            record = session.query(StockInfo).filter(StockInfo.code == code).first()
            if record:
                return {
                    "code": record.code,
                    "name": record.name,
                    "industry": record.industry,
                    "sector": record.sector,
                    "market": record.market,
                    "list_date": record.list_date,
                    "total_shares": record.total_shares,
                    "float_shares": record.float_shares,
                    "total_market_cap": record.total_market_cap,
                    "is_active": record.is_active,
                }
            return None

    def save_ml_model(
        self,
        name: str,
        model_type: str,
        params: dict[str, Any],
        feature_importance: dict[str, float],
        metrics: dict[str, float],
        train_samples: int = 0,
        train_features: int = 0,
        version: str = "1.0.0",
    ) -> int:
        """
        保存ML模型记录

        Returns:
            模型ID
        """
        with self.session_scope() as session:
            record = MLModel(
                name=name,
                model_type=model_type,
                version=version,
                params=json.dumps(params),
                feature_importance=json.dumps(feature_importance),
                metrics=json.dumps(metrics),
                train_samples=train_samples,
                train_features=train_features,
                train_date_start="",
                train_date_end="",
            )
            session.add(record)
            session.flush()
            return record.id

    def get_latest_model(self, name: str = "stock_predictor") -> dict[str, Any] | None:
        """获取最新的ML模型"""
        with self.session_scope() as session:
            record = (
                session.query(MLModel)
                .filter(MLModel.name == name, MLModel.is_active)
                .order_by(desc(MLModel.created_at))
                .first()
            )
            if record:
                return {
                    "id": record.id,
                    "name": record.name,
                    "model_type": record.model_type,
                    "version": record.version,
                    "params": json.loads(record.params),
                    "feature_importance": json.loads(record.feature_importance),
                    "metrics": json.loads(record.metrics),
                    "train_samples": record.train_samples,
                    "train_features": record.train_features,
                    "created_at": record.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
            return None

    def save_prediction(
        self,
        model_id: int,
        code: str,
        prediction: int,
        confidence: float,
        features: dict[str, Any] | None = None,
    ) -> int:
        """保存预测记录"""
        with self.session_scope() as session:
            record = PredictionRecord(
                model_id=model_id,
                code=code,
                predict_date=datetime.now().strftime("%Y-%m-%d"),
                prediction=prediction,
                confidence=confidence,
                features=json.dumps(features or {}),
            )
            session.add(record)
            session.flush()
            return record.id

    def get_predictions(
        self,
        code: str | None = None,
        model_id: int | None = None,
        days: int = 30,
    ) -> list[dict[str, Any]]:
        """获取预测记录"""
        with self.session_scope() as session:
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            query = session.query(PredictionRecord).filter(PredictionRecord.predict_date >= start_date)

            if code:
                query = query.filter(PredictionRecord.code == code)
            if model_id:
                query = query.filter(PredictionRecord.model_id == model_id)

            query = query.order_by(desc(PredictionRecord.created_at))

            results = query.all()
            return [
                {
                    "id": r.id,
                    "model_id": r.model_id,
                    "code": r.code,
                    "predict_date": r.predict_date,
                    "prediction": r.prediction,
                    "confidence": r.confidence,
                    "actual_result": r.actual_result,
                    "is_correct": r.is_correct,
                    "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for r in results
            ]

    def log_sync(
        self,
        data_type: str,
        data_source: str,
        records_total: int = 0,
        records_success: int = 0,
        records_failed: int = 0,
        status: str = "running",
        error_message: str = "",
    ) -> int:
        """记录数据同步日志"""
        with self.session_scope() as session:
            record = DataSyncLog(
                data_type=data_type,
                data_source=data_source,
                sync_start=datetime.now(),
                records_total=records_total,
                records_success=records_success,
                records_failed=records_failed,
                status=status,
                error_message=error_message,
            )
            session.add(record)
            session.flush()
            return record.id

    def update_sync_log(
        self,
        log_id: int,
        records_success: int = 0,
        records_failed: int = 0,
        status: str = "success",
        error_message: str = "",
    ):
        """更新同步日志"""
        with self.session_scope() as session:
            record = session.query(DataSyncLog).filter(DataSyncLog.id == log_id).first()
            if record:
                record.sync_end = datetime.now()
                record.records_success = records_success
                record.records_failed = records_failed
                record.status = status
                record.error_message = error_message

    def get_statistics(self) -> dict[str, Any]:
        """获取数据库统计信息"""
        with self.session_scope() as session:
            kline_count = session.query(func.count(StockKline.id)).scalar() or 0
            stock_count = session.query(func.count(func.distinct(StockKline.code))).scalar() or 0
            model_count = session.query(func.count(MLModel.id)).scalar() or 0
            prediction_count = session.query(func.count(PredictionRecord.id)).scalar() or 0

            latest_kline = session.query(StockKline.date).order_by(desc(StockKline.date)).first()
            latest_date = latest_kline[0] if latest_kline else ""

            data_sources = (
                session.query(
                    StockKline.data_source,
                    func.count(StockKline.id).label("count"),
                )
                .group_by(StockKline.data_source)
                .all()
            )

            return {
                "kline_count": kline_count,
                "stock_count": stock_count,
                "model_count": model_count,
                "prediction_count": prediction_count,
                "latest_date": latest_date,
                "data_sources": {ds: count for ds, count in data_sources if ds},
            }

    def clear_old_data(self, days: int = 365) -> int:
        """清理旧数据"""
        with self.session_scope() as session:
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            deleted = session.query(StockKline).filter(StockKline.date < cutoff_date).delete()
            return deleted

    def auto_sync_history(
        self,
        fast: bool = False,
        days: int = 250,
        daily_limit: int = 100,
    ) -> dict[str, Any]:
        """自动同步股票历史数据

        Args:
            fast: 是否快速模式（减少延迟）
            days: 历史天数
            daily_limit: 每日同步数量限制

        Returns:
            同步结果统计
        """
        from ..data.market_stock_fetcher import MarketStockFetcher
        from .migration import DataMigration

        fetcher = MarketStockFetcher()
        stocks_data = fetcher.get_cached_market_stocks()

        if not stocks_data:
            stocks_data = fetcher.fetch_all_cn_stocks(max_pages=3)
            if stocks_data:
                fetcher.save_market_stocks(stocks_data)

        if not stocks_data:
            return {"synced": 0, "success": 0, "failed": 0, "message": "无法获取股票列表"}

        existing_codes = self.get_stock_codes_with_klines()
        all_codes = [s.get("code", "") for s in stocks_data if s.get("code")]
        need_sync = [c for c in all_codes if c and c not in existing_codes]

        if daily_limit > 0:
            need_sync = need_sync[:daily_limit]

        if not need_sync:
            return {"synced": 0, "success": 0, "failed": 0, "message": "所有股票已同步"}

        migration = DataMigration()
        delay = 0.1 if fast else 0.3
        result = migration.fetch_and_store_history(
            codes=need_sync,
            days=days,
            delay=delay,
        )

        return {
            "synced": result.get("success", 0),
            "success": result.get("success", 0),
            "failed": result.get("failed", 0),
            "total": len(need_sync),
        }


db_manager = DatabaseManager()
