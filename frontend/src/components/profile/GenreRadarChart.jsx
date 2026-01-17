import { useLanguage } from '../../context/LanguageContext';

export default function GenreRadarChart({ radarData }) {
  const { language } = useLanguage();

  const maxRating = 5.0;

  return (
    <div className="bg-white rounded-2xl shadow-md p-6">
      <h3 className="text-lg font-bold mb-4 text-gray-800">
        {language === 'ko' ? '장르별 평가 분포' : language === 'ja' ? 'ジャンル別評価分布' : 'Genre Rating Distribution'}
      </h3>

      {!radarData || !radarData.genres || radarData.genres.length === 0 ? (
        <div className="text-center py-8 text-gray-500 text-sm">
          {language === 'ko' ? '데이터가 없습니다' : language === 'ja' ? 'データがありません' : 'No data available'}
        </div>
      ) : (
        <>
          <div className="space-y-3">
            {radarData.genres.map((genre) => {
          const percentage = (genre.average_rating / maxRating) * 100;

          return (
            <div key={genre.genre}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium text-gray-700">
                  {genre.genre}
                </span>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-600">
                    {genre.count}{language === 'ko' ? '개' : language === 'ja' ? '作品' : ' titles'}
                  </span>
                  <span className="text-xs text-yellow-600">★ {genre.average_rating?.toFixed(1)}</span>
                </div>
              </div>
              <div className="bg-gray-100 rounded-full h-2">
                <div
                  className="h-2 rounded-full transition-all duration-500"
                  style={{
                    width: `${percentage}%`,
                    background: `linear-gradient(to right, ${
                      genre.average_rating >= 4.0
                        ? '#10B981, #059669' // green
                        : genre.average_rating >= 3.0
                        ? '#3B82F6, #2563EB' // blue
                        : '#F59E0B, #D97706' // orange
                    })`
                  }}
                />
              </div>
            </div>
          );
        })}
          </div>

          {/* Note */}
          <div className="mt-4 pt-4 border-t border-gray-100">
            <p className="text-xs text-gray-500">
              {language === 'ko'
                ? '평가한 애니메이션이 가장 많은 상위 8개 장르'
                : language === 'ja'
                ? '評価したアニメが最も多い上位8つのジャンル'
                : 'Top 8 genres by number of rated anime'}
            </p>
          </div>
        </>
      )}
    </div>
  );
}
