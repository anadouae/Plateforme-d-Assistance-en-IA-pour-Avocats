from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "LexHub API"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "change-me-in-production-use-strong-random-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    DATABASE_URL: str = "postgresql://lexhub:lexhub_secret@localhost:5432/lexhub"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001,http://localhost:3002"
    FRONTEND_URL: str = "http://localhost:3000"
    MAX_LOGIN_ATTEMPTS: int = 8
    LOCKOUT_MINUTES: int = 10
    # Prod : 5 login / minute / IP (bruteforce). En DEBUG, rate_limit ×8.
    LOGIN_RATE_LIMIT: int = 5
    LOGIN_RATE_WINDOW_SEC: int = 60
    CAPTCHA_AFTER_FAILURES: int = 3
    # Cloudflare Turnstile (vide = désactivé). Clés de test CF toujours OK en local.
    TURNSTILE_SECRET_KEY: str = ""
    TURNSTILE_SITE_KEY: str = ""
    COOKIE_SECURE: bool = False
    REFRESH_COOKIE_NAME: str = "lexhub_refresh"
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 50
    # Uploads documents+audio / utilisateur authentifié
    UPLOAD_RATE_LIMIT: int = 20
    UPLOAD_RATE_WINDOW_SEC: int = 60
    # Codes cabinet (PREFIX-XXXXXXXX) — expiration + quota d'approbations
    JOIN_CODE_SUFFIX_LEN: int = 8
    JOIN_CODE_EXPIRE_DAYS: int = 14
    JOIN_CODE_MAX_APPROVALS: int = 1
    JOIN_VALIDATE_RATE_LIMIT: int = 5
    JOIN_REQUEST_RATE_LIMIT: int = 3
    JOIN_CODE_ATTEMPT_RATE_LIMIT: int = 8
    JOIN_CODE_ATTEMPT_WINDOW_SEC: int = 600
    ENCRYPTION_KEY: str = ""
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    # Cerveau chat prod : groq | kimi | auto | ollama (fallback local)
    LLM_PROVIDER: str = "auto"
    LLM_ALLOW_CLOUD_FALLBACK: bool = True
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "lexhub-legal"
    # Synthèse documents locale (guide Ollama + Mistral)
    OLLAMA_SYNTHESIS_MODEL: str = "mistral"
    OLLAMA_NUM_PREDICT: int = 256
    # CPU / premier chargement Mistral
    OLLAMA_CHAT_TIMEOUT: float = 600.0
    # Timeout court par tentative cloud / free-router (fallback rapide)
    LLM_HTTP_TIMEOUT_SEC: float = 30.0
    CASE_ANALYSIS_TIMEOUT_SEC: float = 20.0
    # Speech-to-text — prod LexHub = API OpenAI uniquement (même clé ChatGPT)
    WHISPER_ENABLED: bool = False
    WHISPER_MODEL: str = "small"  # tiny|base|small|medium|large-v3 — small = rapide CPU
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"
    # 15 min audio + RTF CPU lent — 30 min max de calcul
    WHISPER_TIMEOUT_SEC: float = 1800.0
    # Découpe interne seulement si audio > 3 min (fenêtres ~2 min, pas 15 s)
    WHISPER_CHUNK_ENABLED: bool = True
    WHISPER_CHUNK_SEC: float = 120.0
    WHISPER_CHUNK_MIN_SEC: float = 180.0
    # dynaudnorm amplifie le bruit → Whisper invente des mots. Off par défaut.
    WHISPER_DENOISE: bool = False
    # Gain audio silencieux (dB) avant Whisper — aide micro faible sans inventer
    WHISPER_GAIN_DB: float = 10.0
    # Fallback cloud STT (désactivé si DICTATION_OPENAI_ONLY)
    GROQ_WHISPER_MODEL: str = "whisper-large-v3"
    DICTATION_LOCAL_ONLY: bool = False
    DICTATION_STT_PREFER_GROQ: bool = False
    # Si True : polish/compose forcé Ollama (inutile sur VPS 2 Go sans Ollama)
    DICTATION_POLISH_LOCAL_ONLY: bool = False
    # True = bouton Corriger utilise ChatGPT (forme fusḥā) ; False = nettoyage local seul
    DICTATION_POLISH_USE_LLM: bool = True
    # STT : uniquement l’API OpenAI (même clé) — pas Groq, pas Whisper local
    DICTATION_OPENAI_ONLY: bool = True
    OPENAI_WHISPER_MODEL: str = "whisper-1"
    # MinIO / OCR
    MINIO_TIMEOUT_SEC: float = 30.0
    # OCR : cloud (Mistral/Gemini) = qualité max + rapide ; Tesseract = secours local
    OCR_CLOUD_ENABLED: bool = True
    OCR_CLOUD_TIMEOUT_SEC: float = 120.0
    MISTRAL_OCR_MODEL: str = "mistral-ocr-latest"
    OCR_TIMEOUT_SEC: float = 480.0
    OCR_PYMUPDF_TIMEOUT_SEC: float = 180.0
    OCR_TESSERACT_TIMEOUT_SEC: float = 480.0
    OCR_DPI: int = 300
    MAX_PDF_OCR_PAGES: int = 80
    MAX_PDF_TESSERACT_PAGES: int = 40
    # Celery hard limits (secondes)
    CELERY_TASK_SOFT_TIME_LIMIT: int = 900
    CELERY_TASK_TIME_LIMIT: int = 960
    CELERY_MAX_RETRIES: int = 3
    # False = pipeline cloud (Groq/Kimi) — recommandé prod
    LLM_CHAT_USE_OLLAMA: bool = False
    # Cloud-first : le LLM cloud rédige toujours (pas coller des extraits bruts)
    LLM_CHAT_CLOUD_FIRST: bool = True
    # Désactivé : ChatGPT (OpenAI) remplace Groq pour chat / web
    LLM_USE_GROQ_FOR_WEB: bool = False
    LLM_USE_GROQ_FOR_CHAT: bool = False
    # Kimi (Moonshot) — API compatible OpenAI, optionnel
    KIMI_API_KEY: str = ""
    KIMI_BASE_URL: str = "https://api.moonshot.ai/v1"
    KIMI_MODEL: str = "kimi-k2.6"
    # Free-tier rotation (optionnel — évite 429 si Groq/Kimi saturés)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
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
    # OpenAI / ChatGPT — politique LexHub : toute génération texte passe par ici si clé présente
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_MODEL_LIGHT: str = "gpt-4o-mini"
    # True = ChatGPT prioritaire partout (rédaction, polish, chat, synthèse…)
    LLM_FORCE_OPENAI: bool = True
    # True = PAS de secours Mistral / Groq / Kimi / Ollama si OpenAI KO
    LLM_OPENAI_STRICT: bool = True
    LLM_USE_FREE_ROUTER: bool = False
    BILLING_TRIAL_DAYS: int = 14
    BILLING_PAYMENT_MOCK: bool = True
    OCR_QUALITY_THRESHOLD: int = 70
    AI_CONFIDENCE_THRESHOLD: int = 60
    # True = pas d'historique chat renvoyé au LLM (économise tokens)
    AI_EPHEMERAL: bool = True
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

    # Email — Resend (prod) ou SMTP (dev / MailHog)
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "LexHub <noreply@lexhub.space>"
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "LexHub <noreply@lexhub.space>"
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

    # Paiement Maroc — environnement CMI / PayZone / virement ICE
    CMI_MERCHANT_ID: str = ""
    CMI_STORE_KEY: str = ""
    CMI_GATEWAY_URL: str = ""
    CMI_ENABLED: bool = False
    PAYZONE_MERCHANT_ID: str = ""
    PAYZONE_API_KEY: str = ""
    PAYZONE_ENABLED: bool = False
    LEXHUB_BANK_RIB: str = ""
    LEXHUB_BANK_NAME: str = "Attijariwafa Bank"
    LEXHUB_BANK_BENEFICIARY: str = "WEBVOICE SARL"
    LEXHUB_COMPANY_ICE: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
