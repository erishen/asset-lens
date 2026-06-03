import json

from asset_lens.ai.result_parser import ParsedResult, ResultParser


class TestParseJsonResponse:
    def test_valid_json(self):
        data = {
            "summary": "组合良好",
            "risk_assessment": "中等风险",
            "suggestions": ["建议1", "建议2", "建议3"],
            "warnings": ["警告1"],
            "score": 85,
        }
        response = json.dumps(data)
        result = ResultParser.parse_json_response(response)
        assert result.success is True
        assert result.summary == "组合良好"
        assert result.risk_assessment == "中等风险"
        assert len(result.suggestions) == 3
        assert len(result.warnings) == 1
        assert result.score == 85

    def test_json_embedded_in_text(self):
        response = '一些文本 {"summary": "测试", "risk_assessment": "低", "suggestions": [], "warnings": [], "score": 70} 更多文本'
        result = ResultParser.parse_json_response(response)
        assert result.success is True
        assert result.summary == "测试"
        assert result.score == 70

    def test_missing_fields_use_defaults(self):
        response = '{"summary": "只有摘要"}'
        result = ResultParser.parse_json_response(response)
        assert result.success is True
        assert result.summary == "只有摘要"
        assert result.risk_assessment == ""
        assert result.suggestions == []
        assert result.warnings == []
        assert result.score == 60

    def test_invalid_json(self):
        result = ResultParser.parse_json_response("not json at all")
        assert result.success is False
        assert result.raw_content == "not json at all"

    def test_empty_string(self):
        result = ResultParser.parse_json_response("")
        assert result.success is False

    def test_partial_json(self):
        result = ResultParser.parse_json_response("{broken json")
        assert result.success is False

    def test_raw_content_preserved(self):
        response = '{"summary": "test"}'
        result = ResultParser.parse_json_response(response)
        assert result.raw_content == response


class TestParseMarkdownResponse:
    def test_full_markdown(self):
        response = """
## 投资摘要
投资组合表现良好，整体稳健。

## 风险评估
当前风险水平适中，需关注市场波动。

## 投资建议
- 增加债券配置
- 减少高风险股票
- 关注消费板块

## 风险警告
- 市场波动加剧
- 外部不确定性增加

综合评分：82
"""
        result = ResultParser.parse_markdown_response(response)
        assert result.success is True
        assert "投资组合" in result.summary
        assert len(result.suggestions) > 0
        assert len(result.warnings) > 0
        assert result.score == 82

    def test_no_matching_sections(self):
        response = "这是一段没有关键词的文本"
        result = ResultParser.parse_markdown_response(response)
        assert result.success is True
        assert result.summary == ""
        assert result.suggestions == []
        assert result.warnings == []
        assert result.score == 60

    def test_score_patterns(self):
        assert ResultParser._extract_score("评分：95") == 95
        assert ResultParser._extract_score("综合评分：88") == 88
        assert ResultParser._extract_score("得分：70") == 70
        assert ResultParser._extract_score("score: 65") == 65
        assert ResultParser._extract_score("SCORE: 55") == 55

    def test_score_clamped_to_range(self):
        assert ResultParser._extract_score("评分：150") == 100

    def test_default_score(self):
        assert ResultParser._extract_score("没有任何评分信息") == 60


class TestExtractSection:
    def test_normal_extraction(self):
        text = "摘要\n这是摘要内容\n风险\n这是风险内容"
        result = ResultParser._extract_section(text, "摘要", "风险")
        assert "这是摘要内容" in result

    def test_start_keyword_not_found(self):
        result = ResultParser._extract_section("没有关键词", "不存在", "风险")
        assert result == ""

    def test_end_keyword_not_found(self):
        text = "摘要\n这是内容"
        result = ResultParser._extract_section(text, "摘要", "不存在")
        assert "这是内容" in result

    def test_no_newline_after_start(self):
        result = ResultParser._extract_section("摘要没有换行", "摘要", "风险")
        assert result == ""


class TestExtractList:
    def test_dash_items(self):
        text = "建议\n- 第一条\n- 第二条\n- 第三条"
        items = ResultParser._extract_list(text, "建议")
        assert len(items) == 3
        assert "第一条" in items[0]

    def test_asterisk_items(self):
        text = "建议\n* 项目A\n* 项目B"
        items = ResultParser._extract_list(text, "建议")
        assert len(items) == 2

    def test_bullet_items(self):
        text = "建议\n• 项目X\n• 项目Y"
        items = ResultParser._extract_list(text, "建议")
        assert len(items) == 2

    def test_keyword_not_found(self):
        items = ResultParser._extract_list("没有关键词", "建议")
        assert items == []

    def test_stops_at_non_heading_text(self):
        text = "建议\n- 第一条\n普通文本\n- 不应包含"
        items = ResultParser._extract_list(text, "建议")
        assert len(items) == 1


class TestToDict:
    def test_converts_all_fields(self):
        result = ParsedResult(
            success=True,
            summary="摘要",
            risk_assessment="风险",
            suggestions=["建议1"],
            warnings=["警告1"],
            score=90,
        )
        d = ResultParser.to_dict(result)
        assert d["success"] is True
        assert d["summary"] == "摘要"
        assert d["risk_assessment"] == "风险"
        assert d["suggestions"] == ["建议1"]
        assert d["warnings"] == ["警告1"]
        assert d["score"] == 90

    def test_default_values(self):
        result = ParsedResult(success=False)
        d = ResultParser.to_dict(result)
        assert d["success"] is False
        assert d["summary"] == ""
        assert d["score"] == 60
        assert d["suggestions"] == []
        assert d["warnings"] == []


class TestParsedResult:
    def test_default_values(self):
        result = ParsedResult(success=True)
        assert result.summary == ""
        assert result.risk_assessment == ""
        assert result.suggestions == []
        assert result.warnings == []
        assert result.score == 60
        assert result.raw_content is None

    def test_custom_values(self):
        result = ParsedResult(
            success=False,
            summary="test",
            score=42,
            raw_content="raw",
        )
        assert result.success is False
        assert result.summary == "test"
        assert result.score == 42
        assert result.raw_content == "raw"
