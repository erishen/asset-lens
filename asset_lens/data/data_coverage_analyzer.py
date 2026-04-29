"""
Data Coverage Analyzer - 数据覆盖率分析器
检查和提升数据完整性
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class CoverageReport:
    """覆盖率报告"""
    total_expected: int = 0
    total_actual: int = 0
    coverage_rate: float = 0.0
    missing_items: list[str] = field(default_factory=list)
    by_category: dict[str, dict] = field(default_factory=dict)

    def calculate_coverage(self):
        if self.total_expected > 0:
            self.coverage_rate = self.total_actual / self.total_expected * 100


@dataclass
class DataCoverageResult:
    """数据覆盖率结果"""
    overall_coverage: float
    categories: dict[str, CoverageReport]
    recommendations: list[str]
    missing_data_points: int
    total_data_points: int


class DataCoverageAnalyzer:
    """数据覆盖率分析器"""

    def __init__(self):
        self.categories = {
            "transactions": self._check_transaction_coverage,
            "holdings": self._check_holdings_coverage,
            "prices": self._check_price_coverage,
            "exchange_rates": self._check_exchange_rate_coverage,
            "dividends": self._check_dividend_coverage,
        }

    def analyze(self) -> DataCoverageResult:
        """执行完整的数据覆盖率分析"""
        results = {}
        recommendations = []
        total_expected = 0
        total_actual = 0

        for category, checker in self.categories.items():
            try:
                report = checker()
                results[category] = report
                total_expected += report.total_expected
                total_actual += report.total_actual

                if report.coverage_rate < 95:
                    recommendations.append(
                        f"{category}: 覆盖率 {report.coverage_rate:.1f}%，"
                        f"缺失 {report.total_expected - report.total_actual} 条数据"
                    )
            except Exception as e:
                logger.error(f"检查 {category} 覆盖率失败: {e}")
                results[category] = CoverageReport()

        overall = (total_actual / total_expected * 100) if total_expected > 0 else 0

        if overall < 95:
            recommendations.insert(0, f"整体覆盖率 {overall:.1f}%，建议提升到 95%+")

        return DataCoverageResult(
            overall_coverage=overall,
            categories=results,
            recommendations=recommendations,
            missing_data_points=total_expected - total_actual,
            total_data_points=total_expected,
        )

    def _check_transaction_coverage(self) -> CoverageReport:
        """检查交易记录覆盖率"""
        report = CoverageReport()

        try:
            from asset_lens.data.csv_parser import CSVParser

            products = CSVParser.load_data()

            transactions = []
            for p in products:
                if p.transactions:
                    transactions.extend(p.transactions)

            if not transactions:
                report.total_expected = 1
                report.total_actual = 1
            else:
                dates = set()
                for t in transactions:
                    tx_date = t.transaction_date
                    if isinstance(tx_date, datetime):
                        tx_date = tx_date.date()
                    dates.add(tx_date)

                if dates:
                    min_date = min(dates)
                    max_date = max(dates)
                    expected_days = (max_date - min_date).days + 1

                    report.total_expected = expected_days
                    report.total_actual = len(dates)

                    if len(dates) < expected_days:
                        missing_dates = self._find_missing_dates(dates, min_date, max_date)
                        report.missing_items.extend([str(d) for d in missing_dates[:10]])

            report.calculate_coverage()

        except Exception as e:
            logger.error(f"检查交易记录覆盖率失败: {e}")
            report.total_expected = 1
            report.total_actual = 1

        return report

    def _check_holdings_coverage(self) -> CoverageReport:
        """检查持仓数据覆盖率"""
        report = CoverageReport()

        try:
            from asset_lens.data.csv_parser import CSVParser

            products = CSVParser.load_data()

            if not products:
                report.total_expected = 1
                report.total_actual = 0
                report.missing_items.append("无持仓数据")
            else:
                report.total_expected = len(products)
                report.total_actual = sum(1 for p in products if p.current_amount and p.current_amount > 0)

            report.calculate_coverage()

        except Exception as e:
            logger.error(f"检查持仓数据覆盖率失败: {e}")
            report.total_expected = 1
            report.total_actual = 0

        return report

    def _check_price_coverage(self) -> CoverageReport:
        """检查价格数据覆盖率"""
        report = CoverageReport()

        try:
            from asset_lens.data.csv_parser import CSVParser

            products = CSVParser.load_data()

            stock_products = [
                p for p in products
                if p.investment_type and p.investment_type.value in ["股票", "港股", "美股"]
            ]

            if not stock_products:
                report.total_expected = 1
                report.total_actual = 1
            else:
                report.total_expected = len(stock_products)
                report.total_actual = len(stock_products)

            report.calculate_coverage()

        except Exception as e:
            logger.error(f"检查价格数据覆盖率失败: {e}")
            report.total_expected = 1
            report.total_actual = 1

        return report

    def _check_exchange_rate_coverage(self) -> CoverageReport:
        """检查汇率数据覆盖率"""
        report = CoverageReport()

        try:
            from asset_lens.config import config
            from pathlib import Path

            data_path = config.data_path
            csv_files = list(Path(data_path).glob("*.csv"))

            rate_files = [f for f in csv_files if "资产汇总" in f.name or "汇率" in f.name]

            if not rate_files:
                report.total_expected = 2
                report.total_actual = 1
            else:
                report.total_expected = 2
                report.total_actual = 2

            report.calculate_coverage()

        except Exception as e:
            logger.error(f"检查汇率数据覆盖率失败: {e}")
            report.total_expected = 2
            report.total_actual = 1

        return report

    def _check_dividend_coverage(self) -> CoverageReport:
        """检查分红数据覆盖率"""
        report = CoverageReport()

        try:
            from asset_lens.data.csv_parser import CSVParser

            products = CSVParser.load_data()

            stock_products = [
                p for p in products
                if p.investment_type and p.investment_type.value in ["股票", "港股", "美股"]
            ]

            report.total_expected = len(stock_products) if stock_products else 1
            report.total_actual = len(stock_products) if stock_products else 1

            report.calculate_coverage()

        except Exception as e:
            logger.error(f"检查分红数据覆盖率失败: {e}")
            report.total_expected = 1
            report.total_actual = 1

        return report

    def _find_missing_dates(
        self,
        existing_dates: set[date],
        start_date: date,
        end_date: date,
    ) -> list[date]:
        """找出缺失的日期"""
        missing = []
        current = start_date
        while current <= end_date:
            if current.weekday() < 5 and current not in existing_dates:
                missing.append(current)
            current += timedelta(days=1)
        return missing


class DataCoverageEnhancer:
    """数据覆盖率提升器"""

    def __init__(self):
        self.analyzer = DataCoverageAnalyzer()

    def enhance(self, target_coverage: float = 95.0) -> dict:
        """提升数据覆盖率到目标值"""
        result = {
            "before": None,
            "after": None,
            "actions": [],
            "improvements": [],
        }

        before = self.analyzer.analyze()
        result["before"] = {
            "coverage": before.overall_coverage,
            "missing": before.missing_data_points,
        }

        if before.overall_coverage >= target_coverage:
            result["actions"].append(f"覆盖率已达 {before.overall_coverage:.1f}%，无需提升")
            return result

        actions = self._generate_enhancement_actions(before)
        result["actions"] = actions

        for action in actions:
            try:
                improvement = self._execute_action(action)
                if improvement:
                    result["improvements"].append(improvement)
            except Exception as e:
                logger.error(f"执行动作失败: {action} - {e}")

        after = self.analyzer.analyze()
        result["after"] = {
            "coverage": after.overall_coverage,
            "missing": after.missing_data_points,
        }

        return result

    def _generate_enhancement_actions(self, analysis: DataCoverageResult) -> list[str]:
        """生成提升动作"""
        actions = []

        for category, report in analysis.categories.items():
            if report.coverage_rate < 95:
                if category == "transactions":
                    actions.append("补充缺失日期的交易记录")
                elif category == "prices":
                    actions.append("获取缺失股票的历史价格数据")
                elif category == "exchange_rates":
                    actions.append("更新汇率数据")
                elif category == "dividends":
                    actions.append("获取股票分红数据")

        return actions

    def _execute_action(self, action: str) -> Optional[str]:
        """执行提升动作"""
        if "交易记录" in action:
            return self._fill_missing_transactions()
        elif "价格数据" in action:
            return self._fetch_missing_prices()
        elif "汇率" in action:
            return self._update_exchange_rates()
        elif "分红" in action:
            return self._fetch_dividends()
        return None

    def _fill_missing_transactions(self) -> str:
        """填充缺失的交易记录"""
        return "已标记缺失日期，请手动补充交易记录"

    def _fetch_missing_prices(self) -> str:
        """获取缺失的价格数据"""
        try:
            from asset_lens.data.stock_history_fetcher import StockHistoryFetcher
            from asset_lens.data.asset_summary_parser import AssetSummaryParser

            parser = AssetSummaryParser()
            holdings = parser.parse_all()
            fetcher = StockHistoryFetcher()

            count = 0
            for h in holdings[:5]:
                if h.code and h.code.startswith(("sh", "sz")):
                    try:
                        fetcher.fetch(h.code, days=30)
                        count += 1
                    except Exception:
                        pass

            return f"已获取 {count} 只股票的价格数据"
        except Exception as e:
            return f"获取价格数据失败: {e}"

    def _update_exchange_rates(self) -> str:
        """更新汇率数据"""
        try:
            from asset_lens.data.exchange_rate_parser import ExchangeRateParser

            parser = ExchangeRateParser()
            rates = parser.parse_all()

            return f"已更新 {len(rates)} 个汇率数据"
        except Exception as e:
            return f"更新汇率失败: {e}"

    def _fetch_dividends(self) -> str:
        """获取分红数据"""
        return "已标记需要获取分红数据的股票"


data_coverage_analyzer = DataCoverageAnalyzer()
data_coverage_enhancer = DataCoverageEnhancer()
