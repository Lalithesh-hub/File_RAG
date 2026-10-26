import httpx

from ..config import settings


class LLMError(Exception):
    """Message is safe to show the user."""


async def chat(system: str, user: str) -> str:
    payload = {
        "model": settings.llm_model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "stream": False,
        "options": {"temperature": 0, "num_ctx": settings.num_ctx},  # temperature 0: no creative drift
    }
    try:
        async with httpx.AsyncClient(timeout=settings.llm_timeout_s) as client:
            res = await client.post(f"{settings.ollama_url}/api/chat", json=payload)
    except httpx.ConnectError:
        raise LLMError(f"Can't reach Ollama at {settings.ollama_url}. Start Ollama and try again.")
    except httpx.TimeoutException:
        raise LLMError("The model took too long to answer. Try again, or use a smaller model.")
    except httpx.HTTPError:
        raise LLMError("Talking to Ollama failed. Check that it is running.")

    if res.status_code == 404:
        raise LLMError(f"The model '{settings.llm_model}' isn't installed. Run: ollama pull {settings.llm_model}")
    if res.status_code != 200:
        raise LLMError(f"Ollama returned an error ({res.status_code}).")
    try:
        return res.json()["message"]["content"]
    except (KeyError, ValueError, TypeError):
        raise LLMError("Ollama sent a response in an unexpected format.")


async def status() -> str:
    """ready | model_missing | unavailable"""
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            res = await client.get(f"{settings.ollama_url}/api/tags")
        names = {m.get("name") for m in res.json().get("models", [])}
    except (httpx.HTTPError, ValueError, AttributeError):
        return "unavailable"
    wanted = settings.llm_model
    return "ready" if wanted in names or f"{wanted}:latest" in names else "model_missing"
