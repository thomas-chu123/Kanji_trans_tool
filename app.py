"""
日文文章轉換網站 - FastAPI 主應用
前後端統一應用，使用 Jinja2 模板後端渲染 + Tailwind CSS
"""

import logging
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware

# 業務邏輯模塊
from processors.furigana import initialize_kakasi, process_text, generate_ruby_html
from processors import storage
from processors.translator import translate_to_chinese, initialize_translator
from db.init_db import init_database

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# 初始化 FastAPI 應用
app = FastAPI(
    title="日文文章轉換工具",
    description="使用 FastAPI + PyKakasi 的日文假名和羅馬音轉換工具",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置靜態文件和模板
BASE_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# 應用啟動事件
@app.on_event("startup")
async def startup_event():
    """應用啟動時的初始化"""
    logger.info("=" * 60)
    logger.info("🚀 日文文章轉換工具 - 啟動中...")
    logger.info("=" * 60)
    
    # 初始化數據庫
    init_database()
    
    # 初始化 PyKakasi
    if not initialize_kakasi():
        logger.warning("⚠️  PyKakasi 初始化失敗，應用可能無法正常工作")
    
    # 初始化翻譯器
    logger.info("🌐 初始化翻譯器...")
    if initialize_translator():
        logger.info("✓ 翻譯器已初始化")
    else:
        logger.warning("⚠️  翻譯器初始化失敗，翻譯功能將不可用")
    
    logger.info("✅ 應用已準備就緒，訪問：http://localhost:8000")
    logger.info("=" * 60)


# ============================================================================
# 前端路由（返回 HTML）
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    主輸入頁面
    """
    try:
        recent_translations = storage.get_history(limit=5)
        favorites = storage.get_favorites(limit=5)
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "recent_translations": recent_translations,
            "favorites": favorites
        })
    except Exception as e:
        logger.error(f"主頁加載失敗: {e}")
        raise HTTPException(status_code=500, detail="頁面加載失敗")


@app.get("/history", response_class=HTMLResponse)
async def history(request: Request, page: int = 1, search: Optional[str] = None):
    """
    轉換歷史頁面
    
    查詢參數：
    - page: 頁碼（默認 1）
    - search: 搜索關鍵字
    """
    try:
        limit = 20
        offset = (page - 1) * limit
        
        translations = storage.get_history(limit=limit, offset=offset, search_keyword=search)
        total_count = storage.get_total_count(search_keyword=search)
        total_pages = (total_count + limit - 1) // limit
        
        # 防止頁碼越界
        if page > total_pages and total_pages > 0:
            page = total_pages
        
        return templates.TemplateResponse("history.html", {
            "request": request,
            "translations": translations,
            "current_page": page,
            "total_pages": total_pages,
            "total_count": total_count,
            "search_keyword": search or ""
        })
    except Exception as e:
        logger.error(f"歷史頁面加載失敗: {e}")
        raise HTTPException(status_code=500, detail="頁面加載失敗")


@app.get("/favorites", response_class=HTMLResponse)
async def favorites_page(request: Request):
    """
    收藏頁面
    """
    try:
        favorites = storage.get_favorites()
        
        return templates.TemplateResponse("favorites.html", {
            "request": request,
            "favorites": favorites
        })
    except Exception as e:
        logger.error(f"收藏頁面加載失敗: {e}")
        raise HTTPException(status_code=500, detail="頁面加載失敗")


@app.get("/results/{translation_id}", response_class=HTMLResponse)
async def results(request: Request, translation_id: int):
    """
    轉換結果頁面
    
    路徑參數：
    - translation_id: 轉換記錄 ID
    """
    try:
        record = storage.get_translation(translation_id)
        
        if not record:
            raise HTTPException(status_code=404, detail="轉換記錄不存在")
        
        # 解析 processed_data
        processed_data = json.loads(record["processed_data"]) if record["processed_data"] else []
        
        return templates.TemplateResponse("results.html", {
            "request": request,
            "translation_id": record["id"],
            "input_text": record["input_text"],
            "result_html": record["output_html"],
            "chinese_translation": record.get("chinese_translation", ""),
            "created_at": record["created_at"],
            "is_favorite": bool(record.get("is_favorite", 0)),
            "notes": record.get("notes", ""),
            "input_text_length": len(record["input_text"]),
            "token_count": len(processed_data)
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"結果頁面加載失敗: {e}")
        raise HTTPException(status_code=500, detail="頁面加載失敗")


# ============================================================================
# API 路由（JSON）
# ============================================================================

@app.post("/convert")
async def convert_text(
    request: Request,
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    simplify_long_vowels: bool = Form(True)
):
    """
    文本轉換 API
    
    表單參數：
    - text: 日文文本（可選，與 file 二選一）
    - file: 上傳的文件（可選，與 text 二選一）
    - simplify_long_vowels: 簡化羅馬音長音（布爾值）
    
    返回：
    - 重定向到結果頁面（HTTP 303）或 JSON 錯誤
    """
    try:
        # 驗證輸入
        input_text = None
        
        if text:
            input_text = text.strip()
        elif file:
            # 讀取上傳的文件
            content = await file.read()
            file_ext = Path(file.filename).suffix.lower()
            
            # 圖片 OCR 處理
            if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                logger.info(f"🖼️  檢測到圖片文件: {file.filename}")
                try:
                    from processors.ocr import extract_text_from_image
                    input_text = await extract_text_from_image(content)
                except Exception as ocr_error:
                    logger.error(f"❌ OCR 處理失敗: {ocr_error}")
                    raise ValueError(f"圖片識別失敗：{str(ocr_error)}")
            else:
                # 文本文件編碼處理
                logger.info(f"📄 檢測到文本文件: {file.filename}")
                for encoding in ['utf-8', 'utf-8-sig', 'shift_jis', 'gbk']:
                    try:
                        input_text = content.decode(encoding).strip()
                        break
                    except (UnicodeDecodeError, LookupError):
                        continue
                
                if input_text is None:
                    raise ValueError("無法識別文件編碼")
        
        if not input_text:
            raise ValueError("輸入內容為空")
        
        if len(input_text) > 100000:
            raise ValueError("文本過長，最多 100,000 字")
        
        logger.info(f"📝 開始轉換: {len(input_text)} 字")
        
        # 處理文本
        processed_data = process_text(input_text, simplify_long_vowels=simplify_long_vowels)
        output_html = generate_ruby_html(processed_data, simplify_long_vowels=simplify_long_vowels)
        
        # 翻譯為中文
        try:
            chinese_translation = translate_to_chinese(input_text)
            if chinese_translation:
                logger.info(f"✓ 翻譯完成: {chinese_translation[:50]}")
            else:
                logger.warning("⚠️  翻譯結果為空")
        except Exception as translate_error:
            logger.error(f"❌ 翻譯過程出錯: {translate_error}", exc_info=True)
            chinese_translation = None
        
        # 轉換為字典列表（便於 JSON 序列化）
        tokens_dict = [
            {
                "original": token.original,
                "hiragana": token.hiragana,
                "romanji": token.romanji,
                "type": token.token_type
            }
            for token in processed_data
        ]
        
        # 保存到數據庫
        translation_id = storage.save_translation(
            input_text=input_text,
            output_html=output_html,
            processed_data=tokens_dict,
            chinese_translation=chinese_translation
        )
        
        if translation_id is None:
            raise RuntimeError("保存轉換記錄失敗")
        
        logger.info(f"✅ 轉換完成: ID={translation_id}")
        
        # 重定向到結果頁面
        return RedirectResponse(url=f"/results/{translation_id}", status_code=303)
        
    except ValueError as e:
        logger.warning(f"⚠️  驗證錯誤: {e}")
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )
    except Exception as e:
        logger.error(f"❌ 轉換失敗: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "轉換失敗，請重試"}
        )


@app.post("/api/favorite")
async def mark_favorite(request: Request):
    """
    標記為收藏
    
    JSON 請求體：
    {
        "translation_id": int,
        "notes": str (可選),
        "tags": str (可選)
    }
    """
    try:
        data = await request.json()
        translation_id = data.get("translation_id")
        notes = data.get("notes", "")
        tags = data.get("tags", "")
        
        if not translation_id:
            raise ValueError("translation_id 不能為空")
        
        success = storage.mark_favorite(
            translation_id=translation_id,
            notes=notes,
            tags=tags
        )
        
        if success:
            return {"success": True, "message": "已添加到收藏"}
        else:
            return {"success": False, "error": "收藏失敗"}
            
    except Exception as e:
        logger.error(f"標記收藏失敗: {e}")
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )


@app.delete("/api/favorite/{translation_id}")
async def unmark_favorite(translation_id: int):
    """
    取消收藏
    
    路徑參數：
    - translation_id: 轉換記錄 ID
    """
    try:
        success = storage.unmark_favorite(translation_id=translation_id)
        
        if success:
            return {"success": True, "message": "已取消收藏"}
        else:
            return {"success": False, "error": "操作失敗"}
            
    except Exception as e:
        logger.error(f"取消收藏失敗: {e}")
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/stats")
async def get_stats():
    """
    獲取統計信息
    
    返回：
    {
        "total_translations": int,
        "total_favorites": int,
        "avg_text_length": float
    }
    """
    try:
        stats = storage.get_stats()
        return stats
    except Exception as e:
        logger.error(f"獲取統計信息失敗: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "無法獲取統計信息"}
        )


@app.get("/health")
async def health_check():
    """
    健康檢查端點
    """
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


# ============================================================================
# 下載功能
# ============================================================================

@app.get("/download/html/{translation_id}")
async def download_html(translation_id: int):
    """
    下載轉換結果為 HTML 文件
    """
    try:
        record = storage.get_translation(translation_id)
        
        if not record:
            raise HTTPException(status_code=404, detail="轉換記錄不存在")
        
        html_content = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>日文轉換結果</title>
    <style>
        body {{
            font-family: 'Segoe UI', 'Noto Sans CJK JP', sans-serif;
            margin: 40px;
            line-height: 1.8;
            color: #333;
            background-color: #f5f5f5;
        }}
        
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        h1 {{ color: #0066cc; margin-bottom: 20px; }}
        h2 {{ color: #333; margin-top: 30px; margin-bottom: 15px; border-bottom: 2px solid #0066cc; padding-bottom: 10px; }}
        
        .original-text {{
            background: #f9f9ff;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            border-left: 4px solid #0066cc;
        }}
        
        .ruby-container {{
            background: #f9f9ff;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
            line-height: 2.5;
        }}
        
        ruby rt {{
            font-size: 0.65em;
            color: #0066cc;
            font-weight: 500;
        }}
        
        .romanji-below {{
            display: inline-block;
            font-size: 0.75em;
            color: #666;
            margin-right: 0.15em;
        }}
        
        .timestamp {{
            color: #999;
            font-size: 0.9em;
            margin-top: 30px;
            border-top: 1px solid #ddd;
            padding-top: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🇯🇵 日文文章轉換結果</h1>
        
        <h2>📖 原始文本</h2>
        <div class="original-text">
            {record["input_text"]}
        </div>
        
        <h2>🎯 轉換結果（假名讀音 + 羅馬音）</h2>
        <div class="ruby-container">
            {record["output_html"]}
        </div>
        
        <div class="timestamp">
            <p>轉換時間：{record["created_at"]}</p>
            <p>由日文文章轉換工具生成</p>
        </div>
    </div>
</body>
</html>"""
        
        return HTMLResponse(
            content=html_content,
            headers={"Content-Disposition": f"attachment; filename=japanese-conversion-{translation_id}.html"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下載 HTML 失敗: {e}")
        raise HTTPException(status_code=500, detail="下載失敗")


# ============================================================================
# 錯誤處理
# ============================================================================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """404 錯誤頁面"""
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error_code": 404,
            "error_message": "頁面不存在"
        },
        status_code=404
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: HTTPException):
    """500 錯誤頁面"""
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error_code": 500,
            "error_message": "服務器內部錯誤"
        },
        status_code=500
    )


# ============================================================================
# 主程序
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # 開發環境配置
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
        reload=True  # 開發環境下啟用自動重載
    )
