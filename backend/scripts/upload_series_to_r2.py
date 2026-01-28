"""
특정 시리즈의 이미지를 AniList에서 다운로드하여 R2에 업로드
Railway 환경에서 실행
"""
import os
import sys
import time
import urllib.request
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.r2_storage import upload_file_bytes_to_r2, is_r2_configured, check_r2_object_exists

API_URL = 'https://graphql.anilist.co'
REQUEST_DELAY = 0.7


def make_request(query: str, variables: dict = None) -> dict:
    """GraphQL 요청"""
    time.sleep(REQUEST_DELAY)

    data = json.dumps({
        'query': query,
        'variables': variables or {}
    }).encode('utf-8')

    req = urllib.request.Request(API_URL, data=data, headers={
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'AniPass/1.0'
    })

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            if 'errors' in result:
                print(f"GraphQL Error: {result['errors']}")
                return None
            return result.get('data')
    except Exception as e:
        print(f"Request failed: {e}")
        return None


def search_anime(search_term: str):
    """애니메이션 검색"""
    query = '''
    query ($search: String) {
        Page(page: 1, perPage: 50) {
            media(search: $search, type: ANIME, sort: POPULARITY_DESC) {
                id
                title {
                    romaji
                    english
                    native
                }
                format
                seasonYear
                coverImage {
                    extraLarge
                    large
                }
            }
        }
    }
    '''
    result = make_request(query, {'search': search_term})
    if result:
        return result['Page']['media']
    return []


def get_anime_by_id(anime_id: int):
    """ID로 애니메이션 정보 가져오기"""
    query = '''
    query ($id: Int) {
        Media(id: $id, type: ANIME) {
            id
            title {
                romaji
                english
                native
            }
            coverImage {
                extraLarge
                large
            }
        }
    }
    '''
    result = make_request(query, {'id': anime_id})
    if result:
        return result.get('Media')
    return None


def get_anime_characters(anime_id: int):
    """애니메이션의 캐릭터 + 성우 정보"""
    all_characters = []
    page = 1

    while True:
        query = '''
        query ($id: Int, $page: Int) {
            Media(id: $id) {
                characters(page: $page, perPage: 25, sort: [ROLE, FAVOURITES_DESC]) {
                    pageInfo {
                        hasNextPage
                    }
                    edges {
                        role
                        node {
                            id
                            name {
                                full
                                native
                            }
                            image { large }
                        }
                        voiceActors(language: JAPANESE) {
                            id
                            name {
                                full
                                native
                            }
                            image { large }
                        }
                    }
                }
            }
        }
        '''
        result = make_request(query, {'id': anime_id, 'page': page})

        if not result or not result.get('Media'):
            break

        characters = result['Media']['characters']
        all_characters.extend(characters['edges'])

        if not characters['pageInfo']['hasNextPage']:
            break
        page += 1

    return all_characters


def download_image(url: str) -> bytes:
    """이미지 다운로드"""
    if not url:
        return None

    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read()
    except Exception as e:
        print(f"  Failed to download {url}: {e}")
        return None


def upload_image_to_r2(image_bytes: bytes, object_key: str) -> bool:
    """R2에 업로드 (이미 있으면 스킵)"""
    if not image_bytes:
        return False

    try:
        # 이미 있는지 확인
        if check_r2_object_exists(object_key):
            print(f"  Already exists: {object_key}")
            return True

        url = upload_file_bytes_to_r2(image_bytes, object_key, 'image/jpeg')
        print(f"  Uploaded: {url}")
        return True
    except Exception as e:
        print(f"  Upload failed: {e}")
        return False


def process_anime_list(anime_ids: list):
    """애니메이션 ID 목록 처리"""
    if not is_r2_configured():
        print("ERROR: R2 is not configured!")
        return

    all_anime = []
    all_characters = {}
    all_staff = {}

    # 애니메이션 정보 가져오기
    print("=" * 60)
    print("Fetching anime info...")
    print("=" * 60)

    for anime_id in anime_ids:
        anime = get_anime_by_id(anime_id)
        if anime:
            all_anime.append(anime)
            print(f"  [{anime_id}] {anime['title']['romaji']}")

    # 커버 이미지 업로드
    print("\n" + "=" * 60)
    print("Uploading cover images...")
    print("=" * 60)

    for anime in all_anime:
        anime_id = anime['id']
        cover_url = anime['coverImage'].get('extraLarge') or anime['coverImage'].get('large')

        if cover_url:
            print(f"\n[{anime_id}] {anime['title']['romaji']}")
            image_bytes = download_image(cover_url)
            if image_bytes:
                upload_image_to_r2(image_bytes, f"covers_large/{anime_id}.jpg")

    # 캐릭터 및 성우 정보 수집
    print("\n" + "=" * 60)
    print("Fetching characters and voice actors...")
    print("=" * 60)

    for anime in all_anime:
        anime_id = anime['id']
        print(f"\n[{anime_id}] {anime['title']['romaji']}")

        characters = get_anime_characters(anime_id)

        for edge in characters:
            char = edge['node']
            char_id = char['id']

            if char_id not in all_characters and char['image'].get('large'):
                all_characters[char_id] = {
                    'name': char['name']['full'],
                    'image_url': char['image']['large']
                }

            for va in edge.get('voiceActors', []):
                va_id = va['id']
                if va_id not in all_staff and va['image'].get('large'):
                    all_staff[va_id] = {
                        'name': va['name']['full'],
                        'image_url': va['image']['large']
                    }

    print(f"\nTotal characters: {len(all_characters)}")
    print(f"Total voice actors: {len(all_staff)}")

    # 캐릭터 이미지 업로드
    print("\n" + "=" * 60)
    print("Uploading character images...")
    print("=" * 60)

    for char_id, info in all_characters.items():
        print(f"\n[{char_id}] {info['name']}")
        image_bytes = download_image(info['image_url'])
        if image_bytes:
            upload_image_to_r2(image_bytes, f"characters/{char_id}.jpg")

    # 성우 이미지 업로드
    print("\n" + "=" * 60)
    print("Uploading voice actor images...")
    print("=" * 60)

    for staff_id, info in all_staff.items():
        print(f"\n[{staff_id}] {info['name']}")
        image_bytes = download_image(info['image_url'])
        if image_bytes:
            upload_image_to_r2(image_bytes, f"staff/{staff_id}.jpg")

    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)


# 슬레이어즈 시리즈 ID
SLAYERS_IDS = [
    534,    # Slayers (1995)
    535,    # Slayers NEXT (1996)
    1172,   # Slayers TRY (1997)
    4028,   # Slayers REVOLUTION (2008)
    5233,   # Slayers EVOLUTION-R (2009)
    536,    # Slayers Movie (1995)
    1171,   # Slayers Excellent (1998)
    1170,   # Slayers Special (1996)
    869,    # Slayers RETURN (1996)
    867,    # Slayers Gorgeous (1998)
    868,    # Slayers Great (1997)
    866,    # Slayers Premium (2001)
]

# 마법진 구루구루 시리즈 ID
GURU_GURU_IDS = [
    331,    # Mahoujin Guru Guru (1994)
    2063,   # Doki Doki Densetsu: Mahoujin Guru Guru (2000)
    98144,  # Mahoujin Guru Guru (2017)
    874,    # Mahoujin Guru Guru Movie
]


if __name__ == '__main__':
    print("Processing Slayers + Mahoujin Guru Guru series...")
    all_ids = SLAYERS_IDS + GURU_GURU_IDS
    process_anime_list(all_ids)
