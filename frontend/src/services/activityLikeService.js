import api from './api';

export const activityLikeService = {
  // Toggle like on activity
  async toggleLike(activityType, activityUserId, itemId) {
    const response = await api.post('/api/activity-likes/', {
      activity_type: activityType,
      activity_user_id: activityUserId,
      item_id: itemId
    });
    return response.data;
  },

  // Check if activity is liked
  async checkLike(activityType, activityUserId, itemId) {
    const response = await api.get('/api/activity-likes/check', {
      params: {
        activity_type: activityType,
        activity_user_id: activityUserId,
        item_id: itemId
      }
    });
    return response.data;
  },

  // Get list of users who liked the activity
  async getLikes(activityType, activityUserId, itemId) {
    const response = await api.get('/api/activity-likes/list', {
      params: {
        activity_type: activityType,
        activity_user_id: activityUserId,
        item_id: itemId
      }
    });
    return response.data;
  }
};
