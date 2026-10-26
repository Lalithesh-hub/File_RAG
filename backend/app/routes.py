import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field, field_validator

from .config import settings
from .generation.answerer import answer_question
from .generation.llm import LLMError
from .indexing.chunker import chunk_pages
from .indexing.index import DocumentIndex
from .parsers.base import ParseError
from .parsers.router import parse_file
from .store import DocumentRecord, store

log = logging.getLogger(__name__)
router = APIRouter()


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)

    @field_validator("question")
    @classmethod
    def not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Question can't be empty.")
        return v


def _build_record(filename: str, data: bytes) -> DocumentRecord:
    pages = parse_file(filename, data)  # CPU/OCR heavy: runs in a worker thread
    chunks = chunk_pages(pages, settings.chunk_words, settings.chunk_overlap_words)
    return DocumentRecord(uuid.uuid4().hex, filename, len(pages), DocumentIndex(chunks))


@router.post("/documents")
async def upload_document(file: UploadFile = File(...)):
    filename = Path(file.filename or "").name or "document"  # strip any client-supplied path
    limit = settings.max_upload_mb * 1024 * 1024
    too_big = HTTPException(413, f"File exceeds {settings.max_upload_mb} MB limit.")
    if file.size is not None and file.size > limit:
        raise too_big
    data = await file.read()
    if len(data) > limit:
        raise too_big

    try:
        record = await run_in_threadpool(_build_record, filename, data)
    except (ParseError, ValueError) as e:
        raise HTTPException(422, str(e))
    except RuntimeError as e:  # e.g. Tesseract missing: a setup problem the user can fix
        raise HTTPException(503, str(e))
    except Exception:
        log.exception("Failed to read %s", filename)
        raise HTTPException(422, "Couldn't read this file. It may be damaged or password-protected.")

    store.put(record)
    return {"doc_id": record.doc_id, "filename": record.filename,
            "pages": record.pages, "chunks": len(record.index.chunks)}


@router.post("/documents/{doc_id}/ask")
async def ask(doc_id: str, body: AskRequest):
    record = store.get(doc_id)
    if record is None:
        raise HTTPException(404, "This file is no longer loaded. Upload it again.")
    try:
        return await answer_question(record.index, body.question)
    except LLMError as e:
        raise HTTPException(503, str(e))


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    return {"deleted": store.delete(doc_id)}
