import api from './api';

export const characterService = {
  // Get characters from rated anime
  async getCharactersFromRatedAnime(params = {}) {
    const response = await api.get('/api/characters/from-rated-anime', { params });
    return response.data;
  },

  // Rate a character
  async rateCharacter(characterId, rating, status = null) {
    const payload = {
      character_id: characterId
    };
    if (rating !== null) {
      payload.rating = rating;
    }
    if (status !== null) {
      payload.status = status;
    }
    const response = await api.post('/api/characters/rate', payload);
    return response.data;
  },

  // Get my rating for a character
  async getCharacterRating(characterId) {
    try {
      const response = await api.get(`/api/characters/rating/${characterId}`);
      return response.data;
    } catch (error) {
      if (error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  },

  // Delete character rating
  async deleteCharacterRating(characterId) {
    const response = await api.delete(`/api/characters/rating/${characterId}`);
    return response.data;
  },

  // Get character stats
  async getCharacterStats() {
    const response = await api.get('/api/characters/stats');
    return response.data;
  },

  // Get character detail
  async getCharacterDetail(characterId) {
    const response = await api.get(`/api/characters/${characterId}`);
    return response.data;
  },

  // Get my rated characters
  async getMyRatedCharacters(params = {}) {
    const response = await api.get('/api/characters/rated', { params });
    return response.data;
  }
};
