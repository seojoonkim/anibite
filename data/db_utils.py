"""
애니 데이터베이스 조회 유틸리티
"""

import sqlite3
import json
from typing import Optional, List, Dict

DB_PATH = 'anime.db'

class AnimeDB:
    def __init__(self, db_path: str = DB_PATH):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
    
    def close(self):
        self.conn.close()
    
    # =========================================
    # 애니메이션 조회
    # =========================================
    
    def get_anime(self, anime_id: int) -> Optional[Dict]:
        """애니메이션 상세 정보"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM anime WHERE id = ?', (anime_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        anime = dict(row)
        
        # 장르 추가
        cursor.execute('''
            SELECT g.name FROM genre g
            JOIN anime_genre ag ON g.id = ag.genre_id
            WHERE ag.anime_id = ?
        ''', (anime_id,))
        anime['genres'] = [r[0] for r in cursor.fetchall()]
        
        # 태그 추가
        cursor.execute('''
            SELECT t.name, at.rank FROM tag t
            JOIN anime_tag at ON t.id = at.tag_id
            WHERE at.anime_id = ?
            ORDER BY at.rank DESC
        ''', (anime_id,))
        anime['tags'] = [{'name': r[0], 'rank': r[1]} for r in cursor.fetchall()]
        
        # 스튜디오 추가
        cursor.execute('''
            SELECT s.name, ast.is_main FROM studio s
            JOIN anime_studio ast ON s.id = ast.studio_id
            WHERE ast.anime_id = ?
        ''', (anime_id,))
        anime['studios'] = [{'name': r[0], 'is_main': bool(r[1])} for r in cursor.fetchall()]
        
        return anime
    
    def search_anime(self, query: str, limit: int = 20) -> List[Dict]:
        """애니메이션 검색"""
        cursor = self.conn.cursor()
        search = f'%{query}%'
        cursor.execute('''
            SELECT id, title_romaji, title_english, title_native,
                   cover_image_url, average_score, popularity, episodes, format
            FROM anime
            WHERE title_romaji LIKE ? OR title_english LIKE ? OR title_native LIKE ?
            ORDER BY popularity DESC
            LIMIT ?
        ''', (search, search, search, limit))
        return [dict(r) for r in cursor.fetchall()]
    
    def get_popular_anime(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """인기 애니메이션 목록"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, title_romaji, title_english, cover_image_url, cover_image_local,
                   average_score, popularity, episodes, format, season, season_year
            FROM anime
            ORDER BY popularity DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        return [dict(r) for r in cursor.fetchall()]
    
    def get_anime_by_genre(self, genre: str, limit: int = 50) -> List[Dict]:
        """장르별 애니메이션"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT a.id, a.title_romaji, a.title_english, a.cover_image_url,
                   a.average_score, a.popularity
            FROM anime a
            JOIN anime_genre ag ON a.id = ag.anime_id
            JOIN genre g ON g.id = ag.genre_id
            WHERE g.name = ?
            ORDER BY a.popularity DESC
            LIMIT ?
        ''', (genre, limit))
        return [dict(r) for r in cursor.fetchall()]
    
    def get_anime_by_season(self, year: int, season: str) -> List[Dict]:
        """시즌별 애니메이션"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, title_romaji, title_english, cover_image_url,
                   average_score, popularity, format
            FROM anime
            WHERE season_year = ? AND season = ?
            ORDER BY popularity DESC
        ''', (year, season.upper()))
        return [dict(r) for r in cursor.fetchall()]
    
    # =========================================
    # 캐릭터 조회
    # =========================================
    
    def get_character(self, char_id: int) -> Optional[Dict]:
        """캐릭터 상세 정보"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM character WHERE id = ?', (char_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        char = dict(row)
        
        # 출연 애니메이션
        cursor.execute('''
            SELECT a.id, a.title_romaji, a.cover_image_url, ac.role
            FROM anime a
            JOIN anime_character ac ON a.id = ac.anime_id
            WHERE ac.character_id = ?
            ORDER BY a.popularity DESC
        ''', (char_id,))
        char['anime'] = [dict(r) for r in cursor.fetchall()]
        
        # 성우
        cursor.execute('''
            SELECT s.id, s.name_full, s.image_url, s.language
            FROM staff s
            JOIN character_voice_actor cva ON s.id = cva.staff_id
            WHERE cva.character_id = ?
        ''', (char_id,))
        char['voice_actors'] = [dict(r) for r in cursor.fetchall()]
        
        return char
    
    def get_anime_characters(self, anime_id: int) -> List[Dict]:
        """애니메이션의 캐릭터 목록"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT c.id, c.name_full, c.name_native, c.image_url, ac.role,
                   c.favourites
            FROM character c
            JOIN anime_character ac ON c.id = ac.character_id
            WHERE ac.anime_id = ?
            ORDER BY 
                CASE ac.role 
                    WHEN 'MAIN' THEN 1 
                    WHEN 'SUPPORTING' THEN 2 
                    ELSE 3 
                END,
                c.favourites DESC
        ''', (anime_id,))
        return [dict(r) for r in cursor.fetchall()]
    
    def search_character(self, query: str, limit: int = 20) -> List[Dict]:
        """캐릭터 검색"""
        cursor = self.conn.cursor()
        search = f'%{query}%'
        cursor.execute('''
            SELECT id, name_full, name_native, image_url, favourites
            FROM character
            WHERE name_full LIKE ? OR name_native LIKE ?
            ORDER BY favourites DESC
            LIMIT ?
        ''', (search, search, limit))
        return [dict(r) for r in cursor.fetchall()]
    
    # =========================================
    # 스태프/성우 조회
    # =========================================
    
    def get_staff(self, staff_id: int) -> Optional[Dict]:
        """스태프 상세 정보"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM staff WHERE id = ?', (staff_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        staff = dict(row)
        
        # 성우로서 연기한 캐릭터
        cursor.execute('''
            SELECT c.id, c.name_full, c.image_url, a.id as anime_id, a.title_romaji
            FROM character c
            JOIN character_voice_actor cva ON c.id = cva.character_id
            JOIN anime a ON a.id = cva.anime_id
            WHERE cva.staff_id = ?
            ORDER BY a.popularity DESC
        ''', (staff_id,))
        staff['characters'] = [dict(r) for r in cursor.fetchall()]
        
        # 스태프로서 참여한 작품
        cursor.execute('''
            SELECT a.id, a.title_romaji, a.cover_image_url, ast.role
            FROM anime a
            JOIN anime_staff ast ON a.id = ast.anime_id
            WHERE ast.staff_id = ?
            ORDER BY a.popularity DESC
        ''', (staff_id,))
        staff['works'] = [dict(r) for r in cursor.fetchall()]
        
        return staff
    
    def get_anime_staff(self, anime_id: int) -> List[Dict]:
        """애니메이션의 스태프 목록"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT s.id, s.name_full, s.image_url, ast.role
            FROM staff s
            JOIN anime_staff ast ON s.id = ast.staff_id
            WHERE ast.anime_id = ?
        ''', (anime_id,))
        return [dict(r) for r in cursor.fetchall()]
    
    def get_anime_voice_actors(self, anime_id: int) -> List[Dict]:
        """애니메이션의 성우 목록 (캐릭터 포함)"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT s.id as staff_id, s.name_full as staff_name, s.image_url as staff_image,
                   c.id as char_id, c.name_full as char_name, c.image_url as char_image,
                   cva.language
            FROM character_voice_actor cva
            JOIN staff s ON s.id = cva.staff_id
            JOIN character c ON c.id = cva.character_id
            WHERE cva.anime_id = ?
        ''', (anime_id,))
        return [dict(r) for r in cursor.fetchall()]
    
    # =========================================
    # 통계
    # =========================================
    
    def get_stats(self) -> Dict:
        """데이터베이스 통계"""
        cursor = self.conn.cursor()
        
        stats = {}
        
        cursor.execute('SELECT COUNT(*) FROM anime')
        stats['total_anime'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM character')
        stats['total_characters'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM staff')
        stats['total_staff'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM genre')
        stats['total_genres'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM tag')
        stats['total_tags'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM studio')
        stats['total_studios'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT name FROM genre ORDER BY name')
        stats['genres'] = [r[0] for r in cursor.fetchall()]
        
        return stats
    
    def get_all_genres(self) -> List[str]:
        """모든 장르 목록"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT name FROM genre ORDER BY name')
        return [r[0] for r in cursor.fetchall()]


# 테스트
if __name__ == '__main__':
    db = AnimeDB()
    
    print("📊 Database Stats:")
    stats = db.get_stats()
    for key, value in stats.items():
        if key != 'genres':
            print(f"   {key}: {value}")
    
    print(f"\n📚 Genres: {', '.join(stats.get('genres', []))}")
    
    print("\n🔝 Top 5 Popular Anime:")
    for anime in db.get_popular_anime(limit=5):
        print(f"   - {anime['title_romaji']} (Score: {anime['average_score']})")
    
    db.close()
