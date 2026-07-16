from __future__ import annotations

import importlib
import json
import os
import re
from hashlib import sha256
from pathlib import Path

import public_doc_e2e_case as case
import pytest
from public_doc_e2e_case import FeaturePoint

from feishu_docx.core.exporter import FeishuExporter
from feishu_docx.utils.config import AppConfig

SNAPSHOT_ROOT = Path(__file__).with_name("e2e_snapshots") / "public_doc"
MARKDOWN_IMAGE_LINK_RE = re.compile(r"!\[[^\]]*]\(([^)]+)\)")


def build_public_doc_exporter() -> FeishuExporter:
    config = AppConfig.load()
    app_id = os.getenv("FEISHU_APP_ID") or config.app_id
    app_secret = os.getenv("FEISHU_APP_SECRET") or config.app_secret
    auth_mode = os.getenv("FEISHU_AUTH_MODE") or config.auth_mode or "tenant"
    if not app_id or not app_secret:
        raise RuntimeError("feishu-docx public doc export requires app credentials")
    return FeishuExporter(
        app_id=app_id,
        app_secret=app_secret,
        auth_mode=auth_mode,
        is_lark=config.is_lark,
    )


def normalize_pdf_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
    text = re.sub(r"[ \t]+([，。！？；：、）】》」』])", r"\1", text)
    text = re.sub(r"([（【《「『])[ \t]+", r"\1", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n+", "\n", text)
    return " ".join(part.strip() for part in text.splitlines() if part.strip())


def normalize_markdown_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
    text = re.sub(r"[ \t]+([，。！？；：、）】》」』])", r"\1", text)
    text = re.sub(r"([（【《「『])[ \t]+", r"\1", text)
    return text.strip()


def load_snapshot(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def load_json_snapshot(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_localized_image_targets(markdown_text: str) -> list[str]:
    prefix = f"{case.FILE_STEM}/"
    targets: list[str] = []
    for match in MARKDOWN_IMAGE_LINK_RE.finditer(markdown_text):
        target = match.group(1).strip()
        if target.startswith("<") and target.endswith(">"):
            target = target[1:-1].strip()
        if target.startswith(prefix):
            targets.append(target)
    return targets


def assert_feature_point(
    feature: FeaturePoint,
    markdown_text: str,
    pdf_text: str,
    pdf_images: list[dict[str, object]],
    snapshot_root: Path = SNAPSHOT_ROOT,
) -> None:
    if feature.markdown_contains_snapshot:
        expected_markdown = normalize_markdown_text(
            load_snapshot(snapshot_root / feature.markdown_contains_snapshot)
        )
        assert expected_markdown in normalize_markdown_text(markdown_text), (
            f"feature {feature.name}: markdown snapshot missing"
        )

    if feature.pdf_text_contains_snapshot:
        expected_pdf = normalize_pdf_text(
            load_snapshot(snapshot_root / feature.pdf_text_contains_snapshot)
        )
        assert expected_pdf in pdf_text, (
            f"feature {feature.name}: pdf text snapshot missing"
        )

    if feature.pdf_image_snapshot:
        expected_image = load_json_snapshot(snapshot_root / feature.pdf_image_snapshot)
        assert any(
            all(actual.get(key) == value for key, value in expected_image.items())
            for actual in pdf_images
        ), f"feature {feature.name}: pdf image snapshot missing"

    for forbidden in feature.markdown_forbid:
        assert forbidden not in markdown_text, (
            f"feature {feature.name}: forbidden marker {forbidden!r} still present in markdown"
        )

    for forbidden in feature.pdf_forbid:
        assert forbidden not in pdf_text, (
            f"feature {feature.name}: forbidden marker {forbidden!r} found in extracted pdf text"
        )


def allow_local_public_doc_skip() -> bool:
    raw = os.environ.get(case.LOCAL_SKIP_ENV, "")
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _fail_or_skip_for_missing_prereq(message: str) -> None:
    if allow_local_public_doc_skip():
        pytest.skip(message)
    pytest.fail(message)


def require_public_doc_export_prereqs_ready(doc_ref: str) -> None:
    try:
        FeishuExporter(app_id="placeholder", app_secret="placeholder").parse_url(doc_ref)
    except ValueError as exc:
        _fail_or_skip_for_missing_prereq(
            f"public doc export prerequisites missing: unsupported doc ref: {exc}"
        )

    try:
        build_public_doc_exporter()
    except RuntimeError as exc:
        _fail_or_skip_for_missing_prereq(
            f"public doc export prerequisites missing: {exc}"
        )

    for module_name, display_name in (("weasyprint", "weasyprint"), ("fitz", "PyMuPDF/fitz")):
        try:
            importlib.import_module(module_name)
        except Exception as exc:  # pragma: no cover - exercised via monkeypatch tests
            _fail_or_skip_for_missing_prereq(
                f"public doc export prerequisites missing: {display_name} import failed: {exc}"
            )


def extract_pdf_text(pdf_path: Path) -> str:
    fitz = importlib.import_module("fitz")
    document = fitz.open(pdf_path)
    try:
        return normalize_pdf_text("\n".join(page.get_text("text") for page in document))
    finally:
        document.close()


def extract_pdf_images(pdf_path: Path) -> list[dict[str, object]]:
    fitz = importlib.import_module("fitz")
    document = fitz.open(pdf_path)
    try:
        images: list[dict[str, object]] = []
        for page_no, page in enumerate(document, start=1):
            for image in page.get_images(full=True):
                meta = document.extract_image(image[0])
                payload = meta.get("image", b"")
                images.append(
                    {
                        "page": page_no,
                        "width": meta.get("width"),
                        "height": meta.get("height"),
                        "ext": meta.get("ext"),
                        "sha256": sha256(payload).hexdigest(),
                    }
                )
        return images
    finally:
        document.close()


def test_normalize_pdf_text_collapses_whitespace():
    assert normalize_pdf_text("A\u200b  \n\nB\t\tC\ufeff\n") == "A B C"


def test_normalize_markdown_text_strips_space_before_cjk_punctuation():
    assert (
        normalize_markdown_text("部署 **HAMi AI Platform** ，并完成验证。\n")
        == "部署 **HAMi AI Platform**，并完成验证。"
    )


def test_collect_localized_image_targets_uses_native_asset_paths():
    markdown = "\n".join(
        [
            f"![cover]({case.FILE_STEM}/cover.png)",
            "![remote](https://example.com/cover.png)",
            f"![diagram](<{case.FILE_STEM}/diagram.svg>)",
        ]
    )

    assert collect_localized_image_targets(markdown) == [
        f"{case.FILE_STEM}/cover.png",
        f"{case.FILE_STEM}/diagram.svg",
    ]


def test_assert_feature_point_reports_named_failure(tmp_path: Path):
    snapshot_root = tmp_path / "snapshots"
    (snapshot_root / "markdown").mkdir(parents=True)
    (snapshot_root / "markdown" / "table.md").write_text(
        "公开 E2E 表格单元格 A", encoding="utf-8"
    )

    feature = FeaturePoint(
        name="markdown_table",
        markdown_contains_snapshot="markdown/table.md",
    )

    with pytest.raises(
        AssertionError, match="feature markdown_table: markdown snapshot missing"
    ):
        assert_feature_point(
            feature,
            "other text",
            "other pdf",
            [],
            snapshot_root=snapshot_root,
        )


def test_require_public_doc_export_prereqs_ready_fails_when_credentials_missing(
    monkeypatch,
):
    monkeypatch.delenv(case.LOCAL_SKIP_ENV, raising=False)
    monkeypatch.setattr(
        "test_public_doc_e2e.build_public_doc_exporter",
        lambda: (_ for _ in ()).throw(
            RuntimeError("feishu-docx public doc export requires app credentials")
        ),
    )

    with pytest.raises(
        pytest.fail.Exception,
        match="public doc export prerequisites missing: feishu-docx public doc export requires app credentials",
    ):
        require_public_doc_export_prereqs_ready(case.CANONICAL_DOC_REF)


def test_require_public_doc_export_prereqs_ready_skips_when_credentials_missing_with_local_gate(
    monkeypatch,
):
    monkeypatch.setenv(case.LOCAL_SKIP_ENV, "1")
    monkeypatch.setattr(
        "test_public_doc_e2e.build_public_doc_exporter",
        lambda: (_ for _ in ()).throw(
            RuntimeError("feishu-docx public doc export requires app credentials")
        ),
    )

    with pytest.raises(
        pytest.skip.Exception,
        match="public doc export prerequisites missing: feishu-docx public doc export requires app credentials",
    ):
        require_public_doc_export_prereqs_ready(case.CANONICAL_DOC_REF)


def test_require_public_doc_export_prereqs_ready_fails_when_fitz_missing(monkeypatch):
    original_import_module = importlib.import_module
    monkeypatch.setattr(
        "test_public_doc_e2e.build_public_doc_exporter",
        lambda: FeishuExporter(app_id="demo", app_secret="demo"),
    )

    def fake_import_module(name: str):
        if name == "fitz":
            raise ModuleNotFoundError("No module named 'fitz'")
        return original_import_module(name)

    monkeypatch.setattr(importlib, "import_module", fake_import_module)

    with pytest.raises(
        pytest.fail.Exception,
        match="public doc export prerequisites missing: PyMuPDF/fitz import failed: No module named 'fitz'",
    ):
        require_public_doc_export_prereqs_ready(case.CANONICAL_DOC_REF)


@pytest.mark.e2e_public_doc
def test_public_doc_export_e2e(tmp_path: Path):
    require_public_doc_export_prereqs_ready(case.DOC_REF)

    output_root = tmp_path / "public-doc-artifacts"
    exporter = build_public_doc_exporter()
    markdown_path = exporter.export(
        case.DOC_REF,
        output_dir=output_root,
        filename=case.FILE_STEM,
        pdf=True,
        silent=True,
    )

    pdf_path = output_root / f"{case.FILE_STEM}.pdf"
    assets_dir = output_root / case.FILE_STEM

    assert markdown_path.is_file()
    assert pdf_path.is_file()

    markdown_text = markdown_path.read_text(encoding="utf-8")
    localized_image_targets = collect_localized_image_targets(markdown_text)
    assert localized_image_targets, "expected localized image targets in exported markdown"
    assert assets_dir.is_dir()
    for relative_target in localized_image_targets:
        assert (output_root / relative_target).is_file()

    pdf_text = extract_pdf_text(pdf_path)
    pdf_images = extract_pdf_images(pdf_path)
    assert len(pdf_images) >= case.MIN_PDF_TOTAL_IMAGES

    for feature in case.FEATURE_POINTS:
        assert_feature_point(
            feature,
            markdown_text,
            pdf_text,
            pdf_images,
        )
