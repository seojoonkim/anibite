import { useRef, useCallback, useEffect } from 'react';
import { animeService } from '../services/animeService';
import { characterService } from '../services/characterService';
import { ratingService } from '../services/ratingService';
import { reviewService } from '../services/reviewService';
import { characterReviewService } from '../services/characterReviewService';
import { prefetchCache, syncCacheSession } from '../services/queryCache';

export function usePrefetch() {
  const timer = useRef(null);
  const handleMouseLeave = useCallback(() => { clearTimeout(timer.current); timer.current = null; }, []);
  useEffect(() => handleMouseLeave, [handleMouseLeave]);
  const prefetchAnimeDetail = useCallback(async (id, user = null) => {
    if (!id) return null;
    syncCacheSession();
    try {
      return await prefetchCache.fetch(`anime_${id}_${user?.id || 'guest'}`, async () => {
        const [anime, myRating = null, myReview = null] = await Promise.all([
          animeService.getAnimeById(id),
          ...(user ? [ratingService.getUserRating(id), reviewService.getMyReview(id)] : [])
        ]);
        return { anime, myRating, myReview };
      });
    } catch { return null; } // Optional optimization: failed reads are never cached.
  }, []);
  const prefetchCharacterDetail = useCallback(async (id, user = null) => {
    if (!id) return null;
    syncCacheSession();
    try {
      return await prefetchCache.fetch(`character_${id}_${user?.id || 'guest'}`, async () => {
        const [character, reviews, myReview = null] = await Promise.all([
          characterService.getCharacterDetail(id),
          characterReviewService.getCharacterReviews(id, { page: 1, page_size: 10 }),
          ...(user ? [characterReviewService.getMyReview(id)] : [])
        ]);
        return { character, reviews, myReview };
      });
    } catch { return null; }
  }, []);
  const handleAnimeMouseEnter = useCallback((id, user) => { handleMouseLeave(); timer.current = setTimeout(() => prefetchAnimeDetail(id, user), 300); }, [handleMouseLeave, prefetchAnimeDetail]);
  const handleCharacterMouseEnter = useCallback((id, user) => { handleMouseLeave(); timer.current = setTimeout(() => prefetchCharacterDetail(id, user), 300); }, [handleMouseLeave, prefetchCharacterDetail]);
  return { prefetchAnimeDetail, prefetchCharacterDetail, handleAnimeMouseEnter, handleCharacterMouseEnter, handleMouseLeave, prefetchCache };
}
export function getPrefetchedData(type, id, userId = null) {
  syncCacheSession();
  return prefetchCache.get(`${type}_${id}_${userId || 'guest'}`)?.data || null;
}
export function clearPrefetchCache() { prefetchCache.clear(); }
