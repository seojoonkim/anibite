import { useState, useEffect } from 'react';
import StarRating from '../common/StarRating';
import { useLanguage } from '../../context/LanguageContext';

export default function CharacterRatingWidget({ characterId, currentRating, onRate, onStatusChange }) {
  const { language } = useLanguage();
  const [tempRating, setTempRating] = useState(currentRating?.rating || 0);

  useEffect(() => {
    setTempRating(currentRating?.rating || 0);
  }, [currentRating]);

  const handleRatingChange = (newRating) => {
    setTempRating(newRating);
    // 바로 저장
    if (newRating > 0) {
      onRate(newRating);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-lg font-bold mb-4">
        {language === 'ko' ? '내 평가' : language === 'ja' ? '私の評価' : 'My Rating'}
      </h3>

      {/* Rating Display/Input */}
      <div className="mb-6">
        <div className="bg-gray-50 rounded-lg p-4">
          <StarRating
            rating={tempRating}
            onRatingChange={handleRatingChange}
            size="lg"
            align="center"
            dynamicSize={true}
            showNumber={true}
          />
        </div>

        {!currentRating?.rating && (
          <p className="text-sm text-gray-500 text-center mt-2">
            {language === 'ko' ? '별을 클릭하여 평가해보세요' : language === 'ja' ? '星をクリックして評価してください' : 'Click stars to rate'}
          </p>
        )}
      </div>

      {currentRating?.created_at && (
        <div className="mt-4 text-sm text-gray-600 text-center">
          {language === 'ko' ? '평가일: ' : language === 'ja' ? '評価日: ' : 'Rated on: '}
          {new Date(currentRating.created_at).toLocaleDateString(language === 'ko' ? 'ko-KR' : language === 'ja' ? 'ja-JP' : 'en-US')}
        </div>
      )}
    </div>
  );
}
