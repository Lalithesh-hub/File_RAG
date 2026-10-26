import math
from collections import Counter, defaultdict

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from .chunker import Chunk
from .tokenizer import tokenize


class BM25:
    """Okapi BM25 with Lucene-style IDF (always >= 0, safe on tiny documents)."""

    def __init__(self, docs: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b, self.n = k1, b, len(docs)
        self.doc_len = np.array([len(d) for d in docs], dtype=float)
        self.avgdl = max(float(self.doc_len.mean()), 1.0)  # guard: all-empty chunks
        self.postings: dict[str, list[tuple[int, int]]] = defaultdict(list)
        for i, doc in enumerate(docs):
            for term, freq in Counter(doc).items():
                self.postings[term].append((i, freq))
        self.idf = {t: math.log(1 + (self.n - len(p) + 0.5) / (len(p) + 0.5))
                    for t, p in self.postings.items()}

    def scores(self, query: list[str]) -> np.ndarray:
        s = np.zeros(self.n)
        for term in set(query):
            if term not in self.postings:
                continue
            for i, f in self.postings[term]:
                norm = f + self.k1 * (1 - self.b + self.b * self.doc_len[i] / self.avgdl)
                s[i] += self.idf[term] * f * (self.k1 + 1) / norm
        return s


def _analyzer(tokens: list[str]) -> list[str]:
    """TF-IDF sees unigrams + bigrams, so it rewards phrase matches; BM25 stays unigram."""
    return tokens + [f"{a}_{b}" for a, b in zip(tokens, tokens[1:])]


class DocumentIndex:
    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        tokenized = [tokenize(c.text) for c in chunks]
        self.tokenized = tokenized  # also used by the relevance gate
        if not any(tokenized):
            raise ValueError("The document has no indexable text.")
        self.bm25 = BM25(tokenized)
        self.vectorizer = TfidfVectorizer(analyzer=_analyzer, sublinear_tf=True)
        self.matrix = self.vectorizer.fit_transform(tokenized)  # rows are L2-normalized

    def _top(self, scores: np.ndarray, k: int) -> list[tuple[int, float]]:
        order = np.argsort(scores)[::-1][:k]
        return [(int(i), float(scores[i])) for i in order if scores[i] > 0]

    def search_bm25(self, query: str, k: int = 10) -> list[tuple[int, float]]:
        q = tokenize(query)
        return self._top(self.bm25.scores(q), k) if q else []

    def search_tfidf(self, query: str, k: int = 10) -> list[tuple[int, float]]:
        q = tokenize(query)
        if not q:
            return []
        vec = self.vectorizer.transform([q])  # cosine similarity (rows already normalized)
        return self._top((self.matrix @ vec.T).toarray().ravel(), k)
