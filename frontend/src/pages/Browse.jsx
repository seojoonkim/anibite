import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { animeService } from '../services/animeService';
import { useLanguage } from '../context/LanguageContext';
import Navbar from '../components/common/Navbar';
import StarRating from '../components/common/StarRating';
import { API_BASE_URL, IMAGE_BASE_URL } from '../config/api';

export default function Browse() {
  const { t, getAnimeTitle, language } = useLanguage();
  const [animeList, setAnimeList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  // 초기 검색어를 비워두고 인기순으로 정렬하여 표시
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    genre: '',
    year: '',
    status: '',
    sort: 'popularity_desc',
  });
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  useEffect(() => {
    loadAnime(true);
  }, [searchTerm, filters]);

  const loadAnime = async (resetList = false) => {
    try {
      setLoading(true);
      setError('');

      const currentPage = resetList ? 1 : page;
      const params = {
        page: currentPage,
        limit: 50,
        search: searchTerm || undefined,
        genre: filters.genre || undefined,
        year: filters.year || undefined,
        status: filters.status || undefined,
        sort: filters.sort,
      };

      const data = await animeService.getAnimeList(params);

      if (resetList) {
        setAnimeList(data.items || []);
        setPage(1);
      } else {
        setAnimeList((prev) => [...prev, ...(data.items || [])]);
      }

      setHasMore(data.has_more || false);
      setLoading(false);
    } catch (err) {
      console.error('Failed to load anime:', err);
      setError('애니메이션을 불러오는데 실패했습니다.');
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    loadAnime(true);
  };

  const handleFilterChange = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setPage(1);
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
    <div className="min-h-screen pt-0 md:pt-16 bg-transparent">
      <Navbar />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8">
        {/* Search and Filters */}
        <div className="bg-white rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] p-6 mb-8">
          <form onSubmit={handleSearch} className="mb-4">
            <div className="flex gap-2">
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder={t('searchPlaceholder')}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 text-sm"
              />
              <button
                type="submit"
                className="bg-gradient-to-r from-cyan-400 to-blue-400 hover:from-cyan-500 hover:to-blue-500 text-white px-6 py-2 rounded-lg font-medium shadow-[0_2px_12px_rgba(0,0,0,0.08)] hover:shadow-[0_2px_12px_rgba(0,0,0,0.08)] transition-all text-sm"
              >
                {t('search')}
              </button>
            </div>
          </form>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                {t('sort')}
              </label>
              <select
                value={filters.sort}
                onChange={(e) => handleFilterChange('sort', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 text-sm"
              >
                <option value="popularity_desc">{t('sortPopularity')}</option>
                <option value="rating_desc">{t('sortRatingDesc')}</option>
                <option value="rating_asc">{t('sortRatingAsc')}</option>
                <option value="title_asc">{t('sortTitle')}</option>
                <option value="year_desc">{t('sortYearDesc')}</option>
                <option value="year_asc">{t('sortYearAsc')}</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                {t('status')}
              </label>
              <select
                value={filters.status}
                onChange={(e) => handleFilterChange('status', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 text-sm"
              >
                <option value="">{t('statusAll')}</option>
                <option value="Currently Airing">{t('statusAiring')}</option>
                <option value="Finished Airing">{t('statusFinished')}</option>
                <option value="Not yet aired">{t('statusNotYetAired')}</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                {t('year')}
              </label>
              <input
                type="number"
                value={filters.year}
                onChange={(e) => handleFilterChange('year', e.target.value)}
                placeholder={t('yearPlaceholder')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                {t('genre')}
              </label>
              <input
                type="text"
                value={filters.genre}
                onChange={(e) => handleFilterChange('genre', e.target.value)}
                placeholder={t('genrePlaceholder')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 text-sm"
              />
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {/* Anime List - Table Format */}
        {loading && animeList.length === 0 ? (
          <div className="flex justify-center items-center h-64">
            <div className="text-xl text-gray-600">{t('loading')}</div>
          </div>
        ) : animeList.length === 0 ? (
          <div className="flex justify-center items-center h-64">
            <div className="text-xl text-gray-600">{t('noResults')}</div>
          </div>
        ) : (
          <>
            <div className="bg-white rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] overflow-hidden mb-8">
              <div className="overflow-x-auto">
                <table className="w-full">
                  {/* Table Header */}
                  <thead className="bg-gradient-to-r from-gray-50 to-gray-100 border-b-2 border-gray-200">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                        {language === 'ko' ? '포스터' : 'Poster'}
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                        {language === 'ko' ? '제목' : 'Title'}
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                        {language === 'ko' ? '상태' : 'Status'}
                      </th>
                      <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider">
                        {language === 'ko' ? '연도' : 'Year'}
                      </th>
                      <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider">
                        {language === 'ko' ? '화수' : 'Episodes'}
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                        {language === 'ko' ? '장르' : 'Genres'}
                      </th>
                      <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider">
                        {language === 'ko' ? '평점' : 'Rating'}
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
                              <div className="font-semibold text-gray-900 hover:text-[#A8E6CF] transition-colors">
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
                          <td className="px-4 py-2">
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
                          <td className="px-4 py-2">
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
                          <td className="px-4 py-3 text-center">
                            {anime.site_rating_count > 0 ? (
                              <div>
                                <div className="flex items-center justify-center gap-1">
                                  <span className="text-yellow-500">★</span>
                                  <span className="font-bold text-gray-900">
                                    {anime.site_average_rating.toFixed(1)}
                                  </span>
                                </div>
                                <div className="text-xs text-gray-500 mt-0.5">
                                  {anime.site_rating_count.toLocaleString()}명
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

            {/* Load More Button */}
            {hasMore && (
              <div className="flex justify-center">
                <button
                  onClick={handleLoadMore}
                  disabled={loading}
                  className="bg-gradient-to-r from-cyan-400 to-blue-500 hover:from-cyan-500 hover:to-blue-600 text-white px-8 py-3 rounded-lg font-medium shadow-[0_2px_12px_rgba(0,0,0,0.08)] hover:shadow-[0_2px_12px_rgba(0,0,0,0.08)] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? t('loading') : t('loadMore')}
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
