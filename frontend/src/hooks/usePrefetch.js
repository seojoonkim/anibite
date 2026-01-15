import { useRef, useCallback } from 'react';
import { animeService } from '../services/animeService';
import { characterService } from '../services/characterService';
import { ratingService } from '../services/ratingService';
import { reviewService } from '../services/reviewService';
import { characterReviewService } from '../services/characterReviewService';

// Cache for prefetched data
const prefetchCache = new Map();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

/**
 * Custom hook for prefetching anime/character detail data on hover
 */
export function usePrefetch() {
  const prefetchTimeoutRef = useRef(null);

  const prefetchAnimeDetail = useCallback(async (animeId, user = null) => {
    if (!animeId) return;

    const cacheKey = `anime_${animeId}_${user?.id || 'guest'}`;
    const cached = prefetchCache.get(cacheKey);

    // Return cached data if still valid
    if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
      return cached.data;
    }

    try {
      // Prefetch anime details and user rating/review in parallel
      const promises = [animeService.getAnimeById(animeId)];

      if (user) {
        promises.push(ratingService.getUserRating(animeId).catch(() => null));
        promises.push(reviewService.getMyReview(animeId).catch(() => null));
      }

      const results = await Promise.all(promises);
      const data = {
        anime: results[0],
        myRating: results[1] || null,
        myReview: results[2] || null
      };

      // Cache the prefetched data
      prefetchCache.set(cacheKey, {
        data,
        timestamp: Date.now()
      });

      return data;
    } catch (error) {
      console.error('Failed to prefetch anime:', error);
      return null;
    }
  }, []);

  const prefetchCharacterDetail = useCallback(async (characterId, user = null) => {
    if (!characterId) return;

    const cacheKey = `character_${characterId}_${user?.id || 'guest'}`;
    const cached = prefetchCache.get(cacheKey);

    // Return cached data if still valid
    if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
      return cached.data;
    }

    try {
      // Prefetch character details and reviews in parallel
      const promises = [
        characterService.getCharacterDetail(characterId),
        characterReviewService.getCharacterReviews(characterId, { page: 1, page_size: 10 }).catch(() => null)
      ];

      if (user) {
        promises.push(characterReviewService.getMyReview(characterId).catch(() => null));
      }

      const results = await Promise.all(promises);
      const data = {
        character: results[0],
        reviews: results[1] || null,
        myReview: results[2] || null
      };

      // Cache the prefetched data
      prefetchCache.set(cacheKey, {
        data,
        timestamp: Date.now()
      });

      return data;
    } catch (error) {
      console.error('Failed to prefetch character:', error);
      return null;
    }
  }, []);

  /**
   * Handle mouse enter on anime card - debounced prefetch
   */
  const handleAnimeMouseEnter = useCallback((animeId, user) => {
    // Clear any existing timeout
    if (prefetchTimeoutRef.current) {
      clearTimeout(prefetchTimeoutRef.current);
    }

    // Prefetch after 300ms hover to avoid unnecessary requests
    prefetchTimeoutRef.current = setTimeout(() => {
      prefetchAnimeDetail(animeId, user);
    }, 300);
  }, [prefetchAnimeDetail]);

  /**
   * Handle mouse enter on character card - debounced prefetch
   */
  const handleCharacterMouseEnter = useCallback((characterId, user) => {
    // Clear any existing timeout
    if (prefetchTimeoutRef.current) {
      clearTimeout(prefetchTimeoutRef.current);
    }

    // Prefetch after 300ms hover to avoid unnecessary requests
    prefetchTimeoutRef.current = setTimeout(() => {
      prefetchCharacterDetail(characterId, user);
    }, 300);
  }, [prefetchCharacterDetail]);

  /**
   * Handle mouse leave - cancel pending prefetch
   */
  const handleMouseLeave = useCallback(() => {
    if (prefetchTimeoutRef.current) {
      clearTimeout(prefetchTimeoutRef.current);
      prefetchTimeoutRef.current = null;
    }
  }, []);

  return {
    prefetchAnimeDetail,
    prefetchCharacterDetail,
    handleAnimeMouseEnter,
    handleCharacterMouseEnter,
    handleMouseLeave,
    prefetchCache // Export cache for consumption by detail pages
  };
}

/**
 * Get prefetched data from cache
 */
export function getPrefetchedData(type, id, userId = null) {
  const cacheKey = `${type}_${id}_${userId || 'guest'}`;
  const cached = prefetchCache.get(cacheKey);

  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.data;
  }

  return null;
}

/**
 * Clear all prefetch cache
 */
export function clearPrefetchCache() {
  prefetchCache.clear();
}
