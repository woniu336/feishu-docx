# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：test_wiki.py
# @Date   ：2026/04/11 15:01
# @Author ：leemysw
# 2026/04/11 15:01   Create
# =====================================================

from pathlib import Path
from types import SimpleNamespace

from feishu_docx.core.exporter import FeishuExporter, NodeInfo
from feishu_docx.core.sdk.base import SDKCore
from feishu_docx.core.sdk.wiki import WikiAPI


def test_get_all_space_nodes_handles_none_items(monkeypatch):
    """空目录分页结果中的 items 为 None 时，应返回空列表。"""
    wiki_api = WikiAPI(SDKCore(token_type="tenant"))

    def fake_get_space_nodes(self, space_id, access_token, parent_node_token=None, page_size=50, page_token=None):  # noqa: ARG001
        return SimpleNamespace(items=None, has_more=False, page_token="")

    monkeypatch.setattr(WikiAPI, "get_space_nodes", fake_get_space_nodes)

    result = wiki_api.get_all_space_nodes(
        space_id="space_id",
        access_token="token",
        parent_node_token="node_token",
    )

    assert result == []


def test_export_wiki_space_root_url_falls_back_to_space_root(tmp_path, monkeypatch):
    """知识空间首页 URL 不应被错误地当成 parent_node_token 过滤条件。"""
    exporter = FeishuExporter.from_token("token")
    captured = {}

    root_node = SimpleNamespace(
        space_id="space_id",
        title="空间首页",
        node_token="root_token",
        has_child=False,
        parent_node_token="",
        obj_type="docx",
        obj_token="doc_token",
    )

    monkeypatch.setattr(exporter, "parse_url", lambda url: NodeInfo(node_type="wiki", node_token="root_token"))
    monkeypatch.setattr(exporter, "_set_document_domain_from_url", lambda url: None)
    monkeypatch.setattr(exporter, "get_access_token", lambda: "token")
    monkeypatch.setattr(
        exporter.sdk.wiki,
        "get_node_by_token",
        lambda token, access_token: root_node,
    )
    monkeypatch.setattr(
        exporter.sdk.wiki,
        "get_space_info",
        lambda space_id, access_token: SimpleNamespace(name="测试空间"),
    )

    def fake_get_all_space_nodes(space_id, access_token, parent_node_token=None):
        captured["space_id"] = space_id
        captured["parent_node_token"] = parent_node_token
        return []

    monkeypatch.setattr(exporter.sdk.wiki, "get_all_space_nodes", fake_get_all_space_nodes)

    result = exporter.export_wiki_space(
        "https://example.feishu.cn/wiki/root_token",
        output_dir=Path(tmp_path),
        silent=True,
    )

    assert captured["space_id"] == "space_id"
    assert captured["parent_node_token"] is None
    assert result["exported"] == 0
    assert result["failed"] == 0


def test_export_wiki_space_reuses_input_host_for_child_urls(tmp_path, monkeypatch):
    """批量导出应复用输入 Wiki URL 的 host 来拼接子文档链接。"""
    exporter = FeishuExporter.from_token("token")
    captured = {}

    root_node = SimpleNamespace(
        space_id="space_id",
        title="空间首页",
        node_token="root_token",
        has_child=False,
        parent_node_token="",
        obj_type="docx",
        obj_token="doc_token",
    )
    child_node = SimpleNamespace(
        node_token="child_node",
        obj_type="docx",
        obj_token="child_docx",
        title="子文档",
        has_child=False,
    )

    monkeypatch.setattr(exporter, "parse_url", lambda url: NodeInfo(node_type="wiki", node_token="root_token"))
    monkeypatch.setattr(exporter, "_set_document_domain_from_url", lambda url: None)
    monkeypatch.setattr(exporter, "get_access_token", lambda: "token")
    monkeypatch.setattr(exporter.sdk.wiki, "get_node_by_token", lambda token, access_token: root_node)
    monkeypatch.setattr(
        exporter.sdk.wiki,
        "get_space_info",
        lambda space_id, access_token: SimpleNamespace(name="测试空间"),
    )
    monkeypatch.setattr(
        exporter.sdk.wiki,
        "get_all_space_nodes",
        lambda space_id, access_token, parent_node_token=None: [child_node],
    )

    def fake_export(url, output_dir=".", filename=None, **kwargs):  # noqa: ARG001
        captured["url"] = url
        return Path(output_dir) / f"{filename}.md"

    monkeypatch.setattr(exporter, "export", fake_export)

    result = exporter.export_wiki_space(
        "https://wuxiang-media-center.feishu.cn/wiki/root_token",
        output_dir=Path(tmp_path),
        silent=True,
        max_depth=0,
    )

    assert captured["url"] == "https://wuxiang-media-center.feishu.cn/docx/child_docx"
    assert result["exported"] == 1
    assert result["failed"] == 0
