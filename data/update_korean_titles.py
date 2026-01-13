"""
한국어 제목 업데이트
1. 웹 검색으로 오피셜 한국어 제목 찾기
2. 없으면 AI로 번역
3. 오피셜 여부를 구분하여 저장
"""
import sqlite3
import time
import sys
import os

# Claude API를 사용하려면 anthropic 라이브러리 필요
try:
    import anthropic
except ImportError:
    print("anthropic 라이브러리가 필요합니다: pip install anthropic")
    sys.exit(1)

DB_PATH = 'anime.db'

def get_anime_without_korean():
    """한국어 제목이 없는 애니메이션 조회 (인기도 순)"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title_romaji, title_english, title_native,
               season_year, format, popularity
        FROM anime
        WHERE title_korean IS NULL
        ORDER BY popularity DESC
        LIMIT 500
    """)

    results = cursor.fetchall()
    conn.close()
    return results

def search_korean_title(title_romaji, title_english, season_year):
    """
    웹 검색으로 오피셜 한국어 제목 찾기
    이 함수는 Claude Code의 WebSearch API를 사용해야 합니다.
    여기서는 구조만 제공하고, 실제로는 별도 처리가 필요합니다.
    """
    # 검색 쿼리 구성
    search_query = f"{title_romaji} 애니메이션 한국어 제목"
    if season_year:
        search_query += f" {season_year}"

    # WebSearch는 Claude Code 내에서만 사용 가능하므로
    # 여기서는 None을 반환하고, 수동으로 처리해야 합니다.
    return None

def translate_title(title_romaji, title_english, title_native):
    """
    AI로 제목 번역
    자연스러운 한국어로 번역하되, 고유명사는 원어 발음 유지
    """
    # Anthropic API를 사용한 번역
    # API 키는 환경변수에서 가져옴
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY 환경변수가 필요합니다.")
        return None

    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""다음 애니메이션 제목을 자연스러운 한국어로 번역해주세요.

로마자 제목: {title_romaji}
영어 제목: {title_english or 'N/A'}
일본어 제목: {title_native or 'N/A'}

규칙:
1. 고유명사(캐릭터명, 지명 등)는 원어 발음을 한글로 표기
2. 의미가 있는 단어는 한국어로 번역
3. 자연스럽고 간결하게
4. 결과는 번역된 제목만 출력 (설명 없이)

번역:"""

    try:
        message = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}]
        )

        translated = message.content[0].text.strip()
        return translated
    except Exception as e:
        print(f"번역 실패: {e}")
        return None

def update_korean_title(anime_id, korean_title, is_official):
    """데이터베이스에 한국어 제목 업데이트"""
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL")
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE anime
        SET title_korean = ?, title_korean_official = ?
        WHERE id = ?
    """, (korean_title, 1 if is_official else 0, anime_id))

    conn.commit()
    conn.close()

def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║   🌏 한국어 제목 업데이트                                  ║
║   - 웹 검색으로 오피셜 제목 찾기                           ║
║   - 없으면 AI 번역                                        ║
╚════════════════════════════════════════════════════════════╝
    """)

    # API 키 확인
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("⚠️ ANTHROPIC_API_KEY 환경변수를 설정해주세요.")
        print("export ANTHROPIC_API_KEY='your-api-key'")
        return

    anime_list = get_anime_without_korean()
    total = len(anime_list)

    print(f"📊 처리 대상: {total:,}개 (인기도 순)\n")

    official_count = 0
    translated_count = 0
    failed_count = 0

    for i, anime in enumerate(anime_list, 1):
        print(f"\n[{i}/{total}] {anime['title_romaji']}")

        # 1단계: 웹 검색으로 오피셜 제목 찾기 (수동)
        # 이 부분은 Claude Code의 WebSearch를 사용해야 하므로
        # 스크립트에서는 처리하지 않고, 번역만 진행

        # 2단계: AI 번역
        korean_title = translate_title(
            anime['title_romaji'],
            anime['title_english'],
            anime['title_native']
        )

        if korean_title:
            update_korean_title(anime['id'], korean_title, is_official=False)
            translated_count += 1
            print(f"  ✅ 번역: {korean_title}")
        else:
            failed_count += 1
            print(f"  ❌ 실패")

        # Rate limiting
        time.sleep(0.5)

        # 진행 상황
        if i % 50 == 0:
            print(f"\n📊 진행 상황: 번역 {translated_count}, 실패 {failed_count}")

    print(f"\n{'='*60}")
    print(f"✅ 완료!")
    print(f"{'='*60}")
    print(f"  전체: {total:,}개")
    print(f"  번역: {translated_count:,}개")
    print(f"  실패: {failed_count:,}개")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 중단됨")
    except Exception as e:
        print(f"\n❌ 에러: {e}")
        import traceback
        traceback.print_exc()
