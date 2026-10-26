from dataclasses import dataclass

from ..indexing.chunker import Chunk
from ..indexing.index import DocumentIndex
from ..indexing.tokenizer import tokenize


def rrf(rankings: list[list[int]], k: int = 60) -> dict[int, float]:
    """Reciprocal Rank Fusion: a chunk's score is the sum of 1/(k+rank) over every ranking it appears in.
    Uses ranks, not raw scores, so BM25 and TF-IDF (different scales) combine without normalization."""
    scores: dict[int, float] = {}
    for ranking in rankings:
        for rank, chunk_id in enumerate(ranking, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)
    return scores


@dataclass
class Hit:
    chunk: Chunk
    score: float


@dataclass
class Retrieval:
    hits: list[Hit]
    coverage: float  # best share of the question's terms found in a single retrieved passage
    passed: bool     # the relevance gate


def retrieve(index: DocumentIndex, query: str, top_k: int, rrf_k: int,
             min_coverage: float, pool: int = 10) -> Retrieval:
    terms = set(tokenize(query))
    bm25_ids = [i for i, _ in index.search_bm25(query, pool)]
    tfidf_ids = [i for i, _ in index.search_tfidf(query, pool)]
    fused = sorted(rrf([bm25_ids, tfidf_ids], rrf_k).items(), key=lambda kv: kv[1], reverse=True)
    hits = [Hit(index.chunks[i], s) for i, s in fused[:top_k]]
    if not hits or not terms:
        return Retrieval(hits, 0.0, False)
    coverage = max(len(terms & set(index.tokenized[h.chunk.id])) / len(terms) for h in hits)
    return Retrieval(hits, coverage, coverage >= min_coverage)
