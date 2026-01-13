import api from './api';

export const reviewService = {
  // Create review
  async createReview(reviewData) {
    const response = await api.post('/api/reviews/', reviewData);
    return response.data;
  },

  // Get reviews for an anime
  async getAnimeReviews(animeId, params = {}) {
    const response = await api.get(`/api/reviews/anime/${animeId}`, { params });
    return response.data;
  },

  // Get user's review for an anime
  async getMyReview(animeId) {
    try {
      const response = await api.get(`/api/reviews/anime/${animeId}/my-review`);
      return response.data;
    } catch (error) {
      if (error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  },

  // Update review
  async updateReview(reviewId, reviewData) {
    const response = await api.put(`/api/reviews/${reviewId}`, reviewData);
    return response.data;
  },

  // Delete review
  async deleteReview(reviewId) {
    const response = await api.delete(`/api/reviews/${reviewId}`);
    return response.data;
  },

  // Like review
  async likeReview(reviewId) {
    const response = await api.post(`/api/reviews/${reviewId}/like`);
    return response.data;
  },

  // Unlike review
  async unlikeReview(reviewId) {
    const response = await api.delete(`/api/reviews/${reviewId}/like`);
    return response.data;
  },
};
