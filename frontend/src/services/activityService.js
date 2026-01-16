/**
 * Activity Service - Unified API client for all user activities
 *
 * Handles: anime ratings/reviews, character ratings/reviews, user posts
 */
import api from './api';

export const activityService = {
  /**
   * Get activities with flexible filtering
   *
   * @param {Object} filters
   * @param {string} filters.activityType - 'anime_rating', 'character_rating', 'user_post'
   * @param {number} filters.userId - Filter by user
   * @param {number} filters.itemId - Filter by item (anime_id or character_id)
   * @param {boolean} filters.followingOnly - Show only followed users
   * @param {number} filters.limit - Results per page
   * @param {number} filters.offset - Pagination offset
   */
  async getActivities({
    activityType = null,
    userId = null,
    itemId = null,
    followingOnly = false,
    limit = 50,
    offset = 0
  } = {}) {
    const params = new URLSearchParams();

    if (activityType) params.append('activity_type', activityType);
    if (userId) params.append('user_id', userId);
    if (itemId) params.append('item_id', itemId);
    if (followingOnly) params.append('following_only', 'true');
    params.append('limit', limit);
    params.append('offset', offset);

    console.log('[activityService] Fetching activities:', {
      activityType,
      userId,
      itemId,
      followingOnly,
      limit,
      offset,
      url: `/api/activities?${params}`
    });

    const response = await api.get(`/api/activities?${params}`);

    console.log('[activityService] Received activities:', {
      count: response.data.items?.length || 0,
      total: response.data.total,
      firstItem: response.data.items?.[0] ? {
        id: response.data.items[0].id,
        username: response.data.items[0].username,
        type: response.data.items[0].activity_type
      } : null
    });

    return response.data;
  },

  /**
   * Get a single activity by ID
   */
  async getActivity(activityId) {
    const response = await api.get(`/api/activities/${activityId}`);
    return response.data;
  },

  /**
   * Create a new activity (mainly for user posts)
   */
  async createActivity(activityData) {
    const response = await api.post('/api/activities', activityData);
    return response.data;
  },

  /**
   * Update activity review content
   */
  async updateActivity(activityId, activityData) {
    const response = await api.put(`/api/activities/${activityId}`, activityData);
    return response.data;
  },

  /**
   * Delete an activity
   */
  async deleteActivity(activityId) {
    await api.delete(`/api/activities/${activityId}`);
  },

  /**
   * Toggle like on an activity
   * Returns: { liked: boolean, likes_count: number }
   */
  async toggleLike(activityId) {
    const response = await api.post(`/api/activities/${activityId}/like`);
    return response.data;
  },

  /**
   * Get comments for an activity
   */
  async getComments(activityId) {
    const response = await api.get(`/api/activities/${activityId}/comments`);
    return response.data;
  },

  /**
   * Create a comment on an activity
   */
  async createComment(activityId, content, parentCommentId = null) {
    const response = await api.post(`/api/activities/${activityId}/comments`, {
      content,
      parent_comment_id: parentCommentId
    });
    return response.data;
  },

  /**
   * Delete a comment
   */
  async deleteComment(commentId) {
    await api.delete(`/api/activities/comments/${commentId}`);
  },

  // ============================================================================
  // LEGACY COMPATIBILITY METHODS
  // These methods provide compatibility with existing code during migration
  // ============================================================================

  /**
   * Get anime activities for a specific anime
   * Legacy compatibility for AnimeDetail page
   */
  async getAnimeActivities(animeId, limit = 50, offset = 0) {
    return this.getActivities({
      activityType: 'anime_rating',
      itemId: animeId,
      limit,
      offset
    });
  },

  /**
   * Get character activities for a specific character
   * Legacy compatibility for CharacterDetail page
   */
  async getCharacterActivities(characterId, limit = 50, offset = 0) {
    return this.getActivities({
      activityType: 'character_rating',
      itemId: characterId,
      limit,
      offset
    });
  },

  /**
   * Get user's activities
   * Legacy compatibility for profile pages
   */
  async getUserActivities(userId, activityType = null, limit = 50, offset = 0) {
    return this.getActivities({
      activityType,
      userId,
      limit,
      offset
    });
  },

  /**
   * Get feed (following + popular)
   * Legacy compatibility for Feed page
   */
  async getFeed(followingOnly = false, limit = 50, offset = 0) {
    return this.getActivities({
      followingOnly,
      limit,
      offset
    });
  }
};

export default activityService;
