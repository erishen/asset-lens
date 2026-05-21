"""
AI Analysis module for asset-lens.
AI 分析模块 - 使用 LiteLLM 支持多种 AI 后端
"""

import hashlib
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class AIAnalysisResult:
    """AI 分析结果"""

    summary: str
    risk_assessment: str
    suggestions: list[str]
    warnings: list[str]
    score: int
    raw_analysis: str | None = None


class AIAnalyzer:
    """AI 分析器 - 使用 LiteLLM 支持多种 AI 后端"""

    SUPPORTED_MODELS: ClassVar[dict[str, str]] = {
        "deepseek": "deepseek/deepseek-chat",
        "deepseek-reasoner": "deepseek/deepseek-reasoner",
        "qwen": "qwen/qwen-turbo",
        "qwen-plus": "qwen/qwen-plus",
        "qwen-max": "qwen/qwen-max",
        "gpt-4": "gpt-4",
        "gpt-4-turbo": "gpt-4-turbo-preview",
        "gpt-3.5-turbo": "gpt-3.5-turbo",
        "claude-3": "claude-3-opus-20240229",
        "claude-3-sonnet": "claude-3-sonnet-20240229",
        "claude-3-haiku": "claude-3-haiku-20240307",
        "ollama-llama3": "ollama/llama3",
        "ollama-qwen": "ollama/qwen2",
    }

    def __init__(self, use_cache: bool = True, cache_ttl: int = 3600):
        """
        初始化 AI 分析器

        Args:
            use_cache: 是否使用缓存
            cache_ttl: 缓存有效期（秒）
        """
        self.api_key = (
            os.getenv("OPENAI_API_KEY")
            or os.getenv("DEEPSEEK_API_KEY")
            or os.getenv("DASHSCOPE_API_KEY")
            or os.getenv("ANTHROPIC_API_KEY")
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("AZURE_API_KEY")
        )
        self.model = os.getenv("AI_MODEL", "deepseek/deepseek-chat")

        if self.model in self.SUPPORTED_MODELS:
            self.model = self.SUPPORTED_MODELS[self.model]

        if not self.model.startswith("deepseek/") and "deepseek" in self.model:
            self.model = f"deepseek/{self.model}"

        self.use_cache = use_cache
        self.cache_ttl = cache_ttl
        self.cache_dir = Path(__file__).parent.parent.parent / ".cache" / "ai"

        if self.use_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._client: Any = None

        self.risk_keywords = {
            "高风险": ["股票", "创业板", "科创板", "芯片", "新能源", "科技"],
            "中风险": ["混合", "债券", "可转债", "指数"],
            "低风险": ["货币", "理财", "存款", "国债", "货币基金"],
        }

    @property
    def client(self):
        """延迟初始化 LiteLLM"""
        if self._client is None:
            try:
                import litellm

                litellm.set_verbose = False
                self._client = litellm
            except ImportError:
                pass
        return self._client

    def analyze_portfolio(self, portfolio_data: dict[str, Any]) -> AIAnalysisResult:
        """
        分析投资组合

        Args:
            portfolio_data: 投资组合数据

        Returns:
            AI 分析结果
        """
        if self.client and self.api_key:
            return self._ai_analyze(portfolio_data)
        else:
            return self._rule_based_analyze(portfolio_data)

    def _ai_analyze(self, portfolio_data: dict[str, Any]) -> AIAnalysisResult:
        """使用 AI 进行深度分析"""
        cache_key = self._generate_cache_key(portfolio_data, "portfolio_analysis")

        if self.use_cache:
            cached = self._get_cache(cache_key)
            if cached:
                return cached

        prompt = self._build_analysis_prompt(portfolio_data)

        try:
            response = self.client.completion(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一位专业的投资顾问，擅长分析投资组合的风险和收益。请基于提供的投资数据，给出专业的投资建议和风险评估。",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=2000,
            )

            ai_analysis = response.choices[0].message.content
            result = self._parse_ai_response(ai_analysis, portfolio_data)

            if self.use_cache:
                self._save_cache(cache_key, result)

            return result

        except Exception as e:
            logger.error(f"AI 分析失败: {e}", exc_info=True)
            return self._rule_based_analyze(portfolio_data)

    def _rule_based_analyze(self, portfolio_data: dict[str, Any]) -> AIAnalysisResult:
        """基于规则的分析（无 AI 时使用）"""
        summary = self._generate_summary(portfolio_data)
        risk_assessment = self._assess_risk(portfolio_data)
        suggestions = self._generate_suggestions(portfolio_data)
        warnings = self._generate_warnings(portfolio_data)
        score = self._calculate_score(portfolio_data)

        return AIAnalysisResult(
            summary=summary,
            risk_assessment=risk_assessment,
            suggestions=suggestions,
            warnings=warnings,
            score=score,
        )

    def _build_analysis_prompt(self, data: dict[str, Any]) -> str:
        """构建 AI 分析提示词"""
        total_value = data.get("total_value", 0)
        total_profit = data.get("total_profit", 0)
        overall_return = data.get("overall_return_rate", 0)
        product_count = data.get("total_products", 0)

        risk_dist = data.get("risk_distribution", {})
        type_dist = data.get("type_distribution", {})

        prompt = f"""
## 投资组合概览

- 总市值: {self._format_money(total_value)} 元
- 累计收益: {self._format_money(total_profit)} 元
- 整体收益率: {overall_return}%
- 产品数量: {product_count} 个

## 风险分布

"""
        for risk_name, stats in risk_dist.items():
            ratio = float(stats.get("percentage", 0))
            prompt += f"- {risk_name}风险: {ratio:.1f}%\n"

        prompt += "\n## 投资类型分布\n\n"
        for type_name, stats in type_dist.items():
            ratio = float(stats.get("percentage", 0))
            prompt += f"- {type_name}: {ratio:.1f}%\n"

        low_returns = data.get("low_returns", [])
        if low_returns:
            prompt += f"\n## 低收益产品（收益率 < 2%）\n\n发现 {len(low_returns)} 个低收益产品：\n"
            for p in low_returns[:5]:
                prompt += f"- {p.get('name', '未知')}: 年化 {p.get('annual_return', '-')}\n"

        prompt += """

## 分析要求

请基于以上投资数据，提供以下分析：

1. **投资摘要**（2-3句话概括投资组合整体情况）
2. **风险评估**（分析当前资产配置的风险水平）
3. **投资建议**（3-5条具体的投资优化建议）
4. **风险警告**（需要关注的风险点）
5. **综合评分**（0-100分，评估投资组合质量）

请以 JSON 格式返回结果：
```json
{
  "summary": "投资摘要...",
  "risk_assessment": "风险评估...",
  "suggestions": ["建议1", "建议2", "建议3"],
  "warnings": ["警告1", "警告2"],
  "score": 75
}
```
"""
        return prompt

    def _parse_ai_response(self, ai_response: str, data: dict[str, Any]) -> AIAnalysisResult:
        """解析 AI 响应"""
        try:
            json_start = ai_response.find("{")
            json_end = ai_response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = ai_response[json_start:json_end]
                result = json.loads(json_str)

                return AIAnalysisResult(
                    summary=result.get("summary", ""),
                    risk_assessment=result.get("risk_assessment", ""),
                    suggestions=result.get("suggestions", []),
                    warnings=result.get("warnings", []),
                    score=result.get("score", 60),
                    raw_analysis=ai_response,
                )
        except (json.JSONDecodeError, ValueError):
            pass

        return self._rule_based_analyze(data)

    def _generate_summary(self, data: dict[str, Any]) -> str:
        """生成投资摘要"""
        total_value = data.get("total_value", 0)
        total_profit = data.get("total_profit", 0)
        overall_return = data.get("overall_return_rate", 0)
        product_count = data.get("total_products", 0)

        profit_status = "盈利" if float(total_profit) > 0 else "亏损"

        return (
            f"您的投资组合共有 {product_count} 个产品，"
            f"总市值 {self._format_money(total_value)} 元，"
            f"累计{profit_status} {self._format_money(abs(float(total_profit)))} 元，"
            f"整体收益率 {overall_return}%。"
        )

    def _assess_risk(self, data: dict[str, Any]) -> str:
        """评估风险"""
        risk_dist = data.get("risk_distribution", {})
        total_value = float(data.get("total_value", 1))

        high_risk_ratio = 0.0
        low_risk_ratio = 0.0

        for risk_name, stats in risk_dist.items():
            ratio = float(stats.get("total_value", 0)) / total_value if total_value > 0 else 0
            if risk_name == "高":
                high_risk_ratio = ratio
            elif risk_name == "中":
                pass
            elif risk_name == "低":
                low_risk_ratio = ratio

        if high_risk_ratio > 0.5:
            return f"您的投资组合风险较高，高风险产品占比 {high_risk_ratio * 100:.1f}%，建议适当降低高风险产品比例。"
        elif high_risk_ratio > 0.3:
            return f"您的投资组合风险适中，高风险产品占比 {high_risk_ratio * 100:.1f}%，整体配置较为合理。"
        else:
            return f"您的投资组合风险较低，低风险产品占比 {low_risk_ratio * 100:.1f}%，适合稳健型投资者。"

    def _generate_suggestions(self, data: dict[str, Any]) -> list[str]:
        """生成投资建议"""
        suggestions = []

        low_returns = data.get("low_returns", [])
        if len(low_returns) > 5:
            suggestions.append(f"发现 {len(low_returns)} 个低收益产品，建议考虑调整或赎回。")

        loss_products = [p for p in data.get("products", []) if float(p.get("profit_amount", 0)) < 0]
        if loss_products:
            suggestions.append(f"发现 {len(loss_products)} 个亏损产品，建议评估是否继续持有。")

        type_dist = data.get("type_distribution", {})
        if type_dist:
            max_type = max(type_dist.items(), key=lambda x: float(x[1].get("total_value", 0)))
            max_ratio = float(max_type[1].get("total_value", 0)) / float(data.get("total_value", 1)) * 100
            if max_ratio > 50:
                suggestions.append(f"{max_type[0]} 类产品占比 {max_ratio:.1f}%，建议分散投资降低风险。")

        short_term = [p for p in data.get("products", []) if p.get("investment_days", 0) < 90]
        if len(short_term) > 5:
            suggestions.append(f"有 {len(short_term)} 个短期投资产品（<90天），短期波动属正常现象。")

        if not suggestions:
            suggestions.append("您的投资组合整体表现良好，继续保持当前投资策略。")

        return suggestions

    def _generate_warnings(self, data: dict[str, Any]) -> list[str]:
        """生成风险警告"""
        warnings = []

        severe_loss = [p for p in data.get("products", []) if float(p.get("return_rate", 0)) < -5]
        if severe_loss:
            warnings.append(f"⚠️ 发现 {len(severe_loss)} 个严重亏损产品（收益率<-5%），请关注市场动态。")

        risk_dist = data.get("risk_distribution", {})
        high_risk_value = float(risk_dist.get("高", {}).get("total_value", 0))
        total_value = float(data.get("total_value", 1))
        if high_risk_value / total_value > 0.6:
            warnings.append("⚠️ 高风险产品占比过高，建议适当配置低风险产品。")

        products = data.get("products", [])
        if products:
            max_product = max(products, key=lambda x: float(x.get("current_amount", 0)))
            max_ratio = float(max_product.get("current_amount", 0)) / total_value * 100
            if max_ratio > 30:
                warnings.append(f"⚠️ 单一产品 {max_product.get('name')} 占比 {max_ratio:.1f}%，建议分散投资。")

        return warnings

    def _calculate_score(self, data: dict[str, Any]) -> int:
        """计算综合评分"""
        score = 60

        return_rate = float(data.get("overall_return_rate", 0))
        if return_rate > 10:
            score += 20
        elif return_rate > 5:
            score += 15
        elif return_rate > 2:
            score += 10
        elif return_rate > 0:
            score += 5
        else:
            score -= 10

        risk_dist = data.get("risk_distribution", {})
        if len(risk_dist) >= 3:
            score += 10

        product_count = data.get("total_products", 0)
        if 10 <= product_count <= 30:
            score += 10
        elif product_count > 30:
            score -= 5

        return max(0, min(100, score))

    def _format_money(self, value: Any) -> str:
        """格式化金额"""
        try:
            amount = float(value)
            if amount >= 10000:
                return f"{amount / 10000:.2f}万"
            return f"{amount:.2f}"
        except (ValueError, TypeError):
            return "0.00"

    def _generate_cache_key(self, data: dict[str, Any], prefix: str) -> str:
        """生成缓存键"""
        key_data = json.dumps(
            {
                "total_value": str(data.get("total_value", 0)),
                "total_profit": str(data.get("total_profit", 0)),
                "product_count": data.get("total_products", 0),
            },
            sort_keys=True,
        )
        return f"{prefix}_{hashlib.md5(key_data.encode()).hexdigest()}"

    def _get_cache(self, key: str) -> AIAnalysisResult | None:
        """获取缓存"""
        if not self.use_cache:
            return None

        cache_file = self.cache_dir / f"{key}.json"
        if not cache_file.exists():
            return None

        try:
            with open(cache_file, encoding="utf-8") as f:
                cached = json.load(f)

            cache_time = datetime.fromisoformat(cached.get("timestamp", "2000-01-01"))
            if (datetime.now() - cache_time).total_seconds() > self.cache_ttl:
                return None

            data = cached.get("data", {})
            return AIAnalysisResult(
                summary=data.get("summary", ""),
                risk_assessment=data.get("risk_assessment", ""),
                suggestions=data.get("suggestions", []),
                warnings=data.get("warnings", []),
                score=data.get("score", 0),
                raw_analysis=data.get("raw_analysis"),
            )
        except (json.JSONDecodeError, ValueError):
            return None

    def _save_cache(self, key: str, data: AIAnalysisResult) -> None:
        """保存缓存"""
        if not self.use_cache:
            return

        cache_file = self.cache_dir / f"{key}.json"
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "data": {
                            "summary": data.summary,
                            "risk_assessment": data.risk_assessment,
                            "suggestions": data.suggestions,
                            "warnings": data.warnings,
                            "score": data.score,
                            "raw_analysis": data.raw_analysis,
                        },
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception as e:
            logger.debug(f"忽略异常: {e}")

    def generate_investment_advice(
        self,
        portfolio_data: dict[str, Any],
        risk_preference: str = "balanced",
    ) -> dict[str, Any]:
        """生成投资建议"""
        analysis = self.analyze_portfolio(portfolio_data)

        return {
            "summary": analysis.summary,
            "risk_assessment": analysis.risk_assessment,
            "score": analysis.score,
            "score_level": self._get_score_level(analysis.score),
            "suggestions": analysis.suggestions,
            "warnings": analysis.warnings,
            "risk_preference": risk_preference,
            "recommended_allocation": self._get_recommended_allocation(risk_preference),
            "ai_enabled": self.client is not None,
            "model": self.model,
        }

    def _get_score_level(self, score: int) -> str:
        """获取评分等级"""
        if score >= 80:
            return "优秀"
        elif score >= 60:
            return "良好"
        elif score >= 40:
            return "一般"
        else:
            return "需改进"

    def _get_recommended_allocation(self, risk_preference: str) -> dict[str, int]:
        """获取推荐资产配置"""
        allocations = {
            "conservative": {
                "货币基金": 30,
                "债券基金": 40,
                "混合基金": 20,
                "股票基金": 10,
            },
            "balanced": {
                "货币基金": 20,
                "债券基金": 30,
                "混合基金": 30,
                "股票基金": 20,
            },
            "aggressive": {
                "货币基金": 10,
                "债券基金": 20,
                "混合基金": 30,
                "股票基金": 40,
            },
        }
        return allocations.get(risk_preference, allocations["balanced"])


ai_analyzer = AIAnalyzer()
