from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM (Ollama)
    ollama_url: str = "http://localhost:11434"
    llm_model: str = "qwen2.5:7b"
    llm_timeout_s: float = 170.0   # keep below the frontend's 180 s so errors arrive as clean messages
    num_ctx: int = 4096

    # Uploads / OCR
    max_upload_mb: int = 50
    tesseract_cmd: str = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    ocr_languages: str = "eng"

    # Indexing
    chunk_words: int = 200
    chunk_overlap_words: int = 40

    # Retrieval and anti-hallucination
    top_k: int = 4                  # passages given to the model
    rrf_k: int = 60                 # standard RRF constant
    min_term_coverage: float = 0.4  # gate: best passage must contain this share of the question's terms
    min_support: float = 0.6        # verifier: share of an answer sentence's words found in the passages

    allowed_origins: list[str] = ["http://localhost:5173"]

    class Config:
        env_file = ".env"


settings = Settings()
