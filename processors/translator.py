"""
日文翻譯模組 - 使用 Translate 進行線上翻譯
支援日文 → 繁體中文（使用 Google Translate）
"""

import logging
from typing import Optional

try:
    from translate import Translator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False

logger = logging.getLogger(__name__)

# 全域翻譯器例項
_translator = None
_translation_cache = {}


def initialize_translator():
    """
    初始化翻譯器
    使用 Google Translate 引擎進行線上翻譯
    """
    global _translator, TRANSLATOR_AVAILABLE
    
    if _translator is not None:
        return True
    
    if not TRANSLATOR_AVAILABLE:
        logger.warning("❌ Translate 套件未安裝")
        return False
    
    try:
        logger.info("🔍 初始化翻譯器...")
        # 建立翻譯器：日文 → 繁體中文 (zh-TW)
        _translator = Translator(from_lang="ja", to_lang="zh-TW")
        logger.info("✓ 翻譯器已初始化 (Google Translate)")
        return True
        
    except Exception as e:
        logger.error(f"❌ 翻譯器初始化失敗: {e}")
        return False


def translate_to_chinese(text: str, use_cache: bool = True) -> Optional[str]:
    """
    將日文翻譯為繁體中文
    
    Args:
        text: 日文文本
        use_cache: 是否使用快取
    
    Returns:
        繁體中文翻譯文本，失敗時返回 None
    """
    
    if not text or not text.strip():
        return ""
    
    if not TRANSLATOR_AVAILABLE:
        logger.warning("❌ Translate 套件未安裝")
        return None
    
    # 初始化翻譯器
    if _translator is None:
        if not initialize_translator():
            return None
    
    # 檢查快取
    if use_cache and text in _translation_cache:
        logger.debug(f"✓ 使用快取翻譯")
        return _translation_cache[text]
    
    try:
        logger.info(f"🌐 翻譯文本: {text[:50]}...")
        
        # 執行翻譯
        translated = _translator.translate(text)
        
        # 保存到快取
        if use_cache:
            _translation_cache[text] = translated
        
        logger.info(f"✓ 翻譯完成")
        return translated
        
    except Exception as e:
        logger.error(f"❌ 翻譯失敗: {e}")
        return None


def clear_cache():
    """清空翻譯快取"""
    global _translation_cache
    _translation_cache.clear()
    logger.info("✓ 翻譯快取已清空")


if __name__ == "__main__":
    # 測試翻譯功能
    logging.basicConfig(level=logging.INFO)
    
    initialize_translator()
    
    test_text = "こんにちは。今日はいい天気ですね。"
    result = translate_to_chinese(test_text)
    
    print(f"原文: {test_text}")
    print(f"翻譯: {result}")

