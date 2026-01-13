import api from './api';

export const reviewLikeService = {
  // Like a review
  async likeReview(reviewId) {
    const response = await api.post(`/api/reviews/${reviewId}/like`);
    return response.data;
  },

  // Unlike a review
  async unlikeReview(reviewId) {
    const response = await api.delete(`/api/reviews/${reviewId}/like`);
    return response.data;
  },
};
