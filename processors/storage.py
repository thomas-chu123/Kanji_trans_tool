"""
SQLite 數據庫操作層
CRUD 操作和查詢邏輯
"""

import sqlite3
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# 修正：數據庫路徑應指向 db/ 目錄，而不是 processors/ 目錄
DB_PATH = Path(__file__).parent.parent / "db" / "translations.db"


def get_db_connection():
    """
    獲取數據庫連接
    設置 row_factory 以返回字典形式的行數據
    """
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_translation_column():
    """
    確保 chinese_translation 列存在（用於遷移舊數據庫）
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 檢查列是否存在
        cursor.execute("PRAGMA table_info(translations)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "chinese_translation" not in columns:
            logger.info("📝 添加 chinese_translation 列到 translations 表...")
            cursor.execute("""
            ALTER TABLE translations 
            ADD COLUMN chinese_translation TEXT
            """)
            conn.commit()
            logger.info("✓ 列已添加")
        
        conn.close()
    except Exception as e:
        logger.warning(f"⚠️  遷移檢查失敗 (可能已存在): {e}")


def save_translation(input_text: str, output_html: str, processed_data: Optional[List[Dict]] = None, chinese_translation: Optional[str] = None) -> Optional[int]:
    """
    保存轉換記錄到數據庫
    
    Args:
        input_text: 輸入的日文文本
        output_html: 生成的 HTML 結果
        processed_data: 處理後的結構化數據（JSON 格式）
        chinese_translation: 中文翻譯文本（可選）
    
    Returns:
        記錄的 ID（用於查詢），失敗返回 None
    """
    
    try:
        # 確保 chinese_translation 列存在
        ensure_translation_column()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 轉換 processed_data 為 JSON 字符串
        processed_data_json = json.dumps(processed_data, ensure_ascii=False) if processed_data else None
        
        cursor.execute("""
        INSERT INTO translations (input_text, output_html, processed_data, chinese_translation, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            input_text,
            output_html,
            processed_data_json,
            chinese_translation,
            datetime.now(),
            datetime.now()
        ))
        
        conn.commit()
        translation_id = cursor.lastrowid
        conn.close()
        
        logger.info(f"✓ 轉換記錄已保存: ID={translation_id}")
        return translation_id
        
    except Exception as e:
        logger.error(f"保存轉換記錄失敗: {e}")
        return None


def get_translation(translation_id: int) -> Optional[Dict]:
    """
    獲取單條轉換記錄
    
    Args:
        translation_id: 記錄 ID
    
    Returns:
        轉換記錄字典或 None
    """
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT 
            t.id,
            t.input_text,
            t.output_html,
            t.processed_data,
            t.created_at,
            t.updated_at,
            CASE WHEN f.id IS NOT NULL THEN 1 ELSE 0 END as is_favorite,
            f.notes,
            f.tags
        FROM translations t
        LEFT JOIN favorites f ON t.id = f.translation_id
        WHERE t.id = ?
        """, (translation_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
        
    except Exception as e:
        logger.error(f"查詢轉換記錄失敗: {e}")
        return None


def get_history(limit: int = 20, offset: int = 0, search_keyword: Optional[str] = None) -> List[Dict]:
    """
    獲取轉換歷史記錄（分頁）
    
    Args:
        limit: 每頁記錄數（最多 100）
        offset: 起始位置
        search_keyword: 搜索關鍵字（按輸入文本搜索）
    
    Returns:
        轉換記錄列表
    """
    
    limit = min(limit, 100)  # 最多 100 條
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if search_keyword:
            # 搜索模式
            search_keyword = f"%{search_keyword}%"
            cursor.execute("""
            SELECT 
                t.id,
                t.input_text,
                t.output_html,
                t.created_at,
                CASE WHEN f.id IS NOT NULL THEN 1 ELSE 0 END as is_favorite,
                SUBSTR(t.input_text, 1, 100) as preview
            FROM translations t
            LEFT JOIN favorites f ON t.id = f.translation_id
            WHERE t.input_text LIKE ?
            ORDER BY t.created_at DESC
            LIMIT ? OFFSET ?
            """, (search_keyword, limit, offset))
        else:
            # 全部記錄
            cursor.execute("""
            SELECT 
                t.id,
                t.input_text,
                t.output_html,
                t.created_at,
                CASE WHEN f.id IS NOT NULL THEN 1 ELSE 0 END as is_favorite,
                SUBSTR(t.input_text, 1, 100) as preview
            FROM translations t
            LEFT JOIN favorites f ON t.id = f.translation_id
            ORDER BY t.created_at DESC
            LIMIT ? OFFSET ?
            """, (limit, offset))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
        
    except Exception as e:
        logger.error(f"查詢歷史記錄失敗: {e}")
        return []


def get_total_count(search_keyword: Optional[str] = None) -> int:
    """
    獲取轉換記錄總數
    
    Args:
        search_keyword: 搜索關鍵字（可選）
    
    Returns:
        記錄總數
    """
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if search_keyword:
            search_keyword = f"%{search_keyword}%"
            cursor.execute("SELECT COUNT(*) FROM translations WHERE input_text LIKE ?", (search_keyword,))
        else:
            cursor.execute("SELECT COUNT(*) FROM translations")
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
        
    except Exception as e:
        logger.error(f"計算記錄總數失敗: {e}")
        return 0


def mark_favorite(translation_id: int, notes: str = "", tags: str = "") -> bool:
    """
    將轉換記錄標記為收藏
    
    Args:
        translation_id: 轉換記錄 ID
        notes: 用戶筆記
        tags: 標籤（逗號分隔，如 "敬語,文學"）
    
    Returns:
        成功返回 True
    """
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT OR IGNORE INTO favorites (translation_id, notes, tags, created_at)
        VALUES (?, ?, ?, ?)
        """, (translation_id, notes, tags, datetime.now()))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✓ 已標記為收藏: ID={translation_id}")
        return True
        
    except Exception as e:
        logger.error(f"標記收藏失敗: {e}")
        return False


def unmark_favorite(translation_id: int) -> bool:
    """
    取消收藏
    
    Args:
        translation_id: 轉換記錄 ID
    
    Returns:
        成功返回 True
    """
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM favorites WHERE translation_id = ?", (translation_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✓ 已取消收藏: ID={translation_id}")
        return True
        
    except Exception as e:
        logger.error(f"取消收藏失敗: {e}")
        return False


def get_favorites(limit: int = 50, offset: int = 0) -> List[Dict]:
    """
    獲取所有收藏的翻譯
    
    Args:
        limit: 每頁記錄數
        offset: 起始位置
    
    Returns:
        收藏記錄列表
    """
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT 
            t.id,
            t.input_text,
            t.output_html,
            t.created_at,
            f.notes,
            f.tags,
            SUBSTR(t.input_text, 1, 100) as preview
        FROM translations t
        INNER JOIN favorites f ON t.id = f.translation_id
        ORDER BY f.created_at DESC
        LIMIT ? OFFSET ?
        """, (limit, offset))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
        
    except Exception as e:
        logger.error(f"查詢收藏失敗: {e}")
        return []


def search_history(keyword: str, limit: int = 20) -> List[Dict]:
    """
    按輸入文本搜索歷史記錄
    
    Args:
        keyword: 搜索關鍵字
        limit: 最多返回記錄數
    
    Returns:
        搜索結果列表
    """
    
    return get_history(limit=limit, search_keyword=keyword)


def delete_translation(translation_id: int) -> bool:
    """
    刪除轉換記錄（連同收藏一起刪除）
    
    Args:
        translation_id: 記錄 ID
    
    Returns:
        成功返回 True
    """
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 由於設置了外鍵 ON DELETE CASCADE，刪除 translations 會自動刪除相關的 favorites
        cursor.execute("DELETE FROM translations WHERE id = ?", (translation_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✓ 已刪除記錄: ID={translation_id}")
        return True
        
    except Exception as e:
        logger.error(f"刪除記錄失敗: {e}")
        return False


def clear_old_records(days: int = 90) -> int:
    """
    清除 N 天前的記錄（不包括收藏）
    
    Args:
        days: 天數
    
    Returns:
        刪除的記錄數
    """
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 僅刪除未被收藏的舊記錄
        cursor.execute("""
        DELETE FROM translations 
        WHERE id NOT IN (SELECT translation_id FROM favorites)
        AND created_at < datetime('now', '-' || ? || ' days')
        """, (days,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"✓ 已清除 {deleted_count} 條舊記錄")
        return deleted_count
        
    except Exception as e:
        logger.error(f"清除舊記錄失敗: {e}")
        return 0


def export_as_json(translation_id: int) -> Optional[str]:
    """
    導出轉換記錄為 JSON（用於下載）
    
    Args:
        translation_id: 記錄 ID
    
    Returns:
        JSON 字符串或 None
    """
    
    try:
        record = get_translation(translation_id)
        if not record:
            return None
        
        export_data = {
            "id": record["id"],
            "input_text": record["input_text"],
            "output_html": record["output_html"],
            "processed_data": json.loads(record["processed_data"]) if record["processed_data"] else None,
            "created_at": record["created_at"],
            "is_favorite": bool(record.get("is_favorite")),
        }
        
        return json.dumps(export_data, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"導出 JSON 失敗: {e}")
        return None


# 數據庫統計函數
def get_stats() -> Dict:
    """
    獲取數據庫統計信息
    
    Returns:
        包含統計信息的字典
    """
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM translations")
        total_translations = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM favorites")
        total_favorites = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(LENGTH(input_text)) FROM translations")
        avg_text_length = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            "total_translations": total_translations,
            "total_favorites": total_favorites,
            "avg_text_length": round(avg_text_length, 2)
        }
        
    except Exception as e:
        logger.error(f"獲取統計信息失敗: {e}")
        return {
            "total_translations": 0,
            "total_favorites": 0,
            "avg_text_length": 0
        }
