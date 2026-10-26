import re
from dataclasses import dataclass

from ..parsers.base import Page


@dataclass
class Chunk:
    id: int
    page: int  # kept for citations
    text: str


_UNIT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")


def _units(text: str, max_words: int) -> list[str]:
    """Sentence/line-sized units; anything longer than max_words is hard-split."""
    units = []
    for part in _UNIT_SPLIT.split(text):
        words = part.split()
        for i in range(0, len(words), max_words):
            units.append(" ".join(words[i:i + max_words]))
    return units


def _overlap_tail(units: list[str], overlap_words: int) -> tuple[list[str], int]:
    tail, count = [], 0
    for u in reversed(units):
        w = len(u.split())
        if count + w > overlap_words:
            break
        tail.insert(0, u)
        count += w
    return tail, count


def chunk_pages(pages: list[Page], max_words: int = 200, overlap_words: int = 40) -> list[Chunk]:
    chunks: list[Chunk] = []

    def emit(page_no: int, units: list[str]) -> None:
        chunks.append(Chunk(len(chunks), page_no, "\n".join(units)))

    for page in pages:  # chunks never cross pages, so every citation is exact
        current, count = [], 0
        for unit in _units(page.text, max_words):
            w = len(unit.split())
            if current and count + w > max_words:
                emit(page.number, current)
                current, count = _overlap_tail(current, overlap_words)
            current.append(unit)
            count += w
        if current:
            emit(page.number, current)
    return chunks
