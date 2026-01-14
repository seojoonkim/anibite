import api from './api';

export const feedService = {
  // Get global feed
  async getFeed(limit = 50, offset = 0, followingOnly = false) {
    const response = await api.get('/api/feed/', {
      params: { limit, offset, following_only: followingOnly }
    });
    return response.data;
  },

  // Get user feed - WORKING FIX: filter from global feed
  async getUserFeed(userId, limit = 50, offset = 0) {
    // Use global feed which works, then filter
    // Request enough to cover offset + limit after filtering
    const response = await api.get('/api/feed/', {
      params: { limit: Math.min(200, offset + limit * 3), offset: 0 }
    });

    // Filter by userId
    const filtered = response.data.filter(activity => activity.user_id === userId);

    // Apply pagination after filtering
    return filtered.slice(offset, offset + limit);
  },
};
