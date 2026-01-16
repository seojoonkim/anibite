/**
 * Rating Page Service - 초고속 평가 페이지 전용 API
 */
import api from './api';

export const ratingPageService = {
  /**
   * 리뷰 작성 페이지 - 초고속 로딩 (0.1초 목표)
   */
  async getItemsForReviews(limit = 50, offset = 0) {
    const response = await api.get('/api/rating-pages/write-reviews', {
      params: { limit, offset }
    });
    return response.data;
  },

  /**
   * 리뷰 작성 통계
   */
  async getReviewStats() {
    const response = await api.get('/api/rating-pages/write-reviews/stats');
    return response.data;
  }
};
