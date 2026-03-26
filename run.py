"""
One-click launcher for the virtual world system.
Starts both API server (engine + data) and Web server (frontend).
"""
import sys
import os
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import WEB_PORT, API_PORT, BIND_HOST, INITIAL_AGENT_COUNT


def run_api_server():
    from api_server import app as api_app, init_engine
    print(f'[API] Initializing engine with {INITIAL_AGENT_COUNT} agents...')
    init_engine(INITIAL_AGENT_COUNT)
    print(f'[API] Starting on http://{BIND_HOST}:{API_PORT}')
    api_app.run(host=BIND_HOST, port=API_PORT, debug=False, threaded=True)


def run_web_server():
    time.sleep(2)  # Wait for API server to start
    from web_server import app as web_app
    print(f'[WEB] Starting on http://{BIND_HOST}:{WEB_PORT}')
    web_app.run(host=BIND_HOST, port=WEB_PORT, debug=False, threaded=True)


def open_browser():
    time.sleep(5)
    import webbrowser
    url = f'http://localhost:{WEB_PORT}'
    webbrowser.open(url)
    print(f'[BROWSER] Opened {url}')


if __name__ == '__main__':
    print('=' * 60)
    print('  Yulong Virtual Agent World')
    print('  Dual-service architecture')
    print('=' * 60)
    print(f'  Web:    http://{BIND_HOST}:{WEB_PORT}')
    print(f'  API:    http://{BIND_HOST}:{API_PORT}')
    print(f'  Agents: {INITIAL_AGENT_COUNT}')
    print('=' * 60)

    api_thread = threading.Thread(target=run_api_server, daemon=True)
    web_thread = threading.Thread(target=run_web_server, daemon=True)

    api_thread.start()
    web_thread.start()

    # Auto-open browser unless --no-browser flag
    if '--no-browser' not in sys.argv:
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('\nShutting down...')
