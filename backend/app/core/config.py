from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Sanad API"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "change-me-in-production-use-strong-random-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    DATABASE_URL: str = "postgresql://sanad:sanad_secret@localhost:5432/sanad"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001,http://localhost:3002"
    FRONTEND_URL: str = "http://localhost:3000"
    MAX_LOGIN_ATTEMPTS: int = 8
    LOCKOUT_MINUTES: int = 10
    # Prod : 5 login / minute / IP (bruteforce). En DEBUG, rate_limit ×8.
    LOGIN_RATE_LIMIT: int = 5
    LOGIN_RATE_WINDOW_SEC: int = 60
    CAPTCHA_AFTER_FAILURES: int = 5
    # Cloudflare Turnstile (vide = désactivé en dev)
    TURNSTILE_SECRET_KEY: str = ""
    TURNSTILE_SITE_KEY: str = ""
    COOKIE_SECURE: bool = False
    REFRESH_COOKIE_NAME: str = "sanad_refresh"
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 50
    # Uploads documents+audio / utilisateur authentifié
    UPLOAD_RATE_LIMIT: int = 20
    UPLOAD_RATE_WINDOW_SEC: int = 60
    # Codes cabinet (ATLAS-XXXX)
    JOIN_VALIDATE_RATE_LIMIT: int = 10
    JOIN_REQUEST_RATE_LIMIT: int = 10
    ENCRYPTION_KEY: str = ""
    GROQ_API_KEY: str = ""
    # Cerveau chat prod : groq | kimi | auto | ollama (fallback local)
    LLM_PROVIDER: str = "auto"
    LLM_ALLOW_CLOUD_FALLBACK: bool = True
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "sanad-legal"
    # Synthèse documents locale (guide Ollama + Mistral)
    OLLAMA_SYNTHESIS_MODEL: str = "mistral"
    OLLAMA_NUM_PREDICT: int = 256
    # CPU / premier chargement Mistral
    OLLAMA_CHAT_TIMEOUT: float = 600.0
    # Timeout court par tentative cloud / free-router (fallback rapide)
    LLM_HTTP_TIMEOUT_SEC: float = 30.0
    # Speech-to-text local (faster-whisper) — cœur plaidoirie VPS
    WHISPER_ENABLED: bool = True
    WHISPER_MODEL: str = "small"  # tiny|base|small|medium|large-v3 — small = rapide CPU
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"
    # Transcription audio-pièce (jusqu'à 50 Mo) — 10 min max
    WHISPER_TIMEOUT_SEC: float = 600.0
    # Dictée : polish/compose uniquement via Ollama local (confidentialité)
    DICTATION_LOCAL_ONLY: bool = False
    # MinIO / OCR
    MINIO_TIMEOUT_SEC: float = 30.0
    OCR_TIMEOUT_SEC: float = 300.0
    # Celery hard limits (secondes)
    CELERY_TASK_SOFT_TIME_LIMIT: int = 900
    CELERY_TASK_TIME_LIMIT: int = 960
    CELERY_MAX_RETRIES: int = 3
    # False = pipeline cloud (Groq/Kimi) — recommandé prod
    LLM_CHAT_USE_OLLAMA: bool = False
    # Cloud-first : le LLM cloud rédige toujours (pas coller des extraits bruts)
    LLM_CHAT_CLOUD_FIRST: bool = True
    # Groq/Kimi rédigent les réponses quand des sources sont trouvées (corpus + web)
    LLM_USE_GROQ_FOR_WEB: bool = True
    LLM_USE_GROQ_FOR_CHAT: bool = True
    # Kimi (Moonshot) — API compatible OpenAI, optionnel
    KIMI_API_KEY: str = ""
    KIMI_BASE_URL: str = "https://api.moonshot.ai/v1"
    KIMI_MODEL: str = "kimi-k2.6"
    # Free-tier rotation (optionnel — évite 429 si Groq/Kimi saturés)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_MODEL: str = "deepseek-chat"
    TOGETHER_API_KEY: str = ""
    TOGETHER_MODEL: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo"
    SAMBANOVA_API_KEY: str = ""
    SAMBANOVA_MODEL: str = "Meta-Llama-3.3-70B-Instruct"
    # Mistral AI — API compatible OpenAI
    MISTRAL_API_KEY: str = ""
    MISTRAL_BASE_URL: str = "https://api.mistral.ai/v1"
    # medium ≈ qualité chat Mistral ; overridable via MISTRAL_MODEL dans .env
    MISTRAL_MODEL: str = "mistral-medium-latest"
    LLM_USE_FREE_ROUTER: bool = True
    OCR_QUALITY_THRESHOLD: int = 70
    AI_CONFIDENCE_THRESHOLD: int = 60
    SEED_DEMO_DATA: bool = False

    # Web search
    WEB_SEARCH_PROVIDER: str = "duckduckgo"  # duckduckgo | tavily
    TAVILY_API_KEY: str = ""

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # MinIO (S3-compatible)
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "sanad_minio"
    MINIO_SECRET_KEY: str = "sanad_minio_secret"
    MINIO_BUCKET: str = "sanad-documents"
    MINIO_SECURE: bool = False
    USE_MINIO: bool = True

    # ChromaDB + embeddings
    CHROMA_PERSIST_DIR: str = "./data/chromadb"
    EMBEDDING_MODEL: str = "BAAI/bge-m3"

    # Email SMTP
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "Sanad <noreply@sanad.ma>"
    SMTP_TLS: bool = False

    # Token expiry
    EMAIL_VERIFY_EXPIRE_HOURS: int = 24
    PASSWORD_RESET_EXPIRE_HOURS: int = 2
    INVITE_EXPIRE_HOURS: int = 72

    # OAuth / 2FA
    GOOGLE_CLIENT_ID: str = ""

    # Logs / erreurs (optionnel — tier gratuit Sentry)
    LOG_JSON: bool = True
    LOG_LEVEL: str = "INFO"
    SENTRY_DSN: str = ""
    BACKUP_DIR: str = "./backups"
    BACKUP_RETENTION_DAYS: int = 7

    class Config:
        env_file = ".env"


settings = Settings()
