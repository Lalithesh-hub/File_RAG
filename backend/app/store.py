from dataclasses import dataclass

from .indexing.index import DocumentIndex


@dataclass
class DocumentRecord:
    doc_id: str
    filename: str
    pages: int
    index: DocumentIndex


class DocumentStore:
    """Single-document, in-memory. Loading a new file replaces the old one."""

    def __init__(self) -> None:
        self._record: DocumentRecord | None = None

    def put(self, record: DocumentRecord) -> None:
        self._record = record

    def get(self, doc_id: str) -> DocumentRecord | None:
        return self._record if self._record and self._record.doc_id == doc_id else None

    def delete(self, doc_id: str) -> bool:
        if self.get(doc_id) is None:
            return False
        self._record = None
        return True

    def clear(self) -> None:
        self._record = None


store = DocumentStore()
