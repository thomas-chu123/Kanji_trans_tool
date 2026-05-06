#!/bin/bash

# 日文文章轉換工具 - 安裝腳本（PM2 部署版本）
# 適用於 macOS 和 Linux

echo "📦 日文文章轉換工具 - PM2 安裝程序"
echo "===================================="

# 檢查 Python 版本
python3 --version > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ 錯誤: 未找到 Python 3"
    echo "請先安裝 Python 3.8 或更高版本"
    exit 1
fi

echo "✓ 找到 Python："
python3 --version

# 檢查 Node.js 和 npm
echo ""
echo "🔍 檢查 Node.js 和 npm..."
node --version > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ 未找到 Node.js"
    echo "請先安裝 Node.js (https://nodejs.org/)"
    exit 1
fi

echo "✓ 找到 Node.js："
node --version

# 檢查 pm2
echo ""
echo "🔍 檢查 PM2..."
npm list -g pm2 > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "📥 全局安裝 PM2..."
    npm install -g pm2
    if [ $? -ne 0 ]; then
        echo "❌ PM2 安裝失敗"
        exit 1
    fi
fi

echo "✓ PM2 已安裝："
pm2 --version

# 創建虛擬環境
echo ""
echo "🔨 創建虛擬環境..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "❌ 虛擬環境創建失敗"
    exit 1
fi

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

echo "✓ 數據庫已初始化"

# 創建 ecosystem.config.js
echo ""
echo "📝 創建 PM2 配置文件..."
pm2 delete japan-dict-tool > /dev/null 2>&1

cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [
    {
      name: 'japan-dict-tool',
      script: 'run.sh',
      interpreter: 'sh',
      instances: 1,
      exec_mode: 'fork',
      env: {
        NODE_ENV: 'production'
      },
      error_file: 'logs/error.log',
      out_file: 'logs/out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      watch: false,
      ignore_watch: ['node_modules', 'venv', 'db', 'logs'],
      max_memory_restart: '500M',
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s'
    }
  ],
  deploy: {
    production: {
      user: process.env.DEPLOY_USER || 'ubuntu',
      host: process.env.DEPLOY_HOST || 'your-server.com',
      key: process.env.DEPLOY_KEY || '~/.ssh/id_rsa',
      ref: 'origin/main',
      repo: 'https://github.com/thomas-chu123/Kanji_trans_tool.git',
      path: '/var/www/japan_dict_tool',
      'post-deploy': 'bash setup.sh && pm2 startOrRestart ecosystem.config.js --env production'
    }
  }
};
EOF

echo "✓ 配置文件已創建"

# 創建日誌目錄
mkdir -p logs

# 啟動應用
echo ""
echo "🚀 啟動應用 (PM2)..."
pm2 start ecosystem.config.js

if [ $? -ne 0 ]; then
    echo "❌ PM2 啟動失敗"
    exit 1
fi

echo ""
echo "===================================="
echo "✅ 安裝和部署完成！"
echo "===================================="
echo ""
echo "📝 PM2 命令："
echo "  查看狀態: pm2 status"
echo "  查看日誌: pm2 logs japan-dict-tool"
echo "  重啟應用: pm2 restart japan-dict-tool"
echo "  停止應用: pm2 stop japan-dict-tool"
echo ""
echo "🌐 訪問應用："
echo "  http://localhost:8888"
echo "  API 文檔: http://localhost:8888/docs"
echo ""
echo "📦 遠程部署 (需要配置 DEPLOY_USER, DEPLOY_HOST, DEPLOY_KEY):"
echo "  pm2 deploy ecosystem.config.js production setup"
echo "  pm2 deploy ecosystem.config.js production"
echo ""
echo "💡 開機自啟動："
echo "  pm2 startup"
echo "  pm2 save"
