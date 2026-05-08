"""
PyKakasi 集成模塊
將日文文本轉換為假名讀音和羅馬音
"""

import re
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

try:
    import pykakasi
    PYKAKASI_AVAILABLE = True
except ImportError:
    PYKAKASI_AVAILABLE = False

try:
    import fugashi
    FUGASHI_AVAILABLE = True
except ImportError:
    FUGASHI_AVAILABLE = False

logger = logging.getLogger(__name__)

# 全局 PyKakasi 實例（避免每次請求都重新初始化）
_kakasi_instance: Optional[Any] = None
# 全局 Fugashi 實例（用於詞性分析）
_tagger: Optional[Any] = None


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


def initialize_tagger():
    """
    初始化 Fugashi 詞性標註器（應用啟動時調用，緩存全局）
    用於詞性分析和彩色標注
    """
    global _tagger
    
    if not FUGASHI_AVAILABLE:
        logger.warning("⚠️  Fugashi 未安裝，詞性標注功能不可用")
        return False
    
    try:
        _tagger = fugashi.Tagger()
        logger.info("✓ Fugashi 詞性標註器已初始化")
        return True
    except Exception as e:
        logger.error(f"Fugashi 初始化失敗: {e}")
        return False


def get_tagger() -> Optional[Any]:
    """獲取全局 Fugashi 詞性標註器"""
    global _tagger
    if _tagger is None and FUGASHI_AVAILABLE:
        initialize_tagger()
    return _tagger


# 詞性 → CSS 類名 映射表
# 使用 UnidDic 日文詞性標籤
POS_TO_CSS_CLASS = {
    # 名詞相關
    '名詞': 'pos-noun',                  # 名詞 - 藍色
    
    # 動詞相關
    '動詞': 'pos-verb',                  # 動詞 - 紅色
    
    # 形容詞相關
    '形容詞': 'pos-adj',                 # 形容詞 - 橙色
    '連体詞': 'pos-adj',                 # 連體詞（修飾名詞） - 橙色
    
    # 副詞相關
    '副詞': 'pos-adv',                   # 副詞 - 綠色
    
    # 助詞/助動詞相關
    '助詞': 'pos-part',                  # 助詞 - 紫色
    '助動詞': 'pos-aux',                 # 助動詞 - 紫色
    
    # 連詞相關
    '接続詞': 'pos-cconj',               # 連詞 - 粉紅色
    
    # 代名詞
    '代名詞': 'pos-pron',                # 代名詞 - 靛藍色
    
    # 感嘆詞
    '感動詞': 'pos-intj',                # 感嘆詞 - 粉紅色
    
    # 數詞
    '数詞': 'pos-num',                   # 數詞 - 棕色
    
    # 記號相關
    '補助記号': 'pos-punct',             # 補助記號 - 灰色
    '接尾辞': 'pos-punct',               # 接尾詞 - 灰色
    '接頭辞': 'pos-punct',               # 接頭詞 - 灰色
    
    # 其他
    'X': 'pos-x',                        # 未知 - 灰色
}


def get_pos_tag(word: str) -> Optional[str]:
    """
    使用 Fugashi 獲取單詞的詞性標籤
    
    Args:
        word: 日文詞彙
    
    Returns:
        詞性標籤字符串（日文），失敗時返回 None
    """
    tagger = get_tagger()
    if tagger is None:
        return None
    
    try:
        # Fugashi 分析單詞
        result = tagger(word)
        if result:
            # 獲取第一個（主要）分析結果
            word_obj = result[0]
            # 獲取詞性信息 (pos1 是主要詞性)
            pos = word_obj.feature.pos1
            return pos if pos else None
    except Exception as e:
        logger.debug(f"詞性分析失敗 '{word}': {e}")
    
    return None


def get_css_class_for_pos(pos: Optional[str]) -> str:
    """
    根據詞性返回對應的 CSS 類名
    
    Args:
        pos: 詞性標籤（日文）
    
    Returns:
        CSS 類名，如果沒有對應則返回空字符串
    """
    if pos is None or pos == '*':
        return ""
    
    return POS_TO_CSS_CLASS.get(pos, "")


@dataclass
class ProcessedToken:
    """處理後的詞彙單位"""
    original: str          # 原文（漢字或假名）
    hiragana: str         # 假名形式
    romanji: str          # 羅馬音
    token_type: str       # 詞類: kanji, hiragana, katakana, symbol, number, space
    pos_tag: Optional[str] = None  # 詞性標籤 (如: NOUN, VERB, ADJ 等)


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
    
    改進版本：使用 Fugashi（MeCab）進行詞級別形態素解析，
    然後用 PyKakasi 轉換假名。這樣能正確識別日文詞邊界。
    
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
    
    tagger = get_tagger()
    
    tokens: List[ProcessedToken] = []
    
    try:
        # 按行處理文本（解決 PyKakasi 換行符 bug）
        lines = text.split('\n')
        first_line = True
        
        for line in lines:
            if not first_line:
                # 在行之間添加換行符 token
                tokens.append(ProcessedToken(
                    original='\n',
                    hiragana='',
                    romanji='',
                    token_type='space',
                    pos_tag=None
                ))
            first_line = False
            
            if not line:
                # 空行跳過
                continue
            
            # 🔄 優先使用 Fugashi 進行詞級別形態素解析（改善斷詞）
            if tagger is not None:
                morphemes = tagger(line)
                
                for morpheme in morphemes:
                    original = morpheme.surface  # 表層形式（原文）
                    
                    # 跳過純空格
                    if original.isspace():
                        tokens.append(ProcessedToken(
                            original=original,
                            hiragana='',
                            romanji='',
                            token_type='space',
                            pos_tag=None
                        ))
                        continue
                    
                    token_type = determine_token_type(original)
                    
                    # 獲取詞性標籤
                    pos_tag = None
                    if token_type not in ["space", "symbol"]:
                        # 優先使用 Fugashi 的詞性信息
                        try:
                            pos_info = morpheme.feature.pos1
                            # 對應到 POS_TO_CSS_CLASS
                            if pos_info in POS_TO_CSS_CLASS:
                                pos_tag = pos_info
                            else:
                                # 備用：使用 get_pos_tag
                                pos_tag = get_pos_tag(original)
                        except:
                            pos_tag = get_pos_tag(original)
                    
                    # 使用 PyKakasi 獲取假名和羅馬音
                    hiragana = ''
                    romanji = ''
                    
                    if token_type not in ["space", "symbol"]:
                        kakasi_result = kakasi.convert(original)
                        if kakasi_result:
                            kakasi_item = kakasi_result[0]
                            hiragana = kakasi_item.get('hira', '')
                            romanji = kakasi_item.get('hepburn', kakasi_item.get('romaji', ''))
                            
                            # 簡化羅馬音長音
                            if simplify_long_vowels:
                                romanji = simplify_romanization(romanji)
                    
                    token = ProcessedToken(
                        original=original,
                        hiragana=hiragana,
                        romanji=romanji,
                        token_type=token_type,
                        pos_tag=pos_tag
                    )
                    tokens.append(token)
            else:
                # 備用方案：如果 Fugashi 不可用，使用原來的 PyKakasi 方法
                logger.warning("⚠️  Fugashi 不可用，使用備用的字符級處理")
                result = kakasi.convert(line)
                
                for item in result:
                    original = item['orig']
                    hiragana = item.get('hira', '')
                    romanji = item.get('hepburn', item.get('romaji', ''))
                    
                    if simplify_long_vowels:
                        romanji = simplify_romanization(romanji)
                    
                    token_type = determine_token_type(original)
                    pos_tag = None
                    if token_type not in ["space", "symbol"]:
                        pos_tag = get_pos_tag(original)
                    
                    token = ProcessedToken(
                        original=original,
                        hiragana=hiragana,
                        romanji=romanji,
                        token_type=token_type,
                        pos_tag=pos_tag
                    )
                    tokens.append(token)
        
        logger.info(f"✓ 文本已處理: {len(text)} 字 → {len(tokens)} 詞 (詞級別斷詞改進)")
        return tokens
        
    except Exception as e:
        logger.error(f"文本處理失敗: {e}")
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
    根據詞性添加相應的 CSS 類名，用於彩色標注
    
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
        # 獲取詞性對應的 CSS 類名
        pos_class = get_css_class_for_pos(token.pos_tag)
        pos_attr = f' pos-type="{token.pos_tag}"' if token.pos_tag else ""
        css_classes = f'ruby-group {pos_class}' if pos_class else 'ruby-group'
        
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
                    f'<div class="{css_classes}"{pos_attr}>'
                    f'<div class="ruby-top">{escape_html(token.hiragana)}</div>'
                    f'<div class="ruby-base">{escape_html(token.original)}</div>'
                    f'<div class="ruby-bottom">{escape_html(token.romanji)}</div>'
                    f'</div>'
                )
            else:
                # 沒有 romanji 則直接顯示
                html_parts.append(f'<span class="{pos_class}" {pos_attr}>{escape_html(token.original)}</span>' if pos_class else f'{escape_html(token.original)}')
        
        elif token.token_type == "katakana":
            # 片假名：有真實轉換時才顯示三層
            if token.hiragana != token.original and token.romanji:
                html_parts.append(
                    f'<div class="{css_classes}"{pos_attr}>'
                    f'<div class="ruby-top">{escape_html(token.hiragana)}</div>'
                    f'<div class="ruby-base">{escape_html(token.original)}</div>'
                    f'<div class="ruby-bottom">{escape_html(token.romanji)}</div>'
                    f'</div>'
                )
            else:
                html_parts.append(f'<span class="{pos_class}">{escape_html(token.original)}</span>' if pos_class else f'{escape_html(token.original)}')
        
        elif token.token_type == "kanji":
            # 漢字：上方假名 → 中間漢字 → 下方羅馬音
            if token.hiragana and token.hiragana != token.original:
                html_parts.append(
                    f'<div class="{css_classes}"{pos_attr}>'
                    f'<div class="ruby-top">{escape_html(token.hiragana)}</div>'
                    f'<div class="ruby-base">{escape_html(token.original)}</div>'
                    f'<div class="ruby-bottom">{escape_html(token.romanji)}</div>'
                    f'</div>'
                )
            else:
                # 如果沒有轉換則直接顯示
                html_parts.append(f'<span class="{pos_class}">{escape_html(token.original)}</span>' if pos_class else f'{escape_html(token.original)}')
    
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
