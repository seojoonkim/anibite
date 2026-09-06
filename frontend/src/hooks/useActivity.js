/**
 * React hooks for activity management
 */
import { useState, useEffect, useCallback } from 'react';
import { usePagedResource } from './usePagedResource';
import { activityService } from '../services/activityService';

/**
 * Hook to fetch activities with automatic refetching
 *
 * @param {Object} filters - Activity filters
 * @param {Object} options - Hook options
 * @param {boolean} options.autoFetch - Auto-fetch on mount (default: true)
 * @param {number} options.refetchInterval - Auto-refetch interval in ms (default: null)
 */
export function useActivities(filters = {}, options = {}) {
  const { autoFetch = true, refetchInterval = null } = options;
  const key = JSON.stringify(filters);
  const loadPage = useCallback(async (_page, signal) => {
    const data = await activityService.getActivities(JSON.parse(key), { signal });
    return { items: data.items || [], total: data.total, hasMore: false };
  }, [key]);
  const resource = usePagedResource(loadPage, false, { autoFetch });
  const refetch = resource.reset;
  useEffect(() => {
    if (refetchInterval > 0) { const timer = setInterval(refetch, refetchInterval); return () => clearInterval(timer); }
  }, [refetchInterval, refetch]);
  return { activities: resource.items, total: resource.total, loading: resource.loading, error: resource.error, refetch };
}


/**
 * Hook to manage a single activity
 */
export function useActivity(activityId) {
  const [activity, setActivity] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchActivity = useCallback(async () => {
    if (!activityId) return;

    setLoading(true);
    setError(null);

    try {
      const data = await activityService.getActivity(activityId);
      setActivity(data);
    } catch (err) {
      console.error('Failed to fetch activity:', err);
      setError(err.message || 'Failed to load activity');
    } finally {
      setLoading(false);
    }
  }, [activityId]);

  useEffect(() => {
    fetchActivity();
  }, [fetchActivity]);

  return {
    activity,
    loading,
    error,
    refetch: fetchActivity
  };
}

/**
 * Hook to manage activity likes
 */
export function useActivityLike(activityId, initialLiked = false, initialCount = 0) {
  const [liked, setLiked] = useState(initialLiked);
  const [likesCount, setLikesCount] = useState(initialCount);
  const [loading, setLoading] = useState(false);

  // Update state when props change (e.g., after parent refetch)
  useEffect(() => {
    setLiked(initialLiked);
    setLikesCount(initialCount);
  }, [initialLiked, initialCount]);

  const toggleLike = async () => {
    if (loading) return;

    setLoading(true);

    // Optimistic update
    const prevLiked = liked;
    const prevCount = likesCount;
    setLiked(!liked);
    setLikesCount(liked ? likesCount - 1 : likesCount + 1);

    try {
      const result = await activityService.toggleLike(activityId);
      console.log('Like API response:', result); // Debug log
      setLiked(result.liked);
      setLikesCount(result.likes_count);
    } catch (err) {
      console.error('Failed to toggle like:', err);
      alert('좋아요 처리에 실패했습니다. 다시 시도해주세요.');
      // Revert on error
      setLiked(prevLiked);
      setLikesCount(prevCount);
    } finally {
      setLoading(false);
    }
  };

  return {
    liked,
    likesCount,
    loading,
    toggleLike
  };
}

/**
 * Hook to manage activity comments
 */
export function useActivityComments(activityId) {
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchComments = useCallback(async () => {
    if (!activityId) return;

    setLoading(true);
    setError(null);

    try {
      const data = await activityService.getComments(activityId);
      setComments(data);
    } catch (err) {
      console.error('Failed to fetch comments:', err);
      setError(err.message || 'Failed to load comments');
    } finally {
      setLoading(false);
    }
  }, [activityId]);

  const createComment = async (content, parentCommentId = null) => {
    try {
      const newComment = await activityService.createComment(activityId, content, parentCommentId);

      if (parentCommentId) {
        // Add reply to parent comment
        setComments(prevComments =>
          prevComments.map(comment => {
            if (comment.id === parentCommentId) {
              return {
                ...comment,
                replies: [...(comment.replies || []), newComment]
              };
            }
            return comment;
          })
        );
      } else {
        // Add top-level comment
        setComments(prevComments => [...prevComments, { ...newComment, replies: [] }]);
      }

      return newComment;
    } catch (err) {
      console.error('Failed to create comment:', err);
      throw err;
    }
  };

  const deleteComment = async (commentId, parentCommentId = null) => {
    try {
      await activityService.deleteComment(commentId);

      if (parentCommentId) {
        // Remove reply from parent comment
        setComments(prevComments =>
          prevComments.map(comment => {
            if (comment.id === parentCommentId) {
              return {
                ...comment,
                replies: (comment.replies || []).filter(reply => reply.id !== commentId)
              };
            }
            return comment;
          })
        );
      } else {
        // Remove top-level comment
        setComments(prevComments => prevComments.filter(comment => comment.id !== commentId));
      }
    } catch (err) {
      console.error('Failed to delete comment:', err);
      throw err;
    }
  };

  useEffect(() => {
    fetchComments();
  }, [fetchComments]);

  return {
    comments,
    loading,
    error,
    refetch: fetchComments,
    createComment,
    deleteComment
  };
}

/**
 * Hook for pagination - 단순하고 빠르게
 */
export function useActivityPagination(filters = {}, pageSize = 50, skip = false) {
  const key = JSON.stringify(filters);
  const loadPage = useCallback(async (page, signal) => {
    const data = await activityService.getActivities({ ...JSON.parse(key), limit: pageSize, offset: (page - 1) * pageSize }, { signal });
    return { items: data.items || [], total: data.total, hasMore: data.has_more ?? (typeof data.total === 'number' ? page * pageSize < data.total : data.items.length === pageSize) };
  }, [key, pageSize]);
  const resource = usePagedResource(loadPage, skip);
  return { ...resource, activities: resource.items, removeActivity: resource.remove };
}
