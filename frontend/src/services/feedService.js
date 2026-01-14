import api from './api';

export const feedService = {
  // Get global feed
  async getFeed(limit = 50, offset = 0, followingOnly = false) {
    const response = await api.get('/api/feed/', {
      params: { limit, offset, following_only: followingOnly }
    });
    return response.data;
  },

  // Get user feed - Use working global feed with client filtering
  async getUserFeed(userId, limit = 50, offset = 0) {
    // /api/feed/ works, /api/feed/user/:id has persistent 500 error
    // Fetch from global feed and filter client-side
    const fetchLimit = Math.min(100, offset + limit * 2);
    const response = await api.get('/api/feed/', {
      params: { limit: fetchLimit, offset: 0 }
    });

    // Filter by user_id
    const filtered = response.data.filter(activity => activity.user_id === userId);

    // Apply offset and limit
    return filtered.slice(offset, offset + limit);
  },
};
