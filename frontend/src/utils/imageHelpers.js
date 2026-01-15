/**
 * Image URL helper utilities
 * R2-first loading strategy with external URL fallback
 */
import { API_BASE_URL, IMAGE_BASE_URL } from '../config/api';

/**
 * Get character image URL
 * Strategy: Try R2 first by extracting character ID from AniList URL
 * @param {number|null} characterId - Character ID for R2 lookup (may not be AniList ID)
 * @param {string|null} imageUrl - External or database image URL
 * @returns {string} Image URL to try first
 */
export const getCharacterImageUrl = (characterId, imageUrl = null) => {
  // If imageUrl contains AniList character URL, extract the AniList character ID from it
  if (imageUrl && imageUrl.includes('anilist.co') && imageUrl.includes('/character/')) {
    const match = imageUrl.match(/\/b(\d+)-/);
    if (match && match[1]) {
      const anilistCharacterId = match[1];
      return `${IMAGE_BASE_URL}/images/characters/${anilistCharacterId}.jpg`;
    }
  }

  // Fallback: R2 우선 - character ID가 있으면 R2에서 찾기 (though this may not work if characterId is internal DB ID)
  if (characterId) {
    return `${IMAGE_BASE_URL}/images/characters/${characterId}.jpg`;
  }

  // character ID가 없으면 imageUrl 사용
  if (!imageUrl) return '/placeholder-anime.svg';
  if (imageUrl.startsWith('http')) return imageUrl;
  if (imageUrl.startsWith('/')) return `${IMAGE_BASE_URL}${imageUrl}`;

  return `${IMAGE_BASE_URL}${imageUrl}`;
};

/**
 * Get fallback image URL for character
 * Used in onError handler when R2 image fails
 * @param {string|null} imageUrl - External or database image URL
 * @returns {string} Fallback image URL
 */
export const getCharacterImageFallback = (imageUrl) => {
  if (!imageUrl) return '/placeholder-anime.svg';
  if (imageUrl.startsWith('http')) return imageUrl;
  return '/placeholder-anime.svg';
};

/**
 * Get avatar URL (for user profile pictures)
 * Strategy: Support both uploads and character avatars
 * @param {string|null} avatarUrl - Avatar URL from user object
 * @param {number|null} characterId - Optional character ID for R2 lookup
 * @returns {string} Avatar URL
 */
export const getAvatarUrl = (avatarUrl, characterId = null) => {
  if (!avatarUrl) return null;

  // 외부 URL은 그대로 사용하되, character ID가 있으면 R2 우선
  if (avatarUrl.startsWith('http')) {
    // If we have character ID, try R2 first (will fallback in onError)
    if (characterId) {
      return `${IMAGE_BASE_URL}/images/characters/${characterId}.jpg`;
    }
    return avatarUrl;
  }

  // /uploads로 시작하면 API 서버 (파일 업로드)
  if (avatarUrl.startsWith('/uploads')) {
    return `${API_BASE_URL}${avatarUrl}`;
  }

  // /images로 시작하면 R2
  if (avatarUrl.startsWith('/images')) {
    return `${IMAGE_BASE_URL}${avatarUrl}`;
  }

  // 그 외는 IMAGE_BASE_URL
  return `${IMAGE_BASE_URL}${avatarUrl}`;
};

/**
 * Get avatar fallback URL
 * Used in onError handler
 * @param {string|null} avatarUrl - Original avatar URL
 * @returns {string|null} Fallback URL or null for gradient placeholder
 */
export const getAvatarFallback = (avatarUrl) => {
  if (!avatarUrl) return null;
  if (avatarUrl.startsWith('http')) return avatarUrl;
  return null;
};

/**
 * Get character display name
 * Prefer English over Japanese/Native
 * @param {object} character - Character object
 * @returns {string} Display name
 */
export const getCharacterDisplayName = (character) => {
  if (!character) return '';

  // Prefer: name_full (English) > name_native (Japanese/Korean) > name_full
  if (character.name_full && !isJapanese(character.name_full)) {
    return character.name_full;
  }

  if (character.name_alternative) {
    return character.name_alternative;
  }

  return character.name_full || character.name_native || '';
};

/**
 * Check if string contains Japanese characters
 * @param {string} str
 * @returns {boolean}
 */
function isJapanese(str) {
  if (!str) return false;
  // Check for Hiragana, Katakana, Kanji
  return /[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]/.test(str);
}
