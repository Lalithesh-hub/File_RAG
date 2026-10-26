import re
from functools import lru_cache

from nltk.stem import SnowballStemmer

_stemmer = SnowballStemmer("english")  # rule-based; needs no data downloads
_TOKEN_RE = re.compile(r"[a-z0-9]+")   # digits kept: "invoice 4521" must stay searchable

# Own short list. sklearn's built-in list strips useful words like "system", "bill", "fire".
STOPWORDS = frozenset("""a an the and or but if then of to in on at by for with about as into
from up down out over under is are was were be been being am do does did have has had it its
this that these those i you he she we they me him her us them my your his our their what which
who whom how when where why can could should would will shall may might must so than too very
just also there here some any""".split())


@lru_cache(maxsize=50_000)
def _stem(word: str) -> str:
    return _stemmer.stem(word)


def tokenize(text: str) -> list[str]:
    """Lowercase -> split -> drop stopwords -> stem. Used for BOTH documents and queries."""
    return [_stem(t) for t in _TOKEN_RE.findall(text.lower()) if t not in STOPWORDS]
