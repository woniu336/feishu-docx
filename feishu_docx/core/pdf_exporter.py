"""
[INPUT]: markdown string or path, optional CSS path
[OUTPUT]: PDF file via WeasyPrint
[POS]: core module, markdown-to-PDF bridge
"""

from datetime import date
from pathlib import Path

import mistune

DEFAULT_CSS = """
@page { size: A4; margin: 2.5cm 2cm; @bottom-center { content: counter(page); font-size: 9pt; color: #999; } }
@page cover { margin: 0; @bottom-center { content: none; } }

body { font-family: "Noto Sans", "Helvetica Neue", Arial, sans-serif; font-size: 11pt; line-height: 1.6; color: #222; max-width: 100%; }

.cover-page { page: cover; page-break-after: always; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100vh; text-align: center; background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%); color: #fff; padding: 3cm; }
.cover-page h1 { font-size: 2.4em; font-weight: 700; border: none; margin-bottom: 0.5em; line-height: 1.3; color: #fff; }
.cover-page .meta { font-size: 1.05em; opacity: 0.75; margin-top: 2em; }
.cover-page .rule { width: 80px; height: 3px; background: rgba(255,255,255,0.5); margin: 1.5em auto; }

h1 { font-size: 1.8em; border-bottom: 2px solid #2563eb; padding-bottom: 0.3em; }
h2 { font-size: 1.4em; border-bottom: 1px solid #e5e7eb; padding-bottom: 0.2em; }
h3 { font-size: 1.15em; }
code { background: #f3f4f6; padding: 0.15em 0.3em; border-radius: 3px; font-size: 0.9em; }
pre { background: #f8fafc; border: 1px solid #e5e7eb; padding: 0.8em; white-space: pre-wrap; word-wrap: break-word; overflow-wrap: break-word; }
pre code { background: none; padding: 0; white-space: pre-wrap; word-wrap: break-word; }
table { border-collapse: collapse; width: 100%; margin: 1em 0; }
th, td { border: 1px solid #d1d5db; padding: 0.5em 0.75em; text-align: left; }
th { background: #f3f4f6; font-weight: 600; }
img { max-width: 100%; height: auto; }
blockquote { border-left: 3px solid #2563eb; margin-left: 0; padding-left: 1em; color: #555; }
"""


def md_to_pdf(
    md_content: str,
    output_path: Path,
    css_path: Path | None = None,
    title: str | None = None,
    logo_path: Path | None = None,
) -> Path:
    """Convert markdown string to PDF using WeasyPrint.

    Args:
        md_content: Markdown source string.
        output_path: Destination .pdf path.
        css_path: Optional path to a CSS file for branding; defaults to built-in styles.
        title: Optional document title for the cover page.
        logo_path: Optional path to an image (SVG/PNG) for the cover page header.

    Returns:
        The output_path that was written.
    """
    # ponytail: lazy import so the CLI works without weasyprint installed
    from weasyprint import HTML  # type: ignore[import-untyped]

    html_body = mistune.html(md_content)
    if css_path:
        css_text = css_path.read_text(encoding="utf-8")
    else:
        css_text = DEFAULT_CSS

    title_html = ""
    if title:
        today = date.today().isoformat()
        logo_img = ""
        if logo_path:
            logo_src = logo_path.resolve().as_uri()
            logo_img = f'<img class="cover-logo" src="{logo_src}" alt="logo">\n'
        title_html = (
            f'<div class="cover-page">\n'
            f'{logo_img}'
            f'<h1>{title}</h1>\n'
            f'<div class="rule"></div>\n'
            f'<div class="meta">{today}</div>\n'
            f"</div>\n"
        )

    html = (
        "<!DOCTYPE html>\n"
        "<html><head><meta charset=\"utf-8\">\n"
        f"<style>{css_text}</style>\n"
        "</head><body>\n"
        f"{title_html}"
        f"{html_body}\n"
        "</body></html>"
    )
    HTML(string=html).write_pdf(output_path)
    return output_path
