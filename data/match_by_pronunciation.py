#!/usr/bin/env python3
"""
발음 기반 일본어→한국어 캐릭터 이름 매칭

같은 애니메이션 내에서:
1. 이미 한국어 이름이 있는 캐릭터의 일본어→한국어 패턴을 학습
2. 한국어 이름이 없는 캐릭터에 적용

예: 귀멸의 칼날에서
   竈門炭治郎 → 카마도 탄지로 (있음)
   竈門禰豆子 → 카마도 네즈코 (없음이었다면 패턴으로 매칭)
"""
import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))

from database import db


def log(msg):
    print(msg, flush=True)


# 가타카나→한글 변환 테이블 (발음 기반)
KATAKANA_TO_KOREAN = {
    # 기본 모음
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
    'ワ': '와', 'ヲ': '오', 'ン': '은',
    # 소문자 (요음)
    'ャ': '야', 'ュ': '유', 'ョ': '요',
    'ッ': '', 'ー': '',  # 촉음, 장음
    # 확장
    'ヴ': '브',
    'ァ': '아', 'ィ': '이', 'ゥ': '우', 'ェ': '에', 'ォ': '오',
}

# 히라가나→가타카나 변환 (발음 동일)
HIRAGANA_TO_KATAKANA = {
    'あ': 'ア', 'い': 'イ', 'う': 'ウ', 'え': 'エ', 'お': 'オ',
    'か': 'カ', 'き': 'キ', 'く': 'ク', 'け': 'ケ', 'こ': 'コ',
    'が': 'ガ', 'ぎ': 'ギ', 'ぐ': 'グ', 'げ': 'ゲ', 'ご': 'ゴ',
    'さ': 'サ', 'し': 'シ', 'す': 'ス', 'せ': 'セ', 'そ': 'ソ',
    'ざ': 'ザ', 'じ': 'ジ', 'ず': 'ズ', 'ぜ': 'ゼ', 'ぞ': 'ゾ',
    'た': 'タ', 'ち': 'チ', 'つ': 'ツ', 'て': 'テ', 'と': 'ト',
    'だ': 'ダ', 'ぢ': 'ヂ', 'づ': 'ヅ', 'で': 'デ', 'ど': 'ド',
    'な': 'ナ', 'に': 'ニ', 'ぬ': 'ヌ', 'ね': 'ネ', 'の': 'ノ',
    'は': 'ハ', 'ひ': 'ヒ', 'ふ': 'フ', 'へ': 'ヘ', 'ほ': 'ホ',
    'ば': 'バ', 'び': 'ビ', 'ぶ': 'ブ', 'べ': 'ベ', 'ぼ': 'ボ',
    'ぱ': 'パ', 'ぴ': 'ピ', 'ぷ': 'プ', 'ぺ': 'ペ', 'ぽ': 'ポ',
    'ま': 'マ', 'み': 'ミ', 'む': 'ム', 'め': 'メ', 'も': 'モ',
    'や': 'ヤ', 'ゆ': 'ユ', 'よ': 'ヨ',
    'ら': 'ラ', 'り': 'リ', 'る': 'ル', 'れ': 'レ', 'ろ': 'ロ',
    'わ': 'ワ', 'を': 'ヲ', 'ん': 'ン',
    'ゃ': 'ャ', 'ゅ': 'ュ', 'ょ': 'ョ',
    'っ': 'ッ',
}


def extract_kana(text):
    """히라가나/가타카나만 추출"""
    kana = ''
    for char in text:
        if '\u3040' <= char <= '\u309F':  # 히라가나
            kana += HIRAGANA_TO_KATAKANA.get(char, char)
        elif '\u30A0' <= char <= '\u30FF':  # 가타카나
            kana += char
    return kana


def kana_to_korean(kana):
    """가타카나를 한글로 변환 (기본 발음)"""
    result = ''
    i = 0
    while i < len(kana):
        char = kana[i]

        # 요음 처리 (キャ, シュ 등)
        if i + 1 < len(kana) and kana[i+1] in 'ャュョァィゥェォ':
            combo = char + kana[i+1]
            # 특수 조합
            if combo in ['キャ', 'キュ', 'キョ']:
                result += {'キャ': '캬', 'キュ': '큐', 'キョ': '쿄'}[combo]
            elif combo in ['シャ', 'シュ', 'ショ']:
                result += {'シャ': '샤', 'シュ': '슈', 'ショ': '쇼'}[combo]
            elif combo in ['チャ', 'チュ', 'チョ']:
                result += {'チャ': '차', 'チュ': '추', 'チョ': '초'}[combo]
            elif combo in ['ニャ', 'ニュ', 'ニョ']:
                result += {'ニャ': '냐', 'ニュ': '뉴', 'ニョ': '뇨'}[combo]
            elif combo in ['ヒャ', 'ヒュ', 'ヒョ']:
                result += {'ヒャ': '햐', 'ヒュ': '휴', 'ヒョ': '효'}[combo]
            elif combo in ['ミャ', 'ミュ', 'ミョ']:
                result += {'ミャ': '먀', 'ミュ': '뮤', 'ミョ': '묘'}[combo]
            elif combo in ['リャ', 'リュ', 'リョ']:
                result += {'リャ': '랴', 'リュ': '류', 'リョ': '료'}[combo]
            elif combo in ['ギャ', 'ギュ', 'ギョ']:
                result += {'ギャ': '갸', 'ギュ': '규', 'ギョ': '교'}[combo]
            elif combo in ['ジャ', 'ジュ', 'ジョ']:
                result += {'ジャ': '쟈', 'ジュ': '쥬', 'ジョ': '죠'}[combo]
            elif combo in ['ビャ', 'ビュ', 'ビョ']:
                result += {'ビャ': '뱌', 'ビュ': '뷰', 'ビョ': '뵤'}[combo]
            elif combo in ['ピャ', 'ピュ', 'ピョ']:
                result += {'ピャ': '퍄', 'ピュ': '퓨', 'ピョ': '표'}[combo]
            # 외래어 표기
            elif combo in ['ファ', 'フィ', 'フェ', 'フォ']:
                result += {'ファ': '파', 'フィ': '피', 'フェ': '페', 'フォ': '포'}[combo]
            elif combo in ['ティ', 'ディ']:
                result += {'ティ': '티', 'ディ': '디'}[combo]
            elif combo in ['ヴァ', 'ヴィ', 'ヴェ', 'ヴォ']:
                result += {'ヴァ': '바', 'ヴィ': '비', 'ヴェ': '베', 'ヴォ': '보'}[combo]
            else:
                # 기본: 첫 글자 + 요음
                result += KATAKANA_TO_KOREAN.get(char, '')
                result += KATAKANA_TO_KOREAN.get(kana[i+1], '')
            i += 2
        else:
            result += KATAKANA_TO_KOREAN.get(char, '')
            i += 1

    return result


def normalize_korean(text):
    """한글 이름 정규화 (비교용)"""
    # 공백, 특수문자 제거
    text = re.sub(r'[^가-힣]', '', text)
    return text.lower()


def similarity_score(str1, str2):
    """두 문자열의 유사도 (0~1)"""
    if not str1 or not str2:
        return 0

    # 길이 차이
    len_diff = abs(len(str1) - len(str2))
    if len_diff > 3:
        return 0

    # 공통 문자 비율
    common = sum(1 for c in str1 if c in str2)
    total = max(len(str1), len(str2))

    return common / total if total > 0 else 0


def get_anime_with_mixed_names():
    """한국어 이름 있는 캐릭터와 없는 캐릭터가 섞인 애니메이션"""
    return db.execute_query('''
        SELECT
            a.id as anime_id,
            a.title_korean,
            COUNT(CASE WHEN c.name_korean IS NOT NULL THEN 1 END) as with_korean,
            COUNT(CASE WHEN c.name_korean IS NULL AND c.name_native IS NOT NULL THEN 1 END) as without_korean
        FROM anime a
        JOIN anime_character ac ON a.id = ac.anime_id
        JOIN character c ON ac.character_id = c.id
        WHERE a.title_korean IS NOT NULL
        GROUP BY a.id
        HAVING with_korean >= 2 AND without_korean > 0
        ORDER BY a.popularity DESC
    ''')


def get_characters_with_korean(anime_id):
    """애니메이션의 한국어 이름 있는 캐릭터"""
    return db.execute_query('''
        SELECT c.id, c.name_full, c.name_native, c.name_korean
        FROM character c
        JOIN anime_character ac ON c.id = ac.character_id
        WHERE ac.anime_id = ?
          AND c.name_korean IS NOT NULL
          AND c.name_native IS NOT NULL
    ''', (anime_id,))


def get_characters_without_korean(anime_id):
    """애니메이션의 한국어 이름 없는 캐릭터"""
    return db.execute_query('''
        SELECT c.id, c.name_full, c.name_native
        FROM character c
        JOIN anime_character ac ON c.id = ac.character_id
        WHERE ac.anime_id = ?
          AND c.name_korean IS NULL
          AND c.name_native IS NOT NULL
          AND c.name_native != ''
    ''', (anime_id,))


def match_by_pronunciation(anime_id, title_korean):
    """
    발음 기반 매칭

    1. 기존 캐릭터의 일본어→한국어 변환 패턴 학습
    2. 학습된 패턴으로 새 캐릭터 매칭
    """
    chars_with = get_characters_with_korean(anime_id)
    chars_without = get_characters_without_korean(anime_id)

    if not chars_with or not chars_without:
        return 0

    # 기존 캐릭터에서 변환 패턴 검증
    # 우리의 자동 변환이 기존 데이터와 얼마나 일치하는지 확인
    valid_conversions = 0
    for char in chars_with:
        native = char['name_native']
        korean = char['name_korean']

        # 일본어 → 가나 추출 → 한글 변환
        kana = extract_kana(native)
        auto_korean = kana_to_korean(kana)

        # 정규화 후 비교
        auto_norm = normalize_korean(auto_korean)
        real_norm = normalize_korean(korean)

        if similarity_score(auto_norm, real_norm) >= 0.6:
            valid_conversions += 1

    # 최소 2개 이상의 검증된 변환이 있어야 신뢰
    conversion_rate = valid_conversions / len(chars_with)
    if conversion_rate < 0.3 or valid_conversions < 2:
        return 0

    # 새 캐릭터에 적용
    matched = 0
    for char in chars_without:
        native = char['name_native']

        kana = extract_kana(native)
        if not kana or len(kana) < 2:
            continue

        auto_korean = kana_to_korean(kana)

        # 최소 길이 체크
        if len(auto_korean) < 2:
            continue

        # 공백 추가 (성 + 이름 분리)
        # 예: 카마도탄지로 → 카마도 탄지로
        # 영어 이름에서 힌트
        english_parts = char['name_full'].split()
        if len(english_parts) == 2 and len(auto_korean) >= 4:
            # 성과 이름 비율 추정
            first_len = len(english_parts[0])
            last_len = len(english_parts[1])
            ratio = first_len / (first_len + last_len)

            split_point = int(len(auto_korean) * ratio)
            if 2 <= split_point <= len(auto_korean) - 2:
                auto_korean = auto_korean[:split_point] + ' ' + auto_korean[split_point:]

        # DB 업데이트
        db.execute_update(
            "UPDATE character SET name_korean = ? WHERE id = ?",
            (auto_korean, char['id'])
        )
        matched += 1

    return matched


def main():
    log("=" * 60)
    log("🔤 발음 기반 일본어→한국어 캐릭터 이름 매칭")
    log("=" * 60)

    anime_list = get_anime_with_mixed_names()
    log(f"\n📋 대상 애니메이션: {len(anime_list)}개")

    total_matched = 0
    processed = 0

    for anime in anime_list:
        anime_id = anime['anime_id']
        title = anime['title_korean']

        matched = match_by_pronunciation(anime_id, title)

        if matched > 0:
            total_matched += matched
            log(f"✓ {title}: {matched}개 매칭")

        processed += 1
        if processed % 50 == 0:
            log(f"   진행: {processed}/{len(anime_list)}")

    log(f"\n{'='*60}")
    log("🎉 완료!")
    log(f"   총 매칭: {total_matched}개 캐릭터")
    log(f"{'='*60}")


if __name__ == "__main__":
    main()
