"""
Feed API Router
활동 피드
"""
from fastapi import APIRouter, Query, Depends, HTTPException
from typing import List, Dict, Optional
from services.feed_service import get_global_feed, get_user_feed, get_following_feed
from models.user import UserResponse
from api.deps import get_current_user, get_current_user_optional
from database import get_db, Database

router = APIRouter()


def enrich_activities_with_engagement(activities: List[Dict], current_user_id: Optional[int], db: Database) -> List[Dict]:
    """
    각 활동에 좋아요 수, 댓글 수, 현재 사용자의 좋아요 여부를 추가
    주의: feed_service에서 이미 comments_count, user_has_liked를 계산했으므로 덮어쓰지 않음
    """
    for activity in activities:
        try:
            # get_user_feed에서 이미 likes_count, user_has_liked를 계산한 경우 건너뛰기
            if 'user_has_liked' in activity and 'likes_count' in activity:
                # user_liked도 설정 (호환성을 위해)
                activity['user_liked'] = activity['user_has_liked']
                continue

            activity_type = activity['activity_type']
            item_id = activity['item_id']
            user_id = activity['user_id']

            # 로그인하지 않은 경우 user_liked는 항상 False
            if current_user_id is None:
                activity['user_liked'] = False
                activity['user_has_liked'] = False
                activity['likes_count'] = 0  # 로그인 없으면 간단하게 0으로
                continue

            # 애니메이션 평가/리뷰는 review_likes/review_comments 사용
            if activity_type in ['anime_rating', 'anime_review']:
                # 리뷰 ID 조회
                review = db.execute_query(
                    "SELECT id, likes_count FROM user_reviews WHERE user_id = ? AND anime_id = ?",
                    (user_id, item_id),
                    fetch_one=True
                )

                if review:
                    review_id = review['id']
                    # 리뷰 테이블의 likes_count 사용
                    activity['likes_count'] = review['likes_count'] or 0

                    # 현재 사용자가 좋아요를 눌렀는지 (로그인한 경우만)
                    if current_user_id is not None:
                        user_liked_result = db.execute_query(
                            "SELECT COUNT(*) FROM review_likes WHERE review_id = ? AND user_id = ?",
                            (review_id, current_user_id),
                            fetch_one=True
                        )
                        activity['user_liked'] = (user_liked_result[0] > 0) if user_liked_result else False
                        activity['user_has_liked'] = activity['user_liked']

                    # comments_count는 feed_service에서 이미 계산했으므로 덮어쓰지 않음
                    # (feed_service가 review_id 유무에 따라 올바른 테이블에서 조회)
                else:
                    # 리뷰가 없는 경우, activity_likes 테이블 확인
                    likes_count_result = db.execute_query(
                        "SELECT COUNT(*) FROM activity_likes WHERE activity_type = ? AND activity_user_id = ? AND item_id = ?",
                        (activity_type, user_id, item_id),
                        fetch_one=True
                    )
                    activity['likes_count'] = likes_count_result[0] if likes_count_result else 0

                    if current_user_id is not None:
                        user_liked_result = db.execute_query(
                            "SELECT COUNT(*) FROM activity_likes WHERE activity_type = ? AND activity_user_id = ? AND item_id = ? AND user_id = ?",
                            (activity_type, user_id, item_id, current_user_id),
                            fetch_one=True
                        )
                        activity['user_liked'] = (user_liked_result[0] > 0) if user_liked_result else False
                        activity['user_has_liked'] = activity['user_liked']
                    # comments_count는 feed_service에서 이미 계산했으므로 덮어쓰지 않음

            # 캐릭터 평가/리뷰는 character_reviews/character_review_likes 사용
            elif activity_type in ['character_rating', 'character_review']:
                # 캐릭터 리뷰 ID 조회
                character_review = db.execute_query(
                    "SELECT id, likes_count FROM character_reviews WHERE user_id = ? AND character_id = ?",
                    (user_id, item_id),
                    fetch_one=True
                )

                if character_review:
                    review_id = character_review['id']
                    # 캐릭터 리뷰 테이블의 likes_count 사용
                    activity['likes_count'] = character_review['likes_count'] or 0

                    # 현재 사용자가 좋아요를 눌렀는지 (로그인한 경우만)
                    if current_user_id is not None:
                        user_liked_result = db.execute_query(
                            "SELECT COUNT(*) FROM character_review_likes WHERE review_id = ? AND user_id = ?",
                            (review_id, current_user_id),
                            fetch_one=True
                        )
                        activity['user_liked'] = (user_liked_result[0] > 0) if user_liked_result else False
                        activity['user_has_liked'] = activity['user_liked']

                    # comments_count는 feed_service에서 이미 계산했으므로 덮어쓰지 않음
                    # (feed_service가 review_id 유무에 따라 올바른 테이블에서 조회)
                else:
                    # 리뷰가 없는 경우, activity_likes 테이블 확인
                    likes_count_result = db.execute_query(
                        "SELECT COUNT(*) FROM activity_likes WHERE activity_type = ? AND activity_user_id = ? AND item_id = ?",
                        (activity_type, user_id, item_id),
                        fetch_one=True
                    )
                    activity['likes_count'] = likes_count_result[0] if likes_count_result else 0

                    if current_user_id is not None:
                        user_liked_result = db.execute_query(
                            "SELECT COUNT(*) FROM activity_likes WHERE activity_type = ? AND activity_user_id = ? AND item_id = ? AND user_id = ?",
                            (activity_type, user_id, item_id, current_user_id),
                            fetch_one=True
                        )
                        activity['user_liked'] = (user_liked_result[0] > 0) if user_liked_result else False
                        activity['user_has_liked'] = activity['user_liked']
                    # comments_count는 feed_service에서 이미 계산했으므로 덮어쓰지 않음

            else:
                # 기존 activity_likes/activity_comments 사용 (user_post 등)
                likes_count_result = db.execute_query(
                    "SELECT COUNT(*) FROM activity_likes WHERE activity_type = ? AND activity_user_id = ? AND item_id = ?",
                    (activity_type, user_id, item_id),
                    fetch_one=True
                )
                activity['likes_count'] = likes_count_result[0] if likes_count_result else 0

                if current_user_id is not None:
                    user_liked_result = db.execute_query(
                        "SELECT COUNT(*) FROM activity_likes WHERE activity_type = ? AND activity_user_id = ? AND item_id = ? AND user_id = ?",
                        (activity_type, user_id, item_id, current_user_id),
                        fetch_one=True
                    )
                    activity['user_liked'] = (user_liked_result[0] > 0) if user_liked_result else False
                    activity['user_has_liked'] = activity['user_liked']

                # comments_count는 feed_service에서 이미 계산했으므로 덮어쓰지 않음

        except Exception as e:
            # Engagement enrichment 실패 시 기본값 설정
            print(f"[WARNING] Failed to enrich activity {activity.get('activity_type')} for user {activity.get('user_id')}: {e}")
            activity.setdefault('likes_count', 0)
            activity.setdefault('user_liked', False)
            activity.setdefault('user_has_liked', False)

    return activities


@router.get("/", response_model=List[Dict])
def get_feed(
    following_only: bool = Query(False),
    user_id: Optional[int] = Query(None, description="Filter by specific user"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: UserResponse = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    활동 피드

    following_only=true: 팔로잉하는 사용자들의 활동만
    user_id=X: 특정 사용자의 활동만
    기본: 모든 사용자의 활동
    """
    try:
        print(f"[DEBUG] get_feed called: user_id={user_id}, following_only={following_only}, limit={limit}, offset={offset}, current_user={current_user.id}")

        # 특정 사용자 피드
        if user_id is not None:
            print(f"[DEBUG] Calling get_user_feed({user_id}, {current_user.id}, {limit}, {offset})")
            activities = get_user_feed(user_id, current_user.id, limit, offset)
            print(f"[DEBUG] get_user_feed returned {len(activities)} activities")
        # 팔로잉 피드
        elif following_only:
            print(f"[DEBUG] Calling get_following_feed")
            activities = get_following_feed(current_user.id, limit, offset)
        # 전체 피드
        else:
            print(f"[DEBUG] Calling get_global_feed")
            activities = get_global_feed(limit, offset)

        print(f"[DEBUG] Calling enrich_activities_with_engagement with {len(activities)} activities")
        enriched = enrich_activities_with_engagement(activities, current_user.id, db)
        print(f"[DEBUG] Returning {len(enriched)} enriched activities")
        return enriched
    except Exception as e:
        print(f"[ERROR] get_feed failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise


@router.get("/user/{user_id}", response_model=List[Dict])
def get_user_activity_feed(
    user_id: int,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: UserResponse = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """
    특정 사용자의 활동 피드
    Direct query from activities table for efficiency
    """
    from database import dict_from_row
    from services.feed_service import _enrich_comments_count

    # Direct query from activities table with user_id filter
    rows = db.execute_query(
        """
        SELECT
            activity_type,
            user_id,
            username,
            display_name,
            avatar_url,
            otaku_score,
            item_id,
            item_title,
            item_title_korean,
            item_image,
            rating,
            NULL as status,
            activity_time,
            anime_title,
            anime_title_korean,
            anime_id,
            CASE
                WHEN activity_type = 'user_post' THEN item_id
                ELSE NULL
            END as review_id,
            review_content,
            review_content as post_content,
            0 as comments_count
        FROM activities
        WHERE user_id = ?
        ORDER BY activity_time DESC
        LIMIT ? OFFSET ?
        """,
        (user_id, limit, offset)
    )

    activities = [dict_from_row(row) for row in rows]

    # Enrich with comments count
    _enrich_comments_count(activities)

    # Enrich with likes and user engagement
    return enrich_activities_with_engagement(activities, current_user.id, db)
