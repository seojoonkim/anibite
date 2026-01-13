import api from './api';

export const followService = {
  // Follow a user
  async followUser(userId) {
    const response = await api.post(`/api/follows/${userId}/follow`);
    return response.data;
  },

  // Unfollow a user
  async unfollowUser(userId) {
    const response = await api.delete(`/api/follows/${userId}/follow`);
    return response.data;
  },

  // Check if following
  async isFollowing(userId) {
    const response = await api.get(`/api/follows/${userId}/is-following`);
    return response.data;
  },

  // Get followers list
  async getFollowers(userId, params = {}) {
    const response = await api.get(`/api/follows/${userId}/followers`, { params });
    return response.data;
  },

  // Get following list
  async getFollowing(userId, params = {}) {
    const response = await api.get(`/api/follows/${userId}/following`, { params });
    return response.data;
  },

  // Get follow counts
  async getFollowCounts(userId) {
    const response = await api.get(`/api/follows/${userId}/follow-counts`);
    return response.data;
  }
};
