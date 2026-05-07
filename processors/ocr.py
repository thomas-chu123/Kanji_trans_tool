"""
OCR 文字識別模塊
支持 JPG、PNG 等圖片格式，使用 PaddleOCR 進行日文識別
使用檔案路徑方式傳遞圖片
"""

import logging
import io
import tempfile
from pathlib import Path
from PIL import Image, ImageEnhance
from paddleocr import PaddleOCR

logger = logging.getLogger(__name__)

# 全局 OCR Reader（首次初始化時加載）
_ocr_reader = None


def initialize_ocr():
    """初始化 PaddleOCR 讀取器"""
    global _ocr_reader
    if _ocr_reader is None:
        try:
            logger.info("🔤 初始化 PaddleOCR 讀取器...")
            # 新版 PaddleOCR 配置
            _ocr_reader = PaddleOCR(
                use_doc_orientation_classify=False,  # 禁用文檔方向分類
                use_doc_unwarping=False,             # 禁用文檔變形校正
                use_textline_orientation=False,      # 禁用文本行方向分類
                # engine="transformers",                # 使用 transformers 引擎
                lang='japan'                          # 日文語言
            )
            logger.info("✓ PaddleOCR 讀取器已初始化")
        except Exception as e:
            logger.error(f"❌ PaddleOCR 初始化失敗: {e}", exc_info=True)
            raise
    return _ocr_reader


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
    temp_file = None
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
        
        # 保存圖片到臨時檔案
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            temp_file = tmp.name
            image.save(temp_file)
            logger.info(f"✓ 臨時圖片已保存: {temp_file}")
        
        # 初始化 OCR 讀取器
        ocr_reader = initialize_ocr()
        
        # 進行 OCR 識別（直接傳遞檔案路徑）
        logger.info("🔍 進行文字偵測和識別...")
        result = ocr_reader.predict(temp_file)
        
        # 新版 PaddleOCR 返回結構包含 rec_texts 和 rec_scores
        if not result:
            logger.warning("⚠️  OCR 返回結果為空")
            return ""
        
        # 列出結果的鍵值，用於除錯
        logger.info(f"🔍 OCR 結果鍵值: {result.keys() if isinstance(result, dict) else type(result)}")
        
        # 嘗試不同的結果格式
        rec_texts = None
        rec_scores = None
        
        if isinstance(result, dict):
            rec_texts = result.get('rec_texts', [])
            rec_scores = result.get('rec_scores', [])
        elif isinstance(result, (list, tuple)):
            # 如果是列表格式，可能是舊版本格式
            logger.info(f"📊 結果是列表，長度: {len(result)}")
            if result and isinstance(result[0], dict) and 'rec_texts' in result[0]:
                rec_texts = result[0].get('rec_texts', [])
                rec_scores = result[0].get('rec_scores', [])
            else:
                # 直接使用結果作為文本
                rec_texts = result
        
        if not rec_texts:
            logger.warning(f"⚠️  OCR 未識別到文字 (類型: {type(result)}, 內容: {result if not isinstance(result, dict) else 'dict with keys: ' + str(result.keys())})")
            return ""
        
        # 提取文字（過濾低信心度的結果）
        extracted_lines = []
        confidence_threshold = 0.3  # 置信度閾值
        
        logger.info(f"📊 處理 {len(rec_texts)} 個識別結果")
        
        for i, text in enumerate(rec_texts):
            if not text or not text.strip():
                continue
            
            # 獲取對應的信心度
            confidence = rec_scores[i] if i < len(rec_scores) else 0.9
            
            try:
                confidence = float(confidence)
            except (ValueError, TypeError):
                confidence = 0.9
            
            if confidence >= confidence_threshold:
                extracted_lines.append(text.strip())
                logger.debug(f"  ✓ 識別: '{text[:50]}...' (信心度: {confidence:.2%})")
            else:
                logger.debug(f"  ✗ 跳過低信心度: '{text[:50]}...' (信心度: {confidence:.2%})")
        
        if not extracted_lines:
            logger.warning(f"⚠️  所有識別結果信心度都低於閾值 ({confidence_threshold})")
            return ""
        
        extracted_text = '\n'.join(extracted_lines)
        logger.info(f"✓ OCR 識別完成，提取 {len(extracted_lines)} 行文字 ({len(extracted_text)} 字)")
        
        return extracted_text.strip()
    
    except Exception as e:
        logger.error(f"❌ OCR 識別失敗: {e}", exc_info=True)
        raise ValueError(f"圖片識別失敗: {str(e)}")
    
    finally:
        # 清理臨時檔案
        if temp_file and Path(temp_file).exists():
            try:
                Path(temp_file).unlink()
                logger.debug(f"✓ 臨時檔案已刪除: {temp_file}")
            except Exception as e:
                logger.warning(f"⚠️  無法刪除臨時檔案: {e}")
