import api from './api';

export const feedService = {
  // Get global feed
  async getFeed(limit = 50, offset = 0, followingOnly = false) {
    const response = await api.get('/api/feed/', {
      params: { limit, offset, following_only: followingOnly }
    });
    return response.data;
  },

  // Get user feed - Use /api/feed/ with user_id parameter
  async getUserFeed(userId, limit = 50, offset = 0) {
    // Use working /api/feed/ endpoint with user_id query parameter
    const response = await api.get('/api/feed/', {
      params: { user_id: userId, limit, offset }
    });
    return response.data;
  },
};
