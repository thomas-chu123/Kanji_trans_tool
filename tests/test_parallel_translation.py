#!/usr/bin/env python3
"""
測試並行翻譯性能改進
驗證 translate_batch 和批量詞彙翻譯的效果
"""

import time
import logging
from processors.translator import translate_to_chinese, translate_batch, initialize_translator
from processors.jlpt_level import get_jamdict_instance

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_sequential_translation():
    """測試順序翻譯（舊方式）"""
    logger.info("=" * 60)
    logger.info("測試 1: 順序翻譯（舊方式）")
    logger.info("=" * 60)
    
    initialize_translator()
    
    test_words = [
        '食べ物', '時間', '電気', '大きい', '学校',
        '好き', '友達', '家族', '仕事', '勉強'
    ]
    
    start_time = time.time()
    results = {}
    
    for word in test_words:
        result = translate_to_chinese(word)
        results[word] = result
        logger.info(f"  ✓ {word} → {result}")
    
    elapsed = time.time() - start_time
    logger.info(f"⏱️  順序翻譯耗時: {elapsed:.2f} 秒 (平均: {elapsed/len(test_words):.2f} 秒/詞)")
    
    return elapsed, results


def test_batch_translation():
    """測試批量翻譯（新方式）"""
    logger.info("\n" + "=" * 60)
    logger.info("測試 2: 批量翻譯（新方式 - 並行）")
    logger.info("=" * 60)
    
    initialize_translator()
    
    test_words = [
        '食べ物', '時間', '電気', '大きい', '学校',
        '好き', '友達', '家族', '仕事', '勉強'
    ]
    
    start_time = time.time()
    results = translate_batch(test_words)
    elapsed = time.time() - start_time
    
    for word, translation in results.items():
        logger.info(f"  ✓ {word} → {translation}")
    
    logger.info(f"⏱️  批量翻譯耗時: {elapsed:.2f} 秒 (加速比: {(10 * 0.1) / elapsed:.1f}x，假設單個翻譯 ~0.1s)")
    
    return elapsed, results


def test_jamdict():
    """測試 JMdict 集成"""
    logger.info("\n" + "=" * 60)
    logger.info("測試 3: JMdict 詞彙查詢")
    logger.info("=" * 60)
    
    jam = get_jamdict_instance()
    if jam:
        test_words = ['食べ物', '時間', '学校', '好き']
        for word in test_words:
            try:
                entries = jam.lookup(word)
                if entries:
                    entry = entries[0]
                    reading = entry.kana_form if hasattr(entry, 'kana_form') else 'N/A'
                    logger.info(f"  ✓ {word} → 讀音: {reading}")
                else:
                    logger.info(f"  ⚠ {word} 不在 JMdict 中")
            except Exception as e:
                logger.error(f"  ❌ {word} 查詢失败: {e}")
    else:
        logger.warning("⚠ JMdict 未初始化")


def main():
    logger.info("🚀 開始測試並行翻譯改進")
    logger.info(f"測試時間: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 測試 JMdict
        test_jamdict()
        
        # 測試順序翻譯
        seq_time, seq_results = test_sequential_translation()
        
        # 清空快取以進行公平比較
        from processors.translator import clear_cache
        clear_cache()
        
        # 測試批量翻譯
        batch_time, batch_results = test_batch_translation()
        
        # 性能對比
        logger.info("\n" + "=" * 60)
        logger.info("性能對比總結")
        logger.info("=" * 60)
        logger.info(f"順序翻譯: {seq_time:.2f} 秒")
        logger.info(f"批量翻譯: {batch_time:.2f} 秒")
        
        if seq_time > 0:
            improvement = ((seq_time - batch_time) / seq_time) * 100
            logger.info(f"性能改進: {improvement:.1f}%")
            
            if improvement > 0:
                logger.info(f"🎉 並行翻譯成功加速了翻譯過程！")
            else:
                logger.info(f"⚠️  由於快取命中率，批量翻譯可能沒有明顯加速")
        
    except Exception as e:
        logger.error(f"❌ 測試失败: {e}", exc_info=True)


if __name__ == "__main__":
    main()
