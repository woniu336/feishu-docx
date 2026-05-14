# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：render_table
# @Date   ：2026/1/10 22:06
# @Author ：leemysw
#
# 2026/1/10 22:06   Create
# =====================================================

import json
from html import escape
from typing import Any


def _segment_text(segment: dict, markdown: bool) -> str:
    """渲染飞书表格富文本片段。"""
    text = (
        segment.get("text")
        or segment.get("name")
        or segment.get("en_name")
        or segment.get("content")
        or segment.get("url")
        or ""
    )
    if not text:
        return ""

    if markdown and segment.get("segmentStyle", {}).get("bold"):
        return f"**{text}**"
    if not markdown and segment.get("segmentStyle", {}).get("bold"):
        return f"<strong>{escape(str(text))}</strong>"
    return str(text)


def _format_cell_value(cell: Any, markdown: bool = True) -> str:
    """将 Sheet / Bitable 单元格值归一化为可读文本。"""
    if cell is None:
        return ""

    if isinstance(cell, list):
        if all(isinstance(item, dict) and "type" in item for item in cell):
            return "".join(_segment_text(item, markdown) for item in cell)
        return ", ".join(_format_cell_value(item, markdown) for item in cell)

    if isinstance(cell, dict):
        text = _segment_text(cell, markdown)
        if text:
            return text
        return json.dumps(cell, ensure_ascii=False)

    return str(cell)


def render_table_html(grid_data, row_count: int, col_count: int) -> str:
    """渲染 HTML 表格"""
    html = ["<table>"]
    for r in range(row_count):
        html.append("  <tr>")
        for c in range(col_count):
            data = grid_data[r][c]
            if data:
                content, r_span, c_span = data
                attrs = ""
                if r_span > 1:
                    attrs += f' rowspan="{r_span}"'
                if c_span > 1:
                    attrs += f' colspan="{c_span}"'
                html.append(f"    <td{attrs}>{content}</td>")
        html.append("  </tr>")
    html.append("</table>")
    return "\n".join(html)


def render_table_markdown(grid_data, row_count: int, col_count: int) -> str:
    """渲染 Markdown 表格"""
    md_lines = []
    for r in range(row_count):
        row_strs = []
        for c in range(col_count):
            if grid_data[r][c]:
                content = grid_data[r][c][0]
                content = content.replace("|", "\\|").replace("\n", "<br>")
                row_strs.append(content)
            else:
                row_strs.append(" ")
        md_lines.append("| " + " | ".join(row_strs) + " |")
        if r == 0:
            md_lines.append("| " + " | ".join(["---"] * col_count) + " |")
    return "\n".join(md_lines)


# ==========================================================================
# Sheet / Bitable 格式转换
# ==========================================================================

def convert_to_markdown(values: list) -> str:
    """将二维数组转换为 Markdown 表格"""
    if not values:
        return ""

    # 补齐列数
    max_cols = max(len(row) for row in values)
    normalized_values = []
    for row in values:
        str_row = [
            _format_cell_value(cell, markdown=True).replace("\n", "<br>").replace("|", "\\|")
            for cell in row
        ]
        str_row.extend([""] * (max_cols - len(str_row)))
        normalized_values.append(str_row)

    md_lines = []
    for i, row in enumerate(normalized_values):
        line = "| " + " | ".join(row) + " |"
        md_lines.append(line)
        if i == 0:
            separator = "| " + " | ".join(["---"] * max_cols) + " |"
            md_lines.append(separator)

    return "\n".join(md_lines)


def convert_to_html(values: list) -> str:
    """将二维数组转换为 HTML 表格"""
    if not values:
        return ""

    html = ["<table>"]
    for row in values:
        html.append("  <tr>")
        for cell in row:
            cell_content = _format_cell_value(cell, markdown=False)
            cell_content = cell_content.replace("\n", "<br>")
            html.append(f"    <td>{cell_content}</td>")
        html.append("  </tr>")
    html.append("</table>")

    return "\n".join(html)
