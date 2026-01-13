import { useState, useEffect } from 'react';
import { animeService } from '../services/animeService';
import { useLanguage } from '../context/LanguageContext';
import Navbar from '../components/common/Navbar';
import AnimeCard from '../components/anime/AnimeCard';

export default function Home() {
  const { language } = useLanguage();
  const [animeList, setAnimeList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [randomPlaceholder, setRandomPlaceholder] = useState(
    language === 'ko' ? '애니메이션 검색...' : 'Search anime...'
  );
  const [filters, setFilters] = useState({
    genre: '',
    year: '',
    status: '',
    sort: 'rating_desc',
  });
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  const loadAnime = async (resetList = false) => {
    try {
      setLoading(true);
      setError('');

      const currentPage = resetList ? 1 : page;
      const params = {
        page: currentPage,
        limit: 24,
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

  useEffect(() => {
    loadAnime(true);
  }, [searchTerm, filters]);

  // 인기 작품 50개 중 랜덤으로 플레이스홀더 설정
  useEffect(() => {
    const loadRandomPlaceholder = async () => {
      try {
        const data = await animeService.getAnimeList({
          page: 1,
          limit: 50,
          sort: 'popularity_desc'
        });

        console.log('Random placeholder data loaded:', data);

        if (data.items && data.items.length > 0) {
          const randomIndex = Math.floor(Math.random() * data.items.length);
          const randomAnime = data.items[randomIndex];
          console.log('Selected random anime:', randomAnime);

          const title = language === 'ko'
            ? (randomAnime.title_korean || randomAnime.title_romaji || randomAnime.title_english)
            : (randomAnime.title_romaji || randomAnime.title_english);

          const placeholderText = language === 'ko' ? `예: ${title}` : `e.g., ${title}`;
          console.log('Setting placeholder to:', placeholderText);
          setRandomPlaceholder(placeholderText);
        }
      } catch (err) {
        console.error('Failed to load random placeholder:', err);
      }
    };

    loadRandomPlaceholder();
  }, []); // 페이지 로드 시 한 번만 실행

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

  return (
    <div className="min-h-screen pt-0 md:pt-16 bg-transparent">
      <Navbar />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search and Filters */}
        <div className="bg-white rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] p-6 mb-8">
          <form onSubmit={handleSearch} className="mb-4">
            <div className="flex gap-2">
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder={randomPlaceholder}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              />
              <button
                type="submit"
                className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg font-medium"
              >
                검색
              </button>
            </div>
          </form>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                정렬
              </label>
              <select
                value={filters.sort}
                onChange={(e) => handleFilterChange('sort', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              >
                <option value="rating_desc">평점 높은순</option>
                <option value="rating_asc">평점 낮은순</option>
                <option value="title_asc">제목순</option>
                <option value="year_desc">최신순</option>
                <option value="year_asc">오래된순</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                방영 상태
              </label>
              <select
                value={filters.status}
                onChange={(e) => handleFilterChange('status', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              >
                <option value="">전체</option>
                <option value="Currently Airing">방영중</option>
                <option value="Finished Airing">완결</option>
                <option value="Not yet aired">미방영</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                연도
              </label>
              <input
                type="number"
                value={filters.year}
                onChange={(e) => handleFilterChange('year', e.target.value)}
                placeholder="예: 2024"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                장르
              </label>
              <input
                type="text"
                value={filters.genre}
                onChange={(e) => handleFilterChange('genre', e.target.value)}
                placeholder="예: Action"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
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

        {/* Anime Grid */}
        {loading && animeList.length === 0 ? (
          <div className="flex justify-center items-center h-64">
            <div className="text-xl text-gray-600">{language === 'ko' ? '로딩 중...' : 'Loading...'}</div>
          </div>
        ) : animeList.length === 0 ? (
          <div className="flex justify-center items-center h-64">
            <div className="text-xl text-gray-600">{language === 'ko' ? '검색 결과가 없습니다.' : 'No results found.'}</div>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-6">
              {animeList.map((anime) => (
                <AnimeCard key={anime.id} anime={anime} />
              ))}
            </div>

            {/* Load More Button */}
            {hasMore && (
              <div className="flex justify-center mt-8">
                <button
                  onClick={handleLoadMore}
                  disabled={loading}
                  className="bg-blue-500 hover:bg-blue-600 text-white px-8 py-3 rounded-lg font-medium disabled:opacity-50"
                >
                  {loading ? (language === 'ko' ? '로딩 중...' : 'Loading...') : (language === 'ko' ? '더 보기' : 'Load More')}
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
