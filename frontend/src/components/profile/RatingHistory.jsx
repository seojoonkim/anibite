import { Link } from 'react-router-dom';
import StarRating from '../common/StarRating';
import { API_BASE_URL } from '../../config/api';

export default function RatingHistory({ ratings }) {
  if (!ratings || ratings.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">최근 평가</h3>
        <p className="text-sm text-gray-500">아직 평가한 애니메이션이 없습니다.</p>
      </div>
    );
  }

  const getImageUrl = (imageUrl) => {
    if (!imageUrl) return '/placeholder-anime.png';
    if (imageUrl.startsWith('http')) return imageUrl;
    return `${import.meta.env.VITE_API_URL || API_BASE_URL}${imageUrl}`;
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        최근 평가 ({ratings.length})
      </h3>

      <div className="space-y-3">
        {ratings.slice(0, 10).map((rating) => {
          return (
            <Link
              key={rating.anime_id}
              to={`/anime/${rating.anime_id}`}
              className="flex gap-4 p-3 rounded-lg hover:bg-gray-50 transition-all border border-gray-100 hover:border-[#3498DB] cursor-pointer group"
            >
              <img
                src={getImageUrl(rating.cover_image_url)}
                alt={rating.title}
                className="w-12 h-16 object-cover rounded flex-shrink-0 border-2 border-transparent group-hover:border-[#3498DB] transition-all"
                onError={(e) => {
                  e.target.src = '/placeholder-anime.png';
                }}
              />

              <div className="flex-1 min-w-0">
                <h4 className="text-sm font-medium text-gray-900 mb-1 truncate group-hover:text-[#3498DB] transition-colors">
                  {rating.title}
                </h4>

                {rating.rating && (
                  <div className="mb-1">
                    <StarRating rating={rating.rating} readonly size="sm" showNumber={false} />
                  </div>
                )}

                <p className="text-xs text-gray-500">
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
