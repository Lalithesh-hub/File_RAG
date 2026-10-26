import unicodedata
from pathlib import Path

from . import documents as d
from .base import Page, ParseError

PARSERS = {
    ".pdf": d.parse_pdf, ".docx": d.parse_docx, ".pptx": d.parse_pptx,
    ".xlsx": d.parse_xlsx, ".csv": d.parse_csv,
    ".html": d.parse_html, ".htm": d.parse_html,
    ".txt": d.parse_text, ".md": d.parse_text,
    ".png": d.parse_image, ".jpg": d.parse_image, ".jpeg": d.parse_image,
    ".tiff": d.parse_image, ".bmp": d.parse_image,
}


def parse_file(filename: str, data: bytes) -> list[Page]:
    ext = Path(filename).suffix.lower()
    parser = PARSERS.get(ext)
    if parser is None:
        raise ParseError(f"Unsupported file type '{ext}'. Supported: {', '.join(sorted(PARSERS))}")
    pages = parser(data)
    if not pages:
        raise ParseError("No readable text found in this file.")
    # NFC-normalize so identical-looking text is always the same byte sequence
    return [Page(p.number, unicodedata.normalize("NFC", p.text)) for p in pages]
