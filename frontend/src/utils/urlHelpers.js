/**
 * URL Helper Functions
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const IMAGE_BASE_URL = import.meta.env.VITE_IMAGE_BASE_URL || API_BASE_URL;

/**
 * Get image URL from R2 CDN
 * @param {string} imageUrl - Image path from database
 * @param {object} options - Options { thumbnail: boolean }
 * @returns {string} Full image URL
 */
export const getImageUrl = (imageUrl, options = {}) => {
  if (!imageUrl) return '/placeholder-anime.svg';
  if (imageUrl.startsWith('http')) return imageUrl;

  // Use covers_large for better quality, unless thumbnail is requested
  let processedUrl = imageUrl;
  if (!options.thumbnail && imageUrl.includes('/covers/')) {
    processedUrl = imageUrl.replace('/covers/', '/covers_large/');
  }

  return `${IMAGE_BASE_URL}${processedUrl}`;
};

/**
 * Get avatar URL (user avatars from uploads directory)
 * @param {string} avatarUrl - Avatar path
 * @returns {string|null} Full avatar URL or null
 */
export const getAvatarUrl = (avatarUrl) => {
  if (!avatarUrl) return null;
  if (avatarUrl.startsWith('http')) return avatarUrl;
  // User avatars are stored on the API server, not R2
  return `${API_BASE_URL}${avatarUrl}`;
};

/**
 * Get API endpoint URL
 * @param {string} path - API path
 * @returns {string} Full API URL
 */
export const getApiUrl = (path) => {
  return `${API_BASE_URL}${path}`;
};
