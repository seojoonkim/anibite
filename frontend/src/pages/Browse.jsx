import { useState, useEffect, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { animeService } from '../services/animeService';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { usePrefetch } from '../hooks/usePrefetch';
import StarRating from '../components/common/StarRating';
import { API_BASE_URL, IMAGE_BASE_URL } from '../config/api';
import api from '../services/api';

// Character card component with proper image loading
function CharacterSearchCard({ character, language }) {
  const [imageError, setImageError] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);

  const imageUrl = character.id ? `${API_BASE_URL}/api/images/characters/${character.id}.jpg` : null;

  return (
    <Link
      to={`/character/${character.id}`}
      className="bg-white rounded-lg shadow-sm hover:shadow-md transition-all overflow-hidden group"
    >
      <div className="aspect-[3/4] bg-gray-200 overflow-hidden relative">
        {/* Always show placeholder first, hide when image loads successfully */}
        {(!imageLoaded || imageError || !imageUrl) && (
          <img
            src="/placeholder-anime.svg"
            alt=""
            className="w-full h-full object-cover absolute inset-0"
          />
        )}
        {imageUrl && !imageError && (
          <img
            src={imageUrl}
            alt={character.name_korean || character.name_full}
            className={`w-full h-full object-cover group-hover:scale-105 transition-transform duration-200 ${imageLoaded ? 'opacity-100' : 'opacity-0'}`}
            onLoad={() => setImageLoaded(true)}
            onError={() => {
              setImageError(true);
              setImageLoaded(false);
            }}
          />
        )}
      </div>
      <div className="p-2">
        <div className="font-medium text-sm text-gray-900 truncate">
          {character.name_korean || character.name_full}
        </div>
        {character.anime_title_korean && (
          <div className="text-xs text-gray-500 truncate">
            {character.anime_title_korean}
          </div>
        )}
        {character.rating && (
          <div className="flex items-center gap-1 mt-1">
            <svg className="w-3 h-3 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
            <span className="text-xs text-gray-600">{character.rating.toFixed(1)}</span>
          </div>
        )}
      </div>
    </Link>
  );
}

export default function Browse() {
  const { user } = useAuth();
  const { t, getAnimeTitle, language } = useLanguage();
  const { handleAnimeMouseEnter, handleMouseLeave } = usePrefetch();
  const [animeList, setAnimeList] = useState([]);
  const [characterList, setCharacterList] = useState([]);
  const [initialLoading, setInitialLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('');
  const [sort, setSort] = useState('popularity_desc');
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [searchMode, setSearchMode] = useState(false);
  const observerRef = useRef(null);
  const loadMoreTriggerRef = useRef(null);

  // Debounce search term (300ms delay)
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm);
    }, 300);

    return () => clearTimeout(timer);
  }, [searchTerm]);

  // Perform search when debounced term or sort changes
  useEffect(() => {
    if (debouncedSearchTerm.trim()) {
      performSearch(debouncedSearchTerm);
    } else {
      loadAnime(true);
    }
  }, [debouncedSearchTerm, sort]);

  // Unified search function
  const performSearch = async (query) => {
    if (!query || !query.trim()) {
      setSearchMode(false);
      loadAnime(true);
      return;
    }

    try {
      setInitialLoading(true);
      setSearchMode(true);
      setError('');

      const response = await api.get('/api/search', {
        params: { q: query.trim(), sort, limit: 30 }
      });

      setAnimeList(response.data.anime || []);
      setCharacterList(response.data.characters || []);
      setHasMore(false);
      setInitialLoading(false);
    } catch (err) {
      console.error('Search failed:', err);
      setError(language === 'ko' ? '검색에 실패했습니다.' : language === 'ja' ? '検索に失敗しました。' : 'Search failed.');
      setInitialLoading(false);
    }
  };

  // Intersection Observer for infinite scroll
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !initialLoading && !loadingMore) {
          handleLoadMore();
        }
      },
      { threshold: 0.1, rootMargin: '200px' }
    );

    if (loadMoreTriggerRef.current) {
      observer.observe(loadMoreTriggerRef.current);
    }

    observerRef.current = observer;

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [hasMore, initialLoading, loadingMore, page]);

  const loadAnime = async (resetList = false) => {
    try {
      if (resetList) {
        setInitialLoading(true);
        setSearchMode(false);
        setCharacterList([]);
      } else {
        setLoadingMore(true);
      }
      setError('');

      const currentPage = resetList ? 1 : page;
      const params = {
        page: currentPage,
        limit: 20,
        sort: sort,
      };

      const data = await animeService.getAnimeList(params);

      if (resetList) {
        setAnimeList(data.items || []);
        setPage(1);
      } else {
        setAnimeList((prev) => [...prev, ...(data.items || [])]);
      }

      setHasMore(data.has_more || false);
      setInitialLoading(false);
      setLoadingMore(false);
    } catch (err) {
      console.error('Failed to load anime:', err);
      setError('애니메이션을 불러오는데 실패했습니다.');
      setInitialLoading(false);
      setLoadingMore(false);
    }
  };

  const handleSortChange = (value) => {
    setSort(value);
    setPage(1);
  };

  const handleClearSearch = () => {
    setSearchTerm('');
    setDebouncedSearchTerm('');
    setSearchMode(false);
    setCharacterList([]);
  };

  const handleLoadMore = () => {
    setPage((prev) => prev + 1);
    loadAnime(false);
  };

  const getImageUrl = (imageUrl) => {
    if (!imageUrl) return '/placeholder-anime.svg';
    if (imageUrl.startsWith('http')) return imageUrl;
    // Use covers_large for better quality
    const processedUrl = imageUrl.includes('/covers/')
      ? imageUrl.replace('/covers/', '/covers_large/')
      : imageUrl;
    return `${IMAGE_BASE_URL}${processedUrl}`;
  };

  const getStatusBadge = (status) => {
    const badges = {
      'Currently Airing': { text: '방영중', color: 'bg-green-100 text-green-800' },
      'Finished Airing': { text: '완결', color: 'bg-blue-100 text-blue-800' },
      'Not yet aired': { text: '미방영', color: 'bg-yellow-100 text-yellow-800' },
    };
    return badges[status] || { text: status, color: 'bg-gray-100 text-gray-800' };
  };

  return (
    <div className="min-h-screen pt-10 md:pt-12 bg-transparent">

      <div className="max-w-[1180px] mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8">
        {/* Search Bar - Sort on left, search input (real-time search) */}
        <div className="bg-white rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] p-4 mb-6">
          <div className="flex items-center gap-2">
            {/* Sort Dropdown */}
            <select
              value={sort}
              onChange={(e) => handleSortChange(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 text-sm bg-white min-w-[100px]"
            >
              <option value="popularity_desc">{t('sortPopularity')}</option>
              <option value="rating_desc">{t('sortRatingDesc')}</option>
              <option value="rating_asc">{t('sortRatingAsc')}</option>
              <option value="title_asc">{t('sortTitle')}</option>
            </select>

            {/* Search Input - Real-time search */}
            <div className="flex-1 relative">
              <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder={language === 'ko' ? '애니메이션, 캐릭터 검색..' : language === 'ja' ? 'アニメ、キャラクターを検索..' : 'Search anime, characters...'}
                className="w-full pl-10 pr-10 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 text-sm"
              />
              {searchTerm && (
                <button
                  type="button"
                  onClick={handleClearSearch}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {/* Character Results - Only show when searching */}
        {searchMode && characterList.length > 0 && (
          <div className="mb-6">
            <h2 className="text-lg font-semibold text-gray-800 mb-3">
              {language === 'ko' ? '캐릭터' : language === 'ja' ? 'キャラクター' : 'Characters'} ({characterList.length})
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
              {characterList.map((character) => (
                <CharacterSearchCard key={character.id} character={character} language={language} />
              ))}
            </div>
          </div>
        )}

        {/* Anime Results Header - Only show when searching */}
        {searchMode && animeList.length > 0 && (
          <h2 className="text-lg font-semibold text-gray-800 mb-3">
            {language === 'ko' ? '애니메이션' : language === 'ja' ? 'アニメ' : 'Anime'} ({animeList.length})
          </h2>
        )}

        {/* Anime List - Table Format */}
        {initialLoading && animeList.length === 0 && characterList.length === 0 ? (
          <div className="flex justify-center items-center h-64">
            <div className="text-xl text-gray-600">{t('loading')}</div>
          </div>
        ) : animeList.length === 0 && characterList.length === 0 ? (
          <div className="flex justify-center items-center h-64">
            <div className="text-xl text-gray-600">{t('noResults')}</div>
          </div>
        ) : animeList.length > 0 ? (
          <>
            <div className="bg-white rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] overflow-hidden mb-8">
              <div className="overflow-x-auto">
                <table className="w-full">
                  {/* Table Header */}
                  <thead className="bg-gradient-to-r from-gray-50 to-gray-100 border-b-2 border-gray-200">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                        {language === 'ko' ? '포스터' : language === 'ja' ? 'ポスター' : 'Poster'}
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                        {language === 'ko' ? '제목' : language === 'ja' ? 'タイトル' : 'Title'}
                      </th>
                      <th className="hidden md:table-cell px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                        {language === 'ko' ? '상태' : language === 'ja' ? 'ステータス' : 'Status'}
                      </th>
                      <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider">
                        {language === 'ko' ? '연도' : language === 'ja' ? '年' : 'Year'}
                      </th>
                      <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider">
                        {language === 'ko' ? '화수' : language === 'ja' ? '話数' : 'Episodes'}
                      </th>
                      <th className="hidden md:table-cell px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                        {language === 'ko' ? '장르' : language === 'ja' ? 'ジャンル' : 'Genres'}
                      </th>
                      <th className="hidden md:table-cell px-4 py-3 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider">
                        {language === 'ko' ? '평점' : language === 'ja' ? '評価' : 'Rating'}
                      </th>
                    </tr>
                  </thead>

                  {/* Table Body */}
                  <tbody className="divide-y divide-gray-200">
                    {animeList.map((anime) => {
                      const statusBadge = getStatusBadge(anime.airing_status);
                      const titles = getAnimeTitle(anime, true);

                      return (
                        <tr
                          key={anime.id}
                          className="hover:bg-gray-50 transition-colors"
                          onMouseEnter={() => handleAnimeMouseEnter(anime.id, user)}
                          onMouseLeave={handleMouseLeave}
                        >
                          {/* Poster */}
                          <td className="px-4 py-2">
                            <Link to={`/anime/${anime.id}`}>
                              <div className="w-16 h-20 bg-gray-200 rounded overflow-hidden shadow-[0_2px_12px_rgba(0,0,0,0.08)]">
                                <img
                                  src={getImageUrl(anime.cover_image_url)}
                                  alt={getAnimeTitle(anime)}
                                  className="w-full h-full object-cover hover:scale-110 transition-transform duration-200"
                                  onError={(e) => {
                                    e.target.src = '/placeholder-anime.svg';
                                  }}
                                />
                              </div>
                            </Link>
                          </td>

                          {/* Title */}
                          <td className="px-4 py-2">
                            <Link to={`/anime/${anime.id}`} className="block">
                              <div className="font-semibold text-gray-900 hover:text-[#5BB5F5] transition-colors">
                                {titles.primary}
                              </div>
                              {titles.secondary && (
                                <div className="text-xs text-gray-500 mt-0.5">
                                  {titles.secondary}
                                </div>
                              )}
                            </Link>
                          </td>

                          {/* Status */}
                          <td className="hidden md:table-cell px-4 py-2">
                            {anime.status && (
                              <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${statusBadge.color}`}>
                                {statusBadge.text}
                              </span>
                            )}
                          </td>

                          {/* Year */}
                          <td className="px-4 py-2 text-center text-sm text-gray-700">
                            {anime.season_year || '-'}
                          </td>

                          {/* Episodes */}
                          <td className="px-4 py-2 text-center text-sm text-gray-700">
                            {anime.episodes ? `${anime.episodes}화` : '-'}
                          </td>

                          {/* Genres */}
                          <td className="hidden md:table-cell px-4 py-2">
                            <div className="flex flex-wrap gap-1">
                              {anime.genres && anime.genres.length > 0 ? (
                                anime.genres.slice(0, 3).map((genre, idx) => (
                                  <span
                                    key={idx}
                                    className="inline-block px-2 py-0.5 bg-gray-100 text-gray-700 rounded text-xs"
                                  >
                                    {genre}
                                  </span>
                                ))
                              ) : (
                                <span className="text-gray-400 text-xs">-</span>
                              )}
                            </div>
                          </td>

                          {/* Rating */}
                          <td className="hidden md:table-cell px-4 py-3 text-center">
                            {anime.site_rating_count > 0 ? (
                              <div>
                                <div className="flex items-center justify-center gap-1">
                                  <svg className="w-4 h-4" fill="#EAB308" viewBox="0 0 20 20">
                                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                  </svg>
                                  <span className="font-bold text-gray-900">
                                    {anime.site_average_rating.toFixed(1)}
                                  </span>
                                </div>
                                <div className="text-xs text-gray-500 mt-0.5">
                                  {anime.site_rating_count.toLocaleString()}개
                                </div>
                              </div>
                            ) : (
                              <span className="text-xs text-gray-400">{t('noRating')}</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Infinite scroll trigger - only when not in search mode */}
            {!searchMode && (
              <div ref={loadMoreTriggerRef} className="h-20 flex items-center justify-center">
                {loadingMore && (
                  <div className="text-gray-500 text-sm">
                    {language === 'ko' ? '로딩 중...' : language === 'ja' ? '読み込み中...' : 'Loading...'}
                  </div>
                )}
                {!initialLoading && !loadingMore && !hasMore && animeList.length > 0 && (
                  <div className="text-gray-400 text-sm">
                    {language === 'ko' ? '모든 애니메이션을 불러왔습니다' : language === 'ja' ? 'すべてのアニメを読み込みました' : 'All anime loaded'}
                  </div>
                )}
              </div>
            )}
          </>
        ) : null}
      </div>
    </div>
  );
}
