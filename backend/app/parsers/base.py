from dataclasses import dataclass


@dataclass
class Page:
    number: int  # 1-based page/sheet/slide number, used for citations
    text: str


class ParseError(Exception):
    """Raised when a file can't be read; message is safe to show the user."""
