import api from './api';

export const characterService = {
  // Get characters from rated anime
  async getCharactersFromRatedAnime(params = {}) {
    const response = await api.get('/api/characters/from-rated-anime', { params });
    return response.data;
  },

  // Create or update character rating (NEW - unified API)
  async rateCharacter(characterId, ratingData) {
    const response = await api.post('/api/character-ratings/', {
      character_id: characterId,
      ...ratingData,
    });
    return response.data;
  },

  // Get my rating for a character (NEW - unified API)
  async getCharacterRating(characterId) {
    try {
      const response = await api.get(`/api/character-ratings/character/${characterId}`);
      return response.data;
    } catch (error) {
      if (error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  },

  // Get all my character ratings (single status filter) (NEW - unified API)
  async getMyRatings(params = {}) {
    const response = await api.get('/api/character-ratings/me', { params });
    return response.data;
  },

  // Get ALL my character ratings at once (RATED, WANT_TO_KNOW, NOT_INTERESTED) - 3x faster! (NEW)
  async getAllMyRatings() {
    const response = await api.get('/api/character-ratings/me/all');
    return response.data;
  },

  // Get other user's character ratings (public, single status filter) (NEW)
  async getUserRatings(userId, params = {}) {
    const response = await api.get(`/api/character-ratings/user/${userId}`, { params });
    return response.data;
  },

  // Get ALL other user's character ratings at once (RATED, WANT_TO_KNOW, NOT_INTERESTED) - 3x faster! (NEW)
  async getAllUserRatings(userId) {
    const response = await api.get(`/api/character-ratings/user/${userId}/all`);
    return response.data;
  },

  // Delete character rating (NEW - unified API)
  async deleteCharacterRating(characterId) {
    const response = await api.delete(`/api/character-ratings/character/${characterId}`);
    return response.data;
  },

  // Get character stats (OLD API - kept for compatibility)
  async getCharacterStats() {
    const response = await api.get('/api/characters/stats');
    return response.data;
  },

  // Get character detail (OLD API - kept for compatibility)
  async getCharacterDetail(characterId) {
    const response = await api.get(`/api/characters/${characterId}`);
    return response.data;
  },

  // DEPRECATED: Use getAllMyRatings() instead
  async getMyRatedCharacters(params = {}) {
    const response = await api.get('/api/characters/rated', { params });
    return response.data;
  },

  /**
   * Get characters for rating page (ULTRA FAST - 0.1s target)
   * Uses optimized endpoint with built-in randomness
   */
  async getCharactersForRating(params = {}) {
    const response = await api.get('/api/rating-pages/characters', { params });
    return response.data;
  },

  /**
   * Get character rating page stats (ULTRA FAST)
   */
  async getCharacterRatingStats() {
    const response = await api.get('/api/rating-pages/characters/stats');
    return response.data;
  }
};
