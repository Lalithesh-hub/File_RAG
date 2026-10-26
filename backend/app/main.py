import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .generation import llm
from .routes import router

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

app = FastAPI(title="File Q&A RAG")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,  # locked to the local frontend only
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)
app.include_router(router)


@app.get("/health")
async def health():
    # llm: ready | model_missing | unavailable (Ollama not running)
    return {"status": "ok", "model": settings.llm_model, "llm": await llm.status()}
