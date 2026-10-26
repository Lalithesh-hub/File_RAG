import { API_URL, USE_MOCK } from "./config";
import { mockAsk, mockUpload } from "./mock";

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function readError(res) {
  try {
    const data = await res.json();
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail)) return data.detail.map((d) => d.msg).join("; ");
  } catch {
    /* body wasn't JSON; fall through */
  }
  return `The server returned an error (${res.status}).`;
}

/** fetch wrapper: timeout, caller cancellation, and readable errors. */
async function request(path, { method = "GET", body, json, signal, timeoutMs = 30_000 } = {}) {
  const controller = new AbortController();
  const forward = () => controller.abort();
  if (signal?.aborted) controller.abort();
  signal?.addEventListener("abort", forward, { once: true });
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  let res;
  try {
    res = await fetch(`${API_URL}${path}`, {
      method,
      body: json ? JSON.stringify(json) : body,
      headers: json ? { "Content-Type": "application/json" } : undefined,
      signal: controller.signal,
    });
  } catch (err) {
    if (signal?.aborted) throw err; // the caller cancelled; they handle AbortError
    if (controller.signal.aborted) {
      throw new ApiError("This took too long. A local model can be slow; try again or ask a shorter question.");
    }
    throw new ApiError(`Can't reach the backend at ${API_URL}. Check that it is running.`);
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener("abort", forward);
  }
  if (!res.ok) throw new ApiError(await readError(res), res.status);
  return res.json();
}

export async function checkHealth() {
  if (USE_MOCK) return { status: "ok" };
  return request("/health", { timeoutMs: 4000 });
}

/** POST /documents -> { doc_id, filename, pages, chunks } */
export async function uploadDocument(file) {
  if (USE_MOCK) return mockUpload(file);
  const form = new FormData();
  form.append("file", file);
  return request("/documents", { method: "POST", body: form, timeoutMs: 180_000 }); // OCR can be slow
}

/** POST /documents/{id}/ask -> { answer, grounded, citations: [{ id, chunk_id, page, score, text }] } */
export async function askQuestion(docId, question, signal) {
  if (USE_MOCK) return mockAsk(docId, question, signal);
  return request(`/documents/${encodeURIComponent(docId)}/ask`, {
    method: "POST",
    json: { question },
    signal,
    timeoutMs: 180_000,
  });
}

export async function deleteDocument(docId) {
  if (USE_MOCK) return;
  await request(`/documents/${encodeURIComponent(docId)}`, { method: "DELETE" });
}
