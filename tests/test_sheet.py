# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：test_sheet.py
# @Date   ：2026/04/08 14:09
# @Author ：leemysw
# 2026/04/08 14:09   Create
# =====================================================

import json

from feishu_docx.core.exporter import FeishuExporter, NodeInfo
from feishu_docx.core.sdk import FeishuSDK
from feishu_docx.schema.models import SheetValueMode, TableMode


class _FakeRawResponse:
    """模拟飞书原始响应体"""

    def __init__(self, payload: dict):
        self.content = json.dumps(payload, ensure_ascii=False).encode("utf-8")


class _FakeResponse:
    """模拟飞书响应对象"""

    def __init__(self, payload: dict):
        self.code = 0
        self.msg = "ok"
        self.raw = _FakeRawResponse(payload)

    @staticmethod
    def success() -> bool:
        return True


def test_get_sheet_uses_formatted_value_rendering(monkeypatch):
    """默认导出表格展示值，避免把公式文本写入 Markdown"""
    sdk = FeishuSDK(token_type="tenant")
    captured = {}

    def fake_request(request, option):  # noqa: ARG001
        captured["queries"] = request.queries
        payload = {
            "data": {
                "valueRange": {
                    "values": [
                        ["部门", "累计", "完成比例"],
                        ["A 部门", 667, "83.38%"],
                    ]
                }
            }
        }
        return _FakeResponse(payload)

    monkeypatch.setattr(sdk.client, "request", fake_request)

    result = sdk.sheet.get_sheet(
        sheet_token="spreadsheet_token",
        sheet_id="sheet_id",
        access_token="token",
        table_mode=TableMode.MARKDOWN,
    )

    assert ("valueRenderOption", "FormattedValue") in captured["queries"]
    assert ("dateTimeRenderOption", "FormattedString") in captured["queries"]
    assert "SUM(" not in result
    assert "83.38%" in result


def test_get_sheet_can_export_formula(monkeypatch):
    """显式指定 formula 时，应返回公式文本。"""
    sdk = FeishuSDK(token_type="tenant")
    captured = {}

    def fake_request(request, option):  # noqa: ARG001
        captured["queries"] = request.queries
        payload = {
            "data": {
                "valueRange": {
                    "values": [
                        ["部门", "累计"],
                        ["A 部门", "=SUM(G5:R5)"],
                    ]
                }
            }
        }
        return _FakeResponse(payload)

    monkeypatch.setattr(sdk.client, "request", fake_request)

    result = sdk.sheet.get_sheet(
        sheet_token="spreadsheet_token",
        sheet_id="sheet_id",
        access_token="token",
        table_mode=TableMode.MARKDOWN,
        value_mode=SheetValueMode.FORMULA,
    )

    assert ("valueRenderOption", "Formula") in captured["queries"]
    assert "=SUM(G5:R5)" in result


def test_export_content_passes_sheet_value_mode(monkeypatch):
    """导出器应把 sheet_value_mode 传递到解析层。"""
    exporter = FeishuExporter.from_token("token")
    captured = {}

    def fake_parse_url(url):  # noqa: ARG001
        return NodeInfo(node_type="sheet", node_token="sheet_token")

    class _FakeSheetParser:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        @staticmethod
        def parse():
            return "ok"

    monkeypatch.setattr(exporter, "parse_url", fake_parse_url)
    monkeypatch.setattr(exporter, "get_access_token", lambda: "token")
    monkeypatch.setattr("feishu_docx.core.exporter.SheetParser", _FakeSheetParser)

    result = exporter.export_content(
        "https://my.feishu.cn/sheets/sheet_token",
        table_format="md",
        sheet_value_mode="formula",
    )

    assert result == "ok"
    assert captured["sheet_value_mode"] == "formula"
