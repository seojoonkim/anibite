"""
Convert Japanese character names to Korean pronunciation
일본어 캐릭터 이름을 한국어 발음으로 변환
"""
import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))

from database import db

# Try to import pykakasi for kanji reading
try:
    import pykakasi
    KAKASI = pykakasi.kakasi()
    HAS_KAKASI = True
except ImportError:
    HAS_KAKASI = False
    print("Warning: pykakasi not installed. Kanji conversion will be limited.")

# Hiragana to Korean mapping
HIRAGANA_TO_KOREAN = {
    # あ행
    'あ': '아', 'い': '이', 'う': '우', 'え': '에', 'お': '오',
    # か행
    'か': '카', 'き': '키', 'く': '쿠', 'け': '케', 'こ': '코',
    'が': '가', 'ぎ': '기', 'ぐ': '구', 'げ': '게', 'ご': '고',
    # さ행
    'さ': '사', 'し': '시', 'す': '스', 'せ': '세', 'そ': '소',
    'ざ': '자', 'じ': '지', 'ず': '즈', 'ぜ': '제', 'ぞ': '조',
    # た행
    'た': '타', 'ち': '치', 'つ': '츠', 'て': '테', 'と': '토',
    'だ': '다', 'ぢ': '지', 'づ': '즈', 'で': '데', 'ど': '도',
    # な행
    'な': '나', 'に': '니', 'ぬ': '누', 'ね': '네', 'の': '노',
    # は행
    'は': '하', 'ひ': '히', 'ふ': '후', 'へ': '헤', 'ほ': '호',
    'ば': '바', 'び': '비', 'ぶ': '부', 'べ': '베', 'ぼ': '보',
    'ぱ': '파', 'ぴ': '피', 'ぷ': '푸', 'ぺ': '페', 'ぽ': '포',
    # ま행
    'ま': '마', 'み': '미', 'む': '무', 'め': '메', 'も': '모',
    # や행
    'や': '야', 'ゆ': '유', 'よ': '요',
    # ら행
    'ら': '라', 'り': '리', 'る': '루', 'れ': '레', 'ろ': '로',
    # わ행
    'わ': '와', 'を': '오', 'ん': 'ㄴ',
    # 작은 글자
    'ゃ': '야', 'ゅ': '유', 'ょ': '요',
    'っ': '',  # 촉음 (다음 자음 중복)
    'ー': '',  # 장음
}

# Katakana to Korean mapping
KATAKANA_TO_KOREAN = {
    # ア행
    'ア': '아', 'イ': '이', 'ウ': '우', 'エ': '에', 'オ': '오',
    # カ행
    'カ': '카', 'キ': '키', 'ク': '쿠', 'ケ': '케', 'コ': '코',
    'ガ': '가', 'ギ': '기', 'グ': '구', 'ゲ': '게', 'ゴ': '고',
    # サ행
    'サ': '사', 'シ': '시', 'ス': '스', 'セ': '세', 'ソ': '소',
    'ザ': '자', 'ジ': '지', 'ズ': '즈', 'ゼ': '제', 'ゾ': '조',
    # タ행
    'タ': '타', 'チ': '치', 'ツ': '츠', 'テ': '테', 'ト': '토',
    'ダ': '다', 'ヂ': '지', 'ヅ': '즈', 'デ': '데', 'ド': '도',
    # ナ행
    'ナ': '나', 'ニ': '니', 'ヌ': '누', 'ネ': '네', 'ノ': '노',
    # ハ행
    'ハ': '하', 'ヒ': '히', 'フ': '후', 'ヘ': '헤', 'ホ': '호',
    'バ': '바', 'ビ': '비', 'ブ': '부', 'ベ': '베', 'ボ': '보',
    'パ': '파', 'ピ': '피', 'プ': '푸', 'ペ': '페', 'ポ': '포',
    # マ행
    'マ': '마', 'ミ': '미', 'ム': '무', 'メ': '메', 'モ': '모',
    # ヤ행
    'ヤ': '야', 'ユ': '유', 'ヨ': '요',
    # ラ행
    'ラ': '라', 'リ': '리', 'ル': '루', 'レ': '레', 'ロ': '로',
    # ワ행
    'ワ': '와', 'ヲ': '오', 'ン': 'ㄴ',
    # 작은 글자
    'ャ': '야', 'ュ': '유', 'ョ': '요',
    'ァ': '아', 'ィ': '이', 'ゥ': '우', 'ェ': '에', 'ォ': '오',
    'ッ': '',  # 촉음
    'ー': '',  # 장음
    # 특수
    'ヴ': '부',
}

# Kanji common readings (most frequent ones)
KANJI_READINGS = {
    # 이름에 자주 나오는 한자
    '一': '이치', '二': '니', '三': '산', '四': '시', '五': '고',
    '六': '로쿠', '七': '시치', '八': '하치', '九': '큐', '十': '쥬',
    '百': '햐쿠', '千': '센', '万': '만',

    # 색상
    '赤': '아카', '青': '아오', '白': '시로', '黒': '쿠로', '金': '킨', '銀': '긴',

    # 자연
    '山': '야마', '川': '카와', '森': '모리', '木': '키', '林': '하야시',
    '海': '우미', '空': '소라', '風': '카제', '火': '히', '水': '미즈',
    '月': '츠키', '日': '히', '星': '호시', '雪': '유키', '雨': '아메',
    '花': '하나', '草': '쿠사', '桜': '사쿠라', '竹': '타케',

    # 신체
    '目': '메', '耳': '미미', '口': '쿠치', '手': '테', '足': '아시',
    '心': '코코로', '頭': '아타마',

    # 성씨 자주 쓰이는 한자
    '田': '타', '村': '무라', '中': '나카', '井': '이', '藤': '토우',
    '野': '노', '原': '하라', '島': '시마', '谷': '타니', '橋': '하시',
    '本': '모토', '上': '우에', '下': '시타', '前': '마에', '後': '고',
    '東': '히가시', '西': '니시', '南': '미나미', '北': '키타',
    '高': '타카', '小': '코', '大': '오오', '長': '나가', '松': '마츠',
    '石': '이시', '池': '이케', '沢': '사와', '浜': '하마',

    # 이름에 자주 쓰이는 한자
    '太': '타', '郎': '로우', '介': '스케', '助': '스케', '平': '헤이',
    '子': '코', '美': '미', '香': '카', '菜': '나', '里': '리',
    '愛': '아이', '恵': '메구미', '優': '유우', '真': '마', '純': '준',
    '明': '아키', '光': '히카루', '輝': '테루', '勇': '유우', '健': '켄',
    '信': '신', '義': '기', '正': '마사', '清': '키요', '秀': '히데',
    '雄': '오', '男': '오', '夫': '오', '彦': '히코', '也': '야',
    '人': '토', '士': '시', '護': '고', '治': '지', '司': '츠카사',

    # 유명 캐릭터 이름 한자
    '護': '고', '崎': '자키', '久': '히사', '朽': '쿠치',
    '織': '오리', '姫': '히메', '魔': '마', '王': '오우',
    '神': '카미', '鬼': '오니', '龍': '류', '虎': '토라',
}

def kanji_to_hiragana(text):
    """Convert kanji to hiragana using pykakasi"""
    if not HAS_KAKASI or not text:
        return text

    result = KAKASI.convert(text)
    # Get hiragana reading
    hiragana = ''.join([item['hira'] for item in result])
    return hiragana


def japanese_to_korean(text):
    """Convert Japanese text to Korean pronunciation"""
    if not text:
        return None

    # First, convert kanji to hiragana using pykakasi
    if HAS_KAKASI:
        text = kanji_to_hiragana(text)

    result = []
    i = 0

    while i < len(text):
        char = text[i]

        # Check for kanji (should be rare if pykakasi worked)
        if '\u4e00' <= char <= '\u9fff':
            if char in KANJI_READINGS:
                result.append(KANJI_READINGS[char])
            else:
                # Unknown kanji - skip or use original
                result.append(char)
        # Check for hiragana
        elif '\u3040' <= char <= '\u309f':
            # Check for combined sounds (きゃ, しゅ, etc.)
            if i + 1 < len(text) and text[i + 1] in 'ゃゅょャュョ':
                combined = char + text[i + 1]
                if combined in COMBINED_SOUNDS:
                    result.append(COMBINED_SOUNDS[combined])
                    i += 2
                    continue
            result.append(HIRAGANA_TO_KOREAN.get(char, char))
        # Check for katakana
        elif '\u30a0' <= char <= '\u30ff':
            # Check for combined sounds
            if i + 1 < len(text) and text[i + 1] in 'ゃゅょャュョァィゥェォ':
                combined = char + text[i + 1]
                if combined in COMBINED_SOUNDS:
                    result.append(COMBINED_SOUNDS[combined])
                    i += 2
                    continue
            result.append(KATAKANA_TO_KOREAN.get(char, char))
        # Punctuation and separators
        elif char in '・':
            result.append(' ')
        elif char in '　 ':
            result.append(' ')
        else:
            # Keep other characters as-is (numbers, latin, etc.)
            result.append(char)

        i += 1

    korean_name = ''.join(result)

    # Clean up
    korean_name = re.sub(r'\s+', ' ', korean_name).strip()

    # Handle ン (ㄴ) - combine with previous syllable
    # 모ㄴ키 → 몬키
    korean_name = combine_korean_syllables(korean_name)

    return korean_name if korean_name else None


def combine_korean_syllables(text):
    """
    Combine ㄴ with previous Korean syllable
    모ㄴ키 → 몬키
    """
    if 'ㄴ' not in text:
        return text

    result = []
    i = 0
    chars = list(text)

    while i < len(chars):
        if i + 1 < len(chars) and chars[i + 1] == 'ㄴ':
            # Check if previous char is Korean syllable
            if '가' <= chars[i] <= '힣':
                # Decompose and add ㄴ as 받침
                syllable = chars[i]
                code = ord(syllable) - 0xAC00
                cho = code // 588
                jung = (code % 588) // 28
                jong = code % 28

                if jong == 0:  # No 받침, can add ㄴ
                    # ㄴ is index 4 in jongsung
                    new_code = 0xAC00 + (cho * 588) + (jung * 28) + 4
                    result.append(chr(new_code))
                    i += 2
                    continue

        result.append(chars[i])
        i += 1

    return ''.join(result)

# Combined sounds (拗音)
COMBINED_SOUNDS = {
    # きゃ행
    'きゃ': '캬', 'きゅ': '큐', 'きょ': '쿄',
    'ぎゃ': '갸', 'ぎゅ': '규', 'ぎょ': '교',
    # しゃ행
    'しゃ': '샤', 'しゅ': '슈', 'しょ': '쇼',
    'じゃ': '자', 'じゅ': '주', 'じょ': '조',
    # ちゃ행
    'ちゃ': '챠', 'ちゅ': '추', 'ちょ': '쵸',
    # にゃ행
    'にゃ': '냐', 'にゅ': '뉴', 'にょ': '뇨',
    # ひゃ행
    'ひゃ': '햐', 'ひゅ': '휴', 'ひょ': '효',
    'びゃ': '뱌', 'びゅ': '뷰', 'びょ': '뵤',
    'ぴゃ': '퍄', 'ぴゅ': '퓨', 'ぴょ': '표',
    # みゃ행
    'みゃ': '먀', 'みゅ': '뮤', 'みょ': '묘',
    # りゃ행
    'りゃ': '랴', 'りゅ': '류', 'りょ': '료',

    # Katakana versions
    'キャ': '캬', 'キュ': '큐', 'キョ': '쿄',
    'ギャ': '갸', 'ギュ': '규', 'ギョ': '교',
    'シャ': '샤', 'シュ': '슈', 'ショ': '쇼',
    'ジャ': '자', 'ジュ': '주', 'ジョ': '조',
    'チャ': '챠', 'チュ': '추', 'チョ': '쵸',
    'ニャ': '냐', 'ニュ': '뉴', 'ニョ': '뇨',
    'ヒャ': '햐', 'ヒュ': '휴', 'ヒョ': '효',
    'ビャ': '뱌', 'ビュ': '뷰', 'ビョ': '뵤',
    'ピャ': '퍄', 'ピュ': '퓨', 'ピョ': '표',
    'ミャ': '먀', 'ミュ': '뮤', 'ミョ': '묘',
    'リャ': '랴', 'リュ': '류', 'リョ': '료',

    # Extended katakana
    'ファ': '파', 'フィ': '피', 'フェ': '페', 'フォ': '포',
    'ティ': '티', 'ディ': '디',
    'ヴァ': '바', 'ヴィ': '비', 'ヴ': '부', 'ヴェ': '베', 'ヴォ': '보',
}


def convert_all_characters(limit=None):
    """Convert all characters with Japanese names to Korean"""

    print("=" * 80)
    print("Japanese to Korean Name Converter")
    print("일본어 → 한국어 이름 변환")
    print("=" * 80)

    # Get characters with Japanese names but no Korean names
    query = """
        SELECT id, name_full, name_native
        FROM character
        WHERE name_native IS NOT NULL
          AND name_korean IS NULL
          AND name_native != ''
        ORDER BY favourites DESC
    """

    if limit:
        query += f" LIMIT {limit}"

    characters = db.execute_query(query)
    print(f"\nFound {len(characters)} characters to convert")

    if not characters:
        print("No characters to convert!")
        return

    success_count = 0
    failed = []

    for i, char in enumerate(characters):
        char_id = char['id']
        name_full = char['name_full']
        name_native = char['name_native']

        korean_name = japanese_to_korean(name_native)

        if korean_name and len(korean_name) >= 2:
            # Check if it's mostly Korean characters
            korean_chars = len(re.findall(r'[가-힣]', korean_name))
            total_chars = len(korean_name.replace(' ', ''))

            if korean_chars / total_chars >= 0.5:  # At least 50% Korean
                db.execute_update(
                    "UPDATE character SET name_korean = ? WHERE id = ?",
                    (korean_name, char_id)
                )
                success_count += 1

                if i < 20 or (i + 1) % 1000 == 0:  # Show first 20 and every 1000th
                    print(f"[{i+1}] {name_full} | {name_native} → {korean_name}")
            else:
                failed.append((name_full, name_native, korean_name))
        else:
            failed.append((name_full, name_native, korean_name))

        if (i + 1) % 5000 == 0:
            print(f"\nProgress: {i+1}/{len(characters)} ({(i+1)/len(characters)*100:.1f}%)")
            print(f"Success: {success_count}")

    print(f"\n{'='*80}")
    print("Conversion Complete!")
    print(f"{'='*80}")
    print(f"Total processed: {len(characters)}")
    print(f"Successful: {success_count} ({success_count/len(characters)*100:.1f}%)")
    print(f"Failed: {len(characters) - success_count}")

    if failed[:10]:
        print(f"\nSample failed conversions:")
        for name_full, name_native, korean in failed[:10]:
            print(f"  {name_full} | {name_native} → {korean}")


if __name__ == "__main__":
    # Test mode: convert first 100
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    convert_all_characters(limit=limit)
