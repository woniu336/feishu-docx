from types import SimpleNamespace

from lark_oapi.api.docx.v1 import Block, InlineLinkPreview, LinkPreview, MentionDoc, Text, TextElement

from feishu_docx.core.parsers.document import DocumentParser
from feishu_docx.schema.models import BlockType


class _FakeContactAPI:
    @staticmethod
    def get_user_name(user_id, access_token):  # noqa: ARG004
        return user_id


class _FakeDocxAPI:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def get_document_info(self, document_id, access_token):
        self.calls.append((document_id, access_token))
        return {"title": "Resolved Target Doc"}


class _FakeSDK:
    def __init__(self) -> None:
        self.contact = _FakeContactAPI()
        self.docx = _FakeDocxAPI()
        self.sheet = SimpleNamespace(get_spreadsheet_info=lambda token, access_token: {"title": token})
        self.bitable = SimpleNamespace(get_bitable_info=lambda token, access_token: {"title": token})
        self.wiki = SimpleNamespace(get_node_metadata=lambda token, access_token: SimpleNamespace(title=token))


def _make_parser(monkeypatch) -> DocumentParser:
    monkeypatch.setattr(DocumentParser, "_preprocess", lambda self: None)
    return DocumentParser(document_id="doc", user_access_token="token", sdk=_FakeSDK(), silent=True)


def test_render_text_payload_uses_inline_link_preview_title(monkeypatch):
    parser = _make_parser(monkeypatch)
    payload = Text.builder().elements(
        [
            TextElement.builder().link_preview(
                InlineLinkPreview.builder()
                .title("Card View Title")
                .url("https://example.com/card")
                .build()
            ).build()
        ]
    ).build()

    assert parser._render_text_payload(payload) == "[Card View Title](https://example.com/card)"


def test_render_text_payload_uses_mention_doc_title_and_url(monkeypatch):
    parser = _make_parser(monkeypatch)
    payload = Text.builder().elements(
        [
            TextElement.builder().mention_doc(
                MentionDoc.builder()
                .title("Mentioned Doc")
                .url("https://foo.feishu.cn/docx/AbCdEf")
                .token("AbCdEf")
                .build()
            ).build()
        ]
    ).build()

    assert parser._render_text_payload(payload) == "[Mentioned Doc](https://foo.feishu.cn/docx/AbCdEf)"


def test_render_block_link_preview_resolves_feishu_doc_title(monkeypatch):
    parser = _make_parser(monkeypatch)
    block = (
        Block.builder()
        .block_type(int(BlockType.LINK_PREVIEW))
        .link_preview(LinkPreview.builder().url("https://foo.feishu.cn/docx/AbCdEf").build())
        .build()
    )

    assert parser._render_block_content(block) == "> Link: [Resolved Target Doc](https://foo.feishu.cn/docx/AbCdEf)"
    assert parser.sdk.docx.calls == [("AbCdEf", "token")]


def test_render_reference_link_preserves_url_escapes(monkeypatch):
    parser = _make_parser(monkeypatch)

    assert parser._render_reference_link("https://example.com/a%20b", block_title="Card") == (
        "[Card](https://example.com/a%20b)"
    )


def test_render_reference_link_decodes_fully_encoded_url(monkeypatch):
    parser = _make_parser(monkeypatch)

    assert parser._render_reference_link(
        "https%3A%2F%2Fexample.com%2Fa%2520b",
        block_title="Card",
    ) == "[Card](https://example.com/a%20b)"
