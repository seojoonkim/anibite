import api from './api';

export const userService = {
  // Get user profile
  async getProfile() {
    const response = await api.get('/api/users/me/profile');
    return response.data;
  },

  // Get other user's profile
  async getUserProfile(userId) {
    const response = await api.get(`/api/users/${userId}/profile`);
    return response.data;
  },

  // Get user statistics
  async getStats() {
    const response = await api.get('/api/users/me/stats');
    return response.data;
  },

  // Get genre preferences
  async getGenrePreferences() {
    const response = await api.get('/api/users/me/genre-preferences');
    return response.data;
  },

  // Get other user's genre preferences
  async getUserGenrePreferences(userId) {
    const response = await api.get(`/api/users/${userId}/genre-preferences`);
    return response.data;
  },

  // Get watch time
  async getWatchTime() {
    const response = await api.get('/api/users/me/watch-time');
    return response.data;
  },

  // Get rating distribution
  async getRatingDistribution() {
    const response = await api.get('/api/users/me/rating-distribution');
    return response.data;
  },

  // Get year distribution
  async getYearDistribution() {
    const response = await api.get('/api/users/me/year-distribution');
    return response.data;
  },

  // Update user profile
  async updateProfile(data) {
    const response = await api.put('/api/users/me/profile', data);
    return response.data;
  },

  // Update password
  async updatePassword(data) {
    const response = await api.put('/api/users/me/password', data);
    return response.data;
  },

  // Get format distribution (Phase 1)
  async getFormatDistribution() {
    const response = await api.get('/api/users/me/format-distribution');
    return response.data;
  },

  // Get episode length distribution (Phase 1)
  async getEpisodeLengthDistribution() {
    const response = await api.get('/api/users/me/episode-length-distribution');
    return response.data;
  },

  // Get rating stats (Phase 1)
  async getRatingStats() {
    const response = await api.get('/api/users/me/rating-stats');
    return response.data;
  },

  // Get studio stats (Phase 1)
  async getStudioStats(limit = 10) {
    const response = await api.get('/api/users/me/studio-stats', { params: { limit } });
    return response.data;
  },

  // Get season stats (Phase 1)
  async getSeasonStats() {
    const response = await api.get('/api/users/me/season-stats');
    return response.data;
  },

  // Get genre combinations (Phase 2)
  async getGenreCombinations(limit = 10) {
    const response = await api.get('/api/users/me/genre-combinations', { params: { limit } });
    return response.data;
  },

  // Get 5-star characters for profile picture selection
  async getFiveStarCharacters() {
    const response = await api.get('/api/users/me/five-star-characters');
    return response.data;
  },

  // Get character ratings
  async getCharacterRatings(params = {}) {
    const response = await api.get('/api/users/me/character-ratings', { params });
    return response.data;
  },

  // Upload profile picture
  async uploadAvatar(file) {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/api/users/me/avatar/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Set profile picture from character
  async setAvatarFromCharacter(characterId) {
    const response = await api.put('/api/users/me/avatar/character', null, {
      params: { character_id: characterId },
    });
    return response.data;
  },

  // Get leaderboard (top users by otaku score)
  async getLeaderboard(limit = 50) {
    const response = await api.get('/api/users/leaderboard', {
      params: { limit },
    });
    return response.data;
  },

  // Get studio preferences (Phase 3)
  async getStudioPreferences(limit = 10) {
    const response = await api.get('/api/users/me/studio-preferences', { params: { limit } });
    return response.data;
  },

  // Get director preferences (Phase 3)
  async getDirectorPreferences(limit = 10) {
    const response = await api.get('/api/users/me/director-preferences', { params: { limit } });
    return response.data;
  },

  // Get hidden gems (Phase 3)
  async getHiddenGems(limit = 10) {
    const response = await api.get('/api/users/me/hidden-gems', { params: { limit } });
    return response.data;
  },

  // Get source preferences (Phase 3)
  async getSourcePreferences() {
    const response = await api.get('/api/users/me/source-preferences');
    return response.data;
  },

  // Get genre radar data (Phase 3)
  async getGenreRadarData() {
    const response = await api.get('/api/users/me/genre-radar');
    return response.data;
  },
};
