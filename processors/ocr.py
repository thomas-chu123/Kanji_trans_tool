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
import asyncio
import sys
import os

logger = logging.getLogger(__name__)

# 全局 OCR Reader（首次初始化時加載）
_ocr_reader = None

# 禁用 PaddleOCR 的日誌干擾
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
paddle_logger = logging.getLogger('paddle')
paddle_logger.setLevel(logging.ERROR)
paddleocr_logger = logging.getLogger('paddleocr')
paddleocr_logger.setLevel(logging.ERROR)


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
        logger.info(f"📢 [DEBUG] 準備呼叫 predict()，temp_file={temp_file}")
        sys.stderr.flush()
        sys.stdout.flush()
        
        # 使用 asyncio.to_thread 在線程中執行同步的 predict 方法
        try:
            result = await asyncio.to_thread(ocr_reader.predict, temp_file)
        except Exception as e:
            logger.error(f"❌ 執行 predict() 失敗: {e}", exc_info=True)
            sys.stderr.flush()
            raise ValueError(f"圖片識別失敗: {str(e)}")
        
        sys.stderr.flush()
        sys.stdout.flush()
        
        logger.info(f"📢 [DEBUG] predict() 返回，result 類型: {type(result)}")
        logger.info(f"📢 [DEBUG] result 是否為 None: {result is None}")
        logger.info(f"📢 [DEBUG] result 是否為空 (bool): {not result}")
        
        if isinstance(result, list):
            logger.info(f"📢 [DEBUG] result 是列表，長度: {len(result)}")
        elif hasattr(result, '__len__'):
            logger.info(f"📢 [DEBUG] result 有長度: {len(result)}")
        
        # 提取識別結果
        extracted_lines = []
        
        if not result:
            logger.warning("⚠️  OCR 返回結果為空")
            return ""
        
        logger.info("📢 [DEBUG] 通過空值檢查，開始處理結果")
        
        # PaddleOCR 可能返回單個結果或列表，每個可能都有 rec_texts
        try:
            # 統一為列表處理
            result_list = result if isinstance(result, list) else [result]
            logger.info(f"📊 處理 {len(result_list)} 個 OCR 結果對象")
            
            for idx, res in enumerate(result_list):
                # 嘗試從每個結果對象中提取 rec_texts
                rec_texts = None
                
                # 方式 1: 對象屬性
                if hasattr(res, 'rec_texts'):
                    rec_texts = res.rec_texts
                    logger.debug(f"  結果 [{idx}] 通過屬性獲得 rec_texts")
                
                # 方式 2: 字典鍵
                elif isinstance(res, dict) and 'rec_texts' in res:
                    rec_texts = res['rec_texts']
                    logger.debug(f"  結果 [{idx}] 通過字典鍵獲得 rec_texts")
                
                if rec_texts:
                    logger.info(f"  結果 [{idx}]: 獲得 {len(rec_texts)} 行文字")
                    # 提取非空文本
                    valid_texts = [text.strip() for text in rec_texts 
                                  if text and isinstance(text, str) and text.strip()]
                    extracted_lines.extend(valid_texts)
                    logger.info(f"  結果 [{idx}]: 提取 {len(valid_texts)} 行有效文字")
                else:
                    logger.debug(f"  結果 [{idx}]: 未找到 rec_texts")
            
            if not extracted_lines:
                logger.warning("⚠️  所有結果中都未找到文字")
                return ""
            
            logger.info(f"✓ OCR 識別完成，共提取 {len(extracted_lines)} 行文字 ({sum(len(t) for t in extracted_lines)} 字)")
        
        except Exception as e:
            logger.error(f"❌ 解析 OCR 結果失敗: {e}", exc_info=True)
            return ""
        
        extracted_text = '\n'.join(extracted_lines)
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
