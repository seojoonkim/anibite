/**
 * Anime Service
 * Fetch anime data
 */
import api from './api';

export const animeService = {
  /**
   * Get anime list with filters
   */
  async getAnimeList(params = {}, options = {}) {
    const { limit, sort, ...rest } = params;
    const sorts = { popularity_desc: 'popularity', rating_desc: 'score', title_asc: 'title' };
    const sortBy = rest.sort_by || sorts[sort] || 'popularity';
    const response = await api.get('/api/anime/', { ...options, params: { ...rest, page_size: rest.page_size || limit || 20, sort_by: ['popularity', 'score', 'trending', 'title', 'recent'].includes(sortBy) ? sortBy : 'popularity' } });
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

  /**
   * Get anime for rating page (ULTRA FAST - 0.1s target)
   * Uses optimized endpoint with built-in randomness
   */
  async getAnimeForRating(params = {}) {
    const response = await api.get('/api/rating-pages/anime', { params });
    return response.data;
  },

  /**
   * Get anime rating page stats (ULTRA FAST)
   */
  async getAnimeRatingStats() {
    const response = await api.get('/api/rating-pages/anime/stats');
    return response.data;
  },
};
