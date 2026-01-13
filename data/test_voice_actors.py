"""
성우 데이터 API 응답 테스트
"""
from anilist_client import AniListClient
import json

client = AniListClient()

# 인기 애니메이션 하나 테스트
anime_id = 16498  # Shingeki no Kyojin

print(f"Testing anime ID: {anime_id}")
response = client.get_anime_characters(anime_id)

if response and 'Media' in response:
    anime_data = response['Media']
    characters = anime_data.get('characters', {}).get('edges', [])

    print(f"\n총 캐릭터 수: {len(characters)}")

    for i, char_edge in enumerate(characters[:3], 1):  # 처음 3명만
        char_node = char_edge.get('node', {})
        char_name = char_node.get('name', {}).get('full', 'Unknown')
        voice_actors = char_edge.get('voiceActors', [])

        print(f"\n캐릭터 {i}: {char_name}")
        print(f"  성우 수: {len(voice_actors)}")

        for va in voice_actors:
            va_name = va.get('name', {}).get('full', 'Unknown')
            va_lang = va.get('language', 'Unknown')
            print(f"    - {va_name} ({va_lang})")
else:
    print("응답 없음")
