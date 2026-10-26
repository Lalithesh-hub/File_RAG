# File Q&A RAG (English, local, BM25 + TF-IDF)

Load one file, ask questions, get answers built only from that file, each with the passages it came from.
Everything runs on your computer: FastAPI backend, React UI, Ollama for the language model.

## How an answer is produced
1. Question -> BM25 ranking and TF-IDF ranking (unigrams + bigrams) -> fused with Reciprocal Rank Fusion.
2. Relevance gate: if the best passage contains too few of the question's terms, we answer
   "I couldn't find this in the document" WITHOUT calling the model.
3. The model sees only the top passages and must cite them, or reply NOT_FOUND.
4. Verifier: every sentence is checked against the passages. Invented numbers or unsupported claims are
   dropped. If nothing survives, the answer is "not found". Citations are recomputed by us, not trusted.

## Run it (Windows). You need three things running.
1. Ollama (tray icon running) with the model pulled:  ollama pull qwen2.5:7b
2. Backend  (Command Prompt #1):
       cd backend
       python -m venv .venv
       .venv\Scripts\activate
       pip install -r requirements.txt
       copy .env.example .env
       uvicorn app.main:app --reload
   Check http://localhost:8000/health  ->  "llm": "ready" means Ollama and the model were found.
3. Frontend (Command Prompt #2):
       cd frontend
       npm install
       copy .env.example .env
       npm run dev
   Open http://localhost:5173  (keep VITE_USE_MOCK=false)

Try sample/aurora_solar_handbook.pdf. Good questions: "How long is the panel warranty?", "What are the
support hours?", "Can I get a refund?". Expected refusal: "What is the CEO salary?"

## Tests
    cd backend
    pip install -r requirements-dev.txt
    python -m pytest -q

## Tuning (backend/.env or app/config.py)
- Too many false "not found": lower MIN_TERM_COVERAGE (0.4) or MIN_SUPPORT (0.6).
- Model inventing details: raise MIN_SUPPORT.
- Slow answers: use a smaller model (LLM_MODEL=qwen2.5:3b) or lower TOP_K.

## Limits
- One file at a time, held in memory: restarting the backend unloads it.
- English only. No chat memory: each question stands alone.
- Scanned pages/images need Tesseract (TESSERACT_CMD in .env).
