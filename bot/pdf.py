"""Render a Markdown report to PDF using markdown + WeasyPrint."""

from __future__ import annotations

import os
import pathlib

import markdown as md_lib
from weasyprint import HTML

# Minimal stylesheet so the PDF doesn't look like a ransom note.
_CSS = """
@page { size: A4; margin: 1.5cm; }
body { font-family: 'Helvetica', 'Arial', sans-serif; font-size: 10pt; line-height: 1.4; color: #222; }
h1   { font-size: 18pt; border-bottom: 2px solid #333; padding-bottom: 0.2em; }
h2   { font-size: 14pt; margin-top: 1.2em; }
h3   { font-size: 12pt; }
code { background: #f4f4f4; padding: 1px 4px; border-radius: 3px; font-size: 9pt; }
pre  { background: #f4f4f4; padding: 8px; border-radius: 4px; overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: 8.5pt; margin: 0.6em 0; }
th, td { border: 1px solid #ccc; padding: 4px 6px; text-align: left; vertical-align: top; }
th { background: #eee; }
img  { max-width: 100%; height: auto; }
a { color: #0058a3; text-decoration: none; }
"""


def md_to_pdf(md_path: str, pdf_path: str | None = None) -> str:
    """Render `md_path` to a PDF; return the PDF's path.

    Image references in the Markdown are resolved relative to the md file's
    directory (so the PNG charts produced by iNotWiki end up in the PDF).
    """
    md_text = pathlib.Path(md_path).read_text(encoding="utf-8")
    body_html = md_lib.markdown(
        md_text,
        extensions=["tables", "fenced_code"],
        output_format="html5",
    )
    full_html = f"<!doctype html><html><head><meta charset='utf-8'><style>{_CSS}</style></head><body>{body_html}</body></html>"

    if pdf_path is None:
        pdf_path = os.path.splitext(md_path)[0] + ".pdf"

    base_url = os.path.dirname(os.path.abspath(md_path))
    HTML(string=full_html, base_url=base_url).write_pdf(pdf_path)
    return pdf_path
