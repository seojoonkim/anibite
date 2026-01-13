"""
기존 애니메이션의 캐릭터/성우 정보 크롤링
"""

import sqlite3
import time
from anilist_client import AniListClient

DB_PATH = 'anime.db'
CHARS_PER_ANIME = 25

class CharacterCrawler:
    def __init__(self):
        self.client = AniListClient()
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.execute("PRAGMA journal_mode=WAL")

    def get_anime_without_characters(self):
        """캐릭터 정보가 없는 애니메이션 목록"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT a.id, a.title_romaji
            FROM anime a
            LEFT JOIN anime_character ac ON a.id = ac.anime_id
            WHERE ac.anime_id IS NULL
            ORDER BY a.popularity DESC
        """)
        return cursor.fetchall()

    def get_anime_with_few_characters(self):
        """캐릭터가 적은 애니메이션 (5개 미만)"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT a.id, a.title_romaji, COUNT(ac.character_id) as char_count
            FROM anime a
            LEFT JOIN anime_character ac ON a.id = ac.anime_id
            GROUP BY a.id
            HAVING char_count < 5 AND char_count > 0
            ORDER BY a.popularity DESC
        """)
        return cursor.fetchall()

    def crawl_anime_characters(self, anime_id: int):
        """특정 애니메이션의 캐릭터 크롤링"""
        page = 1
        total_chars = 0

        while total_chars < CHARS_PER_ANIME:
            try:
                data = self.client.get_anime_characters(anime_id, page)

                if not data or 'Media' not in data or not data['Media']:
                    break

                edges = data['Media'].get('characters', {}).get('edges', [])
                if not edges:
                    break

                cursor = self.conn.cursor()

                for edge in edges:
                    if total_chars >= CHARS_PER_ANIME:
                        break

                    char = edge['node']
                    char_id = char['id']
                    role = edge.get('role')

                    # 캐릭터 저장
                    self._save_character(char)

                    # 애니메이션-캐릭터 관계 저장
                    cursor.execute('''
                        INSERT OR IGNORE INTO anime_character (anime_id, character_id, role)
                        VALUES (?, ?, ?)
                    ''', (anime_id, char_id, role))

                    # 성우 저장
                    for va in edge.get('voiceActors', []):
                        self._save_staff(va)
                        cursor.execute('''
                            INSERT OR IGNORE INTO character_voice_actor
                            (character_id, staff_id, anime_id, language)
                            VALUES (?, ?, ?, ?)
                        ''', (char_id, va['id'], anime_id, va.get('language', 'JAPANESE')))

                    total_chars += 1

                if not data['Media'].get('characters', {}).get('pageInfo', {}).get('hasNextPage'):
                    break
                page += 1

                time.sleep(1.5)  # Rate limit 방지

            except Exception as e:
                print(f"  ⚠️ 에러: {e}")
                if "429" in str(e):
                    print(f"  ⏳ Rate limit, 120초 대기...")
                    time.sleep(120)
                else:
                    break

        self.conn.commit()
        return total_chars

    def _save_character(self, char: dict):
        """캐릭터 정보 저장"""
        cursor = self.conn.cursor()
        char_id = char['id']

        # 이미 있는지 확인
        cursor.execute("SELECT id FROM character WHERE id = ?", (char_id,))
        if cursor.fetchone():
            return

        name = char.get('name', {})
        image = char.get('image', {})
        date_of_birth = char.get('dateOfBirth', {})

        # 생년월일 포맷
        dob = None
        if date_of_birth:
            year = date_of_birth.get('year')
            month = date_of_birth.get('month')
            day = date_of_birth.get('day')
            if year and month and day:
                dob = f"{year}-{month:02d}-{day:02d}"
            elif month and day:
                dob = f"{month:02d}-{day:02d}"

        cursor.execute('''
            INSERT OR REPLACE INTO character (
                id, name_full, name_native, name_alternative,
                description, image_url, gender, age,
                date_of_birth, blood_type, favourites
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            char_id,
            name.get('full'),
            name.get('native'),
            ','.join(name.get('alternative', [])) if name.get('alternative') else None,
            char.get('description'),
            image.get('medium'),
            char.get('gender'),
            char.get('age'),
            dob,
            char.get('bloodType'),
            char.get('favourites', 0)
        ))

    def _save_staff(self, staff: dict):
        """성우/스태프 정보 저장"""
        cursor = self.conn.cursor()
        staff_id = staff['id']

        # 이미 있는지 확인
        cursor.execute("SELECT id FROM staff WHERE id = ?", (staff_id,))
        if cursor.fetchone():
            return

        name = staff.get('name', {})
        image = staff.get('image', {})
        date_of_birth = staff.get('dateOfBirth', {})
        date_of_death = staff.get('dateOfDeath', {})

        # 생년월일 포맷
        dob = None
        if date_of_birth:
            year = date_of_birth.get('year')
            month = date_of_birth.get('month')
            day = date_of_birth.get('day')
            if year and month and day:
                dob = f"{year}-{month:02d}-{day:02d}"
            elif month and day:
                dob = f"{month:02d}-{day:02d}"

        # 사망일 포맷
        dod = None
        if date_of_death:
            year = date_of_death.get('year')
            month = date_of_death.get('month')
            day = date_of_death.get('day')
            if year and month and day:
                dod = f"{year}-{month:02d}-{day:02d}"
            elif month and day:
                dod = f"{month:02d}-{day:02d}"

        # 활동 기간
        years_active = staff.get('yearsActive', [])
        years_start = years_active[0] if years_active and len(years_active) > 0 else None
        years_end = years_active[1] if years_active and len(years_active) > 1 else None

        cursor.execute('''
            INSERT OR REPLACE INTO staff (
                id, name_full, name_native, description,
                image_url, language, gender, age,
                date_of_birth, date_of_death,
                blood_type, home_town, primary_occupations,
                years_active_start, years_active_end, favourites
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            staff_id,
            name.get('full'),
            name.get('native'),
            staff.get('description'),
            image.get('medium'),
            staff.get('languageV2'),
            staff.get('gender'),
            staff.get('age'),
            dob,
            dod,
            staff.get('bloodType'),
            staff.get('homeTown'),
            ','.join(staff.get('primaryOccupations', [])) if staff.get('primaryOccupations') else None,
            years_start,
            years_end,
            staff.get('favourites', 0)
        ))

    def run(self):
        """전체 크롤링 실행"""
        print("🔍 캐릭터 정보가 없는 애니메이션 확인 중...")
        anime_list = self.get_anime_without_characters()
        total = len(anime_list)

        print(f"\n{'='*60}")
        print(f"👤 캐릭터 크롤링 시작")
        print(f"대상: {total}개 애니메이션")
        print(f"{'='*60}\n")

        success_count = 0
        fail_count = 0

        for i, (anime_id, title) in enumerate(anime_list, 1):
            print(f"[{i}/{total}] {title[:50]}")

            try:
                char_count = self.crawl_anime_characters(anime_id)
                if char_count > 0:
                    print(f"  ✅ 캐릭터 {char_count}개 추가")
                    success_count += 1
                else:
                    print(f"  ⚠️ 캐릭터 없음")
                    fail_count += 1
            except Exception as e:
                print(f"  ❌ 실패: {e}")
                fail_count += 1

            # 매 애니메이션마다 2초 대기
            time.sleep(2)

            # 10개마다 추가 휴식
            if i % 10 == 0:
                print(f"  💤 10초 휴식...")
                time.sleep(10)

            if i % 20 == 0:
                print(f"\n📊 진행 상황: 성공 {success_count}, 실패 {fail_count}\n")

        print(f"\n{'='*60}")
        print(f"✅ 완료!")
        print(f"성공: {success_count}, 실패: {fail_count}")
        print(f"{'='*60}")

        self.conn.close()

if __name__ == '__main__':
    crawler = CharacterCrawler()
    crawler.run()
