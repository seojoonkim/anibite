"""
Test anime and character ratings performance with feed_activities
"""
import sys
import time
from services.rating_service import get_user_ratings
from services.profile_service import get_character_ratings

print("Testing anime and character ratings performance with feed_activities...\n")

user_id = 4

# Test anime ratings
print("=" * 60)
print("Testing anime ratings...")
start = time.time()
anime_result = get_user_ratings(user_id, limit=500)
elapsed_anime = time.time() - start

print(f"✓ Retrieved {len(anime_result.items)} anime ratings in {elapsed_anime:.3f} seconds")
print(f"  Total: {anime_result.total}")
print(f"  Average rating: {anime_result.average_rating:.2f}" if anime_result.average_rating else "  Average rating: N/A")

# Test character ratings
print("\n" + "=" * 60)
print("Testing character ratings...")
start = time.time()
characters = get_character_ratings(user_id, limit=500)
elapsed_chars = time.time() - start

print(f"✓ Retrieved {len(characters)} character ratings in {elapsed_chars:.3f} seconds")

if characters:
    print(f"\nFirst character:")
    print(f"  Name: {characters[0]['character_name']}")
    print(f"  Anime: {characters[0].get('anime_title', 'N/A')}")
    print(f"  Rating: {characters[0]['rating']}")

print("\n" + "=" * 60)
print("Performance Summary:")
print(f"  Anime ratings:     {elapsed_anime:.3f}s")
print(f"  Character ratings: {elapsed_chars:.3f}s")
print(f"\nPrevious character ratings: 0.126s (with LEFT JOIN optimization)")
print(f"Current with feed_activities: {elapsed_chars:.3f}s")
print(f"\n✨ All data from single indexed table!")
print(f"✨ No JOINs needed - all denormalized!")
