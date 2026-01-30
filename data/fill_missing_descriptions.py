"""
누락된 애니메이션 및 캐릭터 description을 AniList API에서 가져와서 채우는 스크립트

통계:
- Anime: 4/5000 (0.08%) 누락
- Character: 15281/47557 (32.1%) 누락
"""

import sqlite3
import json
import time
import urllib.request
from typing import Optional, List, Tuple

API_URL = 'https://graphql.anilist.co'
RATE_LIMIT_DELAY = 0.7  # 초 (초당 약 1.4 요청, 분당 90 요청 준수)

class DescriptionFiller:
    def __init__(self, db_path: str = 'anime.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.request_count = 0

    def close(self):
        """데이터베이스 연결 종료"""
        self.conn.commit()
        self.conn.close()

    def _make_anilist_request(self, query: str, variables: dict) -> Optional[dict]:
        """AniList GraphQL 요청"""
        data = json.dumps({
            'query': query,
            'variables': variables
        }).encode('utf-8')

        req = urllib.request.Request(API_URL, data=data, headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                self.request_count += 1
                result = json.loads(response.read().decode('utf-8'))

                if 'errors' in result:
                    print(f"  ❌ GraphQL Error: {result['errors']}")
                    return None

                return result.get('data')
        except Exception as e:
            print(f"  ❌ Request failed: {e}")
            return None

    def get_missing_anime(self) -> List[Tuple[int, str]]:
        """description이 누락된 애니메이션 목록"""
        self.cursor.execute("""
            SELECT id, title_romaji
            FROM anime
            WHERE description IS NULL OR description = ''
            ORDER BY id
        """)
        return self.cursor.fetchall()

    def get_missing_characters(self, limit: Optional[int] = None) -> List[Tuple[int, str]]:
        """description이 누락된 캐릭터 목록"""
        query = """
            SELECT id, name_full
            FROM character
            WHERE description IS NULL OR description = ''
            ORDER BY favourites DESC
        """
        if limit:
            query += f" LIMIT {limit}"

        self.cursor.execute(query)
        return self.cursor.fetchall()

    def fill_anime_description(self, anime_id: int, title: str) -> bool:
        """애니메이션 description 채우기"""
        query = '''
        query ($id: Int) {
            Media(id: $id, type: ANIME) {
                id
                description
            }
        }
        '''

        print(f"  🔍 Fetching: {title} (ID: {anime_id})")

        data = self._make_anilist_request(query, {'id': anime_id})

        if not data or not data.get('Media'):
            print(f"  ⚠️  No data returned")
            return False

        description = data['Media'].get('description')

        if not description:
            print(f"  ⚠️  Description still empty in AniList")
            return False

        # HTML 태그 제거
        description = self._clean_html(description)

        # 데이터베이스 업데이트
        self.cursor.execute("""
            UPDATE anime
            SET description = ?
            WHERE id = ?
        """, (description, anime_id))
        self.conn.commit()

        print(f"  ✅ Updated ({len(description)} chars)")
        return True

    def fill_character_description(self, character_id: int, name: str) -> bool:
        """캐릭터 description 채우기"""
        query = '''
        query ($id: Int) {
            Character(id: $id) {
                id
                description
            }
        }
        '''

        print(f"  🔍 Fetching: {name} (ID: {character_id})")

        data = self._make_anilist_request(query, {'id': character_id})

        if not data or not data.get('Character'):
            print(f"  ⚠️  No data returned")
            return False

        description = data['Character'].get('description')

        if not description:
            print(f"  ⚠️  Description still empty in AniList")
            return False

        # HTML 태그 제거
        description = self._clean_html(description)

        # 데이터베이스 업데이트
        self.cursor.execute("""
            UPDATE character
            SET description = ?
            WHERE id = ?
        """, (description, character_id))
        self.conn.commit()

        print(f"  ✅ Updated ({len(description)} chars)")
        return True

    def _clean_html(self, text: str) -> str:
        """간단한 HTML 태그 제거"""
        import re
        # <br> 태그를 개행으로
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        # 나머지 HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)
        # 여러 개행을 2개로 제한
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def fill_all_anime(self):
        """모든 누락된 애니메이션 description 채우기"""
        missing = self.get_missing_anime()
        total = len(missing)

        if total == 0:
            print("✅ 모든 애니메이션에 description이 있습니다!")
            return

        print(f"\n📊 {total}개의 애니메이션 description을 채웁니다...\n")

        success_count = 0
        for i, (anime_id, title) in enumerate(missing, 1):
            print(f"[{i}/{total}]", end=" ")

            if self.fill_anime_description(anime_id, title):
                success_count += 1

            # Rate limit 준수
            if i < total:
                time.sleep(RATE_LIMIT_DELAY)

        print(f"\n✅ 완료: {success_count}/{total} 성공")
        print(f"📊 총 API 요청: {self.request_count}회")

    def fill_characters(self, limit: int = 100):
        """인기순으로 N개의 캐릭터 description 채우기"""
        missing = self.get_missing_characters(limit)
        total = len(missing)

        if total == 0:
            print("✅ 모든 캐릭터에 description이 있습니다!")
            return

        print(f"\n📊 인기순 {total}개의 캐릭터 description을 채웁니다...\n")

        success_count = 0
        for i, (character_id, name) in enumerate(missing, 1):
            print(f"[{i}/{total}]", end=" ")

            if self.fill_character_description(character_id, name):
                success_count += 1

            # Rate limit 준수
            if i < total:
                time.sleep(RATE_LIMIT_DELAY)

        print(f"\n✅ 완료: {success_count}/{total} 성공")
        print(f"📊 총 API 요청: {self.request_count}회")


def main():
    """메인 실행 함수"""
    import argparse

    parser = argparse.ArgumentParser(description='누락된 description 채우기')
    parser.add_argument('--type', choices=['anime', 'character', 'both'], default='both',
                        help='채울 타입 (기본: both)')
    parser.add_argument('--character-limit', type=int, default=100,
                        help='캐릭터 처리 최대 개수 (기본: 100, 인기순)')
    parser.add_argument('--db', default='anime.db',
                        help='데이터베이스 파일 경로 (기본: anime.db)')

    args = parser.parse_args()

    print("=" * 60)
    print("🔧 Description Filler")
    print("=" * 60)

    filler = DescriptionFiller(args.db)

    try:
        if args.type in ['anime', 'both']:
            filler.fill_all_anime()

        if args.type in ['character', 'both']:
            print()  # 개행
            filler.fill_characters(args.character_limit)

    finally:
        filler.close()

    print("\n" + "=" * 60)
    print("✅ 작업 완료!")
    print("=" * 60)


if __name__ == '__main__':
    main()
