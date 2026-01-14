import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { animeService } from '../services/animeService';
import { ratingService } from '../services/ratingService';
import { seriesService } from '../services/seriesService';
import { useLanguage } from '../context/LanguageContext';
import Navbar from '../components/common/Navbar';
import { API_BASE_URL, IMAGE_BASE_URL } from '../config/api';

function RatingCard({ anime, onRate }) {
  const { getAnimeTitle, t, language } = useLanguage();
  const [hoverRating, setHoverRating] = useState(0);
  const [currentRating, setCurrentRating] = useState(0);
  const [status, setStatus] = useState(anime.user_rating_status || null); // null, 'RATED', 'WANT_TO_WATCH', 'PASS'
  const [showSeriesModal, setShowSeriesModal] = useState(false);
  const [seriesInfo, setSeriesInfo] = useState(null);
  const [pendingStatus, setPendingStatus] = useState(null);
  const [animating, setAnimating] = useState(false);
  const cardRef = useRef(null);
  const [starSize, setStarSize] = useState('3rem');

  const getImageUrl = (imageUrl) => {
    if (!imageUrl) return '/placeholder-anime.svg';
    if (imageUrl.startsWith('http')) return imageUrl;
    // Use covers_large for better quality
    const processedUrl = imageUrl.includes('/covers/')
      ? imageUrl.replace('/covers/', '/covers_large/')
      : imageUrl;
    return `${IMAGE_BASE_URL}${processedUrl}`;
  };

  useEffect(() => {
    const updateStarSize = () => {
      if (cardRef.current) {
        const cardWidth = cardRef.current.offsetWidth;
        // 카드 너비의 85%를 별 5개로 나눔 (더 크게)
        const availableWidth = cardWidth * 0.85;
        const singleStarSize = availableWidth / 5.0; // 더 크게 (6% increase): 5.3 → 5.0
        setStarSize(`${singleStarSize}px`);
      }
    };

    updateStarSize();
    window.addEventListener('resize', updateStarSize);
    return () => window.removeEventListener('resize', updateStarSize);
  }, []);

  const handleStarClick = async (rating) => {
    setCurrentRating(rating);
    setStatus('RATED');
    setAnimating(true);
    setTimeout(() => setAnimating(false), 500);

    try {
      await onRate(anime.id, rating, 'RATED');
    } catch (err) {
      console.error('Failed to rate:', err);
      setStatus(null);
      setCurrentRating(0);
    }
  };

  const handleStatusClick = async (statusType) => {
    // 시리즈 확인
    try {
      const series = await seriesService.getAnimeSequels(anime.id);
      if (series && series.sequels && series.sequels.length > 0) {
        // 시리즈가 있으면 모달 표시
        setSeriesInfo(series);
        setPendingStatus(statusType);
        setShowSeriesModal(true);
        return;
      }
    } catch (err) {
      console.error('Failed to check series:', err);
    }

    // 시리즈가 없으면 바로 처리
    setStatus(statusType);
    setAnimating(true);
    setTimeout(() => setAnimating(false), 500);
    try {
      await onRate(anime.id, null, statusType);
    } catch (err) {
      console.error('Failed to save status:', err);
      setStatus(null);
    }
  };

  const handleSeriesConfirm = async (applyToAll) => {
    setShowSeriesModal(false);

    if (applyToAll && seriesInfo) {
      // 일괄 처리
      const animeIds = [anime.id, ...seriesInfo.sequels.map(s => s.id)];
      try {
        await seriesService.bulkRateSeries(animeIds, pendingStatus);
        setStatus(pendingStatus);
      } catch (err) {
        console.error('Failed to bulk rate:', err);
      }
    } else {
      // 현재만 처리
      setStatus(pendingStatus);
      try {
        await onRate(anime.id, null, pendingStatus);
      } catch (err) {
        console.error('Failed to save status:', err);
        setStatus(null);
      }
    }

    setSeriesInfo(null);
    setPendingStatus(null);
  };

  const handleSeriesCancel = () => {
    setShowSeriesModal(false);
    setSeriesInfo(null);
    setPendingStatus(null);
  };

  const handleStarHover = (star, isLeftHalf) => {
    const rating = isLeftHalf ? star - 0.5 : star;
    setHoverRating(rating);
  };

  const handleMouseMove = (e, star) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const isLeftHalf = x < rect.width / 2;
    handleStarHover(star, isLeftHalf);
  };

  const renderStar = (position) => {
    const displayRating = hoverRating || currentRating;

    const gradientStyle = {
      background: 'linear-gradient(135deg, #833AB4 0%, #E1306C 40%, #F77737 70%, #FCAF45 100%)',
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
      backgroundClip: 'text'
    };

    if (displayRating >= position) {
      return <span style={gradientStyle}>★</span>;
    } else if (displayRating >= position - 0.5) {
      return (
        <span className="relative inline-block">
          <span className="text-gray-600">★</span>
          <span className="absolute top-0 left-0 overflow-hidden w-1/2" style={gradientStyle}>
            ★
          </span>
        </span>
      );
    }
    return <span className="text-gray-600">★</span>;
  };

  const getCardBackgroundColor = () => {
    if (status === 'RATED') return 'bg-[#F5F5F5]';
    if (status === 'WANT_TO_WATCH') return 'bg-[#F5F5F5]';
    if (status === 'PASS') return 'bg-gray-200';
    return 'bg-white';
  };

  return (
    <div className="group relative" ref={cardRef}>
      <div className={`${getCardBackgroundColor()} rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] overflow-hidden hover:shadow-[0_4px_16px_rgba(0,0,0,0.12)] transition-all duration-300 ${animating ? 'scale-105' : 'scale-100'}`}>
        {/* Cover Image */}
        <Link to={`/anime/${anime.id}`} className="block relative aspect-[3/4] bg-gray-200 group/image overflow-hidden">
          <img
            src={getImageUrl(anime.cover_image_url)}
            alt={getAnimeTitle(anime)}
            className="w-full h-full object-cover group-hover/image:scale-110 transition-transform duration-300"
            onError={(e) => {
              e.target.src = '/placeholder-anime.svg';
            }}
          />

          {/* Show faded rating on already rated anime */}
          {status === 'RATED' && currentRating > 0 && (
            <div className="absolute inset-0 flex items-center justify-center group-hover:opacity-0 transition-opacity">
              <div className="flex justify-center gap-1 opacity-40" style={{ fontSize: starSize }}>
                {[1, 2, 3, 4, 5].map((star) => (
                  <span key={star}>
                    {renderStar(star)}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Overlay on hover */}
          <div
            className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-75 transition-all duration-300 flex flex-col items-center justify-center p-4"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
            }}
          >
            <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-300 text-center w-full flex flex-col justify-center h-full">
              {/* Star Rating */}
              <div
                className="flex justify-center gap-1 mb-4 sm:mb-6"
                style={{ fontSize: starSize }}
                onMouseLeave={() => setHoverRating(0)}
              >
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    className="cursor-pointer hover:scale-125 transition-transform"
                    onMouseMove={(e) => handleMouseMove(e, star)}
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      const rect = e.currentTarget.getBoundingClientRect();
                      const x = e.clientX - rect.left;
                      const isLeftHalf = x < rect.width / 2;
                      handleStarClick(isLeftHalf ? star - 0.5 : star);
                    }}
                  >
                    {renderStar(star)}
                  </button>
                ))}
              </div>

              {currentRating > 0 && (
                <div className="text-white text-lg font-semibold mb-6">
                  {currentRating.toFixed(1)}
                </div>
              )}

              {/* Actions - Watch Later & Pass */}
              <div className="flex items-center justify-center gap-4 text-white text-sm">
                <button
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    handleStatusClick('WANT_TO_WATCH');
                  }}
                  className="hover:text-[#A8E6CF] transition-colors underline-offset-2 hover:underline"
                >
                  {t('watchLater')}
                </button>
                <span className="text-gray-400">|</span>
                <button
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    handleStatusClick('PASS');
                  }}
                  className="text-gray-300 hover:text-gray-100 transition-colors underline-offset-2 hover:underline"
                >
                  {t('notInterested')}
                </button>
              </div>
            </div>
          </div>

          {/* Status Badge */}
          {status && (
            <div className={`absolute top-3 right-3 text-white text-xs px-3 py-1.5 rounded-lg font-semibold shadow-[0_2px_12px_rgba(0,0,0,0.08)]`} style={{
              backgroundColor: status === 'RATED' ? '#A8E6CF' : status === 'WANT_TO_WATCH' ? '#364F6B' : '#95a5a6'
            }}>
              {status === 'RATED' && t('ratedBadge')}
              {status === 'WANT_TO_WATCH' && t('watchLater')}
              {status === 'PASS' && t('notInterested')}
            </div>
          )}
        </Link>

        {/* Title */}
        <div className="p-4">
          <Link to={`/anime/${anime.id}`} className="block group/title">
            {(() => {
              const titles = getAnimeTitle(anime, true);
              return (
                <>
                  <h3 className="font-semibold text-base line-clamp-2 text-gray-900 leading-snug mb-1 group-hover/title:text-[#3498DB] transition-colors cursor-pointer">
                    {titles.primary}
                  </h3>
                  {titles.secondary && (
                    <p className="text-xs text-gray-500 line-clamp-1 mb-1">
                      {titles.secondary}
                    </p>
                  )}
                </>
              );
            })()}
          </Link>
          <div className="flex items-center gap-2 text-xs text-gray-500">
            {anime.season_year && <span>{anime.season_year}</span>}
            {anime.episodes && <span>·</span>}
            {anime.episodes && <span>{anime.episodes}{t('episodes')}</span>}
          </div>
        </div>
      </div>

      {/* 시리즈 일괄 처리 모달 */}
      {showSeriesModal && seriesInfo && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={handleSeriesCancel}>
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-xl font-bold mb-4">시리즈 일괄 처리</h3>

            <div className="mb-4">
              <p className="text-gray-700 mb-3">
                이 작품은 {seriesInfo.sequels.length}개의 후속작이 있습니다.
              </p>

              <div className="bg-[#F5F5F5] border-2 rounded-lg p-4 mb-3" style={{ borderColor: '#A8E6CF' }}>
                <p className="text-sm font-medium text-[#34495E] mb-2">
                  후속작 목록:
                </p>
                <div className="max-h-32 overflow-y-auto space-y-1">
                  {seriesInfo.sequels.map((sequel, index) => (
                    <p key={sequel.id} className="text-sm text-gray-700">
                      {index + 1}. {sequel.title_korean || sequel.title_romaji}
                    </p>
                  ))}
                </div>
              </div>

              <p className="text-gray-700 mb-2">
                이 작품과 모든 후속작에 <strong style={{ color: '#364F6B' }}>
                  {pendingStatus === 'WANT_TO_WATCH' ? t('watchLater') : t('notInterested')}
                </strong>를 적용하시겠습니까?
              </p>

              <p className="text-sm text-gray-700 bg-[#F5F5F5] p-3 rounded">
                💡 이전 시즌은 영향받지 않습니다. (이미 보셨거나 다른 평가를 했을 수 있으므로)
              </p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => handleSeriesConfirm(true)}
                className="flex-1 text-white py-2 px-4 rounded font-medium transition-colors"
                style={{ backgroundColor: '#364F6B' }}
                onMouseEnter={(e) => e.target.style.backgroundColor = '#2c3e50'}
                onMouseLeave={(e) => e.target.style.backgroundColor = '#364F6B'}
              >
                모두 적용 ({seriesInfo.sequels.length + 1}개)
              </button>
              <button
                onClick={() => handleSeriesConfirm(false)}
                className="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-700 py-2 px-4 rounded font-medium transition-colors"
              >
                현재만
              </button>
              <button
                onClick={handleSeriesCancel}
                className="bg-gray-200 hover:bg-gray-300 text-gray-700 py-2 px-4 rounded font-medium transition-colors"
              >
                취소
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function Rate() {
  const { t, language } = useLanguage();
  const [animeList, setAnimeList] = useState([]);
  const [loading, setLoading] = useState(false);
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

  useEffect(() => {
    loadAnime();
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      // Use ULTRA FAST optimized stats endpoint (0.1s target)
      const data = await animeService.getAnimeRatingStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to load stats:', err);
      // Fallback to defaults
      setStats({
        total: 3000,
        rated: 0,
        watchLater: 0,
        pass: 0,
        remaining: 3000,
        averageRating: 0
      });
    }
  };

  const loadStatsOld = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || API_BASE_URL}/api/users/me/stats`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setStats({
          total: data.total_anime || 3000,
          rated: data.total_rated || 0,
          averageRating: data.average_rating || 0,
          watchLater: data.total_want_to_watch || 0,
          pass: data.total_pass || 0,
          remaining: (data.total_anime || 3000) - (data.total_rated || 0) - (data.total_pass || 0)
        });
      } else {
        // Fallback to default
        setStats({
          total: 3000,
          rated: 0,
          watchLater: 0,
          pass: 0,
          remaining: 3000
        });
      }
    } catch (err) {
      console.error('Failed to load stats:', err);
      // Fallback to default (관심목록은 다시 평가 가능하므로 남은 개수에 포함)
      setStats({
        total: 3000,
        rated: 0,
        watchLater: 0,
        pass: 0,
        remaining: 3000,
        averageRating: 0
      });
    }
  };

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loading) {
          loadMore();
        }
      },
      { threshold: 0.1 }
    );

    if (observerRef.current) {
      observer.observe(observerRef.current);
    }

    return () => observer.disconnect();
  }, [hasMore, loading]);

  const loadAnime = async () => {
    try {
      setLoading(true);
      // Use ULTRA FAST optimized endpoint (0.1s target)
      const data = await animeService.getAnimeForRating({
        limit: 50,
        offset: 0
      });

      setAnimeList(data.items || []);
      setHasMore(data.has_more !== false);
      setPage(1);
      setLoading(false);
    } catch (err) {
      console.error('Failed to load anime:', err);
      setLoading(false);
    }
  };

  const loadMore = async () => {
    if (loading || !hasMore) {
      console.log('Skip loadMore:', { loading, hasMore });
      return;
    }

    try {
      setLoading(true);
      const nextPage = page + 1;
      const offset = (nextPage - 1) * 50;
      console.log('Loading page:', nextPage, 'offset:', offset);

      // Use ULTRA FAST optimized endpoint (0.1s target)
      const data = await animeService.getAnimeForRating({
        limit: 50,
        offset: offset
      });

      console.log('Loaded data:', data);
      setAnimeList((prev) => [...prev, ...(data.items || [])]);
      setHasMore(data.has_more !== false);
      setPage(nextPage);
      setLoading(false);
    } catch (err) {
      console.error('Failed to load more:', err);
      setLoading(false);
    }
  };

  const handleRate = async (animeId, rating, status = 'RATED') => {
    try {
      const payload = status === 'RATED'
        ? { rating, status: 'RATED' }
        : { status };

      await ratingService.rateAnime(animeId, payload);

      // Reload stats after rating
      await loadStats();
    } catch (err) {
      console.error('Failed to rate:', err);
      throw err;
    }
  };

  return (
    <div className="min-h-screen pt-0 md:pt-16 bg-transparent">
      <Navbar />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header with Stats */}
        <div className="flex justify-center items-center mb-8">
          {/* Stats */}
          <div className="flex gap-3 items-center">
            {/* Rated */}
            <div className="bg-white px-4 py-2.5 rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] hover:shadow-[0_4px_16px_rgba(0,0,0,0.12)] transition-shadow min-w-[100px]">
              <div className="text-xs text-gray-600 mb-0.5 text-center">{language === 'ko' ? '평가했어요' : 'Rated'}</div>
              <div className="text-lg font-bold text-gray-800 text-center tabular-nums">{stats.rated.toLocaleString()}</div>
            </div>

            {/* Watch Later */}
            <div className="bg-white px-4 py-2.5 rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] hover:shadow-[0_4px_16px_rgba(0,0,0,0.12)] transition-shadow min-w-[100px]">
              <div className="text-xs text-gray-600 mb-0.5 text-center">{language === 'ko' ? '보고싶어요' : 'Later'}</div>
              <div className="text-lg font-bold text-gray-800 text-center tabular-nums">{stats.watchLater.toLocaleString()}</div>
            </div>

            {/* Pass */}
            <div className="bg-white px-4 py-2.5 rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] hover:shadow-[0_4px_16px_rgba(0,0,0,0.12)] transition-shadow min-w-[100px]">
              <div className="text-xs text-gray-600 mb-0.5 text-center">{language === 'ko' ? '관심없어요' : 'Pass'}</div>
              <div className="text-lg font-bold text-gray-800 text-center tabular-nums">{stats.pass.toLocaleString()}</div>
            </div>

            {/* Average Rating - Always show */}
            <div className="bg-white px-4 py-2.5 rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] hover:shadow-[0_4px_16px_rgba(0,0,0,0.12)] transition-shadow min-w-[100px]">
              <div className="text-xs text-gray-600 mb-0.5 text-center">{language === 'ko' ? '평균 평점' : 'Avg Rating'}</div>
              <div className="text-lg font-bold text-gray-800 text-center tabular-nums">
                {stats.averageRating > 0 ? `★ ${stats.averageRating.toFixed(1)}` : '-'}
              </div>
            </div>
          </div>
        </div>

        {/* Anime Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-6">
          {animeList.map((anime) => (
            <RatingCard key={anime.id} anime={anime} onRate={handleRate} />
          ))}
        </div>

        {/* Loading indicator */}
        {loading && (
          <div className="text-center py-8">
            <div className="text-gray-600">{t('loading')}</div>
          </div>
        )}

        {/* Intersection observer target */}
        <div ref={observerRef} className="h-10" />

        {!hasMore && animeList.length > 0 && (
          <div className="text-center py-8 text-gray-500">
            {t('allLoaded')}
          </div>
        )}
      </div>
    </div>
  );
}
