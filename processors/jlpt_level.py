"""
JLPT 等級查詢模組
識別日文單字和文法的 JLPT 等級 (N5, N4, N3, N2, N1)

參考：
- JLPT 官方詞彙表（常見詞彙）
- 文法模式識別
"""

import logging
from typing import Optional, Dict, Set, Tuple, List
from functools import lru_cache

logger = logging.getLogger(__name__)

# ============================================================================
# 詞彙翻譯數據庫 (word: (hiragana_reading, translation, level))
# ============================================================================
VOCABULARY_DATABASE = {
    # N5 - 基礎詞彙
    '食べ物': ('たべもの', 'food; food stuff', 'N5'),
    '食べる': ('たべる', 'to eat', 'N5'),
    '物': ('もの', 'thing; object; something', 'N5'),
    '食': ('しょく', 'food; eating', 'N5'),
    '好き': ('すき', 'like; love', 'N5'),
    '好きです': ('すきです', 'I like it', 'N5'),
    '時間': ('じかん', 'time; hour', 'N5'),
    '今': ('いま', 'now; at present', 'N5'),
    '上': ('うえ', 'up; top; above', 'N5'),
    '時': ('とき', 'time; when', 'N5'),
    '電': ('でん', 'electricity', 'N5'),
    '大': ('だい', 'big; large', 'N5'),
    '生': ('せい', 'birth; life', 'N5'),
    '事': ('こと', 'matter; thing; fact', 'N5'),
    '車': ('くるま', 'car; vehicle', 'N5'),
    '側': ('がわ', 'side; flank', 'N5'),
    '難': ('なん', 'difficult', 'N5'),
    '人': ('ひと', 'person; human', 'N5'),
    '回': ('かい', 'times; occasions', 'N5'),
    '手': ('て', 'hand', 'N5'),
    '令': ('れい', 'order; command; example', 'N5'),
    '自': ('じ', 'oneself; self', 'N5'),
    '段': ('だん', 'step; level; grade', 'N4'),
    '通': ('つう', 'normal; through', 'N4'),
    '状': ('じょう', 'state; condition; shape', 'N4'),
    '配': ('はい', 'distribution; supply', 'N4'),
    '以': ('い', 'by; with; exceeding', 'N4'),
    '協': ('きょう', 'cooperation', 'N3'),
    
    # N4 詞彙
    '昨日': ('きのう', 'yesterday', 'N5'),
    '明日': ('あした', 'tomorrow', 'N5'),
    '朝': ('あさ', 'morning', 'N5'),
    '昼': ('ひる', 'daytime; noon', 'N5'),
    '夜': ('よる', 'night', 'N5'),
    '春': ('はる', 'spring', 'N5'),
    '夏': ('なつ', 'summer', 'N5'),
    '秋': ('あき', 'autumn; fall', 'N5'),
    '冬': ('ふゆ', 'winter', 'N5'),
    '雨': ('あめ', 'rain', 'N5'),
    '雪': ('ゆき', 'snow', 'N5'),
    '風': ('かぜ', 'wind; cold', 'N5'),
    '空': ('そら', 'sky', 'N5'),
    '山': ('やま', 'mountain', 'N5'),
    '川': ('かわ', 'river', 'N5'),
    '海': ('うみ', 'sea; ocean', 'N5'),
    '木': ('き', 'tree; wood', 'N5'),
    '草': ('くさ', 'grass; herb', 'N5'),
    '花': ('はな', 'flower', 'N5'),
    '犬': ('いぬ', 'dog', 'N5'),
    '猫': ('ねこ', 'cat', 'N5'),
    '鳥': ('とり', 'bird', 'N5'),
    '魚': ('さかな', 'fish', 'N5'),
    '牛': ('うし', 'cow', 'N5'),
    '馬': ('うま', 'horse', 'N5'),
    '女': ('おんな', 'woman; female', 'N5'),
    '男': ('おとこ', 'man; male', 'N5'),
    '子': ('こ', 'child; kid', 'N5'),
    '小': ('ちいさい', 'small; little', 'N5'),
    '高': ('たかい', 'high; tall', 'N5'),
    '低': ('ひくい', 'low; short', 'N5'),
    '長': ('ながい', 'long', 'N5'),
    '短': ('みじかい', 'short; brief', 'N5'),
    '新': ('あたらしい', 'new', 'N5'),
    '古': ('ふるい', 'old; ancient', 'N5'),
    '白': ('しろい', 'white', 'N5'),
    '赤': ('あかい', 'red', 'N5'),
    '青': ('あおい', 'blue', 'N5'),
    '黒': ('くろい', 'black', 'N5'),
    '色': ('いろ', 'color', 'N5'),
    '飲む': ('のむ', 'to drink', 'N5'),
    '飲': ('いん', 'drinking', 'N5'),
    '家': ('いえ', 'house; home', 'N5'),
    '建': ('たてる', 'to build; construct', 'N5'),
    '戸': ('と', 'door', 'N5'),
    '口': ('くち', 'mouth', 'N5'),
    '門': ('もん', 'gate; door', 'N5'),
    '駅': ('えき', 'station', 'N5'),
    '電気': ('でんき', 'electricity; electric', 'N5'),
    '気': ('き', 'spirit; mood; attention', 'N5'),
    '光': ('ひかり', 'light', 'N5'),
    '音': ('おと', 'sound; noise', 'N5'),
    '声': ('こえ', 'voice; sound', 'N5'),
    '話': ('はなし', 'story; talk', 'N5'),
    '話す': ('はなす', 'to speak; talk', 'N5'),
    '言': ('いう', 'to say', 'N5'),
    '言葉': ('ことば', 'language; word', 'N5'),
    '文': ('ぶん', 'sentence; composition', 'N5'),
    '字': ('じ', 'character; letter', 'N5'),
    '本': ('ほん', 'book', 'N5'),
    '紙': ('かみ', 'paper', 'N5'),
    '足': ('あし', 'foot; leg', 'N5'),
    '頭': ('あたま', 'head', 'N5'),
    '目': ('め', 'eye', 'N5'),
    '耳': ('みみ', 'ear', 'N5'),
    '鼻': ('はな', 'nose', 'N5'),
    '歯': ('は', 'tooth', 'N5'),
    '舌': ('した', 'tongue', 'N5'),
    '肉': ('にく', 'meat; flesh', 'N5'),
    '骨': ('ほね', 'bone', 'N5'),
    '血': ('ち', 'blood', 'N5'),
    '心': ('こころ', 'heart; mind', 'N5'),
    '脳': ('のう', 'brain', 'N5'),
    '病': ('びょう', 'disease; illness', 'N5'),
    '病気': ('びょうき', 'illness; sickness', 'N5'),
    '薬': ('くすり', 'medicine; drug', 'N5'),
    '医者': ('いしゃ', 'doctor; physician', 'N5'),
    '死': ('しぬ', 'to die', 'N5'),
    '走': ('はしる', 'to run', 'N5'),
    '歩く': ('あるく', 'to walk', 'N5'),
    '来': ('くる', 'to come', 'N5'),
    '行く': ('いく', 'to go', 'N5'),
    '行': ('いく', 'to go', 'N5'),
    '去': ('さる', 'to leave; pass', 'N5'),
    '出': ('でる', 'to go out; come out', 'N5'),
    '入': ('はいる', 'to enter; go in', 'N5'),
    '下': ('した', 'under; below; down', 'N5'),
    '左': ('ひだり', 'left', 'N5'),
    '右': ('みぎ', 'right', 'N5'),
    '前': ('まえ', 'front; before', 'N5'),
    '後': ('うしろ', 'back; behind', 'N5'),
    '中': ('なか', 'middle; inside', 'N5'),
    '外': ('そと', 'outside; outer', 'N5'),
    '内': ('うち', 'inside; interior', 'N5'),
    '東': ('ひがし', 'east', 'N5'),
    '西': ('にし', 'west', 'N5'),
    '南': ('みなみ', 'south', 'N5'),
    '北': ('きた', 'north', 'N5'),
    '働く': ('はたらく', 'to work', 'N5'),
    '職': ('しょく', 'job; occupation', 'N5'),
    '仕': ('し', 'serve; work', 'N5'),
    '仕事': ('しごと', 'work; job; task', 'N5'),
    '作': ('つくる', 'to make; create', 'N5'),
    '道': ('みち', 'road; way; path', 'N5'),
    '路': ('ろ', 'path; road; way', 'N5'),
    '街': ('まち', 'town; street', 'N5'),
    '町': ('まち', 'town', 'N5'),
    '村': ('むら', 'village', 'N5'),
    '市': ('し', 'city; municipality', 'N5'),
    '立': ('たつ', 'to stand; set up', 'N5'),
    '座': ('すわる', 'to sit', 'N5'),
    '寝': ('ねる', 'to sleep; lie down', 'N5'),
    '起': ('おきる', 'to wake up; rise', 'N5'),
    '休': ('やすむ', 'to rest; take a break', 'N5'),
    '止': ('とまる', 'to stop; halt', 'N5'),
    '始': ('はじまる', 'to begin; start', 'N5'),
    '終': ('おわる', 'to end; finish', 'N5'),
    '開': ('あける', 'to open; unlock', 'N5'),
    '閉': ('とじる', 'to close; shut', 'N5'),
    '読': ('よむ', 'to read', 'N5'),
    '書': ('かく', 'to write; paint', 'N5'),
    '見': ('みる', 'to see; look; watch', 'N5'),
    '聞': ('きく', 'to listen; hear; ask', 'N5'),
    '知': ('しる', 'to know; learn', 'N5'),
    '忘': ('わすれる', 'to forget', 'N5'),
    '覚': ('おぼえる', 'to remember; learn', 'N5'),
    '思': ('おもう', 'to think; suppose', 'N5'),
    '感': ('かん', 'feeling; sense', 'N5'),
    '嫌': ('きらい', 'dislike; hate', 'N5'),
    '愛': ('あい', 'love; affection', 'N5'),
    '美': ('うつくしい', 'beautiful', 'N5'),
    '汚': ('きたない', 'dirty; filthy', 'N5'),
    '清': ('きれい', 'clean; pure', 'N5'),
    '暑': ('あつい', 'hot; warm', 'N5'),
    '寒': ('さむい', 'cold', 'N5'),
    '熱': ('あつい', 'hot; heat', 'N5'),
    '冷': ('つめたい', 'cold; cool', 'N5'),
    '温': ('あたたかい', 'warm; mild', 'N5'),
    '暖': ('あたたかい', 'warm; comfortable', 'N5'),
    '弱': ('よわい', 'weak; frail', 'N5'),
    '強': ('つよい', 'strong; powerful', 'N5'),
    '易': ('やさしい', 'easy; simple', 'N5'),
    '重': ('おもい', 'heavy', 'N5'),
    '軽': ('かるい', 'light; easy', 'N5'),
    '深': ('ふかい', 'deep; profound', 'N5'),
    '浅': ('あさい', 'shallow; superficial', 'N5'),
    '広': ('ひろい', 'wide; spacious', 'N5'),
    '狭': ('せまい', 'narrow; tight', 'N5'),
    '多': ('おおい', 'many; numerous', 'N5'),
    '少': ('すくない', 'few; little', 'N5'),
    '数': ('かず', 'number; count', 'N5'),
    '量': ('りょう', 'amount; quantity', 'N5'),
    '値': ('あたい', 'value; price', 'N5'),
    '金': ('かね', 'money; metal', 'N5'),
    '銭': ('せん', 'coin; small money', 'N5'),
    '札': ('さつ', 'bill; banknote', 'N5'),
    '銀': ('ぎん', 'silver; silver coin', 'N5'),
    '銅': ('どう', 'copper', 'N5'),
    '鉄': ('てつ', 'iron', 'N5'),
    '石': ('いし', 'stone; rock', 'N5'),
    '砂': ('すな', 'sand', 'N5'),
    '土': ('つち', 'earth; soil; dirt', 'N5'),
    '泥': ('どろ', 'mud; slime', 'N5'),
    '玉': ('たま', 'ball; jewel; bead', 'N5'),
    '宝': ('たから', 'treasure; precious item', 'N5'),
    '品': ('しな', 'quality; article; goods', 'N5'),
    '商': ('しょう', 'commerce; merchant', 'N5'),
    '売': ('うる', 'to sell', 'N5'),
    '買': ('かう', 'to buy; purchase', 'N5'),
    '安': ('やすい', 'cheap; inexpensive', 'N5'),
    '動': ('うごく', 'to move; motion', 'N5'),
    '切': ('きる', 'to cut', 'N5'),
    '折': ('おる', 'to fold; break', 'N5'),
    '曲': ('まがる', 'to bend; curve; turn', 'N5'),
    '回': ('まわる', 'to turn; rotate', 'N5'),
    '転': ('ころがる', 'to roll; turn over', 'N5'),
    '巻': ('まく', 'to wind; wrap', 'N5'),
    '剥': ('むく', 'to peel; strip', 'N5'),
    '裂': ('さく', 'to tear; rip; split', 'N5'),
    '丸': ('まる', 'round; circle', 'N5'),
    '角': ('かど', 'corner; angle', 'N5'),
    
    # N4 詞彙
    '両': ('りょう', 'both; a pair', 'N4'),
    '並': ('ならぶ', 'to line up; arrange', 'N4'),
    '分': ('ぶん', 'portion; part; minute', 'N4'),
    '半': ('はん', 'half; semi', 'N4'),
    '倍': ('ばい', 'times; multiple; double', 'N4'),
    '厚': ('あつい', 'thick; deep', 'N4'),
    '薄': ('うすい', 'thin; weak; pale', 'N4'),
    '幅': ('はば', 'width; breadth', 'N4'),
    '寸': ('すん', 'measurement unit', 'N4'),
    '尺': ('しゃく', 'Japanese unit of length', 'N4'),
    '升': ('ます', 'measuring box', 'N4'),
    '粒': ('つぶ', 'grain; particle; bead', 'N4'),
    '匹': ('ひき', 'counter for small animals', 'N4'),
    '羽': ('わ', 'counter for birds', 'N4'),
    '尾': ('お', 'tail; end', 'N4'),
    '名': ('めい', 'people (counter); name', 'N4'),
    '奥': ('おく', 'interior; back; depth', 'N4'),
    '端': ('はし', 'edge; end; tip', 'N4'),
    '隅': ('すみ', 'corner; nook', 'N4'),
    '辺': ('へ', 'side; around; vicinity', 'N4'),
    '界': ('かい', 'world; boundary; realm', 'N4'),
    '境': ('さかい', 'border; boundary', 'N4'),
    '限': ('かぎる', 'to limit; restrict', 'N4'),
    '度': ('ど', 'degree; time; occurrence', 'N4'),
    '程': ('ほど', 'degree; extent; about', 'N4'),
    '級': ('きゅう', 'class; grade; rank', 'N4'),
    '順': ('じゅん', 'order; sequence', 'N4'),
    '番': ('ばん', 'order; turn; number', 'N4'),
    '等': ('など', 'et cetera; and so on', 'N4'),
    '種': ('しゅ', 'kind; species; type', 'N4'),
    '類': ('るい', 'kind; class; category', 'N4'),
    '別': ('べつ', 'separate; different; other', 'N4'),
    '様': ('よう', 'appearance; manner; style', 'N4'),
    '格': ('かく', 'rank; frame; form', 'N4'),
    '柄': ('から', 'pattern; design; nature', 'N4'),
    '型': ('かた', 'type; model; form', 'N4'),
    '形': ('かたち', 'shape; form; figure', 'N4'),
    '態': ('たい', 'form; appearance; state', 'N4'),
    '性': ('せい', 'nature; quality; sex', 'N4'),
    '質': ('しつ', 'quality; substance; nature', 'N4'),
    '素': ('そ', 'element; basis; raw', 'N4'),
    '成': ('なる', 'to become; be composed', 'N4'),
    '構': ('かまえる', 'to build; frame; set up', 'N4'),
    '組': ('くみ', 'group; pair; set', 'N4'),
    '造': ('つくり', 'structure; construction', 'N4'),
    '部': ('ぶ', 'part; section; group', 'N4'),
    '塊': ('かたまり', 'lump; chunk; mass', 'N4'),
    '片': ('かた', 'piece; one (of pair)', 'N4'),
    '繰': ('くり', 'repeat; curve', 'N4'),
    '貫': ('つらぬく', 'to pierce; penetrate', 'N4'),
    '通': ('とおる', 'to go through; pass', 'N4'),
    '連': ('れん', 'series; chain; link', 'N4'),
    '続': ('つづく', 'to continue; last', 'N4'),
    '継': ('つぐ', 'to inherit; continue', 'N4'),
    '承': ('うけたまわる', 'to hear; be told', 'N4'),
    '次': ('つぎ', 'next; following; order', 'N4'),
    '序': ('じょ', 'order; beginning; preface', 'N4'),
    '列': ('れつ', 'line; queue; column', 'N4'),
    '並': ('ならべる', 'to arrange; line up', 'N4'),
    '排': ('はい', 'expel; arrange; line up', 'N4'),
    '流': ('なが', 'flow; current; style', 'N4'),
    '派': ('は', 'faction; party; school', 'N4'),
    '系': ('けい', 'line; system; family', 'N4'),
    '統': ('とう', 'system; group; control', 'N4'),
    '脈': ('みゃく', 'pulse; vein; line', 'N4'),
    '末': ('すえ', 'end; last; tip', 'N4'),
    '稍': ('やや', 'somewhat; a little; rather', 'N4'),
    '暫': ('しばらく', 'for a while; temporarily', 'N4'),
    '乍': ('ばかり', 'just; only; but', 'N4'),
    '刻': ('きざむ', 'to carve; cut; engrave', 'N4'),
    '瞬': ('しゅん', 'moment; instant; blink', 'N4'),
    '折': ('おり', 'occasion; time; when', 'N4'),
    '重': ('かさなる', 'to overlap; layer', 'N4'),
    '再': ('さい', 'again; re-; twice', 'N4'),
    '又': ('また', 'again; moreover; or', 'N4'),
    
    # N3 詞彙
    '殆': ('ほとんど', 'almost; mostly; nearly', 'N3'),
    '大抵': ('たいてい', 'usually; generally; mostly', 'N3'),
    '大体': ('だいたい', 'roughly; approximately', 'N3'),
    '略': ('ほぼ', 'almost; nearly; practically', 'N3'),
    '凡': ('およそ', 'about; roughly; generally', 'N3'),
    '共': ('ともに', 'together; with', 'N3'),
    '協': ('きょう', 'cooperation; joint', 'N3'),
    '協力': ('きょうりょく', 'cooperation; help', 'N3'),
    '際': ('さい', 'occasion; time; case', 'N3'),
    '象': ('しょう', 'appearance; phenomenon', 'N3'),
    '象徴': ('しょうちょう', 'symbol; emblem', 'N3'),
    '誰': ('だれ', 'who; someone; anyone', 'N3'),
    '彼': ('かれ', 'he; that man', 'N3'),
    '此': ('この', 'this', 'N3'),
    '自': ('じぶん', 'self; oneself', 'N3'),
    '己': ('おのれ', 'oneself; self', 'N3'),
    '俺': ('おれ', 'I; me (rough)', 'N3'),
    '僕': ('ぼく', 'I; me (informal)', 'N3'),
    '私': ('わたし', 'I; me; private', 'N3'),
    '何': ('なに', 'what; something', 'N3'),
    '何人': ('なんにん', 'how many people', 'N3'),
    '幾': ('いく', 'how many; several', 'N3'),
    '幾何': ('きか', 'geometry', 'N3'),
    '余': ('あまり', 'surplus; excess; remainder', 'N3'),
    '以': ('い', 'by means of; with', 'N3'),
    '未': ('いまだ', 'still; yet; not yet', 'N3'),
    '非': ('ひ', 'non-; not-', 'N3'),
}

# ============================================================================
# N5 等級詞彙（基礎詞彙，最易）
# ============================================================================
JLPT_N5_KANJI = {
    # 常用基礎漢字
    '一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
    '百', '千', '万', '円', '日', '月', '火', '水', '木', '金', '土',
    '曜', '時', '分', '秒', '年', '週', '天', '日', '今', '昨', '明',
    '朝', '昼', '夜', '春', '夏', '秋', '冬', '月', '星', '太', '陽',
    '月', '雨', '雪', '風', '雲', '空', '山', '川', '海', '水', '火',
    '木', '草', '花', '鳥', '魚', '犬', '猫', '牛', '馬', '人', '子',
    '女', '男', '大', '小', '高', '低', '長', '短', '新', '古', '白',
    '黒', '赤', '青', '黄', '緑', '色', '食', '飲', '物', '家', '建',
    '木', '戸', '口', '門', '車', '駅', '電', '気', '光', '音', '声',
    '話', '言', '文', '字', '本', '紙', '手', '足', '頭', '目', '耳',
    '鼻', '口', '歯', '舌', '肉', '骨', '血', '心', '脳', '病', '薬',
    '医', '生', '死', '走', '歩', '来', '行', '去', '出', '入', '上',
    '下', '左', '右', '前', '後', '中', '外', '内', '側', '表', '裏',
    '上', '下', '中', '外', '内', '東', '西', '南', '北', '春', '冬',
    '働', '職', '仕', '事', '作', '道', '路', '街', '町', '村', '市',
    '立', '座', '寝', '起', '休', '止', '始', '終', '開', '閉', '閲',
    '読', '書', '見', '聞', '知', '忘', '覚', '思', '感', '好', '嫌',
    '愛', '嫌', '美', '汚', '清', '暑', '寒', '熱', '冷', '温', '暖',
    '弱', '強', '易', '難', '重', '軽', '深', '浅', '広', '狭', '多',
    '少', '数', '量', '値', '金', '銭', '札', '銀', '銅', '鉄', '石',
    '砂', '土', '泥', '玉', '玉', '宝', '物', '品', '商', '売', '買',
    '値', '安', '高', '安', '安', '立', '座', '寝', '起', '動', '止',
    '切', '折', '曲', '回', '転', '巻', '剥', '裂', '裂', '丸', '角',
}

JLPT_N5_GRAMMAR = {
    # 基礎文法模式
    'ます', 'ません', 'ました', 'ます', 'ません',
    'です', 'ですか', 'ではありません', 'ではないです',
    'ている', 'ていません', 'ていました',
    'ました', 'ませんでした', 'ます', 'ません',
    'た', 'なかった', 'たり', 'ったり',
    'て', 'てください', 'てくださいませんか',
    'て', 'ている', 'てきた', 'ていく',
    'たら', 'たり', 'たら', 'たほうがいい',
    'から', 'ので', 'けれども', 'が',
    'と', 'ば', 'ても', 'ならば',
    'か', 'かもしれません', 'かもしれない',
    'だろう', 'でしょう', 'らしい', 'そうだ',
    'つもり', 'はず', 'ようだ', 'みたい',
    'ほうがいい', 'ほかない', 'しかない', 'ばかり',
    'に', 'を', 'は', 'が', 'で', 'の', 'へ', 'まで',
    'ぐらい', 'くらい', 'だけ', 'など', 'やら', 'まで',
}

# ============================================================================
# N4 等級詞彙（初級上，較常用）
# ============================================================================
JLPT_N4_KANJI = {
    '両', '並', '分', '半', '倍', '厚', '薄', '幅', '寸', '尺', '寸',
    '升', '把', '粒', '匹', '羽', '尾', '頭', '名', '人', '中', '央',
    '奥', '端', '隅', '辺', '界', '境', '限', '度', '程', '段', '階',
    '級', '順', '番', '等', '種', '類', '別', '類', '様', '格', '柄',
    '型', '形', '状', '態', '性', '質', '質', '素', '成', '構', '組',
    '造', '部', '分', '塊', '片', '繰', '貫', '通', '連', '続', '継',
    '承', '次', '序', '列', '列', '並', '列', '排', '列', '配', '置',
    '配', '置', '配', '置', '配', '置', '配', '置', '配', '置', '配',
    '流', '派', '系', '統', '脈', '端', '末', '稍', '暫', '乍', '暫',
    '刻', '瞬', '時', '折', '番', '度', '重', '再', '再', '又', '又',
    '々', '其', '彼', '此', '此', '此', '此', '此', '此', '此', '此',
    '自', '己', '俺', '僕', '私', '俺', '僕', '私', '彼', '彼女', '誰',
    '何', '何', '何', '何', '何', '何', '何', '何', '何', '何', '何',
    '誰', '誰', '何', '何人', '何人', '幾', '幾', '幾何', '幾何', '余',
    '余', '余', '余', '以', '以', '未', '末', '将', '既', '既', '既',
    '既', '既', '既', '既', '非', '非', '未', '未', '未', '未', '未',
    '未', '未', '未', '未', '非', '非', '非', '非', '非', '非', '非',
}

JLPT_N4_GRAMMAR = {
    # N4 文法模式
    'ながら', 'ながら', 'ながらも',
    'つつ', 'つつある',
    'ぶり', 'ぶりに',
    'めく', 'めいた',
    'さ', 'さぐらい',
    'ぎみ', 'ぎみだ',
    'ぶ', 'ぶような',
    'かねない', 'かねる',
    'かねる', 'かねない',
    'ものなら', 'もなら',
    'ものなら', 'もするならば',
    'てまで', 'までに',
    'たくて', 'たくない',
    'たい', 'たい', 'たくない',
    'たかった', 'たくなかった',
    'させる', 'させられる',
    'される', 'させられる',
    'られる', 'られた',
    'られない', 'られていない',
    'くなる', 'くなった',
    'になる', 'になった',
}

# ============================================================================
# N3 等級詞彙（中級下）
# ============================================================================
JLPT_N3_KANJI = {
    '殆', '殆ど', '大抵', '大体', '略', '略', '大凡', '凡そ',
    '共', '共に', '協', '協力', '協同', '協働',
    '際', '際立つ', '際立った',
    '様', '様々', '様子', '様相', '様態',
    '象', '象徴', '象', '象', '象',
    '誰彼', '誰彼なく',
    '等', '等々', '等価', '等差',
    '曰', '曰く',
    '瑪', '瑪瑙',
    '鏡', '鏡像', '鏡映',
}

JLPT_N3_GRAMMAR = {
    # N3 文法模式
    'ぞ', 'ぞと',
    'ぶ', 'ぶような',
    'ぶり', 'ぶりに',
    'ぐらい', 'くらい',
    'たって', 'たっても', 'たてば',
    'たり', 'たりなんかしない',
    'てからでないと', 'てからでなければ',
    'てから', 'てからだ',
    'なくてはならない', 'なくてはならぬ',
    'ておく', 'ておかなければ',
    'てしまう', 'てしまった',
    'てみせる', 'てみて',
    'てほしい', 'てくださいませんか',
    'てのける', 'てのけた',
    'てはばかられる', 'ても憚られない',
    'ばかりか', 'ばかりか',
    'ばかりでなく', 'ばかりでなく',
    'ばこそ', 'ばこそだ',
    'ばかり', 'ばかりだ',
    'ばかりが', 'ばかりか',
    'ばかりで', 'ばかりだ',
    'ばかりの', 'ばかりだ',
    'ばかりを', 'ばかりだ',
    'ばいい', 'ばいいだろう',
    'ばいい', 'ばいいのに',
    'ばいい', 'ばいいだろう',
    'ばいい', 'ばいいのに',
    'ばいい', 'ばいいだろう',
    'ばいい', 'ばいいのに',
    'ばいい', 'ばいいだろう',
    'ばいい', 'ばいいのに',
}

# ============================================================================
# N2 等級詞彙（中級上）
# ============================================================================
JLPT_N2_KANJI = {
    '徴', '徴候', '徴兆', '徴', '徴',
    '昭', '昭和',
    '象', '象徴', '象', '象',
    '適', '適切', '適当', '適度', '適応', '適用',
}

JLPT_N2_GRAMMAR = {
    'ものなら', 'もするならば',
    'かねない', 'かねる',
    'ばからず', 'ばかりか',
    'てならない', 'てはならない',
    'ておく', 'ておかなければ',
    'ておっく', 'ておいた',
}

# ============================================================================
# N1 等級詞彙（上級）
# ============================================================================
JLPT_N1_KANJI = {
    '芊', '艎', '艏', '艐', '艑', '艒', '艓',
}

JLPT_N1_GRAMMAR = {
    'もさることながら', 'もさることながら',
}

# ============================================================================
# 合併所有等級的詞彙集合
# ============================================================================
# N5 及以下（仅 N5）
KANJI_N5_AND_BELOW = JLPT_N5_KANJI
GRAMMAR_N5_AND_BELOW = JLPT_N5_GRAMMAR

# N4 及以下
KANJI_N4_AND_BELOW = JLPT_N5_KANJI | JLPT_N4_KANJI
GRAMMAR_N4_AND_BELOW = JLPT_N5_GRAMMAR | JLPT_N4_GRAMMAR

# N3 及以下
KANJI_N3_AND_BELOW = JLPT_N5_KANJI | JLPT_N4_KANJI | JLPT_N3_KANJI
GRAMMAR_N3_AND_BELOW = JLPT_N5_GRAMMAR | JLPT_N4_GRAMMAR | JLPT_N3_GRAMMAR

# N2 及以下
KANJI_N2_AND_BELOW = JLPT_N5_KANJI | JLPT_N4_KANJI | JLPT_N3_KANJI | JLPT_N2_KANJI
GRAMMAR_N2_AND_BELOW = JLPT_N5_GRAMMAR | JLPT_N4_GRAMMAR | JLPT_N3_GRAMMAR | JLPT_N2_GRAMMAR

# N1（所有等級）
KANJI_N1_AND_BELOW = JLPT_N5_KANJI | JLPT_N4_KANJI | JLPT_N3_KANJI | JLPT_N2_KANJI | JLPT_N1_KANJI
GRAMMAR_N1_AND_BELOW = JLPT_N5_GRAMMAR | JLPT_N4_GRAMMAR | JLPT_N3_GRAMMAR | JLPT_N2_GRAMMAR | JLPT_N1_GRAMMAR


def get_kanji_level(kanji: str) -> Optional[str]:
    """
    查詢單個漢字的 JLPT 等級
    
    Args:
        kanji: 單個漢字
        
    Returns:
        等級字符串 ('N5', 'N4', 'N3', 'N2', 'N1') 或 None（未知）
    """
    if kanji in JLPT_N5_KANJI:
        return 'N5'
    elif kanji in JLPT_N4_KANJI:
        return 'N4'
    elif kanji in JLPT_N3_KANJI:
        return 'N3'
    elif kanji in JLPT_N2_KANJI:
        return 'N2'
    elif kanji in JLPT_N1_KANJI:
        return 'N1'
    return None


def get_grammar_level(grammar: str) -> Optional[str]:
    """
    查詢文法表達式的 JLPT 等級
    
    Args:
        grammar: 文法表達式（如：ている、ました、ばかり）
        
    Returns:
        等級字符串 ('N5', 'N4', 'N3', 'N2', 'N1') 或 None（未知）
    """
    if grammar in JLPT_N5_GRAMMAR:
        return 'N5'
    elif grammar in JLPT_N4_GRAMMAR:
        return 'N4'
    elif grammar in JLPT_N3_GRAMMAR:
        return 'N3'
    elif grammar in JLPT_N2_GRAMMAR:
        return 'N2'
    elif grammar in JLPT_N1_GRAMMAR:
        return 'N1'
    return None


def filter_by_level(items: Dict[str, str], min_level: str = 'N5') -> Dict[str, str]:
    """
    按 JLPT 等級過濾項目
    N1 包含所有等級，N4 包含 N4 和 N5，以此類推
    
    Args:
        items: {item: level} 字典
        min_level: 最低等級 ('N1' 表示所有，'N5' 表示僅 N5)
        
    Returns:
        過濾後的字典
    """
    level_order = {'N5': 0, 'N4': 1, 'N3': 2, 'N2': 3, 'N1': 4}
    min_level_value = level_order.get(min_level, 0)
    
    return {
        item: level
        for item, level in items.items()
        if level_order.get(level, 0) <= min_level_value
    }


def categorize_by_level(items: Dict[str, str]) -> Dict[str, List[str]]:
    """
    按等級分類項目
    
    Args:
        items: {item: level} 字典
        
    Returns:
        {level: [items...]} 結構的分類字典
    """
    categorized = {
        'N5': [],
        'N4': [],
        'N3': [],
        'N2': [],
        'N1': [],
    }
    
    for item, level in items.items():
        if level in categorized:
            categorized[level].append(item)
    
    return categorized


def extract_grammatical_patterns(tokens_with_types: List[Tuple[str, str]]) -> List[str]:
    """
    從 token 列表中提取可能的文法模式
    
    Args:
        tokens_with_types: [(token, type), ...] 列表
        
    Returns:
        文法模式列表
    """
    patterns = []
    
    # 提取連續的平假名片段（可能是文法）
    for token, token_type in tokens_with_types:
        if token_type == 'hiragana' and len(token) >= 2:
            patterns.append(token)
            
            # 也加入子模式（例如 ている → ている、ている）
            if len(token) > 3:
                # 加入後 2 個字符
                patterns.append(token[-2:])
                # 加入後 3 個字符
                if len(token) > 4:
                    patterns.append(token[-3:])
    
    return list(set(patterns))  # 去重


def extract_kanji(tokens_with_types: List[Tuple[str, str]]) -> List[str]:
    """
    從 token 列表中提取完整的詞彙（帶漢字的詞）
    
    Args:
        tokens_with_types: [(token, type), ...] 列表
        
    Returns:
        詞彙列表（去重）
    """
    vocab_list = []
    
    for token, token_type in tokens_with_types:
        if token_type == 'kanji':
            # 提取完整詞彙（不拆分單個字符）
            vocab_list.append(token)
    
    return list(set(vocab_list))  # 去重


def get_vocabulary_info(word: str) -> Optional[Tuple[str, str, str]]:
    """
    查詢詞彙的讀音、翻譯和 JLPT 等級
    
    Args:
        word: 日文詞彙
        
    Returns:
        (讀音, 翻譯, 等級) 元組，查不到返回 None
    """
    if word in VOCABULARY_DATABASE:
        return VOCABULARY_DATABASE[word]
    return None


def extract_vocabulary_with_info(tokens_with_types: List[Tuple[str, str]]) -> Dict[str, Dict]:
    """
    從 token 列表中提取完整詞彙及其翻譯信息
    
    Args:
        tokens_with_types: [(token, type), ...] 列表
        
    Returns:
        {詞: {reading, translation, level}} 字典
    """
    vocabulary = {}
    
    for token, token_type in tokens_with_types:
        if token_type == 'kanji':
            # 避免重複
            if token not in vocabulary:
                # 查詢詞彙數據庫
                info = get_vocabulary_info(token)
                if info:
                    reading, translation, level = info
                    vocabulary[token] = {
                        'reading': reading,
                        'translation': translation,
                        'level': level
                    }
                else:
                    # 如果找不到，盡量使用默認值
                    vocabulary[token] = {
                        'reading': '',
                        'translation': '(未知詞彙)',
                        'level': 'N1'  # 預設為最高級
                    }
    
    return vocabulary
