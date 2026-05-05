# 🇯🇵 日文文章轉換工具

使用 **FastAPI + PyKakasi + Tailwind CSS** 構建的日文文章轉換應用。輸入日文文本，即時顯示假名讀音和羅馬音拼音，幫助使用者了解如何打字。

## ✨ 功能特性

- 📝 **即時轉換**：輸入日文文本，實時顯示假名和羅馬音
- 📁 **文件支持**：支持上傳 .txt 和 .pdf 文件
- 💾 **下載功能**：將結果導出為 HTML 文件
- 📜 **轉換歷史**：自動保存所有轉換記錄
- ⭐ **收藏功能**：保存重要的轉換結果
- 🔍 **搜索功能**：快速查找歷史記錄
- 🎨 **美觀界面**：使用 Tailwind CSS 的響應式設計

## 🚀 快速開始

### 前置要求

- **Python 3.8+**
- **macOS / Linux**（Windows 用戶建議使用 WSL2）

### 安裝

**步驟 1：一鍵安裝**

```bash
cd /Users/skynet/PycharmProjects/japan_dict_tool
bash setup.sh
```

這個腳本會：
1. 創建虛擬環境
2. 安裝所有依賴
3. 初始化數據庫

### 啟動應用

**方法 1：使用啟動腳本（推薦）**

```bash
bash run.sh
```

**方法 2：手動啟動**

```bash
source venv/bin/activate
python -m uvicorn app:app --reload
```

**方法 3：生產環境**

```bash
source venv/bin/activate
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

### 訪問應用

打開瀏覽器訪問：

- **主應用**：http://localhost:8000
- **API 文檔**：http://localhost:8000/docs
- **ReDoc**：http://localhost:8000/redoc

## 📖 使用指南

### 基本使用

1. **輸入日文文本**
   - 在文本框中粘貼或輸入日文文本
   - 或點擊「上傳文件」上傳 .txt/.pdf 文件

2. **查看結果**
   - 點擊「開始轉換」
   - 上方顯示假名讀音（藍色小字）
   - 下方顯示羅馬音拼音

3. **操作結果**
   - 📋 複製：複製結果到剪貼板
   - 💾 HTML：下載為 HTML 文件
   - ⭐ 收藏：保存重要結果
   - ↩️ 返回：重新編輯文本

### 高級功能

- **歷史記錄**：查看所有轉換記錄，支持搜索
- **我的收藏**：查看收藏的轉換，支持添加筆記和標籤
- **統計信息**：查看轉換統計數據

## 🏗️ 項目結構

```
japan_dict_tool/
├── app.py                    # FastAPI 主應用
├── requirements.txt          # Python 依賴
├── setup.sh                  # 安裝腳本
├── run.sh                    # 啟動腳本
│
├── processors/               # 業務邏輯層
│   ├── furigana.py          # PyKakasi 集成
│   ├── romanization.py      # 羅馬音轉換
│   └── storage.py           # 數據庫操作
│
├── templates/                # Jinja2 模板
│   ├── base.html            # 基礎模板
│   ├── index.html           # 主輸入頁面
│   ├── results.html         # 結果頁面
│   ├── history.html         # 歷史記錄
│   ├── favorites.html       # 收藏頁面
│   └── error.html           # 錯誤頁面
│
├── static/                   # 靜態文件
│   ├── css/
│   │   └── custom.css       # 自定義 CSS
│   └── js/
│       └── main.js          # 前端 JavaScript
│
├── db/                       # 數據庫
│   ├── init_db.py           # 初始化腳本
│   └── translations.db      # SQLite 數據庫
│
├── docs/                     # 文檔
│   ├── design_guide.md      # 設計指南
│   ├── api_endpoints.md     # API 文檔
│   └── setup_guide.md       # 安裝指南
│
└── tests/                    # 測試代碼（待實現）
    ├── test_furigana.py
    ├── test_api.py
    └── test_storage.py
```

## 🔌 API 端點

### 前端路由

| 路徑 | 方法 | 描述 |
|------|------|------|
| `/` | GET | 主輸入頁面 |
| `/results/{id}` | GET | 轉換結果頁面 |
| `/history` | GET | 歷史記錄頁面 |
| `/favorites` | GET | 收藏頁面 |

### API 端點

| 路徑 | 方法 | 描述 |
|------|------|------|
| `/convert` | POST | 轉換日文文本 |
| `/api/favorite` | POST | 標記為收藏 |
| `/api/favorite/{id}` | DELETE | 取消收藏 |
| `/api/stats` | GET | 獲取統計信息 |
| `/health` | GET | 健康檢查 |
| `/download/html/{id}` | GET | 下載結果為 HTML |

## 🛠️ 故障排除

### PyKakasi 初始化失敗

**症狀**：啟動時出現 "PyKakasi 未安裝" 或 "初始化失敗"

**解決方案**：

```bash
# 重新安裝 PyKakasi
pip install --upgrade pykakasi

# 或使用 conda（如有）
conda install -c conda-forge pykakasi
```

### 文件上傳失敗

**症狀**：上傳文件時出現編碼錯誤

**解決方案**：
- 確保文件是 UTF-8 編碼
- 對於 PDF，建議使用文本層清晰的 PDF
- 文件大小不超過 5MB

### 數據庫連接錯誤

**症狀**：啟動時出現 "數據庫連接失敗"

**解決方案**：

```bash
# 重新初始化數據庫
python db/init_db.py

# 或刪除舊數據庫並重新創建
rm db/translations.db
python db/init_db.py
```

## 📊 技術棧

| 層級 | 技術 | 版本 |
|------|------|------|
| **後端框架** | FastAPI | 0.104.1 |
| **服務器** | Uvicorn | 0.24.0 |
| **模板引擎** | Jinja2 | 3.1.2 |
| **日文處理** | PyKakasi | 2.3.0 |
| **形態分析** | Fugashi | 1.5.2 |
| **字符轉換** | jaconv | 0.3.4 |
| **前端框架** | Tailwind CSS | CDN |
| **數據庫** | SQLite 3 | - |
| **HTTP 客戶端** | aiofiles | 23.2.1 |

## 🚀 性能指標

| 操作 | 預期時間 |
|------|---------|
| 小文本轉換 (< 500 字) | < 1 秒 |
| 中等文本轉換 (500-5000 字) | < 5 秒 |
| 大文本轉換 (5000-100K 字) | < 30 秒 |
| 文件上傳 (< 5MB) | < 10 秒 |

## 🔒 安全性

- ✅ 輸入驗證（文本長度限制 100K 字）
- ✅ 文件大小限制（5MB）
- ✅ SQL 注入防護（參數化查詢）
- ✅ XSS 防護（自動轉義 HTML）
- ✅ 異常錯誤處理

## 🎯 未來計劃

- [ ] 移動應用支持（React Native）
- [ ] 多語言支持（中文、韓文）
- [ ] 自定義字典導入
- [ ] 詞頻分析
- [ ] 批量轉換
- [ ] API 認證（若部署為公開服務）
- [ ] 深色模式

## 📝 許可證

MIT License

## 👨‍💻 開發者

創建於 2026 年 5 月

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request

## 📧 聯繫方式

如有問題或建議，請在 GitHub 上提交 Issue

---

**Made with ❤️ using FastAPI + Jinja2 + Tailwind CSS**
