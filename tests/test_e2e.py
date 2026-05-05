#!/usr/bin/env python3
"""
端到端测试：验证完整的翻译流程
"""

import requests
import sqlite3
import time
from pathlib import Path

def test_complete_workflow():
    """测试完整工作流程"""
    print("\n" + "="*70)
    print("🧪 端到端测试：完整翻译流程")
    print("="*70)
    
    base_url = "http://localhost:8000"
    
    # 测试用例
    test_texts = [
        ("こんにちは", "你好"),
        ("ありがとうございます", "谢谢"),
        ("日本語を勉強しています", "正在学习日语"),
    ]
    
    for original_text, expected_partial in test_texts:
        print(f"\n[测试] 转换: {original_text}")
        
        # 1. 发送转换请求
        print("  1️⃣  发送转换请求...")
        response = requests.post(
            f"{base_url}/convert",
            data={"text": original_text},
            allow_redirects=False,
            timeout=10
        )
        
        if response.status_code != 303:
            print(f"  ❌ 转换请求失败: {response.status_code}")
            continue
        
        # 获取重定向的 ID
        location = response.headers.get('Location')
        translation_id = location.split('/')[-1] if location else None
        print(f"  ✓ 转换记录 ID: {translation_id}")
        
        # 2. 检查数据库
        print("  2️⃣  检查数据库...")
        try:
            conn = sqlite3.connect('db/translations.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT input_text, chinese_translation FROM translations WHERE id = ?",
                (translation_id,)
            )
            row = cursor.fetchone()
            conn.close()
            
            if row:
                db_input = row['input_text']
                db_translation = row['chinese_translation']
                print(f"  ✓ 数据库记录: {db_input} → {db_translation}")
                
                if expected_partial in str(db_translation or ""):
                    print(f"  ✓ 翻译结果正确")
                else:
                    print(f"  ⚠️  翻译结果可能不准确，期望包含: {expected_partial}")
            else:
                print(f"  ❌ 数据库中未找到记录")
        except Exception as e:
            print(f"  ❌ 数据库查询失败: {e}")
        
        # 3. 检查结果页面
        print("  3️⃣  检查结果页面...")
        time.sleep(1)
        try:
            result_response = requests.get(
                f"{base_url}/results/{translation_id}",
                timeout=10
            )
            
            if result_response.status_code == 200:
                html = result_response.text
                
                # 检查是否包含中文翻译框
                if "🌐 中文翻譯（繁體）" in html or "中文翻譯" in html:
                    print(f"  ✓ 结果页面包含中文翻译框")
                    
                    # 检查是否包含翻译文本
                    if db_translation and db_translation in html:
                        print(f"  ✓ 翻译文本正确显示在页面上")
                    else:
                        print(f"  ⚠️  翻译文本未在页面上找到")
                else:
                    print(f"  ❌ 结果页面不包含中文翻译框")
            else:
                print(f"  ❌ 结果页面加载失败: {result_response.status_code}")
        except Exception as e:
            print(f"  ❌ 结果页面请求失败: {e}")
    
    print("\n" + "="*70)
    print("✅ 端到端测试完成")
    print("="*70)

if __name__ == "__main__":
    test_complete_workflow()
