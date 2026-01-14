import api from './api';

export const feedService = {
  // Get global feed
  async getFeed(limit = 50, offset = 0, followingOnly = false) {
    const response = await api.get('/api/feed/', {
      params: { limit, offset, following_only: followingOnly }
    });
    return response.data;
  },

  // Get user feed - use global feed and filter
  async getUserFeed(userId, limit = 50, offset = 0) {
    // TEMP FIX: Use global feed endpoint which works, then filter by userId
    const response = await api.get('/api/feed/', {
      params: { limit: 500, offset: 0 }  // Get more to ensure enough after filtering
    });

    // Filter by userId
    const filtered = response.data.filter(activity => activity.user_id === userId);

    // Apply offset and limit after filtering
    return filtered.slice(offset, offset + limit);
  },
};
