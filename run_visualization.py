"""
御龙军虚拟世界 - 可视化系统启动脚本
版本：v2.0 (整合版)
创建时间：2026-03-17

启动 Flask Web 可视化和 API 服务
"""

import sys
import os
import threading
import webbrowser

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from visualizer_v3 import app as visualizer_app
from api_server import app as api_app

def run_visualizer():
    """运行可视化服务"""
    print("🌐 启动可视化服务...")
    visualizer_app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)

def run_api():
    """运行 API 服务"""
    print("🔌 启动 API 服务...")
    api_app.run(host='0.0.0.0', port=5002, debug=False, threaded=True)

def open_browser():
    """自动打开浏览器"""
    import time
    time.sleep(2)  # 等待服务启动
    webbrowser.open('http://localhost:5001')
    print("📊 可视化界面：http://localhost:5001")
    print("🔌 API 文档：http://localhost:5002/api/v1/docs")

if __name__ == '__main__':
    print("=" * 60)
    print("🐉 御龙军虚拟世界 - 可视化系统 v2.0")
    print("=" * 60)
    
    # 启动线程
    viz_thread = threading.Thread(target=run_visualizer, daemon=True)
    api_thread = threading.Thread(target=run_api, daemon=True)
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    
    print("\n🚀 启动服务...")
    viz_thread.start()
    api_thread.start()
    browser_thread.start()
    
    # 主线程保持运行
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 正在关闭服务...")
