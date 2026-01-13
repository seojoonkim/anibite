"""
Activities API Router - Unified endpoint for all user activities
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from pydantic import BaseModel, Field
from models.user import UserResponse
from api.deps import get_current_user, get_optional_user
from services.activity_service import (
    get_activities,
    get_activity_by_id,
    create_activity,
    update_activity,
    delete_activity,
    like_activity,
    get_activity_comments,
    create_activity_comment
)

router = APIRouter()


class ActivityResponse(BaseModel):
    """Unified activity response"""
    id: int
    activity_type: str  # 'anime_rating', 'character_rating', 'user_post'

    # User info (denormalized)
    user_id: int
    username: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    otaku_score: int

    # Item info (denormalized)
    item_id: Optional[int]
    item_title: Optional[str]
    item_title_korean: Optional[str]
    item_image: Optional[str]

    # Rating & Review
    rating: Optional[float]
    review_title: Optional[str]
    review_content: Optional[str]
    is_spoiler: bool

    # Metadata (for characters)
    anime_id: Optional[int]
    anime_title: Optional[str]
    anime_title_korean: Optional[str]

    # Engagement
    likes_count: int = 0
    comments_count: int = 0
    user_liked: bool = False
    is_my_activity: bool = False

    # Timestamps
    activity_time: str
    created_at: str
    updated_at: str


class ActivityListResponse(BaseModel):
    """Paginated activity list"""
    items: List[ActivityResponse]
    total: int


class ActivityCreate(BaseModel):
    """Create activity (mainly for user_posts)"""
    activity_type: str
    item_id: Optional[int] = None
    rating: Optional[float] = Field(None, ge=0.5, le=5.0)
    review_title: Optional[str] = None
    review_content: Optional[str] = None
    is_spoiler: bool = False


class ActivityUpdate(BaseModel):
    """Update activity review content"""
    review_title: Optional[str] = None
    review_content: Optional[str] = None
    is_spoiler: Optional[bool] = None


class CommentCreate(BaseModel):
    """Create comment"""
    content: str
    parent_comment_id: Optional[int] = None


class CommentResponse(BaseModel):
    """Comment response"""
    id: int
    activity_id: int
    user_id: int
    username: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    otaku_score: int
    content: str
    parent_comment_id: Optional[int]
    replies: List['CommentResponse'] = []
    created_at: str


# Fix forward reference
CommentResponse.model_rebuild()


@router.get("/", response_model=ActivityListResponse)
def get_activities_endpoint(
    activity_type: Optional[str] = Query(None, description="Filter by type: anime_rating, character_rating, user_post"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    item_id: Optional[int] = Query(None, description="Filter by item ID (anime_id or character_id)"),
    following_only: bool = Query(False, description="Show only activities from followed users"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Optional[UserResponse] = Depends(get_optional_user)
):
    """
    Get activities with optional filtering

    - **activity_type**: Filter by activity type
    - **user_id**: Show activities from a specific user
    - **item_id**: Show activities about a specific anime/character
    - **following_only**: Show only activities from followed users (requires auth)
    - **limit**: Number of results per page
    - **offset**: Pagination offset
    """

    current_user_id = current_user.id if current_user else None

    result = get_activities(
        activity_type=activity_type,
        user_id=user_id,
        item_id=item_id,
        following_only=following_only,
        current_user_id=current_user_id,
        limit=limit,
        offset=offset
    )

    return ActivityListResponse(**result)


@router.get("/{activity_id}", response_model=ActivityResponse)
def get_activity_endpoint(
    activity_id: int,
    current_user: Optional[UserResponse] = Depends(get_optional_user)
):
    """Get a single activity by ID"""

    current_user_id = current_user.id if current_user else None
    activity = get_activity_by_id(activity_id, current_user_id)

    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )

    return ActivityResponse(**activity)


@router.post("/", response_model=ActivityResponse)
def create_activity_endpoint(
    activity_data: ActivityCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Create a new activity (mainly for user_posts)

    Note: Anime and character ratings/reviews should be created through their
    respective endpoints. Triggers will automatically sync to activities table.
    """

    try:
        activity = create_activity(
            activity_type=activity_data.activity_type,
            user_id=current_user.id,
            item_id=activity_data.item_id,
            rating=activity_data.rating,
            review_title=activity_data.review_title,
            review_content=activity_data.review_content,
            is_spoiler=activity_data.is_spoiler
        )
        return ActivityResponse(**activity)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{activity_id}", response_model=ActivityResponse)
def update_activity_endpoint(
    activity_id: int,
    activity_data: ActivityUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Update activity review content

    Note: To update ratings, use the rating endpoints. Triggers will sync changes.
    """

    activity = update_activity(
        activity_id=activity_id,
        user_id=current_user.id,
        review_title=activity_data.review_title,
        review_content=activity_data.review_content,
        is_spoiler=activity_data.is_spoiler
    )

    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found or not authorized"
        )

    return ActivityResponse(**activity)


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity_endpoint(
    activity_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Delete an activity

    Note: For anime/character activities, delete the source rating instead.
    This is mainly for user_posts.
    """

    success = delete_activity(activity_id, current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found or not authorized"
        )


@router.post("/{activity_id}/like", response_model=dict)
def like_activity_endpoint(
    activity_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Toggle like on an activity

    Returns: {"liked": true/false, "likes_count": number}
    """

    # Verify activity exists
    activity = get_activity_by_id(activity_id, current_user.id)
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )

    liked = like_activity(activity_id, current_user.id)

    # Get updated count
    updated_activity = get_activity_by_id(activity_id, current_user.id)

    return {
        "liked": liked,
        "likes_count": updated_activity['likes_count']
    }


@router.get("/{activity_id}/comments", response_model=List[CommentResponse])
def get_comments_endpoint(
    activity_id: int
):
    """Get comments for an activity"""

    # Verify activity exists
    activity = get_activity_by_id(activity_id)
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )

    comments = get_activity_comments(activity_id)
    return [CommentResponse(**comment) for comment in comments]


@router.post("/{activity_id}/comments", response_model=CommentResponse)
def create_comment_endpoint(
    activity_id: int,
    comment_data: CommentCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a comment on an activity"""

    try:
        comment = create_activity_comment(
            activity_id=activity_id,
            user_id=current_user.id,
            content=comment_data.content,
            parent_comment_id=comment_data.parent_comment_id
        )
        return CommentResponse(**comment)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
