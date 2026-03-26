"""
Lightweight web server for serving static frontend files.
Proxies /api/* requests to the API server to avoid CORS issues.
"""
from flask import Flask, send_from_directory, request, Response, abort
import requests as http_requests
import os
from config import WEB_PATH, WEB_PORT, BIND_HOST, API_PORT, API_KEY, DATA_PATH

app = Flask(__name__, static_folder=WEB_PATH)

API_BASE = f'http://127.0.0.1:{API_PORT}'


@app.route('/')
def index():
    return send_from_directory(WEB_PATH, 'worldmap.html')


@app.route('/dashboard')
def dashboard():
    return send_from_directory(WEB_PATH, 'index.html')


@app.route('/demo')
def demo_page():
    return send_from_directory(WEB_PATH, 'demo.html')


@app.route('/templates')
def templates_page():
    return send_from_directory(WEB_PATH, 'templates.html')


@app.route('/reports')
def reports_page():
    return send_from_directory(WEB_PATH, 'reports.html')


@app.route('/console')
def console_page():
    return send_from_directory(WEB_PATH, 'console.html')


@app.route('/worldmap')
def worldmap_page():
    return send_from_directory(WEB_PATH, 'worldmap.html')


# ---------- Report file download & view ----------

# Content-Type mapping for report files
_REPORT_MIME = {
    '.html': 'text/html; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.md':   'text/markdown; charset=utf-8',
    '.txt':  'text/plain; charset=utf-8',
}


def _safe_report_filename(filename):
    """Validate filename: no path traversal, no path separators."""
    if '..' in filename or '/' in filename or '\\' in filename:
        abort(400, 'Invalid filename')
    return filename


@app.route('/reports/download/<filename>')
def reports_download(filename):
    """Download a report file from data/ directory."""
    filename = _safe_report_filename(filename)
    filepath = os.path.join(DATA_PATH, filename)
    if not os.path.isfile(filepath):
        abort(404, 'Report not found')
    ext = os.path.splitext(filename)[1].lower()
    mime = _REPORT_MIME.get(ext, 'application/octet-stream')
    return send_from_directory(DATA_PATH, filename,
                               mimetype=mime,
                               as_attachment=True,
                               download_name=filename)


@app.route('/reports/view/<filename>')
def reports_view(filename):
    """View an HTML report directly in the browser."""
    filename = _safe_report_filename(filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext != '.html':
        abort(400, 'Only .html reports can be viewed')
    filepath = os.path.join(DATA_PATH, filename)
    if not os.path.isfile(filepath):
        abort(404, 'Report not found')
    return send_from_directory(DATA_PATH, filename,
                               mimetype='text/html; charset=utf-8')


@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory(os.path.join(WEB_PATH, 'css'), filename)


@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory(os.path.join(WEB_PATH, 'js'), filename)


# API proxy — forward all /api/* requests to the API server
@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_proxy(path):
    # Map v4/v5-style paths to v1 API paths
    # Frontend calls /api/stats, API expects /api/v1/stats
    if path.startswith('v5/'):
        api_path = f'v1/{path[3:]}'
    elif not path.startswith('v1/'):
        api_path = f'v1/{path}'
    else:
        api_path = path
    url = f'{API_BASE}/api/{api_path}'
    try:
        # SSE streams need stream=True and no short timeout
        is_sse = 'events/stream' in path
        if request.method == 'GET':
            resp = http_requests.get(url, params=request.args,
                                     timeout=None if is_sse else 30,
                                     stream=is_sse,
                                     headers={'X-API-Key': API_KEY})
        else:
            resp = http_requests.request(
                request.method, url,
                json=request.get_json(silent=True),
                params=request.args,
                headers={'Content-Type': 'application/json',
                         'X-API-Key': API_KEY},
                timeout=60)

        # Special handling for SSE streams
        if 'text/event-stream' in resp.headers.get('Content-Type', ''):
            def generate():
                for chunk in resp.iter_content(chunk_size=None):
                    yield chunk
            return Response(generate(), mimetype='text/event-stream',
                          headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

        return Response(resp.content, status=resp.status_code,
                       content_type=resp.headers.get('Content-Type', 'application/json'))
    except http_requests.exceptions.ConnectionError:
        return Response('{"error": "API server not available"}', status=503,
                       content_type='application/json')
    except Exception as e:
        return Response(f'{{"error": "{str(e)}"}}', status=500,
                       content_type='application/json')


if __name__ == '__main__':
    print(f'Web server starting on http://{BIND_HOST}:{WEB_PORT}')
    app.run(host=BIND_HOST, port=WEB_PORT, debug=False, threaded=True)
