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


# The live public-doc E2E only needs one Spencer-owned personal-Drive fixture.
# A separate provenance-only source ref used to exist here, but it was not part of
# the runtime export path and only made ownership / fixture governance harder to
# reason about.
CANONICAL_DOC_REF = "https://my.feishu.cn/wiki/IYBZwoUHBizZPPkFJTichjbNnXf"
DOC_REF = os.environ.get("FEISHU_DOCX_PUBLIC_DOC_E2E_REF") or CANONICAL_DOC_REF

LOCAL_SKIP_ENV = "FEISHU_DOCX_ALLOW_LOCAL_PUBLIC_DOC_SKIP"
FILE_STEM = "public-doc-e2e"
MIN_PDF_TOTAL_IMAGES = 2

# Fixture governance: the current canonical fixture is Spencer-owned and published
# as a public wiki node that unwraps to a docx. Future fixture replacement should
# update this module and the pinned snapshots in the same change.
FIXTURE_MAINTAINER = "spencer-cai"
FIXTURE_WIKI_SPACE_ID = "7560658329514328092"
FIXTURE_WIKI_NODE_TOKEN = "IYBZwoUHBizZPPkFJTichjbNnXf"
FIXTURE_WIKI_URL = "https://my.feishu.cn/wiki/IYBZwoUHBizZPPkFJTichjbNnXf"
FIXTURE_DOCX_TOKEN = "FKb0dJYJIoL9KQxFquMczZWenrh"
FIXTURE_DOCX_URL = "https://www.feishu.cn/docx/FKb0dJYJIoL9KQxFquMczZWenrh"
FIXTURE_REPLACEMENT_RULES = (
    "Keep the synced_block, markdown_table, markdown_blockquote, callout, whiteboard, and image signals equivalent.",
    "Refresh snapshots only after confirming the replacement doc preserves those feature points.",
    "If the canonical fixture moves again, update the pinned wiki/docx governance tokens together with the snapshots.",
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
