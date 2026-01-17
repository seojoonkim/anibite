import { Link } from 'react-router-dom';
import { useLanguage } from '../../context/LanguageContext';
import { API_BASE_URL, IMAGE_BASE_URL } from '../../config/api';

export default function HiddenGems({ gems }) {
  const { language } = useLanguage();

  const getImageUrl = (imageUrl) => {
    if (!imageUrl) return '/placeholder-anime.svg';
    if (imageUrl.startsWith('http')) return imageUrl;
    // Use covers_large for better quality
    const processedUrl = imageUrl.includes('/covers/')
      ? imageUrl.replace('/covers/', '/covers_large/')
      : imageUrl;
    return `${IMAGE_BASE_URL}${processedUrl}`;
  };

  return (
    <div className="bg-white rounded-2xl shadow-md p-6">
      <h3 className="text-lg font-bold mb-4 text-gray-800">
        {language === 'ko' ? '숨겨진 보석 & 과대평가' : language === 'ja' ? '隠れた名作 & 過大評価' : 'Hidden Gems & Overrated'}
      </h3>

      {!gems || !Array.isArray(gems) || gems.length === 0 ? (
        <div className="text-center py-8 text-gray-500 text-sm">
          {language === 'ko' ? '데이터가 없습니다' : language === 'ja' ? 'データがありません' : 'No data available'}
        </div>
      ) : (
        <div className="space-y-3">
          {gems.map((anime) => {
          const isHiddenGem = anime.category === 'hidden_gem';

          return (
            <Link
              key={anime.anime_id}
              to={`/anime/${anime.anime_id}`}
              className="flex gap-3 p-2 rounded-lg hover:bg-gray-50 transition-colors"
            >
              {/* Image */}
              <img
                src={getImageUrl(anime.image_url)}
                alt={anime.title}
                className="w-12 h-16 object-cover rounded"
                onError={(e) => {
                  e.target.src = '/placeholder-anime.svg';
                }}
              />

              {/* Info */}
              <div className="flex-1 min-w-0">
                <h4 className="text-sm font-medium text-gray-900 truncate mb-1">
                  {anime.title_korean || anime.title}
                </h4>
                <div className="flex items-center gap-2 text-xs">
                  <span className={`px-2 py-0.5 rounded-full font-semibold ${
                    isHiddenGem
                      ? 'bg-green-100 text-green-800'
                      : 'bg-orange-100 text-orange-800'
                  }`}>
                    {isHiddenGem
                      ? (language === 'ko' ? '숨겨진 보석' : language === 'ja' ? '隠れた名作' : 'Hidden Gem')
                      : (language === 'ko' ? '과대평가' : language === 'ja' ? '過大評価' : 'Overrated')
                    }
                  </span>
                </div>
                <div className="flex items-center gap-3 text-[10px] text-gray-500 mt-1">
                  <span>
                    {language === 'ko' ? '내 평점: ' : language === 'ja' ? '私の評価: ' : 'My rating: '}
                    <span className="font-semibold text-gray-700">★ {anime.my_rating?.toFixed(1)}</span>
                  </span>
                  <span>•</span>
                  <span>
                    {language === 'ko' ? '평균: ' : language === 'ja' ? '平均: ' : 'Average: '}
                    {anime.anilist_score || 'N/A'}
                  </span>
                  <span>•</span>
                  <span className={`font-semibold ${
                    anime.rating_difference > 0 ? 'text-green-600' : 'text-orange-600'
                  }`}>
                    {anime.rating_difference > 0 ? '+' : ''}{anime.rating_difference?.toFixed(1)}
                  </span>
                </div>
              </div>
            </Link>
          );
        })}
        </div>
      )}
    </div>
  );
}
