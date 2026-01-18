import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import StarRating from '../common/StarRating';
import { useLanguage } from '../../context/LanguageContext';
import { IMAGE_BASE_URL } from '../../config/api';

/**
 * Memoized anime card component for profile page
 * Optimized with React.memo to prevent unnecessary re-renders
 * Shows skeleton with title first, then loads image progressively
 */
function MyAnimeCard({ anime }) {
  const { language } = useLanguage();
  const [imageLoaded, setImageLoaded] = useState(false);

  const getImageUrl = (imageUrl) => {
    if (!imageUrl) return '/placeholder-anime.svg';
    if (imageUrl.startsWith('http')) return imageUrl;
    const processedUrl = imageUrl.includes('/covers/')
      ? imageUrl.replace('/covers/', '/covers_large/')
      : imageUrl;
    return `${IMAGE_BASE_URL}${processedUrl}`;
  };

  const getDisplayTitle = () => {
    if (language === 'ja' && anime.title_native) {
      return anime.title_native;
    }
    if (language === 'ko' && anime.title_korean) {
      return anime.title_korean;
    }
    return anime.title_romaji || anime.title_english || 'Unknown';
  };

  const title = getDisplayTitle();
  const imageUrl = anime.image_url;

  return (
    <Link
      to={`/anime/${anime.anime_id}`}
      className="group"
    >
      <div className="bg-white rounded-xl shadow-[0_2px_12px_rgba(0,0,0,0.08)] overflow-hidden hover:shadow-[0_4px_16px_rgba(0,0,0,0.12)] hover:-translate-y-1 transition-all duration-300">
        <div className="relative aspect-[3/4] bg-gray-200">
          {!imageLoaded && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-100 animate-pulse">
              <div className="text-gray-400 text-4xl">📺</div>
            </div>
          )}
          <img
            src={getImageUrl(imageUrl)}
            alt={title}
            className={`w-full h-full object-cover transition-opacity duration-300 ${
              imageLoaded ? 'opacity-100' : 'opacity-0'
            }`}
            loading="lazy"
            onLoad={() => setImageLoaded(true)}
            onError={(e) => {
              e.target.src = '/placeholder-anime.svg';
              setImageLoaded(true);
            }}
          />
        </div>
        <div className="p-3">
          <h3 className="font-medium text-sm mb-1 line-clamp-2">
            {title}
          </h3>
          {anime.rating && (
            <StarRating rating={anime.rating} readonly size="sm" />
          )}
        </div>
      </div>
    </Link>
  );
}

// Memoize the component to prevent re-renders when props haven't changed
export default React.memo(MyAnimeCard);
