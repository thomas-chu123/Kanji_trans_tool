"""
OCR 文字識別模塊
支持 JPG、PNG 等圖片格式，使用 PaddleOCR 進行日文識別
"""

import logging
import io
import numpy as np
from PIL import Image, ImageEnhance
from paddleocr import PaddleOCR

logger = logging.getLogger(__name__)

# 全局 OCR Reader（首次初始化時加載）
_reader = None


def initialize_ocr():
    """初始化 PaddleOCR 讀取器"""
    global _reader
    if _reader is None:
        try:
            logger.info("🔤 初始化 PaddleOCR 讀取器...")
            _reader = PaddleOCR(
                use_angle_cls=True,      # 支援旋轉的文字
                lang='japan',            # 日文語言代碼
                ocr_version='PP-OCRv3'   # 使用 PP-OCRv3 版本
            )
            logger.info("✓ PaddleOCR 讀取器已初始化")
        except Exception as e:
            logger.error(f"❌ PaddleOCR 初始化失敗: {e}", exc_info=True)
            raise
    return _reader


def preprocess_image(image: Image.Image) -> Image.Image:
    """
    預處理圖片以改善 OCR 識別效果
    
    - 增加對比度
    - 銳化圖片
    - 調整亮度
    """
    try:
        # 增加對比度
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)
        
        # 增加銳度
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.2)
        
        # 調整亮度
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.1)
        
        logger.info("✓ 圖片預處理完成")
        return image
    except Exception as e:
        logger.warning(f"⚠️  圖片預處理失敗: {e}")
        return image


async def extract_text_from_image(file_content: bytes) -> str:
    """
    從圖片提取文字
    
    參數：
    - file_content: 圖片二進制內容
    
    返回：
    - 提取的文字內容
    """
    try:
        logger.info(f"📸 開始 PaddleOCR 識別（圖片大小：{len(file_content)} bytes）")
        
        # 打開圖片
        image = Image.open(io.BytesIO(file_content))
        
        # 轉換為 RGB (如果是 RGBA 或其他格式)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        logger.info(f"✓ 圖片已加載，尺寸：{image.size}")
        
        # 預處理圖片
        image = preprocess_image(image)
        
        # 轉換 PIL Image 為 numpy array（PaddleOCR 需要的格式）
        img_array = np.array(image)
        
        # 初始化 OCR 讀取器
        reader = initialize_ocr()
        
        # 進行 OCR 識別 (傳入 numpy array)
        results = reader.ocr(img_array)
        
        if not results or not results[0]:
            logger.warning("⚠️  OCR 未識別到文字")
            return ""
        
        # 提取文字（過濾低信心度的結果）
        extracted_lines = []
        confidence_threshold = 0.3  # 置信度閾值
        
        for line in results[0]:
            if line[1]:  # line[1] 是識別的文字
                confidence = line[2] if len(line) > 2 else 0
                if confidence >= confidence_threshold:
                    extracted_lines.append(line[1])
                    logger.debug(f"  識別: {line[1]} (信心度: {confidence:.2%})")
                else:
                    logger.debug(f"  跳過低信心度: {line[1]} (信心度: {confidence:.2%})")
        
        if not extracted_lines:
            logger.warning(f"⚠️  所有識別結果信心度都低於閾值 ({confidence_threshold})")
            return ""
        
        extracted_text = '\n'.join(extracted_lines)
        logger.info(f"✓ OCR 識別完成，提取 {len(extracted_lines)} 行文字 ({len(extracted_text)} 字)")
        
        return extracted_text.strip()
    
    except Exception as e:
        logger.error(f"❌ OCR 識別失敗: {e}", exc_info=True)
        raise ValueError(f"圖片識別失敗: {str(e)}")
