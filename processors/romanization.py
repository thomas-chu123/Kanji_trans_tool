"""
羅馬音轉換模塊
支持多種羅馬音標準
"""

import logging

logger = logging.getLogger(__name__)


def convert_to_hepburn(hiragana: str) -> str:
    """
    將平假名轉換為 Hepburn 羅馬音
    
    Hepburn 是最廣泛使用的羅馬音標準
    
    Args:
        hiragana: 平假名字符串
    
    Returns:
        Hepburn 式羅馬音
    """
    
    # 映射表：平假名 → Hepburn 羅馬音
    # 基於 PyKakasi 的 Hepburn 標準
    mapping = {
        'あ': 'a', 'い': 'i', 'う': 'u', 'え': 'e', 'お': 'o',
        'か': 'ka', 'き': 'ki', 'く': 'ku', 'け': 'ke', 'こ': 'ko',
        'が': 'ga', 'ぎ': 'gi', 'ぐ': 'gu', 'げ': 'ge', 'ご': 'go',
        'さ': 'sa', 'し': 'shi', 'す': 'su', 'せ': 'se', 'そ': 'so',
        'ざ': 'za', 'じ': 'ji', 'ず': 'zu', 'ぜ': 'ze', 'ぞ': 'zo',
        'た': 'ta', 'ち': 'chi', 'つ': 'tsu', 'て': 'te', 'と': 'to',
        'だ': 'da', 'ぢ': 'ji', 'づ': 'zu', 'で': 'de', 'ど': 'do',
        'な': 'na', 'に': 'ni', 'ぬ': 'nu', 'ね': 'ne', 'の': 'no',
        'は': 'ha', 'ひ': 'hi', 'ふ': 'fu', 'へ': 'he', 'ほ': 'ho',
        'ば': 'ba', 'び': 'bi', 'ぶ': 'bu', 'べ': 'be', 'ぼ': 'bo',
        'ぱ': 'pa', 'ぴ': 'pi', 'ぷ': 'pu', 'ぺ': 'pe', 'ぽ': 'po',
        'ま': 'ma', 'み': 'mi', 'む': 'mu', 'め': 'me', 'も': 'mo',
        'や': 'ya', 'ゆ': 'yu', 'よ': 'yo',
        'ら': 'ra', 'り': 'ri', 'る': 'ru', 'れ': 're', 'ろ': 'ro',
        'わ': 'wa', 'を': 'wo', 'ん': 'n',
        
        # 濁音組合（需要特殊處理）
        'きゃ': 'kya', 'きゅ': 'kyu', 'きょ': 'kyo',
        'しゃ': 'sha', 'しゅ': 'shu', 'しょ': 'sho',
        'ちゃ': 'cha', 'ちゅ': 'chu', 'ちょ': 'cho',
        'にゃ': 'nya', 'にゅ': 'nyu', 'にょ': 'nyo',
        'ひゃ': 'hya', 'ひゅ': 'hyu', 'ひょ': 'hyo',
        'みゃ': 'mya', 'みゅ': 'myu', 'みょ': 'myo',
        'りゃ': 'rya', 'りゅ': 'ryu', 'りょ': 'ryo',
        'ぎゃ': 'gya', 'ぎゅ': 'gyu', 'ぎょ': 'gyo',
        'じゃ': 'ja', 'じゅ': 'ju', 'じょ': 'jo',
        'びゃ': 'bya', 'びゅ': 'byu', 'びょ': 'byo',
        'ぴゃ': 'pya', 'ぴゅ': 'pyu', 'ぴょ': 'pyo',
    }
    
    result = []
    i = 0
    
    while i < len(hiragana):
        # 嘗試 3 字符組合
        if i + 2 < len(hiragana):
            trigram = hiragana[i:i+3]
            if trigram in mapping:
                result.append(mapping[trigram])
                i += 3
                continue
        
        # 嘗試 2 字符組合
        if i + 1 < len(hiragana):
            bigram = hiragana[i:i+2]
            if bigram in mapping:
                result.append(mapping[bigram])
                i += 2
                continue
        
        # 單字符
        char = hiragana[i]
        if char in mapping:
            result.append(mapping[char])
        else:
            # 未知字符，保持原樣
            result.append(char)
        
        i += 1
    
    return ''.join(result)


def normalize_romanization(romanji: str) -> str:
    """
    標準化羅馬音輸出
    
    - 移除多餘空格
    - 統一大小寫（句首大寫）
    """
    # 移除多餘空格
    romanji = ' '.join(romanji.split())
    
    # 句首大寫（可選）
    # romanji = romanji[0].upper() + romanji[1:] if romanji else romanji
    
    return romanji


def handle_long_vowels(hiragana: str, style: str = "hepburn") -> str:
    """
    處理長音符號
    
    例：
    - 'おう' → 'ō' (Hepburn, 打字時簡化為 'ou')
    - 'うう' → 'ū' (Hepburn, 打字時簡化為 'uu')
    
    Args:
        hiragana: 平假名
        style: 羅馬音風格 ('hepburn', 'kunrei', 'nihon')
    
    Returns:
        處理後的羅馬音
    """
    
    romanji = convert_to_hepburn(hiragana)
    
    # 標準化長音符號
    # 注：實際上 Web 版本建議直接使用 ou/uu（無長音符號）便於打字
    
    return romanji


# 替代方案：使用外部庫 romkan（如果 PyKakasi 失效）
def try_romkan_fallback(hiragana: str) -> str:
    """
    嘗試使用 romkan 庫作為備選方案
    """
    try:
        import romkan
        return romkan.to_hepburn(hiragana)
    except ImportError:
        logger.warning("romkan 庫未安裝，使用本地映射表")
        return convert_to_hepburn(hiragana)
    except Exception as e:
        logger.error(f"romkan 轉換失敗: {e}")
        return convert_to_hepburn(hiragana)
