import api from './api';

export const characterReviewService = {
  // 캐릭터 리뷰 목록 조회
  async getCharacterReviews(characterId, params = {}) {
    const { data } = await api.get(`/api/character-reviews/character/${characterId}`, { params });
    return data;
  },

  // 내 캐릭터 리뷰 조회
  async getMyReview(characterId) {
    const { data } = await api.get(`/api/character-reviews/character/${characterId}/my-review`);
    return data;
  },

  // 캐릭터 리뷰 작성
  async createReview(reviewData) {
    const { data } = await api.post('/api/character-reviews/', reviewData);
    return data;
  },

  // 캐릭터 리뷰 수정
  async updateReview(reviewId, reviewData) {
    const { data } = await api.put(`/api/character-reviews/${reviewId}`, reviewData);
    return data;
  },

  // 캐릭터 리뷰 삭제 (review ID로)
  async deleteReview(reviewId) {
    await api.delete(`/api/character-reviews/${reviewId}`);
  },

  // 내 캐릭터 리뷰 삭제 (character ID로)
  async deleteMyReview(characterId) {
    await api.delete(`/api/character-reviews/character/${characterId}/my-review`);
  },

  // 캐릭터 리뷰 좋아요
  async likeReview(reviewId) {
    const { data } = await api.post(`/api/character-reviews/${reviewId}/like`);
    return data;
  },

  // 캐릭터 리뷰 좋아요 취소
  async unlikeReview(reviewId) {
    const { data } = await api.delete(`/api/character-reviews/${reviewId}/like`);
    return data;
  },
};
