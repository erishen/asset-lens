"""
Result Parser - AI 结果解析器

负责解析 AI 返回的结果。
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ParsedResult:
    """解析后的结果"""

    success: bool
    summary: str = ""
    risk_assessment: str = ""
    suggestions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    score: int = 60
    raw_content: str | None = None


class ResultParser:
    """结果解析器 - 解析 AI 返回的结果"""

    @staticmethod
    def parse_json_response(response: str) -> ParsedResult:
        """
        解析 JSON 格式的 AI 响应

        Args:
            response: AI 返回的响应字符串

        Returns:
            解析后的结果
        """
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                result = json.loads(json_str)

                return ParsedResult(
                    success=True,
                    summary=result.get("summary", ""),
                    risk_assessment=result.get("risk_assessment", ""),
                    suggestions=result.get("suggestions", []),
                    warnings=result.get("warnings", []),
                    score=result.get("score", 60),
                    raw_content=response,
                )
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"JSON 解析失败: {e}")

        return ParsedResult(success=False, raw_content=response)

    @staticmethod
    def parse_markdown_response(response: str) -> ParsedResult:
        """
        解析 Markdown 格式的 AI 响应

        Args:
            response: AI 返回的响应字符串

        Returns:
            解析后的结果
        """
        summary = ResultParser._extract_section(response, "摘要", "风险")
        risk_assessment = ResultParser._extract_section(response, "风险", "建议")
        suggestions = ResultParser._extract_list(response, "建议")
        warnings = ResultParser._extract_list(response, "警告")
        score = ResultParser._extract_score(response)

        return ParsedResult(
            success=True,
            summary=summary,
            risk_assessment=risk_assessment,
            suggestions=suggestions,
            warnings=warnings,
            score=score,
            raw_content=response,
        )

    @staticmethod
    def _extract_section(text: str, start_keyword: str, end_keyword: str) -> str:
        """提取文本段落"""
        try:
            start_idx = text.find(start_keyword)
            if start_idx == -1:
                return ""

            start_idx = text.find("\n", start_idx)
            if start_idx == -1:
                return ""

            end_idx = text.find(end_keyword, start_idx)
            if end_idx == -1:
                end_idx = len(text)

            return text[start_idx:end_idx].strip()
        except Exception as e:
            logger.debug(f"忽略异常: {e}")
            return ""

    @staticmethod
    def _extract_list(text: str, keyword: str) -> list[str]:
        """提取列表项"""
        items: list[str] = []
        try:
            start_idx = text.find(keyword)
            if start_idx == -1:
                return items

            section = text[start_idx : start_idx + 500]
            lines = section.split("\n")

            for line in lines[1:]:
                line = line.strip()
                if line.startswith("-") or line.startswith("*") or line.startswith("•"):
                    item = line.lstrip("-*• ").strip()
                    if item:
                        items.append(item)
                elif line and not line.startswith("#"):
                    break
        except Exception as e:
            logger.debug(f"忽略异常: {e}")

        return items

    @staticmethod
    def _extract_score(text: str) -> int:
        """提取评分"""
        import re

        patterns = [
            r"评分[：:]\s*(\d+)",
            r"综合评分[：:]\s*(\d+)",
            r"得分[：:]\s*(\d+)",
            r"score[：:]\s*(\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                score = int(match.group(1))
                return max(0, min(100, score))

        return 60

    @staticmethod
    def to_dict(result: ParsedResult) -> dict[str, Any]:
        """将解析结果转换为字典"""
        return {
            "success": result.success,
            "summary": result.summary,
            "risk_assessment": result.risk_assessment,
            "suggestions": result.suggestions,
            "warnings": result.warnings,
            "score": result.score,
        }
