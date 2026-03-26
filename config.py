"""
Global configuration for the virtual world system.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

WORKSPACE = os.path.dirname(os.path.abspath(__file__))

# Paths
WORLDS_PATH = os.path.join(WORKSPACE, 'worlds')
DATA_PATH = os.path.join(WORKSPACE, 'data')
WEB_PATH = os.path.join(WORKSPACE, 'web')

# Ensure directories exist
os.makedirs(WORLDS_PATH, exist_ok=True)
os.makedirs(DATA_PATH, exist_ok=True)

# Display
MAX_DISPLAY_AGENTS = 2000
REFRESH_INTERVAL_SEC = 5

# Network
WEB_PORT = int(os.environ.get('WEB_PORT', '5001'))
API_PORT = int(os.environ.get('API_PORT', '5002'))
BIND_HOST = os.environ.get('BIND_HOST', '127.0.0.1')

# Security
_env_key = os.environ.get('YULONG_API_KEY', '')
if _env_key:
    API_KEY = _env_key
else:
    import secrets
    API_KEY = secrets.token_hex(16)
    print(f"[SECURITY] No YULONG_API_KEY set. Generated key: {API_KEY}")
    print(f"[SECURITY] Set YULONG_API_KEY env var for persistent key.")

# Engine
INITIAL_AGENT_COUNT = int(os.environ.get('AGENT_COUNT', '10000'))

# Volcengine Doubao LLM API
VOLCENGINE_API_KEY = os.environ.get('VOLCENGINE_API_KEY', '')
VOLCENGINE_MODEL = os.environ.get('VOLCENGINE_MODEL', 'doubao-seed-2.0-pro')
VOLCENGINE_ENDPOINT = os.environ.get('VOLCENGINE_ENDPOINT', 'https://ark.cn-beijing.volces.com/api/v3')

# LLM Decision Mode: 'rule_only' | 'local_llm' | 'cloud_llm'
LLM_MODE = os.environ.get('LLM_MODE', 'rule_only') if VOLCENGINE_API_KEY else 'rule_only'

if VOLCENGINE_API_KEY:
    print(f"[LLM] Volcengine Doubao API configured: {VOLCENGINE_MODEL}")
    print(f"[LLM] Mode: {LLM_MODE}")
else:
    print(f"[LLM] No API key set. Running in rule-only mode.")
