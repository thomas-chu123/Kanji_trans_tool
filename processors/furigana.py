"""
PyKakasi 集成模塊
將日文文本轉換為假名讀音和羅馬音
"""

import re
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

try:
    import pykakasi
    PYKAKASI_AVAILABLE = True
except ImportError:
    PYKAKASI_AVAILABLE = False

logger = logging.getLogger(__name__)

# 全局 PyKakasi 實例（避免每次請求都重新初始化）
_kakasi_instance: Optional[pykakasi.kakasi] = None


def initialize_kakasi():
    """
    初始化 PyKakasi 實例（應用啟動時調用，緩存全局）
    防止每次請求都重新初始化，提高性能
    """
    global _kakasi_instance
    
    if not PYKAKASI_AVAILABLE:
        logger.error("PyKakasi 未安裝")
        return False
    
    try:
        _kakasi_instance = pykakasi.kakasi()
        logger.info("✓ PyKakasi 已初始化")
        return True
    except Exception as e:
        logger.error(f"PyKakasi 初始化失敗: {e}")
        return False


def get_kakasi_instance() -> Optional[pykakasi.kakasi]:
    """獲取全局 PyKakasi 實例"""
    global _kakasi_instance
    if _kakasi_instance is None:
        initialize_kakasi()
    return _kakasi_instance


@dataclass
class ProcessedToken:
    """處理後的詞彙單位"""
    original: str          # 原文（漢字或假名）
    hiragana: str         # 假名形式
    romanji: str          # 羅馬音
    token_type: str       # 詞類: kanji, hiragana, katakana, symbol, number, space


def katakana_to_hiragana(katakana: str) -> str:
    """
    將片假名（katakana）轉換為平假名（hiragana）
    
    Unicode 映射：
    - 片假名（u30A0-u30FF）→ 平假名（u3040-u309F）
    """
    hiragana = ""
    for char in katakana:
        # 片假名 Unicode 範圍：U+30A0 ~ U+30FF
        # 平假名 Unicode 範圍：U+3040 ~ U+309F
        if '\u30a0' <= char <= '\u30ff':
            # 直接轉換
            hiragana += chr(ord(char) - 0x60)
        else:
            hiragana += char
    return hiragana


def determine_token_type(text: str) -> str:
    """
    判定文本的類型
    """
    if not text:
        return "space"
    
    if re.match(r'[\u3040-\u309F]+', text):  # 平假名範圍
        return "hiragana"
    elif re.match(r'[\u30A0-\u30FF]+', text):  # 片假名範圍
        return "katakana"
    elif re.match(r'[\u4E00-\u9FFF]+', text):  # 漢字範圍
        return "kanji"
    elif re.match(r'[\d０-９]+', text):  # 數字（包括全角）
        return "number"
    elif text.isspace():
        return "space"
    else:
        return "symbol"


def process_text(text: str, simplify_long_vowels: bool = True) -> List[ProcessedToken]:
    """
    輸入日文文本，輸出結構化數據
    
    Args:
        text: 日文文本（支持混合假名、漢字、符號）
        simplify_long_vowels: 是否簡化羅馬音長音（ou→ou, uu→uu）
    
    Returns:
        ProcessedToken 列表
    
    Raises:
        ValueError: 文本為空或不是字符串
    """
    
    if not isinstance(text, str):
        raise ValueError("輸入必須是字符串")
    
    text = text.strip()
    if not text:
        raise ValueError("文本不能為空")
    
    kakasi = get_kakasi_instance()
    if kakasi is None:
        logger.error("PyKakasi 實例不可用")
        raise RuntimeError("日文處理引擎初始化失敗")
    
    tokens: List[ProcessedToken] = []
    
    try:
        # 使用 PyKakasi 進行轉換
        result = kakasi.convert(text)
        
        for item in result:
            original = item['orig']
            # PyKakasi 直接提供 hiragana（hira 字段）
            hiragana = item.get('hira', '')
            romanji = item.get('hepburn', item.get('romaji', ''))
            
            # 簡化羅馬音長音
            if simplify_long_vowels:
                romanji = simplify_romanization(romanji)
            
            token_type = determine_token_type(original)
            
            token = ProcessedToken(
                original=original,
                hiragana=hiragana,
                romanji=romanji,
                token_type=token_type
            )
            tokens.append(token)
        
        logger.info(f"✓ 文本已處理: {len(text)} 字 → {len(tokens)} 詞")
        return tokens
        
    except Exception as e:
        logger.error(f"PyKakasi 處理失敗: {e}")
        raise RuntimeError(f"文本處理失敗: {e}")


def simplify_romanization(romanji: str) -> str:
    """
    簡化羅馬音（移除長音符號，便於打字）
    
    例：
    - ō → o
    - ū → u
    - (oo) → ou (自動處理)
    """
    # 移除長音符號
    romanji = romanji.replace('ō', 'o')
    romanji = romanji.replace('ū', 'u')
    romanji = romanji.replace('ā', 'a')
    romanji = romanji.replace('ī', 'i')
    romanji = romanji.replace('ē', 'e')
    
    return romanji


def generate_ruby_html(tokens: List[ProcessedToken], simplify_long_vowels: bool = True) -> str:
    """
    將結構化數據轉換為 HTML Ruby 標籤
    
    三層展示：上方假名 → 中間日文字 → 下方羅馬音
    
    Args:
        tokens: process_text() 的輸出
        simplify_long_vowels: 是否簡化羅馬音
    
    Returns:
        HTML 字符串
    """
    
    if not tokens:
        return ""
    
    html_parts: List[str] = []
    
    for token in tokens:
        if token.token_type == "space":
            # 保留空格
            html_parts.append(" ")
        
        elif token.token_type == "number":
            # 數字直接顯示，不需要上下層
            html_parts.append(f'<span class="number">{escape_html(token.original)}</span>')
        
        elif token.token_type == "symbol":
            # 符號直接顯示，不需要上下層
            html_parts.append(f'<span class="symbol">{escape_html(token.original)}</span>')
        
        elif token.token_type == "hiragana":
            # 純假名：如果有 romanji 才顯示三層
            if token.romanji and token.romanji != token.original:
                html_parts.append(
                    f'<div class="ruby-group">'
                    f'<div class="ruby-top">{escape_html(token.hiragana)}</div>'
                    f'<div class="ruby-base">{escape_html(token.original)}</div>'
                    f'<div class="ruby-bottom">{escape_html(token.romanji)}</div>'
                    f'</div>'
                )
            else:
                # 沒有 romanji 則直接顯示
                html_parts.append(f'{escape_html(token.original)}')
        
        elif token.token_type == "katakana":
            # 片假名：有真實轉換時才顯示三層
            if token.hiragana != token.original and token.romanji:
                html_parts.append(
                    f'<div class="ruby-group">'
                    f'<div class="ruby-top">{escape_html(token.hiragana)}</div>'
                    f'<div class="ruby-base">{escape_html(token.original)}</div>'
                    f'<div class="ruby-bottom">{escape_html(token.romanji)}</div>'
                    f'</div>'
                )
            else:
                html_parts.append(f'{escape_html(token.original)}')
        
        elif token.token_type == "kanji":
            # 漢字：上方假名 → 中間漢字 → 下方羅馬音
            if token.hiragana and token.hiragana != token.original:
                html_parts.append(
                    f'<div class="ruby-group">'
                    f'<div class="ruby-top">{escape_html(token.hiragana)}</div>'
                    f'<div class="ruby-base">{escape_html(token.original)}</div>'
                    f'<div class="ruby-bottom">{escape_html(token.romanji)}</div>'
                    f'</div>'
                )
            else:
                # 如果沒有轉換則直接顯示
                html_parts.append(f'{escape_html(token.original)}')
    
    # 包裝在容器中
    html_content = "".join(html_parts)
    
    html = f"""<div class="ruby-container">
{html_content}
</div>"""
    
    return html


def escape_html(text: str) -> str:
    """對 HTML 特殊字符進行轉義"""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&#39;")
    return text


def convert_text(text: str, simplify_long_vowels: bool = True) -> tuple[List[ProcessedToken], str]:
    """
    一次性完成轉換：從日文文本到 HTML Ruby
    
    Args:
        text: 日文文本
        simplify_long_vowels: 是否簡化羅馬音
    
    Returns:
        (tokens, html) 元組
    """
    tokens = process_text(text, simplify_long_vowels=simplify_long_vowels)
    html = generate_ruby_html(tokens, simplify_long_vowels=simplify_long_vowels)
    return tokens, html
