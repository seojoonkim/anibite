import api from './api';

export const ratingService = {
  // Create or update rating
  async rateAnime(animeId, ratingData) {
    const response = await api.post('/api/ratings/', {
      anime_id: animeId,
      ...ratingData,
    });
    return response.data;
  },

  // Get user's rating for an anime
  async getUserRating(animeId) {
    try {
      const response = await api.get(`/api/ratings/anime/${animeId}`);
      return response.data;
    } catch (error) {
      if (error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  },

  // Get all user's ratings
  async getMyRatings(params = {}) {
    const response = await api.get('/api/ratings/me', { params });
    return response.data;
  },

  // Get other user's ratings (public)
  async getUserRatings(userId, params = {}) {
    const response = await api.get(`/api/ratings/user/${userId}`, { params });
    return response.data;
  },

  // Delete rating
  async deleteRating(animeId) {
    const response = await api.delete(`/api/ratings/anime/${animeId}`);
    return response.data;
  },

  // Get ratings for an anime
  async getAnimeRatings(animeId, params = {}) {
    const response = await api.get(`/api/ratings/anime/${animeId}`, { params });
    return response.data;
  },
};
