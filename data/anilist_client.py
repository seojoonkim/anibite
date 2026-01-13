"""
AniList GraphQL API 클라이언트
인기 애니 3,000개 + 캐릭터/성우/스태프 크롤링용
"""

import urllib.request
import json
import time
from typing import Optional, Dict, List, Any

API_URL = 'https://graphql.anilist.co'
RATE_LIMIT = 90  # requests per minute
REQUEST_DELAY = 60 / RATE_LIMIT  # ~0.67초

class AniListClient:
    def __init__(self):
        self.request_count = 0
        self.last_request_time = 0
    
    def _wait_for_rate_limit(self):
        """Rate limit 준수를 위한 대기"""
        elapsed = time.time() - self.last_request_time
        if elapsed < REQUEST_DELAY:
            time.sleep(REQUEST_DELAY - elapsed)
    
    def _make_request(self, query: str, variables: Dict = None) -> Dict:
        """GraphQL 요청 실행"""
        self._wait_for_rate_limit()
        
        data = json.dumps({
            'query': query,
            'variables': variables or {}
        }).encode('utf-8')
        
        req = urllib.request.Request(API_URL, data=data, headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        })
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                self.last_request_time = time.time()
                self.request_count += 1
                result = json.loads(response.read().decode('utf-8'))
                
                if 'errors' in result:
                    print(f"GraphQL Error: {result['errors']}")
                    return None
                    
                return result.get('data')
        except Exception as e:
            print(f"Request failed: {e}")
            return None
    
    def get_popular_anime_page(self, page: int = 1, per_page: int = 50) -> Dict:
        """인기순 애니메이션 목록 (페이지네이션)"""
        query = '''
        query ($page: Int, $perPage: Int) {
            Page(page: $page, perPage: $perPage) {
                pageInfo {
                    currentPage
                    hasNextPage
                    total
                }
                media(type: ANIME, sort: POPULARITY_DESC) {
                    id
                    idMal
                    title {
                        romaji
                        english
                        native
                    }
                    type
                    format
                    status
                    description
                    season
                    seasonYear
                    episodes
                    duration
                    startDate { year month day }
                    endDate { year month day }
                    coverImage {
                        large
                        color
                    }
                    bannerImage
                    averageScore
                    meanScore
                    popularity
                    favourites
                    trending
                    source
                    countryOfOrigin
                    isAdult
                    isLicensed
                    siteUrl
                    trailer {
                        id
                        site
                    }
                    updatedAt
                    genres
                    tags {
                        id
                        name
                        description
                        category
                        rank
                        isGeneralSpoiler
                        isMediaSpoiler
                        isAdult
                    }
                    studios {
                        edges {
                            isMain
                            node {
                                id
                                name
                                isAnimationStudio
                                siteUrl
                                favourites
                            }
                        }
                    }
                    relations {
                        edges {
                            relationType
                            node {
                                id
                                type
                            }
                        }
                    }
                    recommendations(perPage: 10) {
                        nodes {
                            rating
                            mediaRecommendation {
                                id
                            }
                        }
                    }
                    externalLinks {
                        site
                        url
                        type
                        language
                    }
                    streamingEpisodes {
                        title
                        thumbnail
                        url
                        site
                    }
                    stats {
                        scoreDistribution {
                            score
                            amount
                        }
                        statusDistribution {
                            status
                            amount
                        }
                    }
                }
            }
        }
        '''
        return self._make_request(query, {'page': page, 'perPage': per_page})
    
    def get_anime_characters(self, anime_id: int, page: int = 1) -> Dict:
        """애니메이션의 캐릭터 + 성우 정보"""
        query = '''
        query ($id: Int, $page: Int) {
            Media(id: $id) {
                id
                characters(page: $page, perPage: 25, sort: [ROLE, FAVOURITES_DESC]) {
                    pageInfo {
                        hasNextPage
                        currentPage
                    }
                    edges {
                        role
                        node {
                            id
                            name {
                                first
                                last
                                full
                                native
                                alternative
                            }
                            description
                            gender
                            age
                            dateOfBirth { month day }
                            bloodType
                            image { large }
                            favourites
                        }
                        voiceActors(language: JAPANESE) {
                            id
                            name {
                                first
                                last
                                full
                                native
                            }
                            description
                            gender
                            age
                            dateOfBirth { year month day }
                            dateOfDeath { year month day }
                            homeTown
                            bloodType
                            yearsActive
                            primaryOccupations
                            language
                            image { large }
                            favourites
                        }
                    }
                }
            }
        }
        '''
        return self._make_request(query, {'id': anime_id, 'page': page})
    
    def get_anime_staff(self, anime_id: int, page: int = 1) -> Dict:
        """애니메이션의 스태프 정보"""
        query = '''
        query ($id: Int, $page: Int) {
            Media(id: $id) {
                id
                staff(page: $page, perPage: 25) {
                    pageInfo {
                        hasNextPage
                        currentPage
                    }
                    edges {
                        role
                        node {
                            id
                            name {
                                first
                                last
                                full
                                native
                            }
                            description
                            gender
                            age
                            dateOfBirth { year month day }
                            dateOfDeath { year month day }
                            homeTown
                            bloodType
                            yearsActive
                            primaryOccupations
                            image { large }
                            favourites
                        }
                    }
                }
            }
        }
        '''
        return self._make_request(query, {'id': anime_id, 'page': page})
    
    def get_character_detail(self, character_id: int) -> Dict:
        """캐릭터 상세 정보"""
        query = '''
        query ($id: Int) {
            Character(id: $id) {
                id
                name {
                    first
                    last
                    full
                    native
                    alternative
                }
                description
                gender
                age
                dateOfBirth { month day }
                bloodType
                image { large }
                favourites
            }
        }
        '''
        return self._make_request(query, {'id': character_id})
    
    def get_staff_detail(self, staff_id: int) -> Dict:
        """스태프 상세 정보"""
        query = '''
        query ($id: Int) {
            Staff(id: $id) {
                id
                name {
                    first
                    last
                    full
                    native
                }
                description
                gender
                age
                dateOfBirth { year month day }
                dateOfDeath { year month day }
                homeTown
                bloodType
                yearsActive
                primaryOccupations
                language
                image { large }
                favourites
            }
        }
        '''
        return self._make_request(query, {'id': staff_id})


# 테스트
if __name__ == '__main__':
    client = AniListClient()
    
    print("Testing AniList API client...")
    print("-" * 50)
    
    # 인기 애니 1페이지 가져오기
    result = client.get_popular_anime_page(page=1, per_page=3)
    
    if result:
        page_info = result['Page']['pageInfo']
        media_list = result['Page']['media']
        
        print(f"Total anime: {page_info.get('total', 'N/A')}")
        print(f"Has next page: {page_info['hasNextPage']}")
        print(f"\nTop 3 popular anime:")
        
        for i, anime in enumerate(media_list, 1):
            print(f"\n{i}. {anime['title']['romaji']}")
            print(f"   English: {anime['title'].get('english', 'N/A')}")
            print(f"   Score: {anime.get('averageScore', 'N/A')}")
            print(f"   Popularity: {anime.get('popularity', 'N/A')}")
            print(f"   Episodes: {anime.get('episodes', 'N/A')}")
            print(f"   Genres: {', '.join(anime.get('genres', []))}")
    else:
        print("Failed to fetch data (network might be restricted)")
