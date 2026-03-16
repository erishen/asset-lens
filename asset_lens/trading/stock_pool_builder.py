"""
Stock Pool Builder - 股票池构建层
多来源筛选规则组合与可视化输出

功能:
1. 基本面筛选 - 财务指标、估值指标
2. 技术面筛选 - 趋势、动量、波动
3. 情绪面筛选 - 资金流向、市场情绪
4. 行业轮动 - 板块轮动、行业配置
5. 财务质量 - 盈利质量、现金流
6. 因子分层 - 多因子模型

输出:
- 入池理由矩阵
- 备选股票池
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class FactorCategory(Enum):
    """因子类别"""
    FUNDAMENTAL = "基本面"
    TECHNICAL = "技术面"
    SENTIMENT = "情绪面"
    INDUSTRY = "行业轮动"
    QUALITY = "财务质量"
    FACTOR = "因子分层"


@dataclass
class FilterCondition:
    """筛选条件"""
    name: str
    category: FactorCategory
    field: str
    operator: str  # >, <, >=, <=, ==, !=, between, in
    value: Any
    weight: float = 1.0
    description: str = ""
    
    def evaluate(self, data: Dict[str, Any]) -> bool:
        """评估条件"""
        field_value = data.get(self.field)
        if field_value is None:
            return False
        
        if self.operator == ">":
            return float(field_value) > float(self.value)
        elif self.operator == "<":
            return float(field_value) < float(self.value)
        elif self.operator == ">=":
            return float(field_value) >= float(self.value)
        elif self.operator == "<=":
            return float(field_value) <= float(self.value)
        elif self.operator == "==":
            return bool(field_value == self.value)
        elif self.operator == "!=":
            return bool(field_value != self.value)
        elif self.operator == "between":
            if isinstance(self.value, (list, tuple)) and len(self.value) == 2:
                return float(self.value[0]) <= float(field_value) <= float(self.value[1])
        elif self.operator == "in":
            return field_value in self.value
        
        return False


@dataclass
class EntryReason:
    """入池理由"""
    factor_name: str
    category: FactorCategory
    score: float
    weight: float
    passed: bool
    value: Any
    threshold: Any
    contribution: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "factor_name": self.factor_name,
            "category": self.category.value,
            "score": self.score,
            "weight": self.weight,
            "passed": self.passed,
            "value": self.value,
            "threshold": self.threshold,
            "contribution": self.contribution,
        }


@dataclass
class StockEntryMatrix:
    """股票入池理由矩阵"""
    code: str
    name: str
    total_score: float
    weighted_score: float
    passed_factors: int
    total_factors: int
    entry_reasons: List[EntryReason]
    entry_date: str
    data_source: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "total_score": self.total_score,
            "weighted_score": round(self.weighted_score, 2),
            "passed_factors": self.passed_factors,
            "total_factors": self.total_factors,
            "pass_rate": round(self.passed_factors / self.total_factors * 100, 1) if self.total_factors > 0 else 0,
            "entry_reasons": [r.to_dict() for r in self.entry_reasons],
            "entry_date": self.entry_date,
            "data_source": self.data_source,
        }


class StockPoolBuilder:
    """股票池构建器"""
    
    def __init__(self):
        self.conditions: List[FilterCondition] = []
        self.min_score: float = 60.0
        self.min_pass_rate: float = 0.5
    
    def add_condition(self, condition: FilterCondition) -> None:
        """添加筛选条件"""
        self.conditions.append(condition)
    
    def add_fundamental_filters(self) -> None:
        """添加基本面筛选条件"""
        self.add_condition(FilterCondition(
            name="PE合理",
            category=FactorCategory.FUNDAMENTAL,
            field="pe_ratio",
            operator="<",
            value=30,
            weight=1.0,
            description="市盈率小于30倍",
        ))
        self.add_condition(FilterCondition(
            name="PB合理",
            category=FactorCategory.FUNDAMENTAL,
            field="pb_ratio",
            operator="<",
            value=5,
            weight=0.8,
            description="市净率小于5倍",
        ))
        self.add_condition(FilterCondition(
            name="ROE优秀",
            category=FactorCategory.FUNDAMENTAL,
            field="roe",
            operator=">",
            value=10,
            weight=1.2,
            description="ROE大于10%",
        ))
        self.add_condition(FilterCondition(
            name="营收增长",
            category=FactorCategory.FUNDAMENTAL,
            field="revenue_growth",
            operator=">",
            value=10,
            weight=1.0,
            description="营收增长率大于10%",
        ))
    
    def add_technical_filters(self) -> None:
        """添加技术面筛选条件"""
        self.add_condition(FilterCondition(
            name="均线多头",
            category=FactorCategory.TECHNICAL,
            field="ma_trend",
            operator="==",
            value="bullish",
            weight=1.0,
            description="均线呈多头排列",
        ))
        self.add_condition(FilterCondition(
            name="突破20日高点",
            category=FactorCategory.TECHNICAL,
            field="break_20d_high",
            operator="==",
            value=True,
            weight=1.2,
            description="突破20日新高",
        ))
        self.add_condition(FilterCondition(
            name="成交量放大",
            category=FactorCategory.TECHNICAL,
            field="volume_ratio",
            operator=">",
            value=1.5,
            weight=0.8,
            description="成交量放大1.5倍以上",
        ))
    
    def add_sentiment_filters(self) -> None:
        """添加情绪面筛选条件"""
        self.add_condition(FilterCondition(
            name="主力净流入",
            category=FactorCategory.SENTIMENT,
            field="main_inflow",
            operator=">",
            value=0,
            weight=1.0,
            description="主力资金净流入",
        ))
        self.add_condition(FilterCondition(
            name="北向资金增持",
            category=FactorCategory.SENTIMENT,
            field="north_inflow",
            operator=">",
            value=0,
            weight=0.8,
            description="北向资金净买入",
        ))
    
    def evaluate_stock(self, stock_data: Dict[str, Any]) -> StockEntryMatrix:
        """评估单只股票"""
        code = stock_data.get("code", "")
        name = stock_data.get("name", "")
        
        entry_reasons: List[EntryReason] = []
        total_score = 0.0
        weighted_score = 0.0
        total_weight = 0.0
        passed_count = 0
        
        for condition in self.conditions:
            passed = condition.evaluate(stock_data)
            field_value = stock_data.get(condition.field, "N/A")
            
            score = 100 if passed else 0
            contribution = score * condition.weight
            
            entry_reasons.append(EntryReason(
                factor_name=condition.name,
                category=condition.category,
                score=score,
                weight=condition.weight,
                passed=passed,
                value=field_value,
                threshold=condition.value,
                contribution=contribution,
            ))
            
            total_score += score
            weighted_score += contribution
            total_weight += condition.weight
            
            if passed:
                passed_count += 1
        
        avg_score = total_score / len(self.conditions) if self.conditions else 0
        normalized_weighted_score = weighted_score / total_weight if total_weight > 0 else 0
        
        return StockEntryMatrix(
            code=code,
            name=name,
            total_score=round(avg_score, 2),
            weighted_score=normalized_weighted_score,
            passed_factors=passed_count,
            total_factors=len(self.conditions),
            entry_reasons=entry_reasons,
            entry_date=datetime.now().strftime("%Y-%m-%d"),
            data_source=stock_data.get("data_source", "unknown"),
        )
    
    def build_pool(
        self,
        stocks_data: List[Dict[str, Any]],
        min_score: Optional[float] = None,
        min_pass_rate: Optional[float] = None,
    ) -> List[StockEntryMatrix]:
        """构建股票池"""
        min_score = min_score or self.min_score
        min_pass_rate = min_pass_rate or self.min_pass_rate
        
        results: List[StockEntryMatrix] = []
        
        for stock_data in stocks_data:
            matrix = self.evaluate_stock(stock_data)
            
            pass_rate = matrix.passed_factors / matrix.total_factors if matrix.total_factors > 0 else 0
            
            if matrix.weighted_score >= min_score and pass_rate >= min_pass_rate:
                results.append(matrix)
        
        results.sort(key=lambda x: x.weighted_score, reverse=True)
        
        return results
    
    def get_entry_reason_summary(self, matrix: StockEntryMatrix) -> Dict[str, Any]:
        """获取入池理由摘要"""
        category_scores: Dict[str, List[EntryReason]] = {}
        
        for reason in matrix.entry_reasons:
            cat = reason.category.value
            if cat not in category_scores:
                category_scores[cat] = []
            category_scores[cat].append(reason)
        
        summary = {}
        for cat, reasons in category_scores.items():
            passed = sum(1 for r in reasons if r.passed)
            total = len(reasons)
            avg_score = sum(r.score for r in reasons) / total if total > 0 else 0
            
            summary[cat] = {
                "passed": passed,
                "total": total,
                "pass_rate": round(passed / total * 100, 1) if total > 0 else 0,
                "avg_score": round(avg_score, 1),
                "factors": [
                    {
                        "name": r.factor_name,
                        "passed": r.passed,
                        "value": r.value,
                        "threshold": r.threshold,
                    }
                    for r in reasons
                ],
            }
        
        return summary


stock_pool_builder = StockPoolBuilder()


__all__ = [
    "FactorCategory",
    "FilterCondition",
    "EntryReason",
    "StockEntryMatrix",
    "StockPoolBuilder",
    "stock_pool_builder",
]
