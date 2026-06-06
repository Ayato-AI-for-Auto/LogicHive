import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from core.logging_config import get_logger

logger = get_logger("config")

# Resolve base directory: frozen (executable) vs source (development)
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent.parent.parent.resolve()

PROJECT_ROOT = BASE_DIR

# --- .env loading strategy ---
# 1. Look in the same directory as the EXE or project root
# 2. Look in the user's home directory (~/.logichive/.env) as a fallback
# Resolve HOME_DIR with override support for testing
HOME_DIR = Path(os.getenv("LOGICHIVE_HOME", str(Path.home() / ".logichive")))
HOME_ENV = HOME_DIR / ".env"
LOCAL_ENV = BASE_DIR / ".env"


def _load_config():
    """Tiered configuration loading with prioritized path resolution."""
    config_source = "None (Using defaults/Env)"

    # Priority 1: Local .env (next to EXE or project root)
    if LOCAL_ENV.exists():
        load_dotenv(LOCAL_ENV, override=True)
        config_source = f"Local: {LOCAL_ENV}"

    # Priority 2: User Home fallback
    elif HOME_ENV.exists():
        load_dotenv(HOME_ENV, override=True)
        config_source = f"Home: {HOME_ENV}"

    # Default: Standard CWD-based loading or Environment variables
    else:
        load_dotenv()
        if os.getenv("GEMINI_API_KEY"):
            config_source = "System Environment Variables"
        elif not ("pytest" in sys.modules or os.getenv("LOGICHIVE_TESTING") == "true"):
            # --- FIRST RUN / MISSING CONFIG LOGIC ---
            _create_default_env_if_missing()

    return config_source


def _create_default_env_if_missing():
    """Generates a template .env file to help user onboarding."""
    # Skip during testing to avoid side effects in tests
    if "pytest" in sys.modules or os.getenv("LOGICHIVE_TESTING") == "true":
        return

    if LOCAL_ENV.exists() or HOME_ENV.exists():
        return

    # If in frozen EXE and dist directory, we might want to put it in home instead
    # to avoid permissions issues in Program Files, but for MVP local is fine.

    template = """# ==========================================
# 🛡️ LogicHive: Configuration Template
# ==========================================

# --- 1. Provider Selection ---
# Choose your AI and Embedding providers.
# Options: gemini, ollama
MODEL_TYPE=gemini
EMBEDDING_PROVIDER=gemini

# --- 2. Gemini Settings (Recommended) ---
# Get your key at: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=

# --- 3. Ollama Settings (Alternative) ---
# If you prefer local-only, install Ollama (https://ollama.com)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=mistral-large
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# --- 4. Server Settings ---
PORT=10880
HOST=127.0.0.1

# --- 5. LogicHive Quality Gate ---
# Minimum score (0-100) for an asset to be accepted into the vault.
QUALITY_GATE_THRESHOLD=70
"""
    try:
        HOME_DIR.mkdir(parents=True, exist_ok=True)
        HOME_ENV.write_text(template, encoding="utf-8")
        logger.info(f"Initial configuration template created at: {HOME_ENV}")
        logger.info("Please edit this file and provide your GEMINI_API_KEY to start.")
    except Exception as e:
        logger.error(f"Failed to create configuration template: {e}")


def save_config(updates: dict):
    """Saves multiple configuration updates to the active .env file."""
    # We prefer the Home .env for persistence in frozen mode
    target_env = HOME_ENV

    # Read existing content if any
    content = ""
    if target_env.exists():
        content = target_env.read_text(encoding="utf-8")

    for key, value in updates.items():
        if f"{key}=" in content:
            import re

            content = re.sub(f"{key}=.*", f"{key}={value}", content)
        else:
            content = content.rstrip() + f"\n{key}={value}\n"

    try:
        HOME_DIR.mkdir(parents=True, exist_ok=True)
        target_env.write_text(content, encoding="utf-8")

        # Update current process environment
        for key, value in updates.items():
            os.environ[key] = str(value)
            # Update global variables in this module
            if key in globals():
                globals()[key] = value
        return True
    except Exception as e:
        logger.error(f"Failed to save configuration: {e}")
        return False


CONFIG_SOURCE = _load_config()


# --- Validation Helpers ---


def validate_config_lazy():
    """
    Performs runtime validation of critical settings.
    Returns (is_valid, error_message, config_path).
    """
    # Skip validation during pytest runs
    if "pytest" in sys.modules or os.getenv("LOGICHIVE_TESTING") == "true":
        return True, "", ""

    if MODEL_TYPE == "gemini" or EMBEDDING_PROVIDER == "gemini":
        if not GEMINI_API_KEY:
            return False, "GEMINI_API_KEY is missing.", str(HOME_ENV)

    return True, "", str(HOME_ENV)


# 1. AI & Models
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_TYPE = os.getenv("MODEL_TYPE", "ollama").lower()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/gemma-4-31b-it")
EMBEDDING_MODEL_ID = os.getenv("EMBEDDING_MODEL_ID", "models/gemini-embedding-2")
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "fastembed").lower()
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
FASTEMBED_MODEL = os.getenv("FASTEMBED_MODEL", "nomic-ai/nomic-embed-text-v1.5")


def _validate_gemini_api_key(api_key):
    # Skip validation during pytest runs
    if "pytest" in sys.modules or os.getenv("LOGICHIVE_TESTING") == "true":
        return True
    if not api_key:
        return False
    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        list(client.models.list(config={"page_size": 1}))
        return True
    except Exception as e:
        logger.warning(f"Gemini API Key validation failed: {e}")
        return False


# 2. Ollama Fallback (Internal use or alternative)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:e4b")

# 3. Server Config
PORT = int(os.getenv("PORT", "10880"))
HOST = os.getenv("HOST", "127.0.0.1")

# 4. Search & Vector Config
VECTOR_DIMENSION = int(os.getenv("VECTOR_DIMENSION", 768))

# ==========================================
# ⚙️ Internal System Configuration
# ==========================================

# --- Path Resolution Helpers ---

def get_logic_hive_home() -> Path:
    # Ensure we return an absolute path to avoid ambiguity in tests
    return Path(os.getenv("LOGICHIVE_HOME", str(Path.home() / ".logichive"))).resolve()

def get_data_dir() -> Path:
    # Only use /tmp/logic-hive for Knative services in production
    if os.getenv("K_SERVICE") is not None:
        return Path("/tmp/logic-hive")

    # Respect the resolved home directory
    data_dir = get_logic_hive_home() / "data"

    # Ensure it exists before returning (important for database initialization)
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        # Fallback to local ./data if home is unwritable, but log it
        logger.error(f"Config: Failed to create data directory at {data_dir}: {e}")

    return data_dir

def get_sqlite_db_path() -> str:
    return os.getenv("SQLITE_DB_PATH", str(get_data_dir() / "logichive.db"))

def _get_active_embedding_model_name() -> str:
    """現在の設定に基づいて有効なEmbeddingモデル名を返す"""
    provider = os.getenv("EMBEDDING_PROVIDER", EMBEDDING_PROVIDER).lower()
    if provider == "ollama":
        return os.getenv("OLLAMA_EMBEDDING_MODEL", OLLAMA_EMBEDDING_MODEL)
    elif provider == "fastembed":
        return os.getenv("FASTEMBED_MODEL", FASTEMBED_MODEL)
    else:
        return os.getenv("EMBEDDING_MODEL_ID", EMBEDDING_MODEL_ID)

def get_faiss_index_path() -> str:
    model_name = _get_active_embedding_model_name()
    safe_name = model_name.replace("/", "_").replace("\\", "_").replace(":", "_")
    default_path = str(get_data_dir() / f"faiss_{safe_name}.bin")
    return os.getenv("FAISS_INDEX_PATH", default_path)

def get_faiss_mapping_path() -> str:
    model_name = _get_active_embedding_model_name()
    safe_name = model_name.replace("/", "_").replace("\\", "_").replace(":", "_")
    default_path = str(get_data_dir() / f"faiss_mapping_{safe_name}.json")
    return os.getenv("FAISS_MAPPING_PATH", default_path)

def get_pool_base_dir() -> Path:
    return get_logic_hive_home() / "pools"

# Legacy support for static imports (will be updated over time)
LOGICHIVE_HOME = get_logic_hive_home()
DATA_DIR = get_data_dir()
SQLITE_DB_PATH = get_sqlite_db_path()
FAISS_INDEX_PATH = get_faiss_index_path()
FAISS_MAPPING_PATH = get_faiss_mapping_path()
POOL_BASE_DIR = get_pool_base_dir()

# LogicHive Quality Gate & Storage Thresholds
QUALITY_GATE_THRESHOLD = int(os.getenv("QUALITY_GATE_THRESHOLD", 70))
DEFAULT_VERIFICATION_TIMEOUT = int(os.getenv("DEFAULT_VERIFICATION_TIMEOUT", 60))
MAX_VERIFICATION_TIMEOUT = int(os.getenv("MAX_VERIFICATION_TIMEOUT", 120))

DESCRIPTION_MIN_LENGTH = int(os.getenv("DESCRIPTION_MIN_LENGTH", 10))

# Vector Search (FAISS) Config
FAISS_GHOST_REBUILD_THRESHOLD = int(os.getenv("FAISS_GHOST_REBUILD_THRESHOLD", 10))

# 5. Virtual Environment Pooling (Pre-warming)
ENABLE_ENV_POOLING = os.getenv("ENABLE_ENV_POOLING", "true").lower() == "true"
ENABLE_GPU = os.getenv("ENABLE_GPU", "false").lower() == "true"
POOL_MAX_SIZE = int(os.getenv("POOL_MAX_SIZE", "1"))  # default to 1 to save space

# Default specs for pre-warming
# Format: {spec_name: [list of critical packages]}
DEFAULT_POOL_SPECS = {
    "torch-cpu": ["torch", "numpy"],
    "torch-gpu": ["torch", "numpy"],  # GPU version is auto-detected and handled by uv
}

# 6. Execution Driver (Security Hardening)
# LogicHive defaults to local execution using uv/venv.
EXECUTION_DRIVER = "local"

# Legacy / Platform Compat
TRANSPORT = os.getenv("TRANSPORT", "http")
HUB_URL = os.getenv("HUB_URL", "https://function-store-hub-344411298688.asia-northeast1.run.app")
EXECUTION_MODE = os.getenv("EXECUTION_MODE", "auto")
