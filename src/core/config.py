import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Resolve base directory: frozen (executable) vs source (development)
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent.parent.parent.resolve()

PROJECT_ROOT = BASE_DIR

# --- .env loading strategy ---
# 1. Look in the same directory as the EXE or project root
# 2. Look in the user's home directory (~/.logichive/.env) as a fallback
HOME_DIR = Path.home() / ".logichive"
HOME_ENV = HOME_DIR / ".env"
LOCAL_ENV = BASE_DIR / ".env"

def _load_config():
    """Tiered configuration loading with prioritized path resolution."""
    config_source = "None (Using defaults/Env)"
    
    # Priority 1: Local .env (next to EXE or project root)
    if LOCAL_ENV.exists():
        load_dotenv(LOCAL_ENV)
        config_source = f"Local: {LOCAL_ENV}"
    
    # Priority 2: User Home fallback
    elif HOME_ENV.exists():
        load_dotenv(HOME_ENV)
        config_source = f"Home: {HOME_ENV}"
    
    # Default: Standard CWD-based loading or Environment variables
    else:
        load_dotenv()
        if os.getenv("GEMINI_API_KEY"):
            config_source = "System Environment Variables"
            
    return config_source

from src.core.logger import get_logger
logger = get_logger("config")

# ... (rest of code)
# Ensure home config directory exists
try:
    HOME_DIR.mkdir(parents=True, exist_ok=True)
except Exception as e:
    logger.error(f"Failed to create home config directory at {HOME_DIR}: {e}")



CONFIG_SOURCE = _load_config()

# Inform user about config status during startup (briefly)
if not getattr(sys, "frozen", False) or os.getenv("LOGICHIVE_DEBUG"):
    print(f"[*] LogicHive Configuration Source: {CONFIG_SOURCE}")

# ==========================================
# 🛡️ LogicHive: User Configuration Section
# ==========================================
# 機密情報や環境固有の設定を一箇所にまとめます。
# 必要に応じて環境変数での上書き(Override)も可能です。

# 1. AI & Models
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_TYPE = os.getenv("MODEL_TYPE", "gemini").lower()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/gemma-4-31b")
EMBEDDING_MODEL_ID = os.getenv("EMBEDDING_MODEL_ID", "models/gemini-embedding-2")
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "gemini").lower()
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
FASTEMBED_MODEL = os.getenv("FASTEMBED_MODEL", "nomic-ai/nomic-embed-text-v1.5")

def _validate_gemini_api_key(api_key):
    # Skip validation during pytest runs or testing environments to avoid breaking test suites
    if "pytest" in sys.modules or os.getenv("LOGICHIVE_TESTING") == "true":
        return True
    if not api_key:
        return False
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        # Attempt to list models to verify the key is valid (low overhead call)
        list(client.models.list(config={"page_size": 1}))
        return True
    except Exception as e:
        print(f"\n[ERROR] Gemini API Key validation failed: {e}")
        return False

# Validate configuration
if (MODEL_TYPE == "gemini" or EMBEDDING_PROVIDER == "gemini"):
    if not GEMINI_API_KEY:
        print("\n[WARNING] GEMINI_API_KEY is not set.")
        print("LogicHive requires a Gemini API Key to function in 'gemini' mode.")
        print("Please set the GEMINI_API_KEY environment variable or create a .env file.\n")
        raise ValueError("LogicHive requires a GEMINI_API_KEY when running in 'gemini' mode.")
    if not _validate_gemini_api_key(GEMINI_API_KEY):
        raise ValueError("LogicHive detected an invalid GEMINI_API_KEY. Please provide a valid key.")

# 2. Ollama Fallback (Internal use or alternative)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral-large-3:675b-cloud")

# 3. Server Config
PORT = int(os.getenv("PORT", "10880"))
HOST = os.getenv("HOST", "0.0.0.0")

# 4. Search & Vector Config
VECTOR_DIMENSION = int(os.getenv("VECTOR_DIMENSION", 768))

# ==========================================
# ⚙️ Internal System Configuration
# ==========================================

# Handle Cloud Run or other container environments
IS_CLOUD = os.getenv("K_SERVICE") is not None or os.name != "nt"

if IS_CLOUD:
    # Use /tmp for ALL transient operations in the cloud
    DATA_DIR = Path("/tmp/logic-hive")
else:
    # Local dev: Consolidate to storage/data at root
    DATA_DIR = BASE_DIR / "storage" / "data"

# Ensure transient directory exists
try:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
except Exception as e:
    print(f"[CRITICAL] Failed to create data directory {DATA_DIR}: {e}")

# SQLite Config
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", str(DATA_DIR / "logichive.db"))

# LogicHive Quality Gate & Storage Thresholds
QUALITY_GATE_THRESHOLD = int(os.getenv("QUALITY_GATE_THRESHOLD", 70))
DEFAULT_VERIFICATION_TIMEOUT = int(os.getenv("DEFAULT_VERIFICATION_TIMEOUT", 60))
MAX_VERIFICATION_TIMEOUT = int(os.getenv("MAX_VERIFICATION_TIMEOUT", 120))

# Backup Config (Opt-in)
# デフォルトは False (ローカルのみ) です。GitHub同期を行う場合は .env で true に設定してください。
ENABLE_AUTO_BACKUP = os.getenv("ENABLE_AUTO_BACKUP", "false").lower() == "true"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
DESCRIPTION_MIN_LENGTH = int(os.getenv("DESCRIPTION_MIN_LENGTH", 10))

# Vector Search (FAISS) Config
FAISS_GHOST_REBUILD_THRESHOLD = int(os.getenv("FAISS_GHOST_REBUILD_THRESHOLD", 10))
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", str(DATA_DIR / "faiss_index.bin"))
FAISS_MAPPING_PATH = os.getenv("FAISS_MAPPING_PATH", str(DATA_DIR / "faiss_mapping.json"))

# 5. Virtual Environment Pooling (Pre-warming)
ENABLE_ENV_POOLING = os.getenv("ENABLE_ENV_POOLING", "true").lower() == "true"
POOL_BASE_DIR = DATA_DIR / "pools"
POOL_MAX_SIZE = int(os.getenv("POOL_MAX_SIZE", "1"))  # per spec

# Default specs for pre-warming
# Format: {spec_name: [list of critical packages]}
DEFAULT_POOL_SPECS = {
    "torch-cpu": ["torch", "numpy"],
    "torch-gpu": ["torch", "numpy"],  # GPU version is auto-detected and handled by uv
}

# 6. Execution Driver (Security Hardening)
# "local" (uv/venv), "docker" (isolated container)
EXECUTION_DRIVER = os.getenv("EXECUTION_DRIVER", "local").lower()

# Legacy / Platform Compat
TRANSPORT = os.getenv("TRANSPORT", "http")
HUB_URL = os.getenv("HUB_URL", "https://function-store-hub-344411298688.asia-northeast1.run.app")
EXECUTION_MODE = os.getenv("EXECUTION_MODE", "auto")
