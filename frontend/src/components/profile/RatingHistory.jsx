import { Link } from 'react-router-dom';
import StarRating from '../common/StarRating';
import { useLanguage } from '../../context/LanguageContext';
import { API_BASE_URL, IMAGE_BASE_URL } from '../../config/api';

export default function RatingHistory({ ratings }) {
  const { language } = useLanguage();
  if (!ratings || ratings.length === 0) {
    return (
      <div className="bg-surface rounded-xl shadow-lg border border-border p-6">
        <h3 className="text-lg font-semibold text-text-primary mb-4">최근 평가</h3>
        <p className="text-sm text-text-secondary">아직 평가한 애니메이션이 없습니다.</p>
      </div>
    );
  }

  const getImageUrl = (imageUrl) => {
    if (!imageUrl) return '/placeholder-anime.svg';
    if (imageUrl.startsWith('http')) return imageUrl;
    // Use covers_large for better quality
    const processedUrl = imageUrl.includes('/covers/')
      ? imageUrl.replace('/covers/', '/covers_large/')
      : imageUrl;
    return `${IMAGE_BASE_URL}${processedUrl}`;
  };

  const getDisplayTitle = (rating) => {
    if (language === 'ja' && rating.title_native) {
      return rating.title_native;
    }
    if (language === 'ko' && rating.title_korean) {
      return rating.title_korean;
    }
    return rating.title_romaji || rating.title_english || rating.title;
  };

  return (
    <div className="bg-surface rounded-xl shadow-lg border border-border p-6">
      <h3 className="text-lg font-semibold text-text-primary mb-4">
        최근 평가 ({ratings.length})
      </h3>

      <div className="space-y-3">
        {ratings.slice(0, 10).map((rating) => {
          return (
            <Link
              key={rating.anime_id}
              to={`/anime/${rating.anime_id}`}
              className="flex gap-4 p-3 rounded-lg hover:bg-surface-hover transition-all border border-border hover:border-primary cursor-pointer group"
            >
              <img
                src={getImageUrl(rating.cover_image_url || rating.image_url)}
                alt={getDisplayTitle(rating)}
                className="w-12 h-16 object-cover rounded flex-shrink-0 border-2 border-transparent group-hover:border-primary transition-all"
                onError={(e) => {
                  e.target.src = '/placeholder-anime.svg';
                }}
              />

              <div className="flex-1 min-w-0">
                <h4 className="text-sm font-medium text-text-primary mb-1 truncate group-hover:text-primary transition-colors">
                  {getDisplayTitle(rating)}
                </h4>

                {rating.rating && (
                  <div className="mb-1">
                    <StarRating rating={rating.rating} readonly size="sm" showNumber={false} />
                  </div>
                )}

                <p className="text-xs text-text-tertiary">
                  {new Date(rating.created_at).toLocaleDateString('ko-KR')}
                </p>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
