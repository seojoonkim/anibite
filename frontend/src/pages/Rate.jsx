import { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { animeService } from '../services/animeService';
import { ratingService } from '../services/ratingService';
import RatingWidget from '../components/anime/RatingWidget';
import RatingTabs from '../components/common/RatingTabs';
import { useLanguage } from '../context/LanguageContext';
import { useLogoWiggle } from '../context/LogoWiggleContext';
import { IMAGE_BASE_URL } from '../config/api';

function RatingCard({anime,onRate}) {
 const {getAnimeTitle}=useLanguage();
 const title=getAnimeTitle(anime);
 const image=anime.cover_image_url ? (anime.cover_image_url.startsWith('http') ? anime.cover_image_url : `${IMAGE_BASE_URL}${anime.cover_image_url}`) : '/placeholder-anime.svg';
 return <article className="quick-rating-card"><Link to={`/anime/${anime.id}`}><img src={image} alt="" loading="lazy" decoding="async" className="aspect-[3/4] w-full object-cover" onError={event=>{event.currentTarget.onerror=null;event.currentTarget.src='/placeholder-anime.svg';}}/><h2>{title}</h2></Link><p className="text-sm text-text-secondary">{anime.season_year} · {anime.format}</p><RatingWidget animeId={anime.id} currentRating={{rating:anime.user_rating,status:anime.user_rating_status}} onRate={value=>onRate(anime.id,value,'RATED')} onStatusChange={status=>onRate(anime.id,null,status)}/><Link className="quick-review-link" to={`/anime/${anime.id}#reviews`}>리뷰 작성 / 보기</Link></article>;
}

export default function Rate() {
  const { t, language } = useLanguage();
  const { triggerWiggle } = useLogoWiggle();
  const [animeList, setAnimeList] = useState([]);
  const [allAnimeItems, setAllAnimeItems] = useState([]); // All loaded items
  const [displayedCount, setDisplayedCount] = useState(0); // How many are displayed
  const [loading, setLoading] = useState(true); // Fix: Start with loading true
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [stats, setStats] = useState({
    total: 0,
    rated: 0,
    watchLater: 0,
    pass: 0,
    remaining: 0,
    averageRating: 0
  });
  const observerRef = useRef(null);



  function loadStats() {
    return animeService.getAnimeRatingStats().then(setStats).catch(err => {
      console.error('Failed to load stats:', err);
      setStats({ total: 3000, rated: 0, watchLater: 0, pass: 0, remaining: 3000, averageRating: 0 });
    });
  }





  const loadMore = useCallback(async () => {
    if (loading || !hasMore) {
      return;
    }

    try {
      setLoading(true);

      // If we have more frontend-cached items, show them first
      if (displayedCount < allAnimeItems.length) {
        const newDisplayedCount = Math.min(displayedCount + 20, allAnimeItems.length);
        setAnimeList(allAnimeItems.slice(0, newDisplayedCount));
        setDisplayedCount(newDisplayedCount);
        setHasMore(true); // Always true for infinite scroll
        setPage(page + 1);
        setLoading(false);
      } else {
        // All frontend items shown, load more from backend
        const data = await animeService.getAnimeForRating({
          limit: 50,
          offset: allAnimeItems.length
        });

        if (data.items && data.items.length > 0) {
          const newAllItems = [...allAnimeItems, ...data.items];
          setAllAnimeItems(newAllItems);
          setAnimeList(newAllItems.slice(0, displayedCount + 20));
          setDisplayedCount(displayedCount + 20);
          setHasMore(true); // Keep loading
        } else {
          setHasMore(false); // No more items
        }
        setLoading(false);
      }
    } catch (err) {
      console.error('Failed to load more:', err);
      setLoading(false);
    }
  }, [loading, hasMore, displayedCount, allAnimeItems, page]);

  const handleRate = async (animeId, rating, status = 'RATED') => {
    // Save previous state for rollback
    const prevAnime = animeList.find(a => a.id === animeId);
    const prevRating = prevAnime?.user_rating;
    const prevStatus = prevAnime?.user_rating_status;

    // Optimistic UI update - show success immediately
    const newRating = status === 'RATED' ? rating : 0;
    setAnimeList(prev => prev.map(anime =>
      anime.id === animeId
        ? { ...anime, user_rating_status: status, user_rating: newRating }
        : anime
    ));
    setAllAnimeItems(prev => prev.map(anime =>
      anime.id === animeId
        ? { ...anime, user_rating_status: status, user_rating: newRating }
        : anime
    ));

    try {
      const payload = status === 'RATED'
        ? { rating, status: 'RATED' }
        : { status };

      const response = status === null ? await ratingService.deleteRating(animeId) : await ratingService.rateAnime(animeId, payload);
      triggerWiggle();

      // Update cached otaku_score if provided
      if (response && response.otaku_score !== undefined) {
        localStorage.setItem('cached_otaku_score', response.otaku_score.toString());
        window.dispatchEvent(new Event('storage'));
      }

      // Reload stats after rating
      await loadStats();
    } catch (err) {
      console.error('Failed to rate:', err);

      // Rollback on failure
      setAnimeList(prev => prev.map(anime =>
        anime.id === animeId
          ? { ...anime, user_rating_status: prevStatus, user_rating: prevRating }
          : anime
      ));
      setAllAnimeItems(prev => prev.map(anime =>
        anime.id === animeId
          ? { ...anime, user_rating_status: prevStatus, user_rating: prevRating }
          : anime
      ));


      throw err;
    }
  };

  // Don't filter - keep all anime including rated ones (they'll show with visual feedback)
  const filteredAnimeList = useMemo(() => {
    return animeList;
  }, [animeList]);


  useEffect(() => {
  async function loadAnime() {
    try {
      console.log('[Rate] Loading initial anime list...'); // Debug Log

      // Load 100 items at once, paginate on frontend
      const data = await animeService.getAnimeForRating({
        limit: 100
      });

      console.log('[Rate] Loaded anime:', data?.items?.length); // Debug Log

      const allItems = data.items || [];
      // Show first 20 items immediately
      setAnimeList(allItems.slice(0, 20));
      setAllAnimeItems(allItems);
      setDisplayedCount(20);
      setHasMore(allItems.length > 20);
      setPage(1);
      setLoading(false);
    } catch (err) {
      console.error('Failed to load anime:', err);
      setLoading(false);
    }
  };
    loadAnime();
    loadStats();
  }, []);

useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loading) {
          loadMore();
        }
      },
      { threshold: 0.1, rootMargin: '200px' }
    );

    const currentRef = observerRef.current;
    if (currentRef) {
      observer.observe(currentRef);
    }

    return () => {
      if (currentRef) {
        observer.unobserve(currentRef);
      }
      observer.disconnect();
    };
  }, [hasMore, loading, loadMore]);

return (
    <div className="min-h-screen pt-10 md:pt-12 bg-transparent">

      <div className="max-w-[1180px] mx-auto px-3 sm:px-6 lg:px-8 py-4">
        <RatingTabs/>
        {/* Header with Stats */}
        <div className="flex justify-center items-center mb-4">
          {/* Stats */}
          <div className="flex gap-2 items-center flex-wrap justify-center">
            {/* Rated */}
            <div className="bg-surface px-3 py-1.5 rounded-md shadow-sm hover:shadow-md transition-shadow min-w-[80px] border border-border">
              <div className="text-xs text-text-secondary text-center">{language === 'ko' ? '평가했어요' : language === 'ja' ? '評価済み' : 'Rated'}</div>
              <div className="text-base font-bold text-primary text-center tabular-nums">{stats.rated.toLocaleString()}</div>
            </div>

            {/* Watch Later */}
            <div className="bg-surface px-3 py-1.5 rounded-md shadow-sm hover:shadow-md transition-shadow min-w-[80px] border border-border">
              <div className="text-xs text-text-secondary text-center">{language === 'ko' ? '보고싶어요' : language === 'ja' ? '見たい' : 'Later'}</div>
              <div className="text-base font-bold text-secondary text-center tabular-nums">{stats.watchLater.toLocaleString()}</div>
            </div>

            {/* Pass */}
            <div className="bg-surface px-3 py-1.5 rounded-md shadow-sm hover:shadow-md transition-shadow min-w-[80px] border border-border">
              <div className="text-xs text-text-secondary text-center">{language === 'ko' ? '관심없어요' : language === 'ja' ? '興味なし' : 'Pass'}</div>
              <div className="text-base font-bold text-text-tertiary text-center tabular-nums">{stats.pass.toLocaleString()}</div>
            </div>

            {/* Average Rating - Always show */}
            <div className="bg-surface px-3 py-1.5 rounded-md shadow-sm hover:shadow-md transition-shadow min-w-[80px] border border-border">
              <div className="text-xs text-text-secondary text-center">{language === 'ko' ? '평균 평점' : language === 'ja' ? '平均評価' : 'Avg Rating'}</div>
              <div className="text-base font-bold text-accent text-center tabular-nums flex items-center justify-center gap-1">
                {stats.averageRating > 0 ? (
                  <>
                    <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                    {stats.averageRating.toFixed(1)}
                  </>
                ) : '-'}
              </div>
            </div>
          </div>
        </div>

        {/* Anime Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2 sm:gap-3 items-start">
          {loading && animeList.length === 0 ? (
            // Skeleton cards during initial load (Show 8 skeletons)
            Array.from({ length: 8 }).map((_, index) => (
              <div key={`skeleton-${index}`} className="bg-surface rounded-lg shadow-md overflow-hidden animate-pulse border border-border">
                {/* Skeleton Image */}
                <div className="aspect-[3/4] bg-surface-elevated" />
                {/* Skeleton Title */}
                <div className="p-4 space-y-2">
                  <div className="h-4 bg-surface-elevated rounded w-3/4" />
                  <div className="h-3 bg-surface-elevated rounded w-1/2" />
                </div>
              </div>
            ))
          ) : filteredAnimeList.length > 0 ? (
            filteredAnimeList.map((anime) => (
              <RatingCard key={anime.id} anime={anime} onRate={handleRate} />
            ))
          ) : (
            // Fix: Empty state when not loading and no items
            <div className="col-span-full text-center py-12">
              <div className="text-xl text-text-secondary mb-4">
                {language === 'ko' ? '평가할 애니메이션이 없습니다' : language === 'ja' ? '評価するアニメがありません' : 'No anime to rate'}
              </div>
              <p className="text-text-tertiary">
                {language === 'ko' ? '모든 애니메이션을 평가하셨거나 데이터를 불러올 수 없습니다.' : language === 'ja' ? 'すべてのアニメを評価したか、データを読み込めませんでした。' : 'You have rated all anime or data could not be loaded.'}
              </p>
            </div>
          )}
        </div>

        {/* Loading more indicator */}
        {loading && animeList.length > 0 && (
          <div className="text-center py-8">
            <div className="text-text-secondary">{t('loading')}</div>
          </div>
        )}

        {/* Intersection observer target */}
        <div ref={observerRef} className="h-10" />

        {!hasMore && animeList.length > 0 && (
          <div className="text-center py-8 text-text-tertiary">
            {t('allLoaded')}
          </div>
        )}
      </div>
    </div>
  );
}
