from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    """
    Application Settings - จัดการ Environment Variables
    """
    
    # OpenAI Configuration (optional ถ้าใช้ Ollama แทน)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_temperature: float = 0.7

    # Ollama Configuration (optional)
    use_ollama: bool = False
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:14b"
    ollama_temperature: float = 0.3

    # SEC Open Data API Configuration (ก.ล.ต.)
    sec_api_key: str = ""
    sec_api_base_url: str = "https://api.sec.or.th/v1"
    sec_api_rate_limit: int = 5000


    # Qdrant Configuration
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection_name: str = "tax_knowledge"
    
    # RAG Configuration
    rag_top_k: int = 5
    rag_chunk_size: int = 1000
    rag_chunk_overlap: int = 200
    
    # Cron / Scheduler
    nextauth_url: str = "http://localhost:3000"
    cron_secret: str = ""

    # Application Settings
    app_name: str = "AI Tax Advisor"
    app_version: str = "1.0.0"
    debug_mode: bool = False
    
    # CORS Settings
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://192.168.100.55:3000",
        "http://127.0.0.1:3000"
    ]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()