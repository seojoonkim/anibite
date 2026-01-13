"""
누락된 애니메이션 이미지 다운로드
cover_image_local이 설정되어 있지만 파일이 없는 경우 다운로드
"""
import sqlite3
import requests
import os
from pathlib import Path

def download_missing_images():
    conn = sqlite3.connect('anime.db')
    cursor = conn.cursor()

    # cover_image_local이 있지만 파일이 없는 애니메이션 조회
    cursor.execute("""
        SELECT id, cover_image_url, cover_image_local
        FROM anime
        WHERE cover_image_local IS NOT NULL
        AND cover_image_url IS NOT NULL
    """)

    rows = cursor.fetchall()
    missing_count = 0
    downloaded_count = 0
    exists_count = 0

    for anime_id, cover_url, cover_local in rows:
        file_path = Path(cover_local)

        if not file_path.exists():
            missing_count += 1
            print(f"⬇️  다운로드 중: ID {anime_id} ({cover_local})")

            try:
                # 디렉토리 생성
                file_path.parent.mkdir(parents=True, exist_ok=True)

                # 이미지 다운로드
                response = requests.get(cover_url, timeout=10)
                response.raise_for_status()

                # 파일 저장
                with open(file_path, 'wb') as f:
                    f.write(response.content)

                downloaded_count += 1
                print(f"   ✅ 다운로드 완료")

            except Exception as e:
                print(f"   ❌ 실패: {str(e)}")
        else:
            exists_count += 1

    conn.close()

    print(f"\n📊 결과:")
    print(f"   - 이미 존재: {exists_count}개")
    print(f"   - 누락: {missing_count}개")
    print(f"   - 다운로드 완료: {downloaded_count}개")

if __name__ == "__main__":
    download_missing_images()
