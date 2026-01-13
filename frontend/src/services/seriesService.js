import api from './api';

export const seriesService = {
  // Get anime sequels
  async getAnimeSequels(animeId) {
    const response = await api.get(`/api/series/anime/${animeId}/sequels`);
    return response.data;
  },

  // Bulk rate series
  async bulkRateSeries(animeIds, status) {
    const response = await api.post('/api/series/bulk-rate', {
      anime_ids: animeIds,
      status: status
    });
    return response.data;
  },
};
