import api from './api';

export const feedService = {
  // Get global feed
  async getFeed(limit = 50, offset = 0, followingOnly = false) {
    const response = await api.get('/api/feed', {
      params: { limit, offset, following_only: followingOnly }
    });
    return response.data;
  },

  // Get user feed
  async getUserFeed(userId, limit = 50, offset = 0) {
    const response = await api.get(`/api/feed/user/${userId}`, {
      params: { limit, offset }
    });
    return response.data;
  },
};
