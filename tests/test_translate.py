#!/usr/bin/env python3
"""
測試 Python translate 庫功能
確認翻譯服務是否正常工作
"""

import sys
import time
from pathlib import Path

# 添加項目路徑
sys.path.insert(0, str(Path(__file__).parent))

def test_translate_library():
    """測試 translate 庫"""
    print("\n" + "="*60)
    print("🧪 Python Translate 庫測試工具")
    print("="*60)
    
    # 測試 1: 檢查模塊導入
    print("\n[測試 1] 檢查模塊導入...")
    try:
        import translate
        print(f"✓ translate 模塊版本: {translate.__version__}")
    except ImportError as e:
        print(f"✗ 導入失敗: {e}")
        return False
    
    # 測試 2: 初始化翻譯器
    print("\n[測試 2] 初始化翻譯器 (日文 → 繁體中文)...")
    try:
        from translate import Translator
        translator = Translator(from_lang="ja", to_lang="zh-TW")
        print("✓ 翻譯器初始化成功")
    except Exception as e:
        print(f"✗ 初始化失敗: {e}")
        return False
    
    # 測試 3: 簡單翻譯
    print("\n[測試 3] 簡單翻譯測試...")
    test_texts = [
        "こんにちは",
        "ありがとうございます",
        "イラン情勢が緊迫度を増す中。",
        "毎日新聞",
    ]
    
    for text in test_texts:
        try:
            result = translator.translate(text)
            print(f"  日文: {text}")
            print(f"  中文: {result}")
            print()
        except Exception as e:
            print(f"  ✗ 翻譯失敗: {e}")
            return False
    
    # 測試 4: 從模塊測試
    print("[測試 4] 從 processors.translator 模塊測試...")
    try:
        from processors.translator import translate_to_chinese, initialize_translator
        
        # 初始化
        initialize_translator()
        print("✓ 翻譯器初始化完成")
        
        # 翻譯
        test_text = "トレース"
        result = translate_to_chinese(test_text)
        print(f"  日文: {test_text}")
        print(f"  中文: {result}")
        print("✓ 模塊翻譯成功")
    except Exception as e:
        print(f"✗ 模塊翻譯失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 測試 5: 緩存測試
    print("\n[測試 5] 緩存功能測試...")
    try:
        from processors.translator import translate_to_chinese
        
        test_text = "日本語"
        
        # 第一次翻譯（可能需要網絡）
        start = time.time()
        result1 = translate_to_chinese(test_text)
        time1 = time.time() - start
        print(f"  第一次翻譯: {result1} (耗時: {time1:.3f}秒)")
        
        # 第二次翻譯（應該使用緩存）
        start = time.time()
        result2 = translate_to_chinese(test_text)
        time2 = time.time() - start
        print(f"  第二次翻譯: {result2} (耗時: {time2:.3f}秒)")
        
        if result1 == result2:
            print(f"✓ 緩存運作正常 (第二次快 {time1/time2:.1f}倍)")
        else:
            print(f"⚠️  翻譯結果不一致")
    except Exception as e:
        print(f"✗ 緩存測試失敗: {e}")
        return False
    
    # 測試 6: 批量翻譯測試
    print("\n[測試 6] 批量翻譯測試...")
    try:
        from processors.translator import translate_to_chinese
        
        batch_texts = [
            "りんご",
            "みかん",
            "スイカ",
            "バナナ",
        ]
        
        print("  輸入文本 → 翻譯結果")
        for text in batch_texts:
            result = translate_to_chinese(text)
            print(f"  {text:10} → {result}")
        
        print("✓ 批量翻譯成功")
    except Exception as e:
        print(f"✗ 批量翻譯失敗: {e}")
        return False
    
    # 測試完成
    print("\n" + "="*60)
    print("✅ 所有測試通過！translate 庫工作正常")
    print("="*60 + "\n")
    return True

if __name__ == "__main__":
    success = test_translate_library()
    sys.exit(0 if success else 1)
