"""
AniList 크롤러
인기 애니 3,000개 + 캐릭터/성우/스태프 데이터 수집
커버 이미지만 로컬 저장, 나머지 이미지는 URL만 저장
"""

import sqlite3
import json
import os
import time
import urllib.request
from datetime import datetime
from typing import Optional, Dict, List, Set
from anilist_client import AniListClient

# 설정
DB_PATH = 'anime.db'
IMAGES_DIR = 'images/covers'
TARGET_ANIME_COUNT = 8000
CHARS_PER_ANIME = 25
STAFF_PER_ANIME = 25


class AnimeCrawler:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.client = AniListClient()
        self.conn = None
        
        # 중복 방지용 세트
        self.existing_anime_ids: Set[int] = set()
        self.existing_char_ids: Set[int] = set()
        self.existing_staff_ids: Set[int] = set()
        self.existing_genre_names: Set[str] = set()
        self.existing_tag_ids: Set[int] = set()
        self.existing_studio_ids: Set[int] = set()
        
    def connect(self):
        """DB 연결"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._load_existing_ids()
        
    def close(self):
        """DB 연결 종료"""
        if self.conn:
            self.conn.close()
            
    def _load_existing_ids(self):
        """기존 데이터 ID 로드"""
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("SELECT id FROM anime")
            self.existing_anime_ids = {row[0] for row in cursor.fetchall()}
        except: pass
        
        try:
            cursor.execute("SELECT id FROM character")
            self.existing_char_ids = {row[0] for row in cursor.fetchall()}
        except: pass
        
        try:
            cursor.execute("SELECT id FROM staff")
            self.existing_staff_ids = {row[0] for row in cursor.fetchall()}
        except: pass
        
        try:
            cursor.execute("SELECT name FROM genre")
            self.existing_genre_names = {row[0] for row in cursor.fetchall()}
        except: pass
        
        try:
            cursor.execute("SELECT id FROM tag")
            self.existing_tag_ids = {row[0] for row in cursor.fetchall()}
        except: pass
        
        try:
            cursor.execute("SELECT id FROM studio")
            self.existing_studio_ids = {row[0] for row in cursor.fetchall()}
        except: pass
        
        print(f"📂 기존 데이터: 애니 {len(self.existing_anime_ids)}, "
              f"캐릭터 {len(self.existing_char_ids)}, 스태프 {len(self.existing_staff_ids)}")
    
    def _format_date(self, date_obj: Optional[Dict]) -> Optional[str]:
        """날짜 객체를 문자열로 변환"""
        if not date_obj:
            return None
        year = date_obj.get('year')
        month = date_obj.get('month')
        day = date_obj.get('day')
        
        if year and month and day:
            return f"{year}-{month:02d}-{day:02d}"
        elif year and month:
            return f"{year}-{month:02d}"
        elif year:
            return str(year)
        elif month and day:
            return f"{month:02d}-{day:02d}"
        return None
    
    def _download_image(self, url: str, save_path: str) -> bool:
        """이미지 다운로드"""
        if not url:
            return False
            
        try:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            with urllib.request.urlopen(req, timeout=30) as response:
                with open(save_path, 'wb') as f:
                    f.write(response.read())
            return True
        except Exception as e:
            print(f"  ⚠️ 이미지 실패: {e}")
            return False
    
    # ==================== 애니메이션 ====================
    
    def crawl_anime_list(self, target_count: int = TARGET_ANIME_COUNT):
        """인기순 애니메이션 크롤링"""
        print(f"\n{'='*60}")
        print(f"📺 애니메이션 크롤링 (목표: {target_count}개)")
        print(f"{'='*60}")
        
        page = 1
        per_page = 50
        total_crawled = len(self.existing_anime_ids)
        
        while total_crawled < target_count:
            print(f"\n📄 페이지 {page} ({total_crawled}/{target_count})")
            
            data = self.client.get_popular_anime_page(page=page, per_page=per_page)
            
            if not data or 'Page' not in data:
                print("  ❌ 데이터 없음, 5초 후 재시도...")
                time.sleep(5)
                continue
            
            media_list = data['Page']['media']
            page_info = data['Page']['pageInfo']
            
            for anime in media_list:
                if total_crawled >= target_count:
                    break
                    
                anime_id = anime['id']
                
                if anime_id in self.existing_anime_ids:
                    continue
                
                self._save_anime(anime)
                self.existing_anime_ids.add(anime_id)
                total_crawled += 1
                
                if total_crawled % 100 == 0:
                    self.conn.commit()
                    print(f"  💾 {total_crawled}개 저장됨")
            
            if not page_info['hasNextPage'] or total_crawled >= target_count:
                break
                
            page += 1
        
        self.conn.commit()
        self._update_meta('total_anime', str(total_crawled))
        print(f"\n✅ 애니메이션: {total_crawled}개 완료")
    
    def _save_anime(self, anime: Dict):
        """애니메이션 저장"""
        cursor = self.conn.cursor()
        anime_id = anime['id']
        
        cover_url = anime.get('coverImage', {}).get('large')
        cover_local = f"{IMAGES_DIR}/{anime_id}.jpg" if cover_url else None
        
        trailer_url = None
        trailer_site = None
        if anime.get('trailer'):
            trailer_site = anime['trailer'].get('site')
            trailer_id = anime['trailer'].get('id')
            if trailer_site == 'youtube' and trailer_id:
                trailer_url = f"https://youtube.com/watch?v={trailer_id}"
        
        cursor.execute('''
            INSERT OR REPLACE INTO anime (
                id, id_mal, title_romaji, title_english, title_native,
                type, format, status, description,
                season, season_year, episodes, duration,
                start_date, end_date,
                cover_image_local, cover_image_url, cover_image_color, banner_image_url,
                average_score, mean_score, popularity, favourites, trending,
                source, country_of_origin, is_adult, is_licensed,
                site_url, trailer_url, trailer_site, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            anime_id, anime.get('idMal'),
            anime.get('title', {}).get('romaji'),
            anime.get('title', {}).get('english'),
            anime.get('title', {}).get('native'),
            anime.get('type'), anime.get('format'), anime.get('status'),
            anime.get('description'),
            anime.get('season'), anime.get('seasonYear'),
            anime.get('episodes'), anime.get('duration'),
            self._format_date(anime.get('startDate')),
            self._format_date(anime.get('endDate')),
            cover_local, cover_url,
            anime.get('coverImage', {}).get('color'),
            anime.get('bannerImage'),
            anime.get('averageScore'), anime.get('meanScore'),
            anime.get('popularity'), anime.get('favourites'), anime.get('trending'),
            anime.get('source'), anime.get('countryOfOrigin'),
            1 if anime.get('isAdult') else 0,
            1 if anime.get('isLicensed') else 0,
            anime.get('siteUrl'), trailer_url, trailer_site, anime.get('updatedAt'),
        ))
        
        # 장르
        for genre_name in anime.get('genres', []):
            self._save_genre(anime_id, genre_name)
        
        # 태그
        for tag in anime.get('tags', []):
            self._save_tag(anime_id, tag)
        
        # 스튜디오
        for edge in anime.get('studios', {}).get('edges', []):
            self._save_studio(anime_id, edge)
        
        # 관계 작품
        for edge in anime.get('relations', {}).get('edges', []):
            if edge['node']['type'] == 'ANIME':
                cursor.execute('''
                    INSERT OR IGNORE INTO anime_relation (anime_id, related_anime_id, relation_type)
                    VALUES (?, ?, ?)
                ''', (anime_id, edge['node']['id'], edge['relationType']))
        
        # 추천
        for node in anime.get('recommendations', {}).get('nodes', []):
            if node.get('mediaRecommendation'):
                cursor.execute('''
                    INSERT OR IGNORE INTO anime_recommendation (anime_id, recommended_anime_id, rating)
                    VALUES (?, ?, ?)
                ''', (anime_id, node['mediaRecommendation']['id'], node.get('rating', 0)))
        
        # 외부 링크
        for link in anime.get('externalLinks', []):
            cursor.execute('''
                INSERT INTO anime_external_link (anime_id, site, url, type, language)
                VALUES (?, ?, ?, ?, ?)
            ''', (anime_id, link.get('site'), link.get('url'), link.get('type'), link.get('language')))
        
        # 스트리밍
        for ep in anime.get('streamingEpisodes', []):
            cursor.execute('''
                INSERT INTO anime_streaming_episode (anime_id, title, thumbnail_url, url, site)
                VALUES (?, ?, ?, ?, ?)
            ''', (anime_id, ep.get('title'), ep.get('thumbnail'), ep.get('url'), ep.get('site')))
        
        # 통계
        for dist in anime.get('stats', {}).get('scoreDistribution', []):
            cursor.execute('''
                INSERT OR REPLACE INTO anime_score_distribution (anime_id, score, amount)
                VALUES (?, ?, ?)
            ''', (anime_id, dist['score'], dist['amount']))
        
        for dist in anime.get('stats', {}).get('statusDistribution', []):
            cursor.execute('''
                INSERT OR REPLACE INTO anime_status_distribution (anime_id, status, amount)
                VALUES (?, ?, ?)
            ''', (anime_id, dist['status'], dist['amount']))
    
    def _save_genre(self, anime_id: int, genre_name: str):
        cursor = self.conn.cursor()
        if genre_name not in self.existing_genre_names:
            cursor.execute('INSERT OR IGNORE INTO genre (name) VALUES (?)', (genre_name,))
            self.existing_genre_names.add(genre_name)
        
        cursor.execute('SELECT id FROM genre WHERE name = ?', (genre_name,))
        genre_id = cursor.fetchone()[0]
        cursor.execute('INSERT OR IGNORE INTO anime_genre (anime_id, genre_id) VALUES (?, ?)',
                      (anime_id, genre_id))
    
    def _save_tag(self, anime_id: int, tag: Dict):
        cursor = self.conn.cursor()
        tag_id = tag['id']
        
        if tag_id not in self.existing_tag_ids:
            cursor.execute('''
                INSERT OR REPLACE INTO tag (id, name, description, category, is_adult)
                VALUES (?, ?, ?, ?, ?)
            ''', (tag_id, tag['name'], tag.get('description'), tag.get('category'),
                  1 if tag.get('isAdult') else 0))
            self.existing_tag_ids.add(tag_id)
        
        is_spoiler = tag.get('isGeneralSpoiler') or tag.get('isMediaSpoiler')
        cursor.execute('''
            INSERT OR REPLACE INTO anime_tag (anime_id, tag_id, rank, is_spoiler)
            VALUES (?, ?, ?, ?)
        ''', (anime_id, tag_id, tag.get('rank', 0), 1 if is_spoiler else 0))
    
    def _save_studio(self, anime_id: int, edge: Dict):
        cursor = self.conn.cursor()
        studio = edge['node']
        studio_id = studio['id']
        
        if studio_id not in self.existing_studio_ids:
            cursor.execute('''
                INSERT OR REPLACE INTO studio (id, name, is_animation_studio, site_url, favourites)
                VALUES (?, ?, ?, ?, ?)
            ''', (studio_id, studio['name'], 1 if studio.get('isAnimationStudio') else 0,
                  studio.get('siteUrl'), studio.get('favourites', 0)))
            self.existing_studio_ids.add(studio_id)
        
        cursor.execute('''
            INSERT OR IGNORE INTO anime_studio (anime_id, studio_id, is_main)
            VALUES (?, ?, ?)
        ''', (anime_id, studio_id, 1 if edge.get('isMain') else 0))
    
    # ==================== 캐릭터/성우 ====================
    
    def crawl_characters(self):
        """모든 애니의 캐릭터 크롤링"""
        print(f"\n{'='*60}")
        print(f"👤 캐릭터/성우 크롤링")
        print(f"{'='*60}")
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, title_romaji FROM anime ORDER BY popularity DESC")
        anime_list = cursor.fetchall()
        total = len(anime_list)
        
        for i, (anime_id, title) in enumerate(anime_list, 1):
            if i % 10 == 1:
                print(f"\n[{i}/{total}] {title[:30]}...")
            
            self._crawl_anime_characters(anime_id)
            
            if i % 50 == 0:
                self.conn.commit()
                print(f"  💾 저장됨 (캐릭터: {len(self.existing_char_ids)}, 성우: {len(self.existing_staff_ids)})")
        
        self.conn.commit()
        self._update_meta('total_characters', str(len(self.existing_char_ids)))
        print(f"\n✅ 캐릭터: {len(self.existing_char_ids)}명, 성우: {len(self.existing_staff_ids)}명")
    
    def _crawl_anime_characters(self, anime_id: int):
        """특정 애니 캐릭터 크롤링"""
        page = 1
        total_chars = 0
        
        while total_chars < CHARS_PER_ANIME:
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
                
                self._save_character(char)
                
                cursor.execute('''
                    INSERT OR IGNORE INTO anime_character (anime_id, character_id, role)
                    VALUES (?, ?, ?)
                ''', (anime_id, char_id, role))
                
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
    
    def _save_character(self, char: Dict):
        char_id = char['id']
        if char_id in self.existing_char_ids:
            return
        
        cursor = self.conn.cursor()
        name = char.get('name', {})
        dob = char.get('dateOfBirth', {})
        dob_str = None
        if dob and dob.get('month') and dob.get('day'):
            dob_str = f"{dob['month']:02d}-{dob['day']:02d}"
        
        alternative = name.get('alternative', [])
        
        cursor.execute('''
            INSERT OR REPLACE INTO character (
                id, name_first, name_last, name_full, name_native, name_alternative,
                description, gender, age, date_of_birth, blood_type,
                image_url, favourites
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            char_id, name.get('first'), name.get('last'), name.get('full'), name.get('native'),
            json.dumps(alternative) if alternative else None,
            char.get('description'), char.get('gender'), char.get('age'),
            dob_str, char.get('bloodType'),
            char.get('image', {}).get('large'), char.get('favourites', 0),
        ))
        
        self.existing_char_ids.add(char_id)
    
    def _save_staff(self, staff: Dict):
        staff_id = staff['id']
        if staff_id in self.existing_staff_ids:
            return
        
        cursor = self.conn.cursor()
        name = staff.get('name', {})
        years = staff.get('yearsActive', [])
        occupations = staff.get('primaryOccupations', [])
        
        cursor.execute('''
            INSERT OR REPLACE INTO staff (
                id, name_first, name_last, name_full, name_native,
                description, gender, age,
                date_of_birth, date_of_death, home_town, blood_type,
                years_active_start, years_active_end, primary_occupations, language,
                image_url, favourites
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            staff_id, name.get('first'), name.get('last'), name.get('full'), name.get('native'),
            staff.get('description'), staff.get('gender'), staff.get('age'),
            self._format_date(staff.get('dateOfBirth')),
            self._format_date(staff.get('dateOfDeath')),
            staff.get('homeTown'), staff.get('bloodType'),
            years[0] if years else None, years[1] if len(years) > 1 else None,
            json.dumps(occupations) if occupations else None, staff.get('language'),
            staff.get('image', {}).get('large'), staff.get('favourites', 0),
        ))
        
        self.existing_staff_ids.add(staff_id)
    
    # ==================== 스태프 ====================
    
    def crawl_staff(self):
        """모든 애니의 스태프 크롤링"""
        print(f"\n{'='*60}")
        print(f"🎬 스태프 크롤링")
        print(f"{'='*60}")
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, title_romaji FROM anime ORDER BY popularity DESC")
        anime_list = cursor.fetchall()
        total = len(anime_list)
        
        for i, (anime_id, title) in enumerate(anime_list, 1):
            if i % 10 == 1:
                print(f"[{i}/{total}] {title[:30]}...")
            
            self._crawl_anime_staff(anime_id)
            
            if i % 50 == 0:
                self.conn.commit()
        
        self.conn.commit()
        self._update_meta('total_staff', str(len(self.existing_staff_ids)))
        print(f"\n✅ 스태프: {len(self.existing_staff_ids)}명 완료")
    
    def _crawl_anime_staff(self, anime_id: int):
        """특정 애니 스태프 크롤링"""
        page = 1
        total_staff = 0
        
        while total_staff < STAFF_PER_ANIME:
            data = self.client.get_anime_staff(anime_id, page)
            
            if not data or 'Media' not in data or not data['Media']:
                break
            
            edges = data['Media'].get('staff', {}).get('edges', [])
            if not edges:
                break
            
            cursor = self.conn.cursor()
            
            for edge in edges:
                if total_staff >= STAFF_PER_ANIME:
                    break
                
                staff = edge['node']
                role = edge.get('role')
                
                self._save_staff(staff)
                
                cursor.execute('''
                    INSERT OR IGNORE INTO anime_staff (anime_id, staff_id, role)
                    VALUES (?, ?, ?)
                ''', (anime_id, staff['id'], role))
                
                total_staff += 1
            
            if not data['Media'].get('staff', {}).get('pageInfo', {}).get('hasNextPage'):
                break
            page += 1
    
    # ==================== 이미지 ====================
    
    def download_covers(self):
        """커버 이미지 다운로드"""
        print(f"\n{'='*60}")
        print(f"🖼️ 커버 이미지 다운로드")
        print(f"{'='*60}")
        
        os.makedirs(IMAGES_DIR, exist_ok=True)
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, cover_image_url, cover_image_local 
            FROM anime 
            WHERE cover_image_url IS NOT NULL
            ORDER BY popularity DESC
        """)
        
        anime_list = cursor.fetchall()
        total = len(anime_list)
        downloaded = 0
        skipped = 0
        
        for i, (anime_id, url, local_path) in enumerate(anime_list, 1):
            save_path = f"{IMAGES_DIR}/{anime_id}.jpg"
            
            if os.path.exists(save_path):
                skipped += 1
                continue
            
            if self._download_image(url, save_path):
                cursor.execute(
                    "UPDATE anime SET cover_image_local = ? WHERE id = ?",
                    (save_path, anime_id)
                )
                downloaded += 1
            
            if i % 100 == 0:
                self.conn.commit()
                print(f"  📥 {i}/{total} (다운: {downloaded}, 스킵: {skipped})")
            
            time.sleep(0.05)
        
        self.conn.commit()
        print(f"\n✅ 이미지: {downloaded}개 다운로드 (스킵: {skipped})")
    
    # ==================== 유틸 ====================
    
    def _update_meta(self, key: str, value: str):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO crawl_meta (key, value, updated_at)
            VALUES (?, ?, ?)
        ''', (key, value, datetime.now().isoformat()))
    
    def init_db(self):
        """DB 초기화"""
        with open('schema.sql', 'r') as f:
            self.conn.executescript(f.read())
        self.conn.commit()
        print("✅ DB 초기화 완료")
    
    def print_stats(self):
        """통계 출력"""
        cursor = self.conn.cursor()
        
        print(f"\n{'='*60}")
        print("📊 데이터베이스 통계")
        print(f"{'='*60}")
        
        tables = ['anime', 'character', 'staff', 'genre', 'tag', 'studio']
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  {table}: {count:,}")
            except:
                print(f"  {table}: 0")
        
        try:
            cursor.execute("SELECT COUNT(*) FROM anime WHERE cover_image_local IS NOT NULL")
            img_count = cursor.fetchone()[0]
            
            # 실제 파일 수 확인
            if os.path.exists(IMAGES_DIR):
                file_count = len([f for f in os.listdir(IMAGES_DIR) if f.endswith('.jpg')])
            else:
                file_count = 0
            print(f"  커버 이미지 파일: {file_count}")
        except:
            pass


def main():
    """메인 실행"""
    print("""
╔════════════════════════════════════════════════════════════╗
║   🎌 AniList 크롤러 - 인기작 3,000개 완전체 DB              ║
║   📦 데이터: ~226MB / 🖼️ 커버 이미지: ~161MB               ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    crawler = AnimeCrawler()
    
    try:
        # DB 초기화 또는 연결
        if not os.path.exists(DB_PATH):
            print("📁 새 데이터베이스 생성...")
            crawler.conn = sqlite3.connect(DB_PATH)
            crawler.init_db()
        
        crawler.connect()
        crawler.print_stats()
        
        # 1단계: 애니메이션
        print("\n" + "─"*60)
        print("📌 1단계: 애니메이션 기본 정보")
        crawler.crawl_anime_list(TARGET_ANIME_COUNT)
        
        # 2단계: 캐릭터/성우
        print("\n" + "─"*60)
        print("📌 2단계: 캐릭터/성우")
        crawler.crawl_characters()
        
        # 3단계: 스태프
        print("\n" + "─"*60)
        print("📌 3단계: 스태프")
        crawler.crawl_staff()
        
        # 4단계: 커버 이미지
        print("\n" + "─"*60)
        print("📌 4단계: 커버 이미지 다운로드")
        crawler.download_covers()
        
        # 완료
        crawler._update_meta('last_full_crawl', datetime.now().isoformat())
        crawler.print_stats()
        
        print("\n🎉 크롤링 완료!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 중단됨 (진행상황 저장됨)")
        if crawler.conn:
            crawler.conn.commit()
    except Exception as e:
        print(f"\n❌ 에러: {e}")
        import traceback
        traceback.print_exc()
    finally:
        crawler.close()


if __name__ == '__main__':
    main()
