/**
 * Activity Utils - 통합 평점/리뷰 시스템 유틸리티
 * 애니, 캐릭터, 피드 모든 페이지에서 동일하게 작동
 */

import { activityCommentService } from '../services/activityCommentService';
import { activityService } from '../services/activityService';
import { reviewCommentService } from '../services/reviewCommentService';
import { reviewService } from '../services/reviewService';
import { characterReviewService } from '../services/characterReviewService';
import { commentLikeService } from '../services/commentLikeService';

/**
 * Activity 타입 결정
 * @param {Object} item - 평점/리뷰 아이템
 * @returns {string} - 'anime_rating' | 'anime_review' | 'character_rating' | 'character_review'
 */
export function getActivityType(item) {
  // Feed에서 이미 activity_type이 있으면 그대로 사용
  if (item.activity_type) {
    return item.activity_type;
  }

  // 캐릭터인지 애니인지 확인 (피드는 item_id, 상세 페이지는 character_id/anime_id 사용)
  const isCharacter = item.character_id !== undefined || item.characterId !== undefined;

  // Feed에서는 review_content, CharacterDetail에서는 content
  const content = item.review_content || item.content;
  const reviewId = item.review_id;

  // 리뷰가 있는지 확인 (content가 있거나 review_id가 있으면 리뷰)
  const hasReview = (content && content.length > 0) || (reviewId && reviewId > 0);

  const activityType = isCharacter
    ? (hasReview ? 'character_review' : 'character_rating')
    : (hasReview ? 'anime_review' : 'anime_rating');

  console.log('[ActivityUtils] getActivityType:', {
    activity_type: item.activity_type,
    isCharacter,
    hasReview,
    result: activityType,
    item_fields: {
      character_id: item.character_id,
      characterId: item.characterId,
      anime_id: item.anime_id,
      animeId: item.animeId,
      item_id: item.item_id
    }
  });

  return activityType;
}

/**
 * Activity Key 생성
 * @param {Object} item - 평점/리뷰 아이템
 * @returns {string} - 'activity_type_userId_itemId'
 */
export function getActivityKey(item) {
  const activityType = getActivityType(item);
  const userId = item.user_id || item.userId;
  // Feed에서는 item_id, 상세 페이지에서는 character_id/anime_id 사용
  const itemId = item.item_id || item.character_id || item.characterId || item.anime_id || item.animeId;

  return `${activityType}_${userId}_${itemId}`;
}

/**
 * 평점만 있는지 확인 (리뷰 없음)
 * @param {Object} item - 평점/리뷰 아이템
 * @returns {boolean}
 */
export function isRatingsOnly(item) {
  if (!item) {
    console.log('[ActivityUtils] isRatingsOnly: item is null/undefined');
    return false;
  }

  // review_id 필드를 먼저 체크 (피드와 캐릭터 페이지 모두에서 사용)
  const reviewId = item.review_id;

  // review_id가 명시적으로 있고 양수면 리뷰가 있는 것
  if (reviewId && reviewId > 0) {
    console.log('[ActivityUtils] isRatingsOnly: false (has review_id)', reviewId);
    return false;
  }

  // review_id가 없거나 음수이면, id 필드 체크 (캐릭터 페이지용)
  const id = item.id;
  if (id && id > 0) {
    console.log('[ActivityUtils] isRatingsOnly: false (has positive id)', id);
    return false;
  }

  // 둘 다 없으면 평점만 있는 것
  console.log('[ActivityUtils] isRatingsOnly: true (ratings only)', { review_id: reviewId, id: id });
  return true;
}

/**
 * 댓글 로드 - review_comments에서 로드 (통합됨)
 * @param {Object} item - 평점/리뷰 아이템
 * @returns {Promise<Object>} - { items: [], total: 0 }
 */
export async function loadComments(item) {
  console.log('[ActivityUtils] loadComments CALLED with item:', {
    activity_type: item.activity_type,
    user_id: item.user_id,
    item_id: item.item_id,
    review_id: item.review_id,
    character_id: item.character_id,
    anime_id: item.anime_id,
    item_title: item.item_title
  });

  const activityType = getActivityType(item);
  // review_id 필드가 있으면 사용, 없으면 id 사용 (단, 양수인 경우만)
  const reviewId = item.review_id || (item.id > 0 ? item.id : null);
  const reviewType = activityType.includes('character') ? 'character' : 'anime';

  console.log('[ActivityUtils] loadComments COMPUTED:', {
    activityType,
    reviewId,
    reviewType,
    'activityType.includes(character)': activityType.includes('character')
  });

  // Helper function to convert flat comment list to nested structure
  const convertToNestedStructure = (comments) => {
    // Check if already nested
    const hasNestedReplies = comments.some(comment =>
      comment.replies && Array.isArray(comment.replies) && comment.replies.length > 0
    );

    if (hasNestedReplies) {
      console.log('[ActivityUtils] Comments already nested, using as-is');
      return comments;
    }

    console.log('[ActivityUtils] Converting flat structure to nested');
    const commentsMap = new Map();
    const topLevelComments = [];

    // First, create a map of all comments with empty replies array
    comments.forEach(comment => {
      commentsMap.set(comment.id, { ...comment, replies: [] });
    });

    // Then, build parent-child relationships
    comments.forEach(comment => {
      const commentObj = commentsMap.get(comment.id);
      if (comment.parent_comment_id) {
        // This is a reply, add to parent's replies
        const parent = commentsMap.get(comment.parent_comment_id);
        if (parent) {
          parent.replies.push(commentObj);
        } else {
          // Parent not found, treat as top-level comment
          topLevelComments.push(commentObj);
        }
      } else {
        // This is a top-level comment
        topLevelComments.push(commentObj);
      }
    });

    return topLevelComments;
  };

  // review_id가 있으면 review_comments에서 로드
  if (reviewId && reviewId > 0) {
    console.log('[ActivityUtils] loadComments: calling reviewCommentService with', { reviewId, reviewType });
    try {
      const result = await reviewCommentService.getReviewComments(reviewId, reviewType);
      console.log('[ActivityUtils] loadComments: reviewCommentService SUCCESS, got', result.items?.length || 0, 'comments');

      // Convert flat structure to nested structure
      const nestedComments = convertToNestedStructure(result.items || []);
      console.log('[ActivityUtils] Nested structure:', nestedComments.map(c => ({
        id: c.id,
        replies: c.replies?.length || 0
      })));
      return { ...result, items: nestedComments };
    } catch (error) {
      console.error('[ActivityUtils] loadComments: reviewCommentService ERROR', error);
      // review_comments 실패 시 activity_comments로 폴백
    }
  }

  // review_id가 없거나 위에서 실패한 경우 activity_comments에서 로드
  console.log('[ActivityUtils] loadComments: calling activityCommentService with', {
    activityType,
    user_id: item.user_id,
    item_id: item.item_id
  });
  try {
    const result = await activityCommentService.getActivityComments(
      activityType,
      item.user_id,
      item.item_id
    );
    console.log('[ActivityUtils] loadComments: activityCommentService SUCCESS, got', result.items?.length || 0, 'comments');

    // Convert flat structure to nested structure
    const nestedComments = convertToNestedStructure(result.items || []);
    console.log('[ActivityUtils] Nested structure:', nestedComments.map(c => ({
      id: c.id,
      replies: c.replies?.length || 0
    })));
    return { ...result, items: nestedComments };
  } catch (error) {
    console.error('[ActivityUtils] loadComments: activityCommentService ERROR', error);
    return { items: [], total: 0 };
  }
}

/**
 * 댓글 작성 - 리뷰가 없으면 빈 리뷰 먼저 생성
 * @param {Object} item - 평점/리뷰 아이템
 * @param {string} content - 댓글 내용
 * @returns {Promise<Object>}
 */
export async function createComment(item, content) {
  const activityType = getActivityType(item);
  let reviewId = item.review_id || (item.id > 0 ? item.id : null);
  const reviewType = activityType.includes('character') ? 'character' : 'anime';
  const itemId = item.item_id || item.character_id || item.characterId || item.anime_id || item.animeId;

  console.log('[ActivityUtils] createComment:', {
    activityType,
    reviewId,
    reviewType,
    itemId,
    content: content.substring(0, 50)
  });

  // 리뷰가 없는 경우 (평점만 있음) - 빈 리뷰 먼저 생성
  if (!reviewId || reviewId <= 0) {
    console.log('[ActivityUtils] createComment: creating empty review first');

    try {
      // 빈 리뷰 생성
      if (reviewType === 'character') {
        const newReview = await characterReviewService.createReview({
          character_id: itemId,
          content: '',
          title: null,
          is_spoiler: false
        });
        reviewId = newReview.id;
      } else {
        const newReview = await reviewService.createReview({
          anime_id: itemId,
          content: '',
          title: null,
          is_spoiler: false
        });
        reviewId = newReview.id;
      }
      console.log('[ActivityUtils] createComment: empty review created', reviewId);
    } catch (error) {
      console.error('[ActivityUtils] createComment: failed to create empty review', error);
      throw error;
    }
  }

  // review_comments에 댓글 추가
  console.log('[ActivityUtils] createComment: using review_comments', { reviewId, reviewType });
  return await reviewCommentService.createComment({
    review_id: reviewId,
    review_type: reviewType,
    content: content
  });
}

/**
 * 답글 작성
 * @param {Object} item - 평점/리뷰 아이템
 * @param {number} parentCommentId - 부모 댓글 ID
 * @param {string} content - 답글 내용
 * @returns {Promise<Object>}
 */
export async function createReply(item, parentCommentId, content) {
  const activityType = getActivityType(item);
  const reviewId = item.review_id || (item.id > 0 ? item.id : null);
  const reviewType = activityType.includes('character') ? 'character' : 'anime';

  // review_comments 사용 (통합됨)
  return await reviewCommentService.createReply(parentCommentId, {
    review_id: reviewId,
    review_type: reviewType,
    content: content
  });
}

/**
 * 댓글 삭제
 * @param {Object} item - 평점/리뷰 아이템
 * @param {number} commentId - 댓글 ID
 * @returns {Promise<void>}
 */
export async function deleteComment(item, commentId) {
  // review_comments 사용 (통합됨)
  const result = await reviewCommentService.deleteReviewComment(commentId);
  return result;
}

/**
 * 좋아요 토글 (평점/리뷰에 대한 좋아요)
 * @param {Object} item - 평점/리뷰 아이템 (activity_id가 포함된 객체)
 * @returns {Promise<Object>} - { liked: boolean, likes_count: number }
 */
export async function toggleLike(item) {
  if (!item.id) {
    throw new Error('Activity ID is required for toggling like');
  }
  return await activityService.toggleLike(item.id);
}

/**
 * 댓글 좋아요 토글
 * @param {number} commentId - 댓글 ID
 * @returns {Promise<void>}
 */
export async function toggleCommentLike(commentId) {

  // 댓글 좋아요는 모든 경우에 동일하게 commentLikeService 사용
  return await commentLikeService.toggleLike(commentId);
}

/**
 * 아이템 ID 추출
 * @param {Object} item - 평점/리뷰 아이템
 * @returns {number}
 */
export function getItemId(item) {
  return item.item_id || item.character_id || item.characterId || item.anime_id || item.animeId;
}

/**
 * 사용자 ID 추출
 * @param {Object} item - 평점/리뷰 아이템
 * @returns {number}
 */
export function getUserId(item) {
  return item.user_id || item.userId;
}
