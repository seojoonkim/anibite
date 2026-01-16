import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import StarRating from '../common/StarRating';
import { IMAGE_BASE_URL } from '../../config/api';

/**
 * Memoized character card component for profile page
 * Optimized with React.memo to prevent unnecessary re-renders
 * Shows skeleton with name first, then loads image progressively
 */
function MyCharacterCard({ character, language = 'ko' }) {
  const [imageLoaded, setImageLoaded] = useState(false);

  const getCharacterImageUrl = (characterId, imageUrl) => {
    if (!imageUrl) return '/placeholder-anime.svg';
    if (imageUrl.startsWith('http')) return imageUrl;
    return `${IMAGE_BASE_URL}${imageUrl}`;
  };

  const getCharacterImageFallback = (originalUrl, currentSrc) => {
    if (!originalUrl) return '/placeholder-anime.svg';

    // If current is .jpg, try .png
    if (currentSrc.endsWith('.jpg')) {
      return currentSrc.replace(/\.jpg$/, '.png');
    }
    // If current is .png, try .jpg
    if (currentSrc.endsWith('.png')) {
      return currentSrc.replace(/\.png$/, '.jpg');
    }

    return '/placeholder-anime.svg';
  };

  const name = character.character_name || character.character_name_native || '';

  return (
    <Link
      to={`/character/${character.character_id}`}
      className="group"
    >
      <div className="bg-white rounded-xl shadow-[0_2px_12px_rgba(0,0,0,0.08)] overflow-hidden hover:shadow-[0_4px_16px_rgba(0,0,0,0.12)] hover:-translate-y-1 transition-all duration-300">
        <div className="relative aspect-[3/4] bg-gray-200">
          {!imageLoaded && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-100 animate-pulse">
              <div className="text-gray-400 text-4xl">👤</div>
            </div>
          )}
          <img
            src={getCharacterImageUrl(character.character_id, character.image_url)}
            alt={name}
            className={`w-full h-full object-cover transition-opacity duration-300 ${
              imageLoaded ? 'opacity-100' : 'opacity-0'
            }`}
            loading="lazy"
            onLoad={() => setImageLoaded(true)}
            onError={(e) => {
              const step = e.target.dataset.fallbackStep || '0';

              if (step === '0') {
                // Step 1: Try alternate extension (.jpg ↔ .png)
                e.target.dataset.fallbackStep = '1';
                const fallbackUrl = getCharacterImageFallback(character.image_url, e.target.src);
                e.target.src = fallbackUrl;
              } else if (step === '1') {
                // Step 2: Try original external URL
                e.target.dataset.fallbackStep = '2';
                if (character.image_url && character.image_url.startsWith('http')) {
                  e.target.src = character.image_url;
                } else {
                  e.target.src = '/placeholder-anime.svg';
                  setImageLoaded(true);
                }
              } else {
                // Step 3: Give up, use placeholder
                e.target.src = '/placeholder-anime.svg';
                setImageLoaded(true);
              }
            }}
          />
        </div>
        <div className="p-3">
          <h3 className="font-medium text-sm mb-1 line-clamp-2">
            {name}
          </h3>
          {character.rating && (
            <StarRating rating={character.rating} readonly size="sm" />
          )}
          {character.anime_title && (
            <p className="text-xs text-gray-500 mt-1 line-clamp-1">
              {language === 'ko' && character.anime_title_korean
                ? character.anime_title_korean
                : character.anime_title}
            </p>
          )}
        </div>
      </div>
    </Link>
  );
}

// Memoize the component to prevent re-renders when props haven't changed
export default React.memo(MyCharacterCard);
