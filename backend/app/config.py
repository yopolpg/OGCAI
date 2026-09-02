from pathlib import Path
# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base Directory of OGCAI
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
STORAGE_ROOT = WORKSPACE_ROOT / "storage"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OGCAI_", env_file=".env", extra="ignore")

    APP_NAME: str = "OGCAI Core Engine"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Server configuration
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    # Ollama Local Service Configuration
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_TIMEOUT_SECONDS: float = 120.0
    OLLAMA_KEEP_ALIVE: str = "30m"
    
    # Local Model Allocation
    DEFAULT_MODEL: str = "qwen2.5-coder:7b"
    ADVISOR_MODEL: str = "llama3.1:8b"
    HEAVY_LOGIC_MODEL: str = "deepseek-coder-v2:16b"
    FAST_WORKER_MODEL: str = "qwen2.5:3b"
    FALLBACK_MODEL: str = "phi3.5:latest"
    
    # High-Capacity Storage Directories
    STORAGE_DIR: Path = STORAGE_ROOT
    DB_DIR: Path = STORAGE_ROOT / "db"
    VECTORS_DIR: Path = STORAGE_ROOT / "vectors"
    VAULT_DIR: Path = STORAGE_ROOT / "vault"
    CACHE_DIR: Path = STORAGE_ROOT / "cache"
    
    def ensure_directories(self):
        """Create storage directories if they do not exist."""
        for path in [self.STORAGE_DIR, self.DB_DIR, self.VECTORS_DIR, self.VAULT_DIR, self.CACHE_DIR]:
            path.mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.ensure_directories()
