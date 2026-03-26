"""
One-click launcher for the virtual world system.
Starts both API server (engine + data) and Web server (frontend).

Fixed threading for Windows: initialize first, then start both servers correctly.
"""
import sys
import os
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import WEB_PORT, API_PORT, BIND_HOST, INITIAL_AGENT_COUNT

print('=' * 60)
print('  VanX · 万象界')
print('  Dual-service architecture')
print('=' * 60)
print(f'  Web:    http://{BIND_HOST}:{WEB_PORT}')
print(f'  API:    http://{BIND_HOST}:{API_PORT}')
print(f'  Agents: {INITIAL_AGENT_COUNT}')
print('=' * 60)

# Pre-initialize everything BEFORE starting servers
# This fixes Windows threading exit bug
from api_server import app as api_app, init_engine
print(f'[API] Initializing engine with {INITIAL_AGENT_COUNT} agents...')
init_engine(INITIAL_AGENT_COUNT)

# Auto-open browser unless --no-browser
if '--no-browser' not in sys.argv:
    # Wait a second then open
    time.sleep(1)
    import webbrowser
    url = f'http://localhost:{WEB_PORT}'
    webbrowser.open(url)
    print(f'[BROWSER] Opened {url}')

# Start API server in non-daemon thread (so it doesn't get killed when main thread runs web server)
def run_api_server():
    from api_server import app as api_app
    print(f'[API] Starting on http://{BIND_HOST}:{API_PORT}')
    api_app.run(host=BIND_HOST, port=API_PORT, debug=False, threaded=True)

api_thread = threading.Thread(target=run_api_server)
# NOT daemon = True → keeps process alive
api_thread.start()

# Give API server time to start
time.sleep(0.5)

# Start web server in main thread (will never return, keeps process alive)
from web_server import app as web_app
print(f'[WEB] Starting on http://{BIND_HOST}:{WEB_PORT}')
web_app.run(host=BIND_HOST, port=WEB_PORT, debug=False, threaded=True)
