/**
 * React hooks for activity management
 */
import { useState, useEffect, useCallback } from 'react';
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

  const [activities, setActivities] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchActivities = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await activityService.getActivities(filters);
      setActivities(data.items);
      setTotal(data.total);
    } catch (err) {
      console.error('Failed to fetch activities:', err);
      setError(err.message || 'Failed to load activities');
    } finally {
      setLoading(false);
    }
  }, [JSON.stringify(filters)]);

  useEffect(() => {
    if (autoFetch) {
      fetchActivities();
    }
  }, [autoFetch, fetchActivities]);

  // Auto-refetch interval
  useEffect(() => {
    if (refetchInterval && refetchInterval > 0) {
      const intervalId = setInterval(fetchActivities, refetchInterval);
      return () => clearInterval(intervalId);
    }
  }, [refetchInterval, fetchActivities]);

  return {
    activities,
    total,
    loading,
    error,
    refetch: fetchActivities
  };
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
 * Hook for pagination
 */
export function useActivityPagination(filters = {}, pageSize = 50) {
  const [page, setPage] = useState(0);
  const [allActivities, setAllActivities] = useState([]);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(false);

  const loadMore = useCallback(async () => {
    if (loading || !hasMore) return;

    setLoading(true);

    try {
      const data = await activityService.getActivities({
        ...filters,
        limit: pageSize,
        offset: page * pageSize
      });

      setAllActivities(prev => [...prev, ...data.items]);
      setHasMore(data.items.length === pageSize);
      setPage(prev => prev + 1);
    } catch (err) {
      console.error('Failed to load more activities:', err);
    } finally {
      setLoading(false);
    }
  }, [filters, page, pageSize, loading, hasMore]);

  const reset = useCallback(() => {
    setPage(0);
    setAllActivities([]);
    setHasMore(true);
  }, []);

  useEffect(() => {
    reset();
  }, [JSON.stringify(filters)]);

  useEffect(() => {
    if (page === 0) {
      loadMore();
    } else if (page === 1) {
      // Auto-load second batch immediately after first batch
      setTimeout(() => {
        if (hasMore && !loading) {
          loadMore();
        }
      }, 100);
    }
  }, [page]);

  return {
    activities: allActivities,
    loading,
    hasMore,
    loadMore,
    reset
  };
}
