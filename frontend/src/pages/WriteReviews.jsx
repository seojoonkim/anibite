import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ratingService } from '../services/ratingService';
import { reviewService } from '../services/reviewService';
import { characterService } from '../services/characterService';
import { characterReviewService } from '../services/characterReviewService';
import { ratingPageService } from '../services/ratingPageService';
import { useLanguage } from '../context/LanguageContext';
import StarRating from '../components/common/StarRating';
import { API_BASE_URL, IMAGE_BASE_URL } from '../config/api';
import { getCharacterImageUrl } from '../utils/imageHelpers';

export default function WriteReviews() {
  const { getAnimeTitle, language } = useLanguage();
  const [filter, setFilter] = useState('all'); // all, anime, character
  const [allItems, setAllItems] = useState([]);
  const [reviews, setReviews] = useState({});
  const [loading, setLoading] = useState(true);
  const [reviewsLoading, setReviewsLoading] = useState(true); // 리뷰 로딩 상태
  const [editingId, setEditingId] = useState(null);
  const [editContent, setEditContent] = useState('');
  const [editRating, setEditRating] = useState(0);
  const [justCompleted, setJustCompleted] = useState(new Set()); // 방금 작성 완료한 항목
  const [stats, setStats] = useState({
    anime: { reviewed: 0, pending: 0 },
    character: { reviewed: 0, pending: 0 },
    total: { reviewed: 0, pending: 0 }
  });
  const [toast, setToast] = useState(null); // { message, type: 'success'|'error' }
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);

  useEffect(() => {
    loadData(true);
    loadStats();
  }, []);

  // Infinite scroll handler
  useEffect(() => {
    const handleScroll = () => {
      if (loadingMore || !hasMore) return;

      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      const scrollHeight = document.documentElement.scrollHeight;
      const clientHeight = document.documentElement.clientHeight;

      // Load more when user is 500px from bottom
      if (scrollTop + clientHeight >= scrollHeight - 500) {
        loadMore();
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [loadingMore, hasMore, offset]);

  const loadMore = async () => {
    if (loadingMore || !hasMore) return;

    try {
      setLoadingMore(true);
      console.log('[WriteReviews] Loading more items... offset:', offset);

      const data = await ratingPageService.getItemsForReviews(50, offset);
      console.log('[WriteReviews] Loaded more items:', data?.items?.length || 0);

      const items = (data.items || []).map(item => {
        const processed = {
          type: item.type,
          id: `${item.type}_${item.item_id}`,
          itemId: item.item_id,
          rating: item.rating,
          updated_at: item.updated_at,
          ...(item.type === 'anime' ? {
            anime_id: item.item_id,
            title_romaji: item.item_title,
            title_english: item.item_title,
            title_native: item.item_title_native,
            title_korean: item.item_title_korean,
            image_url: item.item_image,
            year: item.item_year
          } : {}),
          ...(item.type === 'character' ? {
            character_id: item.item_id,
            character_name: item.item_title,
            character_name_korean: item.item_title_korean,
            character_name_native: item.item_title_native,
            character_image: item.item_image,
            anime_id: item.anime_id,
            anime_title_korean: item.anime_title_korean,
            anime_title_native: item.anime_title_native,
            anime_title: item.anime_title
          } : {})
        };
        return processed;
      });

      setAllItems(prev => [...prev, ...items]);
      setOffset(prev => prev + items.length);
      setHasMore(items.length === 50);
    } catch (err) {
      console.error('[WriteReviews] Failed to load more:', err);
    } finally {
      setLoadingMore(false);
    }
  };

  const loadStats = async () => {
    try {
      const data = await ratingPageService.getReviewStats();
      setStats(data);
      console.log('[WriteReviews] Stats loaded:', data);
    } catch (err) {
      console.error('[WriteReviews] Failed to load stats:', err);
    }
  };

  const loadData = async (resetOffset = false) => {
    try {
      setLoading(true);
      const currentOffset = resetOffset ? 0 : offset;
      console.log('[WriteReviews] Starting to load data... offset:', currentOffset);

      // 초고속 API 사용 - 단일 쿼리로 애니+캐릭터 모두 가져오기 (0.1초 목표)
      const data = await ratingPageService.getItemsForReviews(50, currentOffset);
      console.log('[WriteReviews] API response:', data);
      console.log('[WriteReviews] Items count:', data?.items?.length || 0);

      // 응답 데이터를 기존 형식으로 변환
      const items = (data.items || []).map(item => {
        const processed = {
          type: item.type,
          id: `${item.type}_${item.item_id}`,
          itemId: item.item_id,
          rating: item.rating,
          updated_at: item.updated_at,
          // 애니메이션 필드
          ...(item.type === 'anime' ? {
            anime_id: item.item_id,
            title_romaji: item.item_title,
            title_english: item.item_title,
            title_native: item.item_title_native,
            title_korean: item.item_title_korean,
            image_url: item.item_image,
            year: item.item_year
          } : {}),
          // 캐릭터 필드
          ...(item.type === 'character' ? {
            character_id: item.item_id,
            character_name: item.item_title,
            character_name_korean: item.item_title_korean,
            character_name_native: item.item_title_native,
            character_image: item.item_image,
            anime_id: item.anime_id,
            anime_title_korean: item.anime_title_korean,
            anime_title_native: item.anime_title_native,
            anime_title: item.anime_title
          } : {})
        };

        // Debug: log character items with anime info
        if (item.type === 'character') {
          console.log('[WriteReviews] Character item:', {
            name: processed.character_name,
            anime_id: processed.anime_id,
            anime_title: processed.anime_title
          });
        }

        return processed;
      });

      console.log('[WriteReviews] Processed items:', items.length);

      // 이미 백엔드에서 정렬되어 옴 (popularity + 랜덤성)
      if (resetOffset) {
        setAllItems(items);
        setOffset(50);
      } else {
        setAllItems(prev => [...prev, ...items]);
        setOffset(prev => prev + items.length);
      }

      // Check if there are more items
      setHasMore(items.length === 50);

      setReviewsLoading(false);
      setLoading(false);
      console.log('[WriteReviews] Data loading complete');
    } catch (err) {
      console.error('[WriteReviews] Failed to load data:', err);
      console.error('[WriteReviews] Error details:', err.response?.data || err.message);
      console.error('[WriteReviews] Error status:', err.response?.status);
      setLoading(false);
      setReviewsLoading(false);
    }
  };

  const handleStartEdit = async (item, existingContent = '', currentRating = 0) => {
    setEditingId(item.id);
    setEditRating(currentRating);

    // Load existing review if not already loaded and no content provided
    if (!existingContent && !reviews[item.id]) {
      try {
        let myReview;
        if (item.type === 'anime') {
          myReview = await reviewService.getMyReview(item.itemId);
        } else {
          myReview = await characterReviewService.getMyReview(item.itemId);
        }

        if (myReview && myReview.content && myReview.content.trim()) {
          setReviews(prev => ({
            ...prev,
            [item.id]: myReview
          }));
          setEditContent(myReview.content);
        } else {
          setEditContent('');
        }
      } catch (err) {
        // No review exists, start with empty content
        setEditContent('');
      }
    } else {
      setEditContent(existingContent);
    }
  };

  const handleSaveAnimeReview = async (animeId) => {
    const trimmedContent = editContent.trim();

    if (!trimmedContent) {
      alert('리뷰 내용을 입력해주세요.');
      return;
    }

    if (trimmedContent.length < 10) {
      alert('리뷰는 최소 10자 이상 작성해야 합니다.');
      return;
    }

    if (trimmedContent.length > 5000) {
      alert('리뷰는 최대 5000자까지 작성할 수 있습니다.');
      return;
    }

    if (!editRating || editRating === 0) {
      alert('평점을 선택해주세요.');
      return;
    }

    try {
      // 평점 업데이트
      await ratingService.rateAnime(animeId, {
        rating: editRating,
        status: 'RATED'
      });

      // 리뷰 저장 또는 업데이트
      const existingReview = reviews[`anime_${animeId}`];
      let savedReview;

      if (existingReview) {
        savedReview = await reviewService.updateReview(existingReview.id, {
          content: trimmedContent
        });
      } else {
        savedReview = await reviewService.createReview({
          anime_id: animeId,
          content: trimmedContent
        });
      }

      // Update only the changed review (only if there's content)
      if (savedReview && savedReview.content && savedReview.content.trim()) {
        setReviews(prev => ({
          ...prev,
          [`anime_${animeId}`]: savedReview
        }));
      }

      // Update the rating in the items list
      setAllItems(prev => prev.map(item =>
        item.id === `anime_${animeId}`
          ? { ...item, rating: editRating, updated_at: new Date().toISOString() }
          : item
      ));

      // Mark as just completed
      setJustCompleted(prev => new Set([...prev, `anime_${animeId}`]));

      // Remove from justCompleted after 3 seconds (animation duration)
      setTimeout(() => {
        setJustCompleted(prev => {
          const newSet = new Set(prev);
          newSet.delete(`anime_${animeId}`);
          return newSet;
        });
      }, 3000);

      // Reload stats to reflect the new review
      loadStats();

      setEditingId(null);
      setEditContent('');
      setEditRating(0);
    } catch (err) {
      console.error('Failed to save review:', err);
      const errorMessage = err.response?.data?.detail || '리뷰 저장에 실패했습니다.';
      alert(errorMessage);
    }
  };

  const handleSaveCharacterReview = async (characterId) => {
    const trimmedContent = editContent.trim();

    if (!trimmedContent) {
      alert('리뷰 내용을 입력해주세요.');
      return;
    }

    if (trimmedContent.length < 10) {
      alert('리뷰는 최소 10자 이상 작성해야 합니다.');
      return;
    }

    if (trimmedContent.length > 5000) {
      alert('리뷰는 최대 5000자까지 작성할 수 있습니다.');
      return;
    }

    if (!editRating || editRating === 0) {
      alert('평점을 선택해주세요.');
      return;
    }

    try {
      // 평점 업데이트
      await characterService.rateCharacter(characterId, editRating);

      // 리뷰 저장 또는 업데이트
      const existingReview = reviews[`character_${characterId}`];
      let savedReview;

      if (existingReview) {
        savedReview = await characterReviewService.updateReview(existingReview.id, {
          content: trimmedContent
        });
      } else {
        savedReview = await characterReviewService.createReview({
          character_id: characterId,
          content: trimmedContent
        });
      }

      // Update only the changed review (only if there's content)
      if (savedReview && savedReview.content && savedReview.content.trim()) {
        setReviews(prev => ({
          ...prev,
          [`character_${characterId}`]: savedReview
        }));
      }

      // Update the rating in the items list
      setAllItems(prev => prev.map(item =>
        item.id === `character_${characterId}`
          ? { ...item, rating: editRating, updated_at: new Date().toISOString() }
          : item
      ));

      // Mark as just completed
      setJustCompleted(prev => new Set([...prev, `character_${characterId}`]));

      // Remove from justCompleted after 3 seconds (animation duration)
      setTimeout(() => {
        setJustCompleted(prev => {
          const newSet = new Set(prev);
          newSet.delete(`character_${characterId}`);
          return newSet;
        });
      }, 3000);

      // Reload stats to reflect the new review
      loadStats();

      setEditingId(null);
      setEditContent('');
      setEditRating(0);
    } catch (err) {
      console.error('Failed to save review:', err);
      const errorMessage = err.response?.data?.detail || '리뷰 저장에 실패했습니다.';
      alert(errorMessage);
    }
  };

  const handleSaveReview = async (item) => {
    if (item.type === 'anime') {
      await handleSaveAnimeReview(item.itemId);
    } else {
      await handleSaveCharacterReview(item.itemId);
    }
  };

  const handleCancel = () => {
    setEditingId(null);
    setEditContent('');
    setEditRating(0);
  };

  const getImageUrl = (imageUrl, itemType = 'anime', characterId = null) => {
    if (!imageUrl) return '/placeholder-anime.svg';

    // For character images, use the character image helper
    if (itemType === 'character') {
      return getCharacterImageUrl(characterId, imageUrl);
    }

    // For anime images
    if (imageUrl.startsWith('http')) return imageUrl;
    // Use covers_large for better quality
    const processedUrl = imageUrl.includes('/covers/')
      ? imageUrl.replace('/covers/', '/covers_large/')
      : imageUrl;
    return `${IMAGE_BASE_URL}${processedUrl}`;
  };

  const getFilteredItems = () => {
    // Filter out items that already have reviews, except those just completed
    const itemsWithoutReviews = allItems.filter(item => !reviews[item.id] || justCompleted.has(item.id));

    if (filter === 'all') return itemsWithoutReviews;
    return itemsWithoutReviews.filter(item => item.type === filter);
  };

  const getFilteredStats = () => {
    // Use backend stats (pre-calculated, not real-time)
    if (filter === 'all') {
      return {
        reviewed: stats.total.reviewed,
        remaining: stats.total.pending
      };
    } else if (filter === 'anime') {
      return {
        reviewed: stats.anime.reviewed,
        remaining: stats.anime.pending
      };
    } else if (filter === 'character') {
      return {
        reviewed: stats.character.reviewed,
        remaining: stats.character.pending
      };
    }
  };

  const filteredItems = getFilteredItems();
  const currentStats = getFilteredStats();
  const hasStats = stats.total.reviewed !== undefined;

  return (
    <div className="min-h-screen pt-10 md:pt-12 bg-transparent">

      <div className="max-w-[1180px] mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8">
        {/* Filter Toggle and Stats - Always visible */}
        <div className="mb-12 relative">
          {/* Filter Toggle */}
          <div className="flex gap-2 w-fit">
            <button
              onClick={() => setFilter('all')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${filter === 'all'
                ? 'bg-[#3797F0] text-white font-semibold'
                : 'text-gray-600 hover:text-gray-900'
                }`}
            >
              {language === 'ko' ? '모두' : language === 'ja' ? 'すべて' : 'All'}
            </button>
            <button
              onClick={() => setFilter('anime')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${filter === 'anime'
                ? 'bg-[#3797F0] text-white font-semibold'
                : 'text-gray-600 hover:text-gray-900'
                }`}
            >
              {language === 'ko' ? '애니' : language === 'ja' ? 'アニメ' : 'Anime'}
            </button>
            <button
              onClick={() => setFilter('character')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${filter === 'character'
                ? 'bg-[#3797F0] text-white font-semibold'
                : 'text-gray-600 hover:text-gray-900'
                }`}
            >
              {language === 'ko' ? '캐릭터' : language === 'ja' ? 'キャラクター' : 'Character'}
            </button>
          </div>

          {/* Stats - Show skeleton or actual data */}
          <div className="absolute left-1/2 top-0 -translate-x-1/2 flex gap-3">
            {hasStats ? (
              <>
                <div className="bg-white px-4 py-2.5 rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] hover:shadow-[0_4px_16px_rgba(0,0,0,0.12)] transition-shadow min-w-[100px]">
                  <div className="text-xs text-gray-600 mb-0.5 text-center">{language === 'ko' ? '작성완료' : language === 'ja' ? '作成完了' : 'Completed'}</div>
                  <div className="text-lg font-bold text-gray-800 text-center tabular-nums">{currentStats.reviewed.toLocaleString()}</div>
                </div>
                <div className="bg-white px-4 py-2.5 rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] hover:shadow-[0_4px_16px_rgba(0,0,0,0.12)] transition-shadow min-w-[100px]">
                  <div className="text-xs text-gray-600 mb-0.5 text-center">{language === 'ko' ? '작성대기' : language === 'ja' ? '作成待ち' : 'Pending'}</div>
                  <div className="text-lg font-bold text-gray-800 text-center tabular-nums">{currentStats.remaining.toLocaleString()}</div>
                </div>
              </>
            ) : (
              <>
                {[1, 2].map((i) => (
                  <div key={i} className="bg-white rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] px-4 py-2.5 animate-pulse min-w-[100px]">
                    <div className="h-3 w-16 bg-gray-200 rounded mb-1 mx-auto"></div>
                    <div className="h-5 w-12 bg-gray-200 rounded mx-auto"></div>
                  </div>
                ))}
              </>
            )}
          </div>
        </div>

        {/* Review Cards Grid - Show skeleton or actual cards */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 auto-rows-max items-start">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="bg-white rounded-xl shadow-[0_2px_12px_rgba(0,0,0,0.08)] border border-gray-200 animate-pulse overflow-hidden self-start">
                <div className="flex items-start">
                  <div className="w-32 h-48 bg-gray-200 flex-shrink-0"></div>
                  <div className="flex-1 p-6 flex flex-col">
                    <div className="h-5 w-3/4 bg-gray-200 rounded mb-2"></div>
                    <div className="h-4 w-1/2 bg-gray-200 rounded mb-3"></div>
                    <div className="h-10 w-full bg-gray-200 rounded"></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 auto-rows-max items-start">
            {filteredItems.map((item) => {
              const hasReview = reviews[item.id];
              const isEditing = editingId === item.id;
              const isJustCompleted = justCompleted.has(item.id);

              return (
                <div
                  key={item.id}
                  className="rounded-xl transition-all duration-500 ease-out self-start"
                  style={{
                    background: isJustCompleted
                      ? 'linear-gradient(135deg, #FFD700 0%, #FFA500 50%, #FF8C00 100%)'
                      : 'transparent',
                    padding: isJustCompleted ? '2px' : '0',
                    boxShadow: isJustCompleted
                      ? '0 4px 20px rgba(225, 48, 108, 0.3)'
                      : undefined
                  }}
                >
                  <div className={`bg-white rounded-xl shadow-[0_2px_12px_rgba(0,0,0,0.08)] hover:shadow-[0_4px_16px_rgba(0,0,0,0.12)] transition-all duration-500 ease-out overflow-hidden relative group ${!isJustCompleted ? 'border border-gray-200' : ''
                    }`}>
                    <div className="flex items-start relative">
                      {/* 작성완료 뱃지 */}
                      {isJustCompleted && (
                        <div className="absolute top-2 right-2 z-10">
                          <span className="px-3 py-1 text-white text-xs font-bold rounded-full shadow-lg" style={{
                            background: 'linear-gradient(135deg, #FFD700 0%, #FFA500 50%, #FF8C00 100%)'
                          }}>
                            {language === 'ko' ? '작성완료' : language === 'ja' ? '作成完了' : 'Completed'}
                          </span>
                        </div>
                      )}

                      <Link
                        to={item.type === 'anime' ? `/anime/${item.itemId}` : `/character/${item.itemId}`}
                        className="flex-shrink-0 cursor-pointer overflow-hidden"
                      >
                        <img
                          src={getImageUrl(
                            item.type === 'anime' ? item.image_url : item.character_image,
                            item.type,
                            item.type === 'character' ? item.character_id : null
                          )}
                          alt={item.type === 'anime' ? getAnimeTitle(item) : (language === 'ko' && item.character_name_native ? item.character_name_native : item.character_name)}
                          className="w-32 h-48 object-cover object-top group-hover:scale-110 transition-transform duration-[1500ms]"
                          onError={(e) => {
                            e.target.src = '/placeholder-anime.svg';
                          }}
                        />
                      </Link>

                      <div className="flex-1 min-w-0 p-6 flex flex-col transition-all duration-500 ease-in-out">
                        {/* Title with Badge */}
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-semibold text-lg">
                            <Link
                              to={item.type === 'anime' ? `/anime/${item.itemId}` : `/character/${item.itemId}`}
                              className="text-gray-900 hover:text-[#3797F0] transition-colors hover:underline cursor-pointer"
                            >
                              {item.type === 'anime' ? (
                                language === 'ko' ? (
                                  <span>
                                    {item.title_korean || item.title_romaji || item.title_english}
                                    {item.title_korean && (item.title_romaji || item.title_english) && (
                                      <span className="text-xs text-gray-400 font-normal ml-1.5">({item.title_romaji || item.title_english})</span>
                                    )}
                                  </span>
                                ) : language === 'ja' ? (
                                  <span>
                                    {item.title_native || item.title_romaji || item.title_english}
                                    {item.title_native && (item.title_romaji || item.title_english) && (
                                      <span className="text-xs text-gray-400 font-normal ml-1.5">({item.title_romaji || item.title_english})</span>
                                    )}
                                  </span>
                                ) : (
                                  item.title_romaji || item.title_english || item.title_korean
                                )
                              ) : language === 'ko' ? (
                                <span>
                                  {item.character_name_korean || item.character_name_native || item.character_name}
                                  {(item.character_name_korean || item.character_name_native) && item.character_name && (
                                    <span className="text-xs text-gray-400 font-normal ml-1.5">({item.character_name})</span>
                                  )}
                                </span>
                              ) : language === 'ja' ? (
                                <span>
                                  {item.character_name_native || item.character_name}
                                  {item.character_name_native && item.character_name && (
                                    <span className="text-xs text-gray-400 font-normal ml-1.5">({item.character_name})</span>
                                  )}
                                </span>
                              ) : (
                                item.character_name || item.character_name_native
                              )}
                            </Link>
                          </h3>
                          <span className={`px-2 py-0.5 rounded text-xs font-medium flex-shrink-0 ${item.type === 'anime'
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-pink-100 text-pink-800'
                            }`}>
                            {item.type === 'anime' ? (language === 'ko' ? '애니' : language === 'ja' ? 'アニメ' : 'Anime') : (language === 'ko' ? '캐릭터' : language === 'ja' ? 'キャラクター' : 'Character')}
                          </span>
                        </div>

                        {/* Character's Anime */}
                        {item.type === 'character' && (item.anime_title_korean || item.anime_title_native || item.anime_title) && (
                          <p className="text-xs text-gray-500 mb-1">
                            from:{' '}
                            {item.anime_id ? (
                              <Link
                                to={`/anime/${item.anime_id}`}
                                className="hover:text-[#3797F0] hover:underline transition-colors"
                              >
                                {language === 'ko' ? (
                                  <>
                                    {item.anime_title_korean || item.anime_title}
                                    {item.anime_title_korean && item.anime_title && (
                                      <span className="text-[10px] text-gray-400 font-normal ml-1">({item.anime_title})</span>
                                    )}
                                  </>
                                ) : language === 'ja' ? (
                                  <>
                                    {item.anime_title_native || item.anime_title}
                                    {item.anime_title_native && item.anime_title && (
                                      <span className="text-[10px] text-gray-400 font-normal ml-1">({item.anime_title})</span>
                                    )}
                                  </>
                                ) : (
                                  item.anime_title
                                )}
                              </Link>
                            ) : (
                              language === 'ko' ? (
                                <>
                                  {item.anime_title_korean || item.anime_title}
                                  {item.anime_title_korean && item.anime_title && (
                                    <span className="text-[10px] text-gray-400 font-normal ml-1">({item.anime_title})</span>
                                  )}
                                </>
                              ) : language === 'ja' ? (
                                <>
                                  {item.anime_title_native || item.anime_title}
                                  {item.anime_title_native && item.anime_title && (
                                    <span className="text-[10px] text-gray-400 font-normal ml-1">({item.anime_title})</span>
                                  )}
                                </>
                              ) : (
                                item.anime_title
                              )
                            )}
                          </p>
                        )}

                        {!isEditing ? (
                          <div className="transition-all duration-300 ease-in-out">
                            <div className="flex items-center gap-3 text-sm text-gray-500 mb-3">
                              <div className="flex items-center">
                                <StarRating rating={item.rating || 0} readonly size="sm" showNumber={false} />
                              </div>
                              {item.type === 'anime' && item.year && <span>• {item.year}</span>}
                            </div>
                            {hasReview ? (
                              <>
                                <p className="text-sm text-gray-700 mb-3 line-clamp-2">
                                  {hasReview.content}
                                </p>
                                <button
                                  onClick={() => handleStartEdit(item, hasReview.content, item.rating)}
                                  className="text-sm text-[#3797F0] hover:text-[#2C7CB8]"
                                >
                                  {language === 'ko' ? '수정' : language === 'ja' ? '編集' : 'Edit'}
                                </button>
                              </>
                            ) : (
                              <button
                                onClick={() => handleStartEdit(item, '', item.rating)}
                                className="text-sm text-gray-500 hover:text-gray-700 border border-gray-300 px-4 py-2 rounded hover:border-gray-400 transition-all group-hover:bg-blue-50 group-hover:text-blue-600 group-hover:border-blue-300"
                              >
                                {language === 'ko' ? '리뷰 작성하기' : language === 'ja' ? 'レビュー作成' : 'Write Review'}
                              </button>
                            )}
                          </div>
                        ) : (
                          <div className="space-y-3 animate-fadeIn">
                            {/* 평점 선택 */}
                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-2">
                                {language === 'ko' ? '평점 (클릭하여 수정 가능)' : language === 'ja' ? '評価 (クリックして変更)' : 'Rating (Click to edit)'}
                              </label>
                              <StarRating
                                rating={editRating}
                                onRatingChange={setEditRating}
                                readonly={false}
                                size="lg"
                                showNumber={true}
                              />
                            </div>

                            {/* 리뷰 입력 */}
                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-2">
                                {language === 'ko' ? '리뷰' : language === 'ja' ? 'レビュー' : 'Review'}
                              </label>
                              <textarea
                                value={editContent}
                                onChange={(e) => setEditContent(e.target.value)}
                                placeholder={language === 'ko' ? '리뷰를 작성하세요...' : language === 'ja' ? 'レビューを作成...' : 'Write your review...'}
                                className="w-full text-sm border border-gray-300 rounded px-3 py-2 focus:outline-none focus:border-blue-500 resize-none"
                                rows="4"
                                autoFocus
                              />
                            </div>
                            <div className="flex gap-2">
                              <button
                                onClick={() => handleSaveReview(item)}
                                disabled={!editContent.trim() || !editRating}
                                className="text-sm px-4 py-2 rounded disabled:opacity-50 transition-colors"
                                style={{ backgroundColor: '#3797F0', color: 'white', fontWeight: '600' }}
                                onMouseEnter={(e) => !e.target.disabled && (e.target.style.backgroundColor = '#1877F2')}
                                onMouseLeave={(e) => !e.target.disabled && (e.target.style.backgroundColor = '#3797F0')}
                              >
                                {language === 'ko' ? '저장' : language === 'ja' ? '保存' : 'Save'}
                              </button>
                              <button
                                onClick={handleCancel}
                                className="text-sm bg-gray-200 hover:bg-gray-300 text-gray-700 px-4 py-2 rounded transition-colors"
                              >
                                {language === 'ko' ? '취소' : language === 'ja' ? 'キャンセル' : 'Cancel'}
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}

            {/* Loading more indicator */}
            {loadingMore && (
              <div className="text-center py-8">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                <p className="text-gray-500 mt-2">{language === 'ko' ? '더 불러오는 중...' : language === 'ja' ? '読み込み中...' : 'Loading more...'}</p>
              </div>
            )}

            {/* No more items */}
            {!hasMore && filteredItems.length > 0 && (
              <div className="text-center py-8 text-gray-500">
                {language === 'ko' ? '모든 항목을 불러왔습니다' : language === 'ja' ? 'すべての項目を読み込みました' : 'All items loaded'}
              </div>
            )}

            {filteredItems.length === 0 && !loading && (
              <div className="text-center py-16">
                <p className="text-gray-600">
                  {filter === 'all'
                    ? (language === 'ko' ? '아직 평가한 애니나 캐릭터가 없습니다.' : language === 'ja' ? 'まだ評価したアニメやキャラクターがありません。' : 'No rated anime or characters yet.')
                    : filter === 'anime'
                      ? (language === 'ko' ? '아직 평가한 애니가 없습니다.' : language === 'ja' ? 'まだ評価したアニメがありません。' : 'No rated anime yet.')
                      : (language === 'ko' ? '아직 평가한 캐릭터가 없습니다.' : language === 'ja' ? 'まだ評価したキャラクターがありません。' : 'No rated characters yet.')
                  }
                </p>
                <p className="text-sm text-gray-500 mt-2">
                  {filter === 'all'
                    ? (language === 'ko' ? '애니나 캐릭터를 평가하면 리뷰를 작성할 수 있습니다.' : language === 'ja' ? 'アニメやキャラクターを評価するとレビューを作成できます。' : 'Rate anime or characters to write reviews.')
                    : filter === 'anime'
                      ? (language === 'ko' ? '애니를 평가하면 리뷰를 작성할 수 있습니다.' : language === 'ja' ? 'アニメを評価するとレビューを作成できます。' : 'Rate anime to write reviews.')
                      : (language === 'ko' ? '캐릭터를 평가하면 리뷰를 작성할 수 있습니다.' : language === 'ja' ? 'キャラクターを評価するとレビューを作成できます。' : 'Rate characters to write reviews.')
                  }
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
