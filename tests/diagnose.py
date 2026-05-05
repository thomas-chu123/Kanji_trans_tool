#!/usr/bin/env python3
"""
诊断工具：追踪 POST /convert 请求的执行流程
"""

import sys
import time
import subprocess
from pathlib import Path

def test_with_direct_server():
    """直接启动服务器并发送请求"""
    print("\n" + "="*70)
    print("🔍 诊断模式：直接服务器测试")
    print("="*70)
    
    print("\n[步骤 1] 启动服务器（前台模式，1 秒后发送请求）...")
    
    # 启动服务器进程
    proc = subprocess.Popen(
        ["python3", "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", "8001"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    
    # 等待服务器启动
    time.sleep(2)
    
    print("[步骤 2] 发送测试请求...")
    
    # 发送请求
    import requests
    try:
        response = requests.post(
            "http://127.0.0.1:8001/convert",
            data={"text": "テスト"},
            allow_redirects=False,
            timeout=10
        )
        print(f"  HTTP 状态码: {response.status_code}")
        print(f"  重定向位置: {response.headers.get('Location', 'N/A')}")
    except Exception as e:
        print(f"  请求失败: {e}")
    
    # 收集服务器输出 3 秒
    print("\n[步骤 3] 收集服务器日志（等待 3 秒）...")
    time.sleep(3)
    
    print("\n[服务器输出]")
    print("-" * 70)
    
    # 读取 app.log 的最后部分
    try:
        result = subprocess.run(
            ["tail", "-30", "app.log"],
            capture_output=True,
            text=True
        )
        print(result.stdout)
    except:
        pass
    
    print("-" * 70)
    
    # 终止服务器
    proc.terminate()
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()
    
    print("\n[分析结果]")
    print("检查以下内容是否在日志中出现：")
    print("  1. '🚨 CONVERT_TEXT ENTRY POINT' - 入口点日志")
    print("  2. '📝 開始轉換' - 开始转换日志")
    print("  3. '⚡ DEBUG: convert_text 函数被调用' - 调试日志")
    print("  4. '🚨 BEFORE TRANSLATE_TO_CHINESE' - 翻译前日志")
    print("  5. '🚨 AFTER TRANSLATE_TO_CHINESE' - 翻译后日志")

def check_import_path():
    """检查导入路径"""
    print("\n" + "="*70)
    print("🔍 检查导入路径")
    print("="*70)
    
    import sys
    print(f"\n当前工作目录: {Path.cwd()}")
    print(f"\nPython 路径:")
    for p in sys.path[:5]:
        print(f"  - {p}")
    
    print(f"\n是否存在 app.py: {Path('app.py').exists()}")
    print(f"是否存在 processors 包: {Path('processors').exists()}")

def main():
    import os
    os.chdir("/Users/skynet/PycharmProjects/japan_dict_tool")
    
    check_import_path()
    
    # 注意：不能同时启动两个 Uvicorn 实例在同一端口
    # test_with_direct_server()
    
    print("\n" + "="*70)
    print("✅ 诊断工具完成")
    print("="*70)
    print("\n建议:")
    print("1. 检查 app.py 的 convert_text 函数是否真的被装饰为 @app.post('/convert')")
    print("2. 检查是否有其他地方定义了相同的路由")
    print("3. 检查 PM2 是否确实运行了最新版本的代码")
    print("4. 检查日志是否被重定向到其他地方")

if __name__ == "__main__":
    main()
