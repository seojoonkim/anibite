"""
커버 이미지 다운로드 (medium 해상도)
large 대신 medium 사용으로 용량 절약
"""
import sqlite3
import os
import time
import urllib.request
from datetime import datetime

DB_PATH = 'anime.db'
IMAGES_DIR = 'images/covers'

def download_image(url: str, save_path: str) -> bool:
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
        print(f"  ⚠️ 실패: {e}")
        return False

def get_medium_cover_url(large_url: str) -> str:
    """large URL을 medium URL로 변환"""
    if not large_url:
        return None

    # AniList CDN URL 패턴: .../large.jpg -> .../medium.jpg
    if '/large.' in large_url:
        return large_url.replace('/large.', '/medium.')
    elif '/cover/large/' in large_url:
        return large_url.replace('/cover/large/', '/cover/medium/')
    else:
        # 패턴을 찾지 못하면 large 사용
        return large_url

def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║   🖼️  커버 이미지 다운로드 (medium 해상도)                ║
║   용량 절약: ~100KB/이미지 (large: ~230KB)                 ║
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

        # medium URL로 변환
        medium_url = get_medium_cover_url(large_url)

        # 다운로드
        if i % 50 == 1:
            print(f"\n📥 [{i}/{total}] {title[:40]}...")
            print(f"   URL: {medium_url[:70]}...")

        if download_image(medium_url, save_path):
            # DB 업데이트 (즉시 커밋으로 락 최소화)
            try:
                cursor.execute(
                    "UPDATE anime SET cover_image_local = ? WHERE id = ?",
                    (save_path, anime_id)
                )
                conn.commit()  # 즉시 커밋으로 락 시간 최소화
                downloaded += 1

                if downloaded % 100 == 0:
                    elapsed = time.time() - start_time
                    avg_time = elapsed / downloaded
                    remaining = (total - i) * avg_time
                    print(f"  💾 {downloaded}개 저장 (예상 남은 시간: {remaining/60:.1f}분)")
            except sqlite3.OperationalError as e:
                print(f"  ⚠️ DB 업데이트 실패: {e}")
                failed += 1
        else:
            failed += 1

        # Rate limiting
        time.sleep(0.2)  # 백엔드와 충돌 방지를 위해 증가

    conn.commit()

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

    conn.close()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 중단됨")
    except Exception as e:
        print(f"\n❌ 에러: {e}")
        import traceback
        traceback.print_exc()
