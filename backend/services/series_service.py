"""
Series Service
시리즈 관계 조회 및 처리
"""
from typing import List, Dict
from database import db, dict_from_row


def get_sequel_series(anime_id: int) -> List[Dict]:
    """
    현재 애니메이션의 후속작들 조회 (재귀적으로)
    2기 -> 3기 -> 4기 식으로 모든 후속작을 찾음
    """
    sequels = []

    def find_sequels(current_id: int):
        # 현재 애니메이션의 직접적인 후속작 찾기
        rows = db.execute_query(
            """
            SELECT
                a.id,
                a.title_romaji,
                a.title_english,
                a.title_korean,
                a.title_korean_official,
                COALESCE('/' || a.cover_image_local, a.cover_image_url) as cover_image_url
            FROM anime_relation ar
            JOIN anime a ON ar.related_anime_id = a.id
            WHERE ar.anime_id = ? AND ar.relation_type = 'SEQUEL'
            ORDER BY a.season_year ASC, a.season ASC
            """,
            (current_id,)
        )

        for row in rows:
            sequel_dict = dict_from_row(row)
            sequels.append(sequel_dict)
            # 재귀적으로 그 다음 후속작 찾기
            find_sequels(sequel_dict['id'])

    find_sequels(anime_id)
    return sequels


def get_series_info(anime_id: int) -> Dict:
    """
    시리즈 정보 조회 (현재 작품 + 모든 후속작)
    """
    # 현재 애니메이션 정보
    current = db.execute_query(
        """
        SELECT
            id,
            title_romaji,
            title_english,
            title_korean,
            title_korean_official,
            COALESCE('/' || cover_image_local, cover_image_url) as cover_image_url
        FROM anime
        WHERE id = ?
        """,
        (anime_id,),
        fetch_one=True
    )

    if not current:
        return None

    # 후속작들
    sequels = get_sequel_series(anime_id)

    return {
        'current': dict_from_row(current),
        'sequels': sequels,
        'total_sequels': len(sequels)
    }
