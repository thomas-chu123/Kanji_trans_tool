#!/bin/bash

# 日文文章轉換工具 - 啟動腳本
# 使用：bash run.sh

echo "🚀 日文文章轉換工具 - 啟動"
echo "================================"

# 檢查虛擬環境
if [ ! -d "venv" ]; then
    echo "❌ 未找到虛擬環境"
    echo "請先運行: bash setup.sh"
    exit 1
fi

# 激活虛擬環境
source venv/bin/activate

# 檢查 Python 依賴
python -c "import fastapi" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ 依賴未安裝"
    echo "請先運行: bash setup.sh"
    exit 1
fi

echo "✓ 環境已準備"
echo ""
echo "🌐 啟動應用..."
echo "訪問: http://localhost:8000"
echo "API 文檔: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止服務器"
echo "================================"
echo ""

# 啟動 FastAPI 開發服務器
python -m uvicorn app:app --host 0.0.0.0 --port 8888 --reload
