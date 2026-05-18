"""
日文翻譯模組 - 使用 Translate 進行線上翻譯
支援日文 → 繁體中文（使用 Google Translate）
支持並行翻譯以提高性能
"""

import logging
from typing import Optional, Dict, List
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading

try:
    from translate import Translator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False

logger = logging.getLogger(__name__)

# 全域翻譯器例項和執行緒池
_translator = None
_translation_cache = {}
_executor = ThreadPoolExecutor(max_workers=4)  # 4 個並行執行緒用於翻譯
_cache_lock = threading.Lock()  # 快取線程安全鎖


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
    將日文翻譯為繁體中文（同步版本）
    支持快取以避免重複翻譯
    
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
    if use_cache:
        with _cache_lock:
            if text in _translation_cache:
                logger.debug(f"✓ 使用快取翻譯: {text[:30]}...")
                return _translation_cache[text]
    
    try:
        logger.debug(f"🌐 翻譯文本: {text[:50]}...")
        
        # 執行翻譯
        translated = _translator.translate(text)
        
        # 保存到快取
        if use_cache:
            with _cache_lock:
                _translation_cache[text] = translated
        
        logger.debug(f"✓ 翻譯完成: {translated[:50]}...")
        return translated
        
    except Exception as e:
        logger.warning(f"⚠ 翻譯失敗: {e}")
        return None


def translate_batch(texts: List[str], use_cache: bool = True) -> Dict[str, Optional[str]]:
    """
    並行翻譯多個文本
    使用執行緒池進行並行翻譯，大幅提升性能
    
    Args:
        texts: 日文文本列表
        use_cache: 是否使用快取
    
    Returns:
        {原文: 翻譯} 字典
    """
    if not texts:
        return {}
    
    if not TRANSLATOR_AVAILABLE:
        logger.warning("❌ Translate 套件未安裝")
        return {text: None for text in texts}
    
    # 初始化翻譯器
    if _translator is None:
        if not initialize_translator():
            return {text: None for text in texts}
    
    # 過濾掉已經在快取中的文本
    to_translate = []
    cached_results = {}
    
    if use_cache:
        with _cache_lock:
            for text in texts:
                if text in _translation_cache:
                    cached_results[text] = _translation_cache[text]
                else:
                    to_translate.append(text)
    else:
        to_translate = texts
    
    if not to_translate:
        logger.debug(f"✓ 所有文本已在快取中")
        return cached_results
    
    logger.info(f"🌐 並行翻譯 {len(to_translate)} 個文本... (快取命中: {len(cached_results)})")
    
    # 使用執行緒池進行並行翻譯
    results = {}
    futures = {}
    
    for text in to_translate:
        future = _executor.submit(translate_to_chinese, text, use_cache)
        futures[text] = future
    
    # 收集結果
    for text, future in futures.items():
        try:
            result = future.result(timeout=10)  # 10 秒超時
            results[text] = result
        except Exception as e:
            logger.warning(f"⚠ 翻譯超時或失敗 ({text}): {e}")
            results[text] = None
    
    # 合併快取結果和新翻譯結果
    all_results = {**cached_results, **results}
    logger.info(f"✓ 批量翻譯完成 (成功: {sum(1 for v in all_results.values() if v)}/{len(all_results)})")
    
    return all_results


def translate_batch_async(texts: List[str], use_cache: bool = True) -> Dict[str, Optional[str]]:
    """
    非同步並行翻譯多個文本（異步版本）
    
    Args:
        texts: 日文文本列表
        use_cache: 是否使用快取
    
    Returns:
        {原文: 翻譯} 字典
    """
    # 如果在同步上下文中，使用同步版本
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果有事件迴圈在運行，使用線程池版本
            return translate_batch(texts, use_cache)
    except RuntimeError:
        pass
    
    # 否則使用執行緒池版本
    return translate_batch(texts, use_cache)


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

