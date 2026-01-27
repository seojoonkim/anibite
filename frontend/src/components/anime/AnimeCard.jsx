import { Link } from 'react-router-dom';
import StarRating from '../common/StarRating';
import { IMAGE_BASE_URL } from '../../config/api';

export default function AnimeCard({ anime }) {
  const getStatusColor = (status) => {
    const colors = {
      'Currently Airing': 'bg-success/20 text-success',
      'Finished Airing': 'bg-primary/20 text-primary',
      'Not yet aired': 'bg-warning/20 text-warning',
    };
    return colors[status] || 'bg-surface-elevated text-text-secondary';
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

  return (
    <Link to={`/anime/${anime.id}`} className="group">
      <div className="bg-surface rounded-xl shadow-md overflow-hidden hover:shadow-2xl hover:-translate-y-1 transition-all duration-300 border border-border">
        <div className="relative aspect-[3/4] overflow-hidden bg-surface-elevated">
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
          <h3 className="font-bold text-lg mb-2 line-clamp-2 group-hover:text-primary transition-colors text-text-primary">
            {anime.title}
          </h3>

          {anime.title_english && anime.title_english !== anime.title && (
            <p className="text-sm text-text-secondary mb-2 line-clamp-1">
              {anime.title_english}
            </p>
          )}

          <div className="flex items-center justify-between mb-2 overflow-hidden">
            {anime.average_rating ? (
              <div className="flex-shrink-0">
                <StarRating rating={anime.average_rating} readonly size="sm" />
              </div>
            ) : (
              <span className="text-sm text-text-tertiary">평점 없음</span>
            )}
          </div>

          <div className="flex items-center justify-between text-sm text-text-secondary">
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
                  className="text-xs bg-surface-elevated text-text-secondary px-2 py-1 rounded"
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
