# 日文文章轉換網站 - 設計指南

## 概述

本項目構建一個 **FastAPI + Jinja2 + Tailwind CSS** 的統一應用，用戶輸入日文文章後，網站在日文上方顯示假名讀音（furigana），下方顯示羅馬音拼音，方便使用者了解如何打字。

**關鍵特性**：
- 前後端同一個應用，無需分離（使用 Jinja2 模板後端渲染）
- 支持文本框輸入和文件上傳（.txt、.pdf）
- 多種輸出格式（網頁實時顯示、下載為 HTML/PDF）
- 轉換記錄存儲 + 收藏功能
- 本地部署（localhost:8000）

---

## 技術棧決策

| 層級 | 選擇 | 依據 |
|------|------|------|
| **後端框架** | FastAPI | 簡單快速、原生支持 Jinja2、異步、自動 API 文檔 |
| **前端模板** | Jinja2 + Tailwind CSS | 後端渲染 HTML，無需分離前端；Tailwind 開發高效 |
| **日文處理主庫** | PyKakasi 2.3.0+ | 最新維護、直接輸出假名+羅馬音、易用性最高 |
| **日文分詞備選** | Fugashi + unidic-lite | 高性能形態分析，用於複雜分詞場景 |
| **字符規範化** | jaconv | 平假名↔片假名、半角↔全角轉換 |
| **數據庫** | SQLite 3 | 無依賴、無需配置、適合本地應用 |
| **CSS 框架** | Tailwind CSS (CDN) | 實用優先、快速開發、直接在 HTML 中使用 |
| **HTML 假名渲染** | Ruby 標籤 (`<ruby>`) | HTML 標準方案、支持 PDF 導出、國際標準 |

---

## 應用架構

### 目錄結構

```
japan_dict_tool/
├── app.py                          # FastAPI 主應用入口
├── requirements.txt                # Python 依賴清單
├── setup.sh                        # 初始化腳本（macOS/Linux）
├── run.sh                          # 啟動腳本
│
├── processors/                     # 核心業務邏輯層
│   ├── __init__.py
│   ├── furigana.py                # PyKakasi 集成 + Ruby HTML 生成
│   ├── romanization.py            # 羅馬音轉換邏輯
│   └── storage.py                 # SQLite CRUD 操作
│
├── templates/                      # Jinja2 模板
│   ├── base.html                  # 基礎模板（導航、頁腳、Tailwind 配置）
│   ├── index.html                 # 主輸入頁面
│   └── results.html               # 結果顯示頁面
│
├── static/                         # 靜態文件
│   ├── css/
│   │   └── custom.css             # 自定義 CSS（補充 Tailwind）
│   └── js/
│       └── main.js                # 前端交互邏輯（可選）
│
├── db/                             # 數據庫相關
│   ├── init_db.py                 # 數據庫初始化腳本
│   └── translations.db            # SQLite 數據庫文件（運行時生成）
│
├── docs/                           # 文檔
│   ├── design_guide.md            # 本文件
│   ├── api_endpoints.md           # API 文檔
│   └── setup_guide.md             # 安裝指南
│
└── tests/                          # 測試代碼
    ├── test_furigana.py           # 單元測試：文本處理
    ├── test_api.py                # 集成測試：API 端點
    └── test_storage.py            # 單元測試：數據庫操作
```

### 核心組件

#### 1. **FastAPI 主應用** (`app.py`)
**職責**：HTTP 請求路由、模板渲染、靜態文件服務

**關鍵路由**：
- `GET /` - 渲染主輸入頁面
- `POST /convert` - 處理文本轉換請求
- `POST /convert/file` - 文件上傳轉換
- `GET /history` - 獲取轉換歷史
- `POST /favorite` - 標記為收藏
- `GET /download/html` - 下載轉換結果為 HTML
- `GET /download/pdf` - 下載轉換結果為 PDF
- `GET /api/docs` - FastAPI 自動生成的 API 文檔

**配置**：
```python
# Jinja2 模板路徑配置
templates = Jinja2Templates(directory="templates")

# 靜態文件路徑配置
app.mount("/static", StaticFiles(directory="static"), name="static")

# CORS（若有前端跨域需求）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["localhost:*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 2. **文本處理引擎** (`processors/furigana.py`)
**職責**：日文文本轉換核心邏輯

**主要函數**：

```python
def initialize_kakasi():
    """
    初始化 PyKakasi 實例（應用啟動時調用，緩存全局）
    防止每次請求都重新初始化
    """

def process_text(text: str) -> List[Dict]:
    """
    輸入日文文本，輸出結構化數據
    
    Args:
        text: 日文文本（支持混合假名、漢字、符號）
    
    Returns:
        結構化列表，每項包含：
        {
            "original": "日本",      # 原文
            "hiragana": "にほん",    # 假名形式
            "romanji": "nihon",      # 羅馬音（Hepburn 式）
            "type": "kanji"          # 詞類：kanji / hiragana / katakana / symbol / number / space
        }
    
    Raises:
        ValueError: 文本為空或不是字符串
    """

def generate_ruby_html(processed_data: List[Dict]) -> str:
    """
    將結構化數據轉換為 HTML Ruby 標籤
    
    Args:
        processed_data: process_text() 的輸出
    
    Returns:
        HTML 字符串，格式示例：
        <div class="ruby-container">
            <ruby>日本<rp>（</rp><rt>にほん</rt><rp>）</rp></ruby>
            <div class="romanji">nihon</div>
        </div>
    
    特殊處理：
    - 連續的假名：保持原樣，不添加 Ruby
    - 符號/數字：直接輸出
    - 空格：保留
    """

def handle_kanji_sequences(text: str) -> str:
    """
    處理漢字序列，確保相鄰漢字的假名正確分組
    
    示例：
    輸入: "東京都"
    輸出: 
        <ruby>東<rt>とう</rt></ruby><ruby>京<rt>きょう</rt></ruby><ruby>都<rt>と</rt></ruby>
    """
```

**邊界情況處理**：
- 空文本：返回空列表
- 純假名：輸出不變，type 為 "hiragana"
- 混合日英：英文保持原樣，type 為 "symbol"
- 特殊符號：保持原樣，type 為 "symbol"
- 數字：保持原樣，type 為 "number"
- 換行/空格：保留

#### 3. **羅馬音轉換** (`processors/romanization.py`)
**職責**：多種羅馬音標準支持

**支持的標準**：
- **Hepburn 式（推薦）**：最廣泛使用，PyKakasi 默認
  - 例：しゃ → sha、ち → chi、つ → tsu
- **訓令式**：日本官方標準（備用）
  - 例：しゃ → sya、ち → ti、つ → tu
- **日本式**：專業人士使用（備用）
  - 例：しゃ → sya、ち → tti、つ → tu

**主要函數**：
```python
def convert_to_hepburn(hiragana: str) -> str:
    """Hiragana → Hepburn 羅馬音（PyKakasi 直接支持）"""

def normalize_romanization(romanji: str) -> str:
    """標準化羅馬音輸出（移除多餘空格、統一大小寫）"""

def handle_long_vowels(romanji: str, style: str = "hepburn") -> str:
    """
    處理長音
    - Hepburn：おう → ō，うう → ū
    - 簡化（推薦 Web 用）：おう → ou，うう → uu
    """
```

**設計決策**：
- 預設使用 Hepburn 式（易學易用）
- Web 版本可選擇長音簡化（ou/uu）以便打字
- 保留 romkan 庫作為備選（防止 PyKakasi 失效）

#### 4. **數據庫操作層** (`processors/storage.py`)
**職責**：SQLite 數據持久化

**表結構**：

```sql
-- 轉換記錄表
CREATE TABLE translations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    input_text TEXT NOT NULL,
    output_html TEXT NOT NULL,
    processed_data TEXT,  -- JSON 格式，便於再編輯
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 收藏表
CREATE TABLE favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    translation_id INTEGER UNIQUE,
    notes TEXT,
    tags TEXT,  -- 逗號分隔，如 "敬語,文學"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(translation_id) REFERENCES translations(id) ON DELETE CASCADE
);

-- 索引
CREATE INDEX idx_translations_created_at ON translations(created_at DESC);
CREATE INDEX idx_favorites_tags ON favorites(tags);
```

**主要函數**：
```python
def init_db():
    """初始化數據庫、創建表"""

def save_translation(input_text: str, output_html: str, processed_data: List[Dict]) -> int:
    """保存轉換記錄，返回 ID"""

def get_history(limit: int = 20, offset: int = 0) -> List[Dict]:
    """獲取最近的轉換記錄（分頁）"""

def mark_favorite(translation_id: int, notes: str = "", tags: str = "") -> bool:
    """標記為收藏"""

def unmark_favorite(translation_id: int) -> bool:
    """取消收藏"""

def get_favorites(limit: int = 50) -> List[Dict]:
    """獲取所有收藏"""

def search_history(keyword: str, limit: int = 20) -> List[Dict]:
    """按輸入文本搜索歷史記錄"""

def delete_translation(translation_id: int) -> bool:
    """刪除記錄"""
```

**連接池**：
- 使用 `sqlite3.connect()` 的 `check_same_thread=False` 以支持多線程（FastAPI 默認）
- 考慮使用 `aiosqlite` 進行異步操作（若性能成為瓶頸）

---

## 前端設計

### UI/UX 原則

1. **極簡主義**：最少化用戶操作步驟
2. **實時反饋**：轉換結果立即顯示，無重載
3. **可訪問性**：支持鍵盤快捷鍵、大字體
4. **響應式**：適配桌面、平板、手機

### 頁面設計

#### **Base 模板** (`templates/base.html`)
```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}日文文章轉換工具{% endblock %}</title>
    
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    
    {% block extra_head %}{% endblock %}
</head>
<body class="bg-gradient-to-br from-blue-50 to-indigo-100 min-h-screen">
    <!-- 導航欄 -->
    <nav class="bg-white shadow">
        <div class="max-w-4xl mx-auto px-4 py-4 flex justify-between items-center">
            <h1 class="text-2xl font-bold text-indigo-600">日文轉換</h1>
            <div class="space-x-4">
                <a href="/" class="text-gray-600 hover:text-indigo-600">首頁</a>
                <a href="/history" class="text-gray-600 hover:text-indigo-600">歷史</a>
            </div>
        </div>
    </nav>

    <!-- 主內容 -->
    <main class="max-w-4xl mx-auto px-4 py-8">
        {% block content %}{% endblock %}
    </main>

    <!-- 頁腳 -->
    <footer class="bg-white mt-12 border-t">
        <div class="max-w-4xl mx-auto px-4 py-6 text-center text-gray-500 text-sm">
            <p>© 2026 日文文章轉換工具 | 使用 FastAPI + PyKakasi</p>
        </div>
    </footer>

    {% block extra_script %}{% endblock %}
</body>
</html>
```

#### **主輸入頁面** (`templates/index.html`)
```html
{% extends "base.html" %}

{% block content %}
<div class="bg-white rounded-lg shadow-lg p-8">
    <!-- 標題 & 說明 -->
    <h2 class="text-3xl font-bold text-gray-800 mb-2">日文文章轉換</h2>
    <p class="text-gray-600 mb-6">輸入日文文章，即時顯示假名讀音與羅馬音</p>

    <!-- 輸入表單 -->
    <form method="post" action="/convert" id="convertForm" class="space-y-4">
        <!-- 文本輸入框 -->
        <div>
            <label for="inputText" class="block text-sm font-medium text-gray-700 mb-2">
                日文文本
            </label>
            <textarea 
                id="inputText" 
                name="text" 
                rows="8"
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
                placeholder="粘貼或輸入日文文本..."
            ></textarea>
            <div class="mt-2 text-sm text-gray-500">
                字數：<span id="charCount">0</span>
            </div>
        </div>

        <!-- 文件上傳（可選） -->
        <div class="border-t pt-4">
            <label for="fileUpload" class="block text-sm font-medium text-gray-700 mb-2">
                或上傳文件 (.txt, .pdf)
            </label>
            <input 
                type="file" 
                id="fileUpload" 
                name="file" 
                accept=".txt,.pdf"
                class="block w-full text-sm text-gray-500
                    file:mr-4 file:py-2 file:px-4
                    file:rounded-full file:border-0
                    file:text-sm file:font-semibold
                    file:bg-indigo-50 file:text-indigo-700
                    hover:file:bg-indigo-100"
            />
        </div>

        <!-- 選項 -->
        <div class="border-t pt-4 space-y-3">
            <div class="flex items-center">
                <input 
                    type="checkbox" 
                    id="longVowelSimplify" 
                    name="simplify_long_vowels"
                    class="w-4 h-4 text-indigo-600 rounded focus:ring-2 focus:ring-indigo-500"
                    checked
                />
                <label for="longVowelSimplify" class="ml-2 text-sm text-gray-700">
                    羅馬音簡化長音 (ou→ou, uu→uu，便於打字)
                </label>
            </div>
        </div>

        <!-- 按鈕 -->
        <div class="flex gap-4 pt-4">
            <button 
                type="submit" 
                class="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-6 rounded-lg transition"
            >
                🔄 轉換
            </button>
            <button 
                type="reset" 
                class="px-6 py-3 bg-gray-200 hover:bg-gray-300 text-gray-700 font-bold rounded-lg transition"
            >
                清空
            </button>
        </div>
    </form>
</div>

<!-- 最近轉換記錄預覽 -->
{% if recent_translations %}
<div class="bg-white rounded-lg shadow-lg p-8 mt-8">
    <h3 class="text-xl font-bold text-gray-800 mb-4">最近轉換</h3>
    <ul class="space-y-2 max-h-48 overflow-y-auto">
        {% for item in recent_translations[:5] %}
        <li class="text-sm text-gray-700 pb-2 border-b hover:bg-gray-50 p-2 cursor-pointer">
            <span class="text-gray-500">{{ item.created_at }}</span>
            <p class="text-gray-600">{{ item.input_text[:80] }}...</p>
        </li>
        {% endfor %}
    </ul>
    <a href="/history" class="text-indigo-600 hover:text-indigo-700 text-sm mt-4 inline-block">查看全部 →</a>
</div>
{% endif %}

<!-- 客戶端 JavaScript -->
<script>
    // 字數計算
    document.getElementById('inputText').addEventListener('input', function() {
        document.getElementById('charCount').textContent = this.value.length;
    });

    // 文本輸入與文件上傳互斥
    document.getElementById('inputText').addEventListener('input', function() {
        if (this.value.trim()) {
            document.getElementById('fileUpload').value = '';
        }
    });

    document.getElementById('fileUpload').addEventListener('change', function() {
        if (this.value) {
            document.getElementById('inputText').value = '';
        }
    });

    // 表單驗證
    document.getElementById('convertForm').addEventListener('submit', function(e) {
        const text = document.getElementById('inputText').value.trim();
        const file = document.getElementById('fileUpload').value;
        if (!text && !file) {
            e.preventDefault();
            alert('請輸入文本或選擇文件');
        }
    });
</script>
{% endblock %}
```

#### **結果顯示頁面** (`templates/results.html`)
```html
{% extends "base.html" %}

{% block content %}
<div class="space-y-6">
    <!-- Ruby 文本顯示 -->
    <div class="bg-white rounded-lg shadow-lg p-8">
        <h2 class="text-2xl font-bold text-gray-800 mb-4">轉換結果</h2>
        
        <!-- Ruby 容器 -->
        <div class="bg-gray-50 p-6 rounded-lg border-2 border-indigo-200 font-serif text-lg leading-loose">
            {{ result_html | safe }}
        </div>

        <!-- 複製按鈕 -->
        <div class="flex gap-4 mt-6">
            <button 
                onclick="copyToClipboard()" 
                class="flex-1 bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-lg transition"
            >
                📋 複製結果
            </button>
            
            <button 
                onclick="downloadHTML()" 
                class="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg transition"
            >
                💾 下載 HTML
            </button>
            
            <button 
                onclick="downloadPDF()" 
                class="flex-1 bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded-lg transition"
            >
                📄 下載 PDF
            </button>

            {% if not is_favorite %}
            <button 
                onclick="markFavorite()" 
                class="flex-1 bg-yellow-600 hover:bg-yellow-700 text-white font-bold py-2 px-4 rounded-lg transition"
            >
                ⭐ 收藏
            </button>
            {% else %}
            <button 
                onclick="unmarkFavorite()" 
                class="flex-1 bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded-lg transition"
            >
                ✓ 已收藏
            </button>
            {% endif %}
        </div>

        <!-- 返回編輯 -->
        <div class="mt-6">
            <a href="/" class="inline-block text-indigo-600 hover:text-indigo-700">
                ← 返回編輯
            </a>
        </div>
    </div>
</div>

<!-- JavaScript 功能 -->
<script>
    const translationId = {{ translation_id }};

    function copyToClipboard() {
        const resultDiv = document.querySelector('.bg-gray-50');
        const text = resultDiv.innerText;
        navigator.clipboard.writeText(text).then(() => {
            alert('已複製到剪貼板！');
        });
    }

    function downloadHTML() {
        const html = `<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>日文轉換結果</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma; margin: 40px; }
        ruby { font-size: 1em; }
        rt { font-size: 0.6em; }
        .romanji { font-size: 0.9em; color: #666; }
    </style>
</head>
<body>
    {{ result_html | safe }}
</body>
</html>`;
        
        const blob = new Blob([html], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'japanese_conversion.html';
        a.click();
    }

    function downloadPDF() {
        // 可選：使用 html2pdf.js 庫或後端生成
        alert('PDF 下載功能開發中');
    }

    function markFavorite() {
        fetch('/favorite', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ translation_id: translationId })
        }).then(() => location.reload());
    }

    function unmarkFavorite() {
        fetch('/favorite/' + translationId, {
            method: 'DELETE'
        }).then(() => location.reload());
    }
</script>
{% endblock %}
```

---

## API 設計

### 基本信息
- **協議**：HTTP/HTTPS
- **格式**：JSON（請求/響應）、HTML（頁面）
- **認證**：無（本地應用）
- **版本**：v1

### 端點列表

#### **1. 主頁** - `GET /`
**描述**：返回輸入頁面

**響應**：HTML 頁面

---

#### **2. 文本轉換** - `POST /convert`
**描述**：轉換日文文本

**請求**：
```json
{
    "text": "日本の作家、九段理江氏（３３）は同国で最も栄誉ある文学賞の一つを受賞した後...",
    "simplify_long_vowels": true
}
```

**響應（成功）**：
```html
<!-- 重定向到結果頁面 -->
HTTP 303 See Other
Location: /results/{translation_id}
```

**響應（失敗）**：
```json
{
    "error": "文本為空或過長（>100000 字）",
    "code": "INVALID_TEXT"
}
```

---

#### **3. 文件轉換** - `POST /convert/file`
**描述**：上傳文件進行轉換

**請求**：
```
Content-Type: multipart/form-data
file: <binary file (.txt or .pdf)>
simplify_long_vowels: true
```

**響應**：同 `/convert`

**限制**：
- 文件大小 ≤ 5MB
- 格式：.txt (UTF-8)、.pdf
- 超時：30 秒

---

#### **4. 結果顯示** - `GET /results/{translation_id}`
**描述**：顯示轉換結果頁面

**路徑參數**：
- `translation_id` (int): 轉換記錄 ID

**響應**：HTML 結果頁面

---

#### **5. 轉換歷史** - `GET /history?page=1&limit=20`
**描述**：獲取用戶轉換歷史

**查詢參數**：
- `page` (int, optional, default=1): 頁碼
- `limit` (int, optional, default=20): 每頁記錄數
- `search` (string, optional): 搜索關鍵字

**響應**：
```json
{
    "items": [
        {
            "id": 1,
            "input_text": "日本の...",
            "created_at": "2026-05-05T10:30:00",
            "is_favorite": false,
            "preview": "日本の作家、..."
        }
    ],
    "total": 150,
    "page": 1,
    "total_pages": 8
}
```

---

#### **6. 標記收藏** - `POST /favorite`
**描述**：將轉換結果標記為收藏

**請求**：
```json
{
    "translation_id": 1,
    "notes": "敬語表達很好",
    "tags": "敬語,文學"
}
```

**響應**：
```json
{
    "success": true,
    "message": "已添加到收藏"
}
```

---

#### **7. 取消收藏** - `DELETE /favorite/{translation_id}`
**描述**：從收藏中移除

**響應**：
```json
{
    "success": true,
    "message": "已從收藏中移除"
}
```

---

#### **8. 下載 HTML** - `GET /download/html/{translation_id}`
**描述**：下載轉換結果為 HTML 文件

**響應**：
```
Content-Type: text/html
Content-Disposition: attachment; filename="japanese_conversion.html"
```

---

#### **9. 下載 PDF** - `GET /download/pdf/{translation_id}`
**描述**：下載轉換結果為 PDF 文件

**響應**：
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="japanese_conversion.pdf"
```

---

#### **10. 健康檢查** - `GET /health`
**描述**：檢查應用狀態

**響應**：
```json
{
    "status": "ok",
    "timestamp": "2026-05-05T10:30:00"
}
```

---

## 實現路線圖

### 階段 1：基礎設置 *(Week 1)*
- [ ] 初始化 FastAPI 應用 + Jinja2 配置
- [ ] 創建目錄結構
- [ ] SQLite 數據庫初始化
- [ ] 安裝 PyKakasi 依賴

### 階段 2：核心引擎 *(Week 1-2)*
- [ ] 實現 `processors/furigana.py` - PyKakasi 集成
- [ ] 實現 Ruby HTML 生成
- [ ] 單元測試：邊界情況

### 階段 3：前端 UI *(Week 2)*
- [ ] 實現 `templates/base.html` + Tailwind CSS
- [ ] 實現主輸入頁面
- [ ] 實現結果顯示頁面

### 階段 4：API 端點 *(Week 2-3)*
- [ ] 實現文本轉換端點 (`POST /convert`)
- [ ] 實現結果顯示端點 (`GET /results/{id}`)
- [ ] 集成測試：API 流程

### 階段 5：數據庫 *(Week 3)*
- [ ] 實現 CRUD 操作層
- [ ] 集成存儲到 API 路由
- [ ] 歷史記錄 + 收藏功能

### 階段 6：高級功能 *(Week 3-4)*
- [ ] 文件上傳 (.txt, .pdf)
- [ ] HTML/PDF 下載
- [ ] 搜索和過濾

### 階段 7：測試與優化 *(Week 4)*
- [ ] 完整測試套件
- [ ] 性能優化（PyKakasi 緩存、異步大文件）
- [ ] 文檔完善

### 階段 8：部署 *(Week 4)*
- [ ] 生成 `requirements.txt`
- [ ] 編寫安裝腳本 `setup.sh`
- [ ] 編寫啟動腳本 `run.sh`
- [ ] 用戶指南編寫

---

## 性能與安全考慮

### 性能目標
| 操作 | 目標時間 | 優化方法 |
|------|--------|--------|
| 小文本轉換 (< 500 字) | < 1 秒 | PyKakasi 實例全局緩存 |
| 中等文本轉換 (500-5000 字) | < 5 秒 | 同上 |
| 大文本轉換 (5000-100000 字) | < 30 秒 | 異步處理 + 流式 HTML |
| 文件上傳 (< 5MB) | < 10 秒 | 後端文件流處理 |
| 歷史查詢 (分頁) | < 200ms | SQLite 索引優化 |

### 優化策略
1. **全局 PyKakasi 實例緩存**：應用啟動時初始化一次
2. **異步文件上傳**：使用 `aiofiles` 處理大文件
3. **SQLite 查詢優化**：為 `created_at` 和 `tags` 建立索引
4. **HTML 流式響應**：大文本分批返回
5. **前端優化**：使用 event debouncing 防止過度請求

### 安全考慮
1. **輸入驗證**：文本長度限制 100,000 字、文件大小限制 5MB
2. **SQL 注入防護**：使用參數化查詢（SQLite3 內置支持）
3. **XSS 防護**：Jinja2 自動轉義 HTML，Ruby 標籤由後端生成
4. **CSRF 防護**：POST 請求（未來可加 CSRF token）
5. **速率限制**：可選（如需部署到公網）

---

## 常見邊界情況與處理

| 情況 | 預期行為 |
|------|--------|
| 空文本輸入 | 顯示驗證錯誤提示 |
| 純假名輸入 | 顯示原文不變，羅馬音轉換 |
| 混合日英 | 日文部分轉換，英文保持原樣 |
| 特殊符號（標點、數字） | 保持原樣 |
| 換行/制表符 | 保留格式 |
| 超大文本 (> 100KB) | 限制或分批處理 |
| PDF 格式文本亂碼 | 嘗試編碼檢測，失敗則報錯 |
| PyKakasi 初始化失敗 | 使用備用方案（romkan）或顯示錯誤 |

---

## 故障恢復與日誌

### 日誌記錄
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

**日誌級別**：
- INFO：應用啟動、轉換完成
- WARNING：PyKakasi 初始化時間過長
- ERROR：數據庫錯誤、文件上傳失敗
- DEBUG：詳細的處理流程（開發環境）

### 故障恢復
1. **PyKakasi 初始化失敗**：提示用戶安裝依賴
2. **數據庫連接失敗**：自動重試 3 次（間隔 1 秒）
3. **文件上傳失敗**：返回詳細錯誤提示
4. **轉換超時**：返回部分結果或取消操作

---

## 未來擴展建議

1. **多語言支持**：新增中文、韓文處理
2. **API 認證**：若部署為公開服務
3. **批量轉換**：支持拖拽多個文件
4. **自定義字典**：用戶可上傳自定義漢字讀音
5. **統計分析**：詞頻分析、難度評估
6. **集成輸入法**：直接輸入到打字軟件
7. **移動應用**：React Native 或 Flutter

---

## 參考資源

- **PyKakasi 文檔**：https://pykakasi.readthedocs.io/
- **Fugashi 文檔**：https://fugashi.readthedocs.io/
- **FastAPI 文檔**：https://fastapi.tiangolo.com/
- **Tailwind CSS 文檔**：https://tailwindcss.com/docs
- **HTML Ruby 標籤規範**：https://html.spec.whatwg.org/ruby/

---

**文檔版本**：1.0  
**最後更新**：2026年5月5日  
**維護者**：開發團隊
