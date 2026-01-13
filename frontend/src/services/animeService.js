/**
 * Anime Service
 * Fetch anime data
 */
import api from './api';

export const animeService = {
  /**
   * Get anime list with filters
   */
  async getAnimeList(params = {}) {
    const response = await api.get('/api/anime/', { params });
    return response.data;
  },

  /**
   * Get anime by ID
   */
  async getAnimeById(id) {
    const response = await api.get(`/api/anime/${id}`);
    return response.data;
  },

  /**
   * Search anime
   */
  async searchAnime(query, params = {}) {
    const response = await api.get('/api/anime/search', {
      params: { q: query, ...params },
    });
    return response.data;
  },

  /**
   * Get popular anime
   */
  async getPopularAnime(limit = 50) {
    const response = await api.get('/api/anime/popular', {
      params: { limit },
    });
    return response.data;
  },

  /**
   * Get top rated anime
   */
  async getTopRatedAnime(limit = 50) {
    const response = await api.get('/api/anime/top-rated', {
      params: { limit },
    });
    return response.data;
  },

  /**
   * Get all genres
   */
  async getGenres() {
    const response = await api.get('/api/anime/genres');
    return response.data;
  },
};
