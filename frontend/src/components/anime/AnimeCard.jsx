import { Link } from 'react-router-dom';
import StarRating from '../common/StarRating';
import { API_BASE_URL } from '../../config/api';

export default function AnimeCard({ anime }) {
  const getStatusColor = (status) => {
    const colors = {
      'Currently Airing': 'bg-green-100 text-green-800',
      'Finished Airing': 'bg-blue-100 text-blue-800',
      'Not yet aired': 'bg-yellow-100 text-yellow-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getImageUrl = (imageUrl) => {
    if (!imageUrl) return '/placeholder-anime.png';
    if (imageUrl.startsWith('http')) return imageUrl;
    return `${import.meta.env.VITE_API_URL || API_BASE_URL}${imageUrl}`;
  };

  return (
    <Link to={`/anime/${anime.id}`} className="group">
      <div className="bg-white rounded-xl shadow-md overflow-hidden hover:shadow-2xl hover:-translate-y-1 transition-all duration-300">
        <div className="relative aspect-[3/4] overflow-hidden bg-gray-200">
          <img
            src={getImageUrl(anime.cover_image_url)}
            alt={anime.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            onError={(e) => {
              e.target.src = '/placeholder-anime.png';
            }}
          />
          {anime.airing_status && (
            <div className={`absolute top-2 right-2 px-2 py-1 rounded text-xs font-medium ${getStatusColor(anime.airing_status)}`}>
              {anime.airing_status === 'Currently Airing' ? '방영중' :
               anime.airing_status === 'Finished Airing' ? '완결' :
               anime.airing_status === 'Not yet aired' ? '미방영' : anime.airing_status}
            </div>
          )}
        </div>

        <div className="p-4">
          <h3 className="font-bold text-lg mb-2 line-clamp-2 group-hover:text-blue-600 transition-colors">
            {anime.title}
          </h3>

          {anime.title_english && anime.title_english !== anime.title && (
            <p className="text-sm text-gray-500 mb-2 line-clamp-1">
              {anime.title_english}
            </p>
          )}

          <div className="flex items-center justify-between mb-2 overflow-hidden">
            {anime.average_rating ? (
              <div className="flex-shrink-0">
                <StarRating rating={anime.average_rating} readonly size="sm" />
              </div>
            ) : (
              <span className="text-sm text-gray-400">평점 없음</span>
            )}
          </div>

          <div className="flex items-center justify-between text-sm text-gray-600">
            {anime.aired_from && (
              <span>{new Date(anime.aired_from).getFullYear()}</span>
            )}
            {anime.episodes && (
              <span>{anime.episodes}화</span>
            )}
          </div>

          {anime.genres && anime.genres.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {anime.genres.slice(0, 3).map((genre) => (
                <span
                  key={genre}
                  className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded"
                >
                  {genre}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </Link>
  );
}
