/**
 * Image URL helper utilities
 * R2-first loading strategy with external URL fallback
 */
import { API_BASE_URL, IMAGE_BASE_URL } from '../config/api';

/**
 * Get character image URL
 * Strategy: Use character ID directly with proper extension from original URL
 * @param {number|null} characterId - AniList character ID for R2 lookup
 * @param {string|null} imageUrl - External or database image URL (for extension and fallback)
 * @returns {string} Image URL to try first
 */
export const getCharacterImageUrl = (characterId, imageUrl = null) => {
  let finalUrl;

  // Priority 1: characterId가 있으면 백엔드 API 사용 (가장 안정적)
  // 백엔드가 R2에서 찾거나 없으면 AniList에서 자동 다운로드
  if (characterId) {
    finalUrl = `${API_BASE_URL}/api/images/characters/${characterId}.jpg`;
  }
  // Priority 2: imageUrl이 R2 URL이면 그대로 사용 (어드민에서 업로드한 이미지)
  else if (imageUrl && imageUrl.includes(IMAGE_BASE_URL)) {
    finalUrl = imageUrl;
  }
  // Priority 3: imageUrl이 AniList URL이면 character ID 추출 후 백엔드 API 사용
  else if (imageUrl && imageUrl.includes('anilist.co') && imageUrl.includes('/character/')) {
    const match = imageUrl.match(/\/b(\d+)-/);
    if (match && match[1]) {
      const extractedId = match[1];
      finalUrl = `${API_BASE_URL}/api/images/characters/${extractedId}.jpg`;
    } else {
      // ID 추출 실패 - placeholder 사용
      finalUrl = null;
    }
  }
  // Priority 4: 상대 경로면 IMAGE_BASE_URL 붙이기
  else if (imageUrl && !imageUrl.startsWith('http')) {
    finalUrl = `${IMAGE_BASE_URL}${imageUrl}`;
  }

  if (!finalUrl) return '/placeholder-anime.svg';

  return finalUrl;
};

/**
 * Get fallback image URL for character
 * Used in onError handler when R2 image fails
 * Strategy: jpg → png → jpeg → webp → gif → original AniList URL → placeholder
 * @param {string|null} imageUrl - External or database image URL
 * @param {string|null} currentSrc - Current src that failed (to try alternate extension)
 * @returns {string} Fallback image URL
 */
export const getCharacterImageFallback = (imageUrl, currentSrc = null) => {
  // Extension fallback order
  const extensionOrder = ['jpg', 'png', 'jpeg', 'webp', 'gif'];

  // If current src is R2 character image, try next extension
  if (currentSrc && currentSrc.includes('/images/characters/')) {
    // Extract current extension
    const currentExtMatch = currentSrc.match(/\.([a-z]+)$/i);
    if (currentExtMatch && currentExtMatch[1]) {
      const currentExt = currentExtMatch[1].toLowerCase();
      const currentIndex = extensionOrder.indexOf(currentExt);

      // Try next extension in the order
      if (currentIndex !== -1 && currentIndex < extensionOrder.length - 1) {
        const nextExt = extensionOrder[currentIndex + 1];
        return currentSrc.replace(/\.[a-z]+$/i, `.${nextExt}`);
      }

      // All extensions tried, fallback to original AniList URL if available
      if (imageUrl && imageUrl.startsWith('http')) {
        return imageUrl;
      }

      // No original URL, use placeholder
      return '/placeholder-anime.svg';
    }
  }

  // No valid R2 path, use placeholder
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

  // 외부 URL(AniList 등) - 백엔드 API 사용
  if (avatarUrl.startsWith('http')) {
    // If we have character ID parameter, use backend API
    if (characterId) {
      return `${API_BASE_URL}/api/images/characters/${characterId}.jpg`;
    }

    // Try to extract character ID from AniList URL
    if (avatarUrl.includes('anilist.co') && avatarUrl.includes('/character/')) {
      const match = avatarUrl.match(/\/b(\d+)-/);
      if (match && match[1]) {
        const extractedCharacterId = match[1];
        return `${API_BASE_URL}/api/images/characters/${extractedCharacterId}.jpg`;
      }
    }

    // External URL without character ID - return null (will show gradient placeholder)
    return null;
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
 * @param {string|null} currentSrc - Current src that failed
 * @returns {string|null} Fallback URL or null for gradient placeholder
 */
export const getAvatarFallback = (avatarUrl, currentSrc = null) => {
  // If R2 URL failed and we have original AniList URL, use it
  if (currentSrc && currentSrc.includes('/images/characters/') && avatarUrl && avatarUrl.startsWith('http')) {
    return avatarUrl;
  }

  // No external URL fallback - use gradient placeholder
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
