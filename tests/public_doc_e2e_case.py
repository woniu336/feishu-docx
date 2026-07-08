from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class FeaturePoint:
    name: str
    markdown_contains_snapshot: str | None = None
    pdf_text_contains_snapshot: str | None = None
    pdf_image_snapshot: str | None = None
    markdown_forbid: tuple[str, ...] = ()
    pdf_forbid: tuple[str, ...] = ()


# Provenance-only source doc. The canonical regression target is the Spencer-owned
# personal-Drive copy below.
SOURCE_DOC_REF = "https://www.feishu.cn/docx/IkCedJjFIoypyzxwXjacRSy9nBg"
CANONICAL_DOC_REF = "https://www.feishu.cn/docx/RlZrd8hDoo4hGWxFHYjcCHwgnXb"
DOC_REF = os.environ.get("FEISHU_DOCX_PUBLIC_DOC_E2E_REF") or CANONICAL_DOC_REF

LOCAL_SKIP_ENV = "FEISHU_DOCX_ALLOW_LOCAL_PUBLIC_DOC_SKIP"
FILE_STEM = "public-doc-e2e"
MIN_PDF_TOTAL_IMAGES = 2

# Fixture governance: Spencer owns the current canonical copy and the containing
# personal-drive folder. Future fixture replacement should update this module and
# the pinned snapshots in the same change.
FIXTURE_MAINTAINER = "spencer-cai"
FIXTURE_FOLDER_NAME = "feishu-docx-public-fixtures"
FIXTURE_FOLDER_TOKEN = "MVVpfLzYKlPLvfdMOP2chBM6nIe"
FIXTURE_FOLDER_URL = "https://dynamia-ai.feishu.cn/drive/folder/MVVpfLzYKlPLvfdMOP2chBM6nIe"
FIXTURE_REPLACEMENT_RULES = (
    "Keep the synced_block, markdown_table, markdown_blockquote, callout, whiteboard, and image signals equivalent.",
    "Refresh snapshots only after confirming the replacement doc preserves those feature points.",
    "Update CANONICAL_DOC_REF together with any snapshot refresh in the same reviewable change.",
)

FEATURE_POINTS: tuple[FeaturePoint, ...] = (
    FeaturePoint(
        name="synced_block",
        markdown_contains_snapshot="markdown/synced_block.md",
        pdf_text_contains_snapshot="pdf/synced_block.txt",
        markdown_forbid=("<synced_reference", "<synced-source"),
        pdf_forbid=("不支持导出查看",),
    ),
    FeaturePoint(
        name="markdown_table",
        markdown_contains_snapshot="markdown/table.md",
        pdf_text_contains_snapshot="pdf/table.txt",
    ),
    FeaturePoint(
        name="markdown_blockquote",
        markdown_contains_snapshot="markdown/blockquote.md",
        pdf_text_contains_snapshot="pdf/blockquote.txt",
    ),
    FeaturePoint(
        name="callout",
        markdown_contains_snapshot="markdown/callout.md",
        pdf_text_contains_snapshot="pdf/callout.txt",
        markdown_forbid=("<callout",),
    ),
    FeaturePoint(
        name="whiteboard",
        pdf_image_snapshot="pdf/whiteboard_image.json",
        markdown_forbid=("<!-- 画板 ",),
    ),
    FeaturePoint(
        name="image",
        pdf_image_snapshot="pdf/image_image.json",
        markdown_forbid=("authcode/?code=", "![图片下载失败（无权限）]"),
        pdf_forbid=("加载失败",),
    ),
)
