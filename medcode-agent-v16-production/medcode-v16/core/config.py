"""
MedCode AI Agent -- Configuration & Settings
=============================================
Central configuration: environment variables, API keys, and constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

# -- OMOPHub ------------------------------------------------------------
OMOPHUB_API_KEY = os.getenv("OMOPHUB_API_KEY", "")
OMOPHUB_TIMEOUT = int(os.getenv("OMOPHUB_TIMEOUT", "30"))

# -- PRIMARY LLM: DeepSeek V4 (OpenAI-compatible) ----------------------
LLM_PRIMARY = "deepseek"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

# -- LLM FALLBACK CHAIN ------------------------------------------------
# Groq: up to 7 keys for rotation
GROQ_KEYS = [
    k for k in [
        os.getenv("GROQ_API_KEY", "").strip(),
        os.getenv("GROQ_API_KEY_1", "").strip(),
        os.getenv("GROQ_API_KEY_2", "").strip(),
        os.getenv("GROQ_API_KEY_3", "").strip(),
        os.getenv("GROQ_API_KEY_4", "").strip(),
        os.getenv("GROQ_API_KEY_5", "").strip(),
        os.getenv("GROQ_API_KEY_6", "").strip(),
        os.getenv("GROQ_API_KEY_7", "").strip(),
    ] if k
]
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

# Cerebras: up to 9 keys for rotation
CEREBRAS_KEYS = [
    k for k in [
        os.getenv("CEREBRAS_API_KEY", "").strip(),
        os.getenv("CEREBRAS_API_KEY_1", "").strip(),
        os.getenv("CEREBRAS_API_KEY_2", "").strip(),
        os.getenv("CEREBRAS_API_KEY_3", "").strip(),
        os.getenv("CEREBRAS_API_KEY_4", "").strip(),
        os.getenv("CEREBRAS_API_KEY_5", "").strip(),
        os.getenv("CEREBRAS_API_KEY_6", "").strip(),
        os.getenv("CEREBRAS_API_KEY_7", "").strip(),
        os.getenv("CEREBRAS_API_KEY_8", "").strip(),
    ] if k
]
CEREBRAS_URL = "https://api.cerebras.ai/v1/chat/completions"
CEREBRAS_MODEL = "llama3.1-8b"

# Additional fallbacks
TOGETHER_KEY = os.getenv("TOGETHER_API_KEY", "").strip()
TOGETHER_URL = "https://api.together.xyz/v1/chat/completions"
TOGETHER_MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"

GEMINI_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
GEMINI_MODEL = "gemini-2.0-flash"

MISTRAL_KEY = os.getenv("MISTRAL_API_KEY", "").strip()
MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"
MISTRAL_MODEL = "mistral-large-latest"

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "meta-llama/llama-3.2-3b-instruct:free"

# -- APP CONFIG ---------------------------------------------------------
APP_PORT = int(os.getenv("APP_PORT", "8000"))
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///medcode.db")

# -- PostgreSQL (opt-in via DATABASE_URL) -----------------------------------
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "medcode")
POSTGRES_USER = os.getenv("POSTGRES_USER", "medcode")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
POSTGRES_SSL_MODE = os.getenv("POSTGRES_SSL_MODE", "disable")

# -- Connection Pool Settings -----------------------------------------------
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))

MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE", "25"))
DEFAULT_MODE = os.getenv("DEFAULT_MODE", "balanced")
APP_VERSION = "5.0.0-ml"

# -- CODING PARAMS ------------------------------------------------------
MAX_SEARCH_RESULTS = 15
BEAM_WIDTH_BALANCED = 5
BEAM_WIDTH_DEEP = 10
BFS_MAX_DEPTH_BALANCED = 2
BFS_MAX_DEPTH_DEEP = 3
BFS_EXPLORE_THRESHOLD = 60  # LLM score threshold to expand branch
BFS_MAX_ITERATIONS_BALANCED = 8
BFS_MAX_ITERATIONS_DEEP = 20
MAX_FINAL_CODES = 10
LLM_TEMPERATURE = 0.1
LLM_MAX_TOKENS = 2000

# -- SECURITY (V19 HIPAA) ------------------------------------------------
MEDCODE_SECRET_KEY = os.getenv("MEDCODE_SECRET_KEY", "dev_key_change_in_production")
MEDCODE_ENCRYPTION_KEY = os.getenv("MEDCODE_ENCRYPTION_KEY", "")
MEDCODE_AUDIT_HMAC_KEY = os.getenv("MEDCODE_AUDIT_HMAC_KEY", "")
JWT_SECRET = os.getenv("JWT_SECRET", "dev_jwt_secret_change_in_production")
JWT_EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", "30"))
SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "15"))
FORCE_HTTPS = os.getenv("FORCE_HTTPS", "false").lower() == "true"
RATE_LIMIT_RPM = int(os.getenv("RATE_LIMIT_RPM", "60"))
AUDIT_LOG_PATH = os.getenv("AUDIT_LOG_PATH", "data/audit_log.jsonl")

# -- COMPLIANCE ---------------------------------------------------------
CURRENT_FISCAL_YEAR = 2026
# Codes that require 7th character
SEVENTH_CHAR_REQUIRED_CATEGORIES = [
    "S",  # Injury, poisoning
    "T",  # External causes
    "M80", "M84", "M85",  # Pathological fractures
]
# Laterality-required codes (right/left/bilateral)
LATERALITY_REQUIRED = [
    "M17",  # Knee osteoarthritis
    "M16",  # Hip osteoarthritis
    "H",    # Eye disorders
    "Q",    # Ear disorders
]


def validate_production_secrets() -> None:
    """Validate that production secrets are not using default/dev values."""
    MEDCODE_ENV = os.getenv("MEDCODE_ENV", "development")
    if MEDCODE_ENV != "production":
        return

    errors = []

    if MEDCODE_SECRET_KEY == "dev_key_change_in_production":
        errors.append(
            "MEDCODE_SECRET_KEY is using the default dev value. "
            "Set a strong random secret in your environment."
        )

    if JWT_SECRET == "dev_jwt_secret_change_in_production":
        errors.append(
            "JWT_SECRET is using the default dev value. "
            "Set a strong random secret in your environment."
        )

    if not MEDCODE_ENCRYPTION_KEY:
        errors.append(
            "MEDCODE_ENCRYPTION_KEY is empty. "
            "Set a valid encryption key in your environment."
        )

    if errors:
        raise ValueError(
            "PRODUCTION SECURITY CHECK FAILED:\n" + "\n".join(errors)
        )


validate_production_secrets()
