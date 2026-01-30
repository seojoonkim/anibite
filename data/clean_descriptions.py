"""
Description에서 HTML 태그와 마크다운 문법을 정리하는 스크립트

처리 대상:
- HTML 태그 (<br>, <i>, <b>, etc.)
- 마크다운 문법 (__, **, ~~, etc.)
- 불필요한 공백 및 개행
"""

import sqlite3
import re
from typing import Tuple

class DescriptionCleaner:
    def __init__(self, db_path: str = 'anime.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    def close(self):
        """데이터베이스 연결 종료"""
        self.conn.commit()
        self.conn.close()

    def clean_html(self, text: str) -> str:
        """HTML 태그 제거 및 정리"""
        if not text:
            return text

        # <br> 태그를 개행으로 변환
        text = re.sub(r'<br\s*/?>\s*', '\n', text, flags=re.IGNORECASE)

        # <i>, <b>, <em>, <strong> 등의 태그는 내용만 남기고 제거
        text = re.sub(r'<(i|b|em|strong)>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'</(i|b|em|strong)>', '', text, flags=re.IGNORECASE)

        # 나머지 HTML 태그 제거 (내용 유지)
        text = re.sub(r'<[^>]+>', '', text)

        # HTML 엔티티 변환
        text = text.replace('&quot;', '"')
        text = text.replace('&apos;', "'")
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&nbsp;', ' ')

        return text

    def clean_markdown(self, text: str) -> str:
        """마크다운 문법 제거 및 정리"""
        if not text:
            return text

        # Bold/Italic (**text**, __text__, *text*, _text_)
        # 두 개짜리 먼저 처리
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'__(.+?)__', r'\1', text)

        # 한 개짜리 (너무 공격적이면 문제가 될 수 있으므로 조심)
        # 단어 강조에만 사용되는 경우만 제거
        text = re.sub(r'(?<!\w)\*([^*\n]+?)\*(?!\w)', r'\1', text)
        text = re.sub(r'(?<!\w)_([^_\n]+?)_(?!\w)', r'\1', text)

        # Strikethrough (~~text~~)
        text = re.sub(r'~~(.+?)~~', r'\1', text)

        # Headers (# Header, ## Header, etc.) - 제목 기호만 제거
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

        # Links ([text](url)) - 텍스트만 남김
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

        # Images (![alt](url)) - alt 텍스트만 남김
        text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'\1', text)

        # Code blocks (```code```) - 내용만 남김
        text = re.sub(r'```[^\n]*\n(.+?)\n```', r'\1', text, flags=re.DOTALL)

        # Inline code (`code`) - 내용만 남김
        text = re.sub(r'`([^`]+)`', r'\1', text)

        return text

    def clean_whitespace(self, text: str) -> str:
        """불필요한 공백과 개행 정리"""
        if not text:
            return text

        # 연속된 공백을 하나로
        text = re.sub(r' +', ' ', text)

        # 줄 끝 공백 제거
        text = re.sub(r' +\n', '\n', text)

        # 연속된 개행을 최대 2개로 제한
        text = re.sub(r'\n{3,}', '\n\n', text)

        # 앞뒤 공백 제거
        text = text.strip()

        return text

    def clean_description(self, text: str) -> str:
        """전체 정리 프로세스"""
        if not text:
            return text

        # 1. HTML 태그 제거
        text = self.clean_html(text)

        # 2. 마크다운 문법 제거
        text = self.clean_markdown(text)

        # 3. 공백 정리
        text = self.clean_whitespace(text)

        return text

    def preview_changes(self, table: str, limit: int = 5):
        """변경 사항 미리보기"""
        query = f"""
            SELECT id, description
            FROM {table}
            WHERE description IS NOT NULL
            AND description != ''
            AND (
                description LIKE '%<br%'
                OR description LIKE '%<i>%'
                OR description LIKE '%<b>%'
                OR description LIKE '%__%'
                OR description LIKE '%**%'
            )
            LIMIT {limit}
        """

        self.cursor.execute(query)
        rows = self.cursor.fetchall()

        print(f"\n{'='*80}")
        print(f"📋 {table.upper()} - 변경 사항 미리보기 (최대 {limit}개)")
        print('='*80)

        for row_id, description in rows:
            cleaned = self.clean_description(description)

            print(f"\n🆔 ID: {row_id}")
            print(f"\n[BEFORE] ({len(description)} chars)")
            print('-'*80)
            print(description[:300] + ('...' if len(description) > 300 else ''))
            print(f"\n[AFTER] ({len(cleaned)} chars)")
            print('-'*80)
            print(cleaned[:300] + ('...' if len(cleaned) > 300 else ''))
            print('='*80)

    def clean_table(self, table: str, dry_run: bool = False) -> Tuple[int, int]:
        """테이블의 모든 description 정리"""
        # 정리가 필요한 항목 찾기
        query = f"""
            SELECT id, description
            FROM {table}
            WHERE description IS NOT NULL
            AND description != ''
            AND (
                description LIKE '%<%'
                OR description LIKE '%__%'
                OR description LIKE '%**%'
                OR description LIKE '%~~%'
            )
        """

        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        total = len(rows)

        if total == 0:
            print(f"✅ {table}: 정리가 필요한 항목이 없습니다!")
            return 0, 0

        print(f"\n{'='*80}")
        print(f"🧹 {table.upper()} - {total}개 항목 정리 중...")
        print('='*80)

        updated_count = 0

        for i, (row_id, description) in enumerate(rows, 1):
            cleaned = self.clean_description(description)

            # 실제로 변경이 있었는지 확인
            if cleaned != description:
                if not dry_run:
                    # 데이터베이스 업데이트
                    update_query = f"""
                        UPDATE {table}
                        SET description = ?
                        WHERE id = ?
                    """
                    self.cursor.execute(update_query, (cleaned, row_id))

                updated_count += 1

            # 진행 상황 출력 (100개마다)
            if i % 100 == 0:
                print(f"  진행: {i}/{total} ({updated_count} 업데이트됨)")

        if not dry_run:
            self.conn.commit()

        print(f"\n✅ 완료: {updated_count}/{total} 업데이트됨")
        return total, updated_count


def main():
    """메인 실행 함수"""
    import argparse

    parser = argparse.ArgumentParser(description='Description HTML/Markdown 정리')
    parser.add_argument('--preview', action='store_true',
                        help='변경사항 미리보기만 표시')
    parser.add_argument('--preview-limit', type=int, default=5,
                        help='미리보기 항목 개수 (기본: 5)')
    parser.add_argument('--table', choices=['anime', 'character', 'both'], default='both',
                        help='정리할 테이블 (기본: both)')
    parser.add_argument('--db', default='anime.db',
                        help='데이터베이스 파일 경로 (기본: anime.db)')

    args = parser.parse_args()

    print("=" * 80)
    print("🧹 Description Cleaner")
    print("=" * 80)

    cleaner = DescriptionCleaner(args.db)

    try:
        if args.preview:
            # 미리보기 모드
            if args.table in ['anime', 'both']:
                cleaner.preview_changes('anime', args.preview_limit)

            if args.table in ['character', 'both']:
                cleaner.preview_changes('character', args.preview_limit)
        else:
            # 실제 정리 모드
            total_processed = 0
            total_updated = 0

            if args.table in ['anime', 'both']:
                processed, updated = cleaner.clean_table('anime')
                total_processed += processed
                total_updated += updated

            if args.table in ['character', 'both']:
                processed, updated = cleaner.clean_table('character')
                total_processed += processed
                total_updated += updated

            print(f"\n{'='*80}")
            print(f"📊 전체 결과")
            print('='*80)
            print(f"  처리: {total_processed}개")
            print(f"  업데이트: {total_updated}개")
            print('='*80)

    finally:
        cleaner.close()

    print("\n✅ 작업 완료!")


if __name__ == '__main__':
    main()
