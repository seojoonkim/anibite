"""
커버 이미지 다운로드 (large 해상도 - 고퀄리티)
별도 폴더에 저장: images/covers_large/
"""
import sqlite3
import os
import time
import urllib.request
from datetime import datetime

DB_PATH = 'anime.db'
IMAGES_DIR = 'images/covers_large'

def download_image(url: str, save_path: str, retries: int = 3) -> bool:
    """이미지 다운로드 (재시도 포함)"""
    if not url:
        return False

    for attempt in range(retries):
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
            if attempt < retries - 1:
                time.sleep(1)
                continue
            else:
                print(f"  ⚠️ 실패: {e}")
                return False

def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║   🖼️  커버 이미지 다운로드 (large 해상도 - 고퀄리티)      ║
║   폴더: images/covers_large/                              ║
║   예상 용량: ~690 MB (~230KB/이미지)                       ║
╚════════════════════════════════════════════════════════════╝
    """)

    os.makedirs(IMAGES_DIR, exist_ok=True)

    # WAL 모드로 데이터베이스 열기 (동시 읽기/쓰기 지원)
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL")
    cursor = conn.cursor()

    # 커버 이미지 URL이 있는 애니메이션 조회
    cursor.execute("""
        SELECT id, cover_image_url, title_romaji
        FROM anime
        WHERE cover_image_url IS NOT NULL
        ORDER BY popularity DESC
    """)

    anime_list = cursor.fetchall()
    total = len(anime_list)
    downloaded = 0
    skipped = 0
    failed = 0

    print(f"📊 다운로드 대상: {total:,}개\n")

    start_time = time.time()

    for i, (anime_id, large_url, title) in enumerate(anime_list, 1):
        save_path = f"{IMAGES_DIR}/{anime_id}.jpg"

        # 이미 존재하면 건너뛰기
        if os.path.exists(save_path):
            skipped += 1
            if i % 100 == 0:
                print(f"  [{i}/{total}] 스킵 중... (다운: {downloaded}, 스킵: {skipped}, 실패: {failed})")
            continue

        # 다운로드 (large URL 그대로 사용)
        if i % 50 == 1:
            print(f"\n📥 [{i}/{total}] {title[:40]}...")
            print(f"   URL: {large_url[:70]}...")

        if download_image(large_url, save_path):
            downloaded += 1

            if downloaded % 100 == 0:
                elapsed = time.time() - start_time
                avg_time = elapsed / downloaded
                remaining = (total - i) * avg_time
                print(f"  💾 {downloaded}개 저장 (예상 남은 시간: {remaining/60:.1f}분)")
        else:
            failed += 1

        # Rate limiting
        time.sleep(0.2)

    conn.close()

    # 통계
    elapsed = time.time() - start_time

    print(f"\n{'='*60}")
    print(f"✅ 다운로드 완료!")
    print(f"{'='*60}")
    print(f"  전체: {total:,}개")
    print(f"  성공: {downloaded:,}개")
    print(f"  스킵: {skipped:,}개")
    print(f"  실패: {failed:,}개")
    print(f"  소요 시간: {elapsed/60:.1f}분")

    # 파일 크기 확인
    if os.path.exists(IMAGES_DIR):
        files = [f for f in os.listdir(IMAGES_DIR) if f.endswith('.jpg')]
        if files:
            total_size = sum(os.path.getsize(f"{IMAGES_DIR}/{f}") for f in files)
            avg_size = total_size / len(files)
            print(f"  이미지 파일: {len(files):,}개")
            print(f"  전체 용량: {total_size / 1024 / 1024:.1f} MB")
            print(f"  평균 크기: {avg_size / 1024:.1f} KB")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 중단됨")
    except Exception as e:
        print(f"\n❌ 에러: {e}")
        import traceback
        traceback.print_exc()
