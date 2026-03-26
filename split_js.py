import sys, re
sys.stdout.reconfigure(encoding='utf-8')

with open('web/js/all.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Find key function/section boundaries
def find_pos(pattern):
    m = re.search(pattern, js)
    return m.start() if m else -1

# Identify sections
sse_start = find_pos(r'// ===== SSE')
if sse_start == -1:
    sse_start = find_pos(r'let _evtSource')

search_start = find_pos(r'// ===== Search')
if search_start == -1:
    search_start = find_pos(r'function populateFilters')

region_start = find_pos(r'// ===== Region Popup')
if region_start == -1:
    region_start = find_pos(r'function toggleRegionPopup')

trend_start = find_pos(r'// ===== Trend Metrics')
if trend_start == -1:
    trend_start = find_pos(r'const TREND_METRICS')

rose_start = find_pos(r'function renderPie')
init_trend_start = find_pos(r'function initTrend')
mock_trend_start = find_pos(r'function mockTrend')
load_events_start = find_pos(r'async function loadEvents')
render_ev_start = find_pos(r'function renderEv')
flt_ev_start = find_pos(r'function fltEv')
mock_events_start = find_pos(r'function mockEvents')

print(f'SSE: {sse_start}')
print(f'Search: {search_start}')
print(f'Region: {region_start}')
print(f'Trend metrics: {trend_start}')
print(f'Rose: {rose_start}')
print(f'initTrend: {init_trend_start}')
print(f'mockTrend: {mock_trend_start}')
print(f'loadEvents: {load_events_start}')
print(f'renderEv: {render_ev_start}')
print(f'fltEv: {flt_ev_start}')
print(f'mockEvents: {mock_events_start}')
print(f'Total JS: {len(js)}')
