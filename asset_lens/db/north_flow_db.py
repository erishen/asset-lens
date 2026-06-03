import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import desc

from .models import NorthIndustryFlow

logger = logging.getLogger(__name__)


class NorthFlowDBMixin:
    def save_north_industry_flow(
        self,
        date: str,
        industry_data: list[dict[str, Any]],
        data_source: str = "东方财富(Playwright)",
    ) -> dict[str, int]:
        with self.session_scope() as session:
            added_count = 0
            updated_count = 0
            now = datetime.now()

            for data in industry_data:
                industry = data.get("industry", "")
                if not industry:
                    continue

                existing = (
                    session.query(NorthIndustryFlow)
                    .filter(NorthIndustryFlow.date == date, NorthIndustryFlow.industry == industry)
                    .first()
                )

                if existing:
                    existing.net_inflow = data.get("net_inflow", 0)
                    existing.change_rate = data.get("change_rate", 0)
                    existing.data_source = data_source
                    existing.updated_at = now
                    updated_count += 1
                else:
                    record = NorthIndustryFlow(
                        date=date,
                        industry=industry,
                        net_inflow=data.get("net_inflow", 0),
                        change_rate=data.get("change_rate", 0),
                        data_source=data_source,
                    )
                    session.add(record)
                    added_count += 1

            return {"added": added_count, "updated": updated_count, "total": added_count + updated_count}

    def get_north_industry_flow(
        self,
        date: str | None = None,
        industry: str | None = None,
        days: int = 30,
    ) -> list[dict[str, Any]]:
        with self.session_scope() as session:
            query = session.query(NorthIndustryFlow)

            if date:
                query = query.filter(NorthIndustryFlow.date == date)
            elif days > 0:
                start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
                query = query.filter(NorthIndustryFlow.date >= start_date)

            if industry:
                query = query.filter(NorthIndustryFlow.industry == industry)

            query = query.order_by(desc(NorthIndustryFlow.date), desc(NorthIndustryFlow.net_inflow))

            results = query.all()
            return [r.to_dict() for r in results]

    def get_north_industry_flow_dates(self, days: int = 30) -> list[str]:
        with self.session_scope() as session:
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            results = (
                session.query(NorthIndustryFlow.date)
                .filter(NorthIndustryFlow.date >= start_date)
                .distinct()
                .order_by(desc(NorthIndustryFlow.date))
                .all()
            )

            return [r[0] for r in results]

    def get_north_industry_flow_trend(self, industry: str, days: int = 30) -> list[dict[str, Any]]:
        with self.session_scope() as session:
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            results = (
                session.query(NorthIndustryFlow)
                .filter(
                    NorthIndustryFlow.industry == industry,
                    NorthIndustryFlow.date >= start_date,
                )
                .order_by(NorthIndustryFlow.date)
                .all()
            )

            return [r.to_dict() for r in results]
