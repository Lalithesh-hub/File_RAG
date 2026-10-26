import pytest
from fastapi.testclient import TestClient

from app.generation import llm
from app.main import app
from app.retrieval.retriever import rrf
from app.store import store

DOC = (
    "Aurora panels are covered by a 10 year product warranty. The inverter carries a separate 5 year warranty.\n\n"
    "Customers may request a full refund within 30 days of installation completion. "
    "Refund requests are processed within 14 business days.\n\n"
    "The support desk is open from 9 am to 6 pm, Monday to Friday."
).encode()


@pytest.fixture()
def client():
    store.clear()
    return TestClient(app)


@pytest.fixture()
def doc_id(client):
    res = client.post("/documents", files={"file": ("policy.txt", DOC)})
    assert res.status_code == 200
    return res.json()["doc_id"]


def stub_llm(monkeypatch, reply):
    async def fake(system, user):
        return reply
    monkeypatch.setattr(llm, "chat", fake)


def ask(client, doc_id, q):
    return client.post(f"/documents/{doc_id}/ask", json={"question": q})


def test_upload_returns_contract(client):
    body = client.post("/documents", files={"file": ("policy.txt", DOC)}).json()
    assert set(body) == {"doc_id", "filename", "pages", "chunks"}
    assert body["filename"] == "policy.txt" and body["pages"] == 1


def test_grounded_answer_has_verified_citations(client, doc_id, monkeypatch):
    stub_llm(monkeypatch, "The panels have a 10 year warranty [1]. The inverter has a 5 year warranty [1].")
    body = ask(client, doc_id, "How long is the panel warranty?").json()
    assert body["grounded"] is True
    assert "[1]" in body["answer"] and len(body["citations"]) == 1
    assert body["citations"][0]["page"] == 1


def test_invented_number_sentence_is_dropped(client, doc_id, monkeypatch):
    stub_llm(monkeypatch, "The panels have a 10 year warranty [1]. The battery is covered for 25 years [1].")
    body = ask(client, doc_id, "How long is the panel warranty?").json()
    assert body["grounded"] is True
    assert "10" in body["answer"] and "25" not in body["answer"]


def test_fully_invented_answer_is_refused(client, doc_id, monkeypatch):
    stub_llm(monkeypatch, "The CEO earns 5 million dollars.")
    body = ask(client, doc_id, "How long is the panel warranty?").json()
    assert body["grounded"] is False and body["reason"] == "unverified" and body["citations"] == []


def test_model_declining_is_respected(client, doc_id, monkeypatch):
    stub_llm(monkeypatch, "NOT_FOUND")
    body = ask(client, doc_id, "How long is the panel warranty?").json()
    assert body["grounded"] is False and body["reason"] == "model_declined"


def test_gate_refuses_without_calling_the_model(client, doc_id, monkeypatch):
    async def must_not_run(system, user):
        raise AssertionError("LLM was called for an unrelated question")
    monkeypatch.setattr(llm, "chat", must_not_run)
    body = ask(client, doc_id, "What is the CEO salary?").json()
    assert body["grounded"] is False and body["reason"] == "no_match"


def test_missing_citation_is_added(client, doc_id, monkeypatch):
    stub_llm(monkeypatch, "Refunds are available within 30 days.")
    body = ask(client, doc_id, "Can I get a refund?").json()
    assert body["grounded"] is True and body["answer"].endswith("[1].")


def test_llm_down_gives_clear_503(client, doc_id, monkeypatch):
    async def down(system, user):
        raise llm.LLMError("Can't reach Ollama at http://localhost:11434. Start Ollama and try again.")
    monkeypatch.setattr(llm, "chat", down)
    res = ask(client, doc_id, "How long is the panel warranty?")
    assert res.status_code == 503 and "Ollama" in res.json()["detail"]


def test_unknown_document_is_404(client):
    assert ask(client, "nope", "anything").status_code == 404


def test_bad_inputs_rejected(client, doc_id):
    assert client.post("/documents", files={"file": ("x.exe", b"zz")}).status_code == 422
    assert client.post("/documents", files={"file": ("e.txt", b"")}).status_code == 422
    assert ask(client, doc_id, "   ").status_code == 422
    assert ask(client, doc_id, "x" * 1001).status_code == 422


def test_replacing_a_file_invalidates_the_old_id(client, doc_id):
    client.post("/documents", files={"file": ("other.txt", b"Different text about cats.")})
    assert ask(client, doc_id, "warranty").status_code == 404


def test_rrf_rewards_agreement():
    scores = rrf([[1, 2, 3], [3, 1, 2]])
    assert max(scores, key=scores.get) in (1, 3) and scores[2] < scores[1]
