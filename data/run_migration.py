"""
데이터베이스 마이그레이션 실행 스크립트
"""
import sqlite3
import os

DB_PATH = 'data/anime.db'
MIGRATIONS_DIR = 'data/migrations'

def run_migration(migration_file):
    """마이그레이션 파일 실행"""
    print(f"📋 마이그레이션 실행: {migration_file}")

    conn = sqlite3.connect(DB_PATH)

    try:
        with open(os.path.join(MIGRATIONS_DIR, migration_file), 'r') as f:
            sql = f.read()

        conn.executescript(sql)
        conn.commit()
        print(f"✅ 마이그레이션 완료: {migration_file}\n")

        # 적용된 테이블 확인
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]

        print("📊 현재 테이블 목록:")
        for table in tables:
            if table.startswith('user') or table in ['migration_history', 'recommendation_cache']:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  - {table}: {count}개")

        return True

    except Exception as e:
        print(f"❌ 마이그레이션 실패: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()

def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║   🗄️  AniPass 데이터베이스 마이그레이션                    ║
╚════════════════════════════════════════════════════════════╝
    """)

    if not os.path.exists(DB_PATH):
        print(f"❌ 데이터베이스 파일이 없습니다: {DB_PATH}")
        return

    if not os.path.exists(MIGRATIONS_DIR):
        print(f"❌ 마이그레이션 디렉토리가 없습니다: {MIGRATIONS_DIR}")
        return

    # 마이그레이션 파일 목록
    migration_files = sorted([f for f in os.listdir(MIGRATIONS_DIR) if f.endswith('.sql')])

    if not migration_files:
        print("⚠️  마이그레이션 파일이 없습니다.")
        return

    print(f"발견된 마이그레이션: {len(migration_files)}개\n")

    # 각 마이그레이션 실행
    for migration_file in migration_files:
        success = run_migration(migration_file)
        if not success:
            print("⚠️  마이그레이션 중단")
            break

    print("\n🎉 모든 마이그레이션 완료!")

if __name__ == '__main__':
    main()
