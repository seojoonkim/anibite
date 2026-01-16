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

  // Get all user's ratings (single status filter)
  async getMyRatings(params = {}) {
    const response = await api.get('/api/ratings/me', { params });
    return response.data;
  },

  // Get ALL user's ratings at once (RATED, WANT_TO_WATCH, PASS) - 3x faster!
  async getAllMyRatings(params = {}) {
    const response = await api.get('/api/ratings/me/all', { params });
    return response.data;
  },

  // Get ratings by specific rating value (for progressive loading)
  async getMyRatingsByRating(rating, status = 'RATED') {
    const response = await api.get('/api/ratings/me/all', {
      params: { rating, status }
    });
    return response.data;
  },

  // Get other user's ratings (public, single status filter)
  async getUserRatings(userId, params = {}) {
    const response = await api.get(`/api/ratings/user/${userId}`, { params });
    return response.data;
  },

  // Get ALL other user's ratings at once (RATED, WANT_TO_WATCH, PASS) - 3x faster!
  async getAllUserRatings(userId) {
    const response = await api.get(`/api/ratings/user/${userId}/all`);
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
