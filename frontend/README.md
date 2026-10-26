# Frontend (React + Vite)

## Run (Windows, Command Prompt)
    cd frontend
    npm install
    copy .env.example .env
    npm run dev
Open http://localhost:5173

The backend implements this contract. Set `VITE_USE_MOCK=true` in `.env` only if you want to try the UI with
sample answers while the backend isn't running.

## API contract between UI and backend
POST   /documents              multipart field "file"
                               -> { doc_id, filename, pages, chunks }
POST   /documents/{id}/ask     { "question": "..." }
                               -> { answer, grounded, citations: [{ id, chunk_id, page, score, text }] }
DELETE /documents/{id}         -> any 2xx
GET    /health                 -> any 2xx
Errors: FastAPI style { "detail": "message" } with a 4xx/5xx status; the message is shown to the user.

Rules the UI relies on:
- Cite sources in `answer` as [1], [2]; each number must match a citation `id`. Unknown numbers stay plain text.
- When the file doesn't contain the answer, return grounded=false, citations=[] and a short `answer`.
- All text is rendered as plain text (never HTML), so document content can't inject script.

## Structure
src/api.js            fetch wrapper: timeout, cancel, readable errors
src/mock.js           fake backend for demo mode
src/config.js         API URL, accepted file types, size limit (keep in sync with backend)
src/components/       UploadPanel, Conversation, AnswerCard, QuestionInput
