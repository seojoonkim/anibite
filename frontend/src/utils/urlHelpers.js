/**
 * URL Helper Functions
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const getImageUrl = (imageUrl) => {
  if (!imageUrl) return '/placeholder-anime.png';
  if (imageUrl.startsWith('http')) return imageUrl;
  return `${API_BASE_URL}${imageUrl}`;
};

export const getAvatarUrl = (avatarUrl) => {
  if (!avatarUrl) return null;
  if (avatarUrl.startsWith('http')) return avatarUrl;
  return `${API_BASE_URL}${avatarUrl}`;
};

export const getApiUrl = (path) => {
  return `${API_BASE_URL}${path}`;
};
