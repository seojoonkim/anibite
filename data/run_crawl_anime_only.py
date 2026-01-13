"""
애니메이션 3000개까지만 크롤링 (캐릭터/스태프/이미지 제외)
"""
import os
import sqlite3
from datetime import datetime
from crawler import AnimeCrawler, TARGET_ANIME_COUNT

def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║   🎌 AniList 크롤러 - 애니메이션 3,000개 크롤링            ║
╚════════════════════════════════════════════════════════════╝
    """)

    crawler = AnimeCrawler()

    try:
        crawler.connect()
        crawler.print_stats()

        # 애니메이션만 크롤링
        print("\n" + "─"*60)
        print("📌 애니메이션 3,000개 크롤링 시작")
        crawler.crawl_anime_list(TARGET_ANIME_COUNT)

        # 완료
        crawler._update_meta('last_anime_crawl', datetime.now().isoformat())
        crawler.print_stats()

        print("\n🎉 애니메이션 크롤링 완료!")

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
