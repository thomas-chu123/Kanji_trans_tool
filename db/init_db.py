"""
SQLite 數據庫初始化腳本
"""

import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "translations.db"


def init_database():
    """初始化 SQLite 數據庫，創建必要的表"""
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # 轉換記錄表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS translations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        input_text TEXT NOT NULL,
        output_html TEXT NOT NULL,
        processed_data TEXT,
        chinese_translation TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 收藏表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        translation_id INTEGER UNIQUE,
        notes TEXT,
        tags TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(translation_id) REFERENCES translations(id) ON DELETE CASCADE
    )
    """)
    
    # 創建索引用於快速查詢
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_translations_created_at 
    ON translations(created_at DESC)
    """)
    
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_favorites_tags 
    ON favorites(tags)
    """)
    
    conn.commit()
    conn.close()
    
    print(f"✓ 數據庫已初始化: {DB_PATH}")


if __name__ == "__main__":
    init_database()
