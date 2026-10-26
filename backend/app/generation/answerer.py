import logging
import re
from dataclasses import dataclass

from ..config import settings
from ..indexing.chunker import Chunk
from ..indexing.index import DocumentIndex
from ..indexing.tokenizer import tokenize
from ..retrieval.retriever import retrieve
from . import llm
from .prompt import SYSTEM_PROMPT, build_user_message
from .verify import MARK, content_tokens, is_supported, overlap, split_sentences

log = logging.getLogger(__name__)
NOT_FOUND_TEXT = "I couldn't find this in the document."


@dataclass
class Passage:
    n: int  # number shown to the model, 1-based
    chunk: Chunk
    score: float
    tokens: set[str]


def not_found(reason: str) -> dict:
    return {"answer": NOT_FOUND_TEXT, "grounded": False, "citations": [], "reason": reason}


def finalize(raw: str, passages: list[Passage], min_support: float) -> dict | None:
    """Verify the model's answer sentence by sentence against the passages, drop anything
    unsupported, and attach citations we computed ourselves. None means nothing survived."""
    text = raw.strip()
    if not text or text.upper().startswith("NOT_FOUND"):
        return None

    union: set[str] = set().union(*(p.tokens for p in passages))
    kept: list[tuple[str, list[int]]] = []
    for sentence in split_sentences(text):
        cited = {int(m) for m in MARK.findall(sentence) if 1 <= int(m) <= len(passages)}
        clean = MARK.sub("", sentence).strip()
        tokens = content_tokens(clean)
        if not clean or not is_supported(tokens, union, min_support):
            continue
        ratios = {p.n: overlap(tokens, p.tokens) for p in passages}
        best = max(ratios, key=lambda n: (ratios[n], -n))
        chosen = {best} | {n for n in cited if ratios[n] >= 0.5}
        kept.append((clean, sorted(chosen)))

    if not kept:
        return None

    renumber: dict[int, int] = {}  # model's numbers -> 1..m in order of first use
    for _, ns in kept:
        for n in ns:
            renumber.setdefault(n, len(renumber) + 1)

    sentences = []
    for clean, ns in kept:
        body, punct = re.match(r"^(.*?)([.!?]*)$", clean, re.S).groups()
        marks = "".join(f"[{renumber[n]}]" for n in ns)
        sentences.append(f"{body}{marks}{punct}")

    by_n = {p.n: p for p in passages}
    citations = [
        {"id": new, "chunk_id": by_n[old].chunk.id, "page": by_n[old].chunk.page,
         "score": round(by_n[old].score, 4), "text": by_n[old].chunk.text}
        for old, new in sorted(renumber.items(), key=lambda kv: kv[1])
    ]
    return {"answer": " ".join(sentences), "grounded": True, "citations": citations}


async def answer_question(index: DocumentIndex, question: str) -> dict:
    result = retrieve(index, question, settings.top_k, settings.rrf_k, settings.min_term_coverage)
    if not result.passed:  # the gate: never ask the model when the document has nothing relevant
        log.info("refused (no_match): coverage=%.2f", result.coverage)
        return not_found("no_match")

    passages = [Passage(i, h.chunk, h.score, set(tokenize(h.chunk.text)))
                for i, h in enumerate(result.hits, start=1)]
    raw = await llm.chat(SYSTEM_PROMPT, build_user_message(question, passages))

    final = finalize(raw, passages, settings.min_support)
    if final is None:
        reason = "model_declined" if raw.strip().upper().startswith("NOT_FOUND") else "unverified"
        log.info("refused (%s): %r", reason, raw[:200])
        return not_found(reason)
    return final
