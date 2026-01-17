#!/usr/bin/env python3
"""
한국어 이름 검증 스크립트
- 잘못된 패턴 감지
- 상위 캐릭터 수동 검증
- 통계 출력
"""
import sys
import os
import re
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))

from config import DATABASE_PATH


# 잘못된 패턴들 (작품 제목, 일반 문장 등)
BAD_PATTERNS = [
    # 작품 제목 패턴
    '%의 장미%', '%의 성%', '%의 금서목록%', '%의 사역마%', '%의 관리인%',
    '%의 스타더스트%', '%의 장난감%', '%의 엑소시스트%', '%의 리부트%',
    '%의 아쿠아%', '%의 마술사%', '%의 프리렌%', '%의 거인%',
    # 일반 문장/단어
    '%올림픽%', '%새로운%', '%시작%', '%가는%', '%연애%', '%고백%',
    '%싶어%', '%재난%', '%따라해%', '%동급생%', '%골프%', '%블랙 사탄%',
    '%레서판다%', '%마릴린%', '%짐승의 길%', '%웃는 세일즈맨%',
    '%별 셋 컬러즈%', '%밤은 고양이%', '%평범한 경음부%',
    # 너무 긴 것 (5단어 이상)
]

# 상위 캐릭터 기대값 (수동 검증용)
EXPECTED_NAMES = {
    "Satoru Gojou": "고죠 사토루",
    "Luffy Monkey": ["몽키 D. 루피", "몽키 루피"],
    "Levi": "리바이",
    "Killua Zoldyck": ["키르아 조르딕", "키루아 조르딕", "키르아 졸딕"],
    "Eren Yeager": ["엘런 예거", "에렌 예거"],
    "Zoro Roronoa": ["롤로노아 조로", "로로노아 조로"],
    "Emilia": ["에밀리아", "에미리아"],
    "Ken Kaneki": ["카네키 켄", "카네키"],
    "Guts": "가츠",
    "L Lawliet": "엘",
    "Mikasa Ackerman": ["미카사 아커만", "미카사 아커맨"],
    "Makima": "마키마",
    "Frieren": "프리렌",
    "Maomao": "마오마오",
    "Naruto Uzumaki": "우즈마키 나루토",
    "Itachi Uchiha": "우치하 이타치",
    "Sasuke Uchiha": "우치하 사스케",
    "Edward Elric": ["에드워드 엘릭", "에드"],
    "Spike Spiegel": "스파이크 스피겔",
    "Light Yagami": ["야가미 라이토", "라이토"],
}


def validate():
    conn = sqlite3.connect(str(DATABASE_PATH))
    cursor = conn.cursor()

    print("=" * 70)
    print("🔍 한국어 이름 검증")
    print("=" * 70)

    # 1. 통계
    cursor.execute("SELECT COUNT(*) FROM character")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM character WHERE name_korean IS NOT NULL")
    has_korean = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM character WHERE name_korean IS NULL AND name_native IS NOT NULL")
    missing = cursor.fetchone()[0]

    print(f"\n📊 통계:")
    print(f"   전체 캐릭터: {total:,}개")
    print(f"   한국어 이름 있음: {has_korean:,}개 ({has_korean/total*100:.1f}%)")
    print(f"   한국어 이름 없음 (native 있음): {missing:,}개")

    # 2. 잘못된 패턴 감지
    print(f"\n🚨 잘못된 패턴 감지:")
    bad_count = 0
    bad_examples = []

    for pattern in BAD_PATTERNS:
        cursor.execute(
            "SELECT name_full, name_korean FROM character WHERE name_korean LIKE ? LIMIT 5",
            (pattern,)
        )
        results = cursor.fetchall()
        if results:
            bad_count += len(results)
            for name_full, name_korean in results:
                bad_examples.append((name_full, name_korean, pattern))

    if bad_examples:
        print(f"   ❌ {bad_count}개 발견:")
        for name_full, name_korean, pattern in bad_examples[:10]:
            print(f"      {name_full}: '{name_korean}' (패턴: {pattern})")
        if len(bad_examples) > 10:
            print(f"      ... 외 {len(bad_examples) - 10}개")
    else:
        print(f"   ✅ 잘못된 패턴 없음")

    # 3. 너무 긴 이름 (정보 표시용 - 유럽식 긴 이름의 음역은 정상)
    print(f"\n📏 긴 이름 (정보용):")
    cursor.execute("""
        SELECT COUNT(*) FROM character
        WHERE name_korean IS NOT NULL
          AND (LENGTH(REPLACE(name_korean, ' ', '')) > 12
               OR LENGTH(name_korean) - LENGTH(REPLACE(name_korean, ' ', '')) >= 4)
    """)
    long_count = cursor.fetchone()[0]
    if long_count > 0:
        print(f"   ℹ️ {long_count}개 (유럽식 이름 음역 등 - 정상)")
    else:
        print(f"   ✅ 긴 이름 없음")

    # 4. 상위 캐릭터 검증
    print(f"\n🎯 상위 캐릭터 검증:")
    correct = 0
    incorrect = []

    for english_name, expected in EXPECTED_NAMES.items():
        cursor.execute(
            "SELECT name_korean FROM character WHERE name_full = ?",
            (english_name,)
        )
        result = cursor.fetchone()
        if result:
            actual = result[0]
            if isinstance(expected, list):
                if actual in expected:
                    correct += 1
                else:
                    incorrect.append((english_name, actual, expected[0]))
            else:
                if actual == expected:
                    correct += 1
                else:
                    incorrect.append((english_name, actual, expected))

    print(f"   ✅ 정확: {correct}/{len(EXPECTED_NAMES)}")
    if incorrect:
        print(f"   ❌ 불일치:")
        for name, actual, expected in incorrect:
            print(f"      {name}: '{actual}' (기대: '{expected}')")

    # 5. 상위 30개 캐릭터 출력
    print(f"\n📋 상위 30개 인기 캐릭터:")
    print("-" * 70)
    cursor.execute("""
        SELECT name_full, name_korean, favourites
        FROM character
        WHERE name_native IS NOT NULL
        ORDER BY favourites DESC
        LIMIT 30
    """)
    for i, row in enumerate(cursor.fetchall(), 1):
        name_full, name_korean, favs = row
        status = "✅" if name_korean else "❌"
        print(f"   {i:2}. {status} {name_full:25} | {name_korean or 'NULL':15} | ♥{favs:,}")

    # 6. 요약
    print(f"\n" + "=" * 70)
    print("📝 요약:")

    issues = []
    if bad_count > 0:
        issues.append(f"잘못된 패턴 {bad_count}개")
    if incorrect:
        issues.append(f"상위 캐릭터 불일치 {len(incorrect)}개")

    if issues:
        print(f"   ⚠️ 문제: {', '.join(issues)}")
        print(f"   권장: 수동 수정 필요")
    else:
        print(f"   ✅ 모든 검증 통과!")

    print("=" * 70)

    conn.close()

    # 반환값: 문제 있으면 1, 없으면 0
    return 1 if issues else 0


if __name__ == "__main__":
    exit_code = validate()
    sys.exit(exit_code)
