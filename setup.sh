#!/bin/bash

# 日文文章轉換工具 - 安裝腳本
# 適用於 macOS 和 Linux

echo "📦 日文文章轉換工具 - 安裝程序"
echo "================================"

# 檢查 Python 版本
python3 --version > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ 錯誤: 未找到 Python 3"
    echo "請先安裝 Python 3.8 或更高版本"
    exit 1
fi

echo "✓ 找到 Python："
python3 --version

# 創建虛擬環境
echo ""
echo "🔨 創建虛擬環境..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "❌ 虛擬環境創建失敗"
    exit 1
fi

# 激活虛擬環境
echo "✓ 虛擬環境已創建"
echo ""
echo "📥 激活虛擬環境並安裝依賴..."

source venv/bin/activate

# 升級 pip
pip install --upgrade pip setuptools wheel -q

# 安裝依賴
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ 依賴安裝失敗"
    exit 1
fi

echo "✓ 依賴已安裝"

# 初始化數據庫
echo ""
echo "🗄️  初始化數據庫..."
python db/init_db.py

if [ $? -ne 0 ]; then
    echo "❌ 數據庫初始化失敗"
    exit 1
fi

echo ""
echo "================================"
echo "✅ 安裝完成！"
echo "================================"
echo ""
echo "📝 後續步驟："
echo "1. 激活虛擬環境: source venv/bin/activate"
echo "2. 啟動應用: python -m uvicorn app:app --reload"
echo "3. 訪問: http://localhost:8000"
echo ""
echo "💡 或直接運行: bash run.sh"
