"""
Prompt Builder - AI Prompt 构建器

负责构建 AI 分析所需的 Prompt。
"""

from typing import Any


class PromptBuilder:
    """Prompt 构建器 - 构建 AI 分析所需的 Prompt"""

    @staticmethod
    def build_portfolio_analysis_prompt(data: dict[str, Any]) -> str:
        """
        构建投资组合分析 Prompt

        Args:
            data: 投资组合数据

        Returns:
            构建好的 Prompt 字符串
        """
        total_value = data.get("total_value", 0)
        total_profit = data.get("total_profit", 0)
        overall_return = data.get("overall_return_rate", 0)
        product_count = data.get("total_products", 0)

        risk_dist = data.get("risk_distribution", {})
        type_dist = data.get("type_distribution", {})

        prompt = f"""
## 投资组合概览

- 总市值: {PromptBuilder._format_money(total_value)} 元
- 累计收益: {PromptBuilder._format_money(total_profit)} 元
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

    @staticmethod
    def build_risk_assessment_prompt(data: dict[str, Any]) -> str:
        """
        构建风险评估 Prompt

        Args:
            data: 投资组合数据

        Returns:
            构建好的 Prompt 字符串
        """
        risk_dist = data.get("risk_distribution", {})
        total_value = float(data.get("total_value", 1))

        prompt = "## 风险分布分析\n\n"

        for risk_name, stats in risk_dist.items():
            value = float(stats.get("total_value", 0))
            ratio = value / total_value * 100 if total_value > 0 else 0
            prompt += f"- {risk_name}风险: {ratio:.1f}% ({value:,.0f} 元)\n"

        prompt += "\n请分析当前风险配置是否合理，并给出调整建议。"
        return prompt

    @staticmethod
    def build_suggestion_prompt(
        data: dict[str, Any],
        risk_preference: str = "balanced",
    ) -> str:
        """
        构建投资建议 Prompt

        Args:
            data: 投资组合数据
            risk_preference: 风险偏好

        Returns:
            构建好的 Prompt 字符串
        """
        prompt = f"""
## 投资组合数据

- 总市值: {PromptBuilder._format_money(data.get("total_value", 0))} 元
- 累计收益: {PromptBuilder._format_money(data.get("total_profit", 0))} 元
- 整体收益率: {data.get("overall_return_rate", 0)}%
- 风险偏好: {risk_preference}

## 请提供以下建议

1. 资产配置优化建议
2. 风险控制建议
3. 产品调整建议
4. 投资时机建议

请以 JSON 格式返回：
```json
{{
  "allocation_suggestions": ["建议1", "建议2"],
  "risk_suggestions": ["建议1", "建议2"],
  "product_suggestions": ["建议1", "建议2"],
  "timing_suggestions": ["建议1", "建议2"]
}}
```
"""
        return prompt

    @staticmethod
    def _format_money(value: Any) -> str:
        """格式化金额"""
        try:
            amount = float(value)
            if amount >= 10000:
                return f"{amount / 10000:.2f}万"
            return f"{amount:.2f}"
        except (ValueError, TypeError):
            return "0.00"

    @staticmethod
    def get_system_prompt() -> str:
        """获取系统 Prompt"""
        return (
            "你是一位专业的投资顾问，擅长分析投资组合的风险和收益。请基于提供的投资数据，给出专业的投资建议和风险评估。"
        )
