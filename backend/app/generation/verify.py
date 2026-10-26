import re

from ..indexing.tokenizer import tokenize

MARK = re.compile(r"\[(\d+)\]")
_SENTENCE = re.compile(r"(?<=[.!?])\s+|\n+")
_IGNORED = {"yes", "no"}  # answers to yes/no questions have no checkable content


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE.split(text) if s.strip()]


def content_tokens(sentence: str) -> list[str]:
    return [t for t in tokenize(MARK.sub("", sentence)) if t not in _IGNORED]


def is_supported(tokens: list[str], passage_tokens: set[str], min_support: float) -> bool:
    """A sentence is kept only if (a) every number in it appears in the passages and
    (b) enough of its other words do. Catches invented figures and invented claims."""
    if not tokens:
        return True
    if any(t.isdigit() and t not in passage_tokens for t in tokens):
        return False
    return sum(t in passage_tokens for t in tokens) / len(tokens) >= min_support


def overlap(tokens: list[str], passage_tokens: set[str]) -> float:
    return sum(t in passage_tokens for t in tokens) / len(tokens) if tokens else 0.0
