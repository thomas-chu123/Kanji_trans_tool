"""
OCR 功能測試
"""

import asyncio
import sys
from pathlib import Path

# 添加 processors 模塊到路徑
sys.path.insert(0, str(Path(__file__).parent))

async def test_ocr():
    """測試 OCR 功能"""
    try:
        from processors.ocr import initialize_ocr, extract_text_from_image
        from PIL import Image, ImageDraw, ImageFont
        import io
        
        print("🧪 開始 OCR 功能測試...")
        
        # 創建測試圖片
        print("📸 創建測試圖片...")
        image = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(image)
        
        # 在圖片中添加日文文字
        test_text = "こんにちは、世界！日本語です。"
        draw.text((50, 50), test_text, fill='black')
        
        # 轉換為字節
        image_bytes = io.BytesIO()
        image.save(image_bytes, format='PNG')
        image_content = image_bytes.getvalue()
        
        print(f"✓ 測試圖片已創建（{len(image_content)} bytes）")
        
        # 測試 OCR 識別
        print("\n🔤 初始化 OCR 讀取器...")
        initialize_ocr()
        print("✓ OCR 讀取器初始化完成")
        
        print("\n📖 開始識別圖片文字...")
        result = await extract_text_from_image(image_content)
        print(f"✓ 識別結果：\n{result}")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_ocr())
    sys.exit(0 if success else 1)
