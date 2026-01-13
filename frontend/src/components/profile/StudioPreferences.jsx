import { useLanguage } from '../../context/LanguageContext';

export default function StudioPreferences({ studios }) {
  const { language } = useLanguage();

  return (
    <div className="bg-white rounded-2xl shadow-md p-6">
      <h3 className="text-lg font-bold mb-4 text-gray-800">
        {language === 'ko' ? '선호하는 제작사' : 'Favorite Studios'}
      </h3>

      {!studios || !Array.isArray(studios) || studios.length === 0 ? (
        <div className="text-center py-8 text-gray-500 text-sm">
          {language === 'ko' ? '데이터가 없습니다' : 'No data available'}
        </div>
      ) : (
        <div className="space-y-3">
          {studios.map((studio, index) => {
          return (
            <div key={studio.studio_id} className="space-y-1">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <span className="text-xs font-bold text-gray-400 w-5">#{index + 1}</span>
                  <span className="text-sm font-medium text-gray-700 truncate">
                    {studio.studio_name}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-600">{studio.anime_count}개</span>
                  <span className="text-xs text-yellow-600">★ {studio.average_rating?.toFixed(1)}</span>
                </div>
              </div>

              {/* Rating range indicator */}
              <div className="flex items-center gap-2 text-[10px] text-gray-400 ml-7">
                <span>최고 {studio.max_rating?.toFixed(1)}</span>
                <span>•</span>
                <span>최저 {studio.min_rating?.toFixed(1)}</span>
                <span>•</span>
                <span className={`font-medium ${
                  studio.average_rating > studio.overall_avg ? 'text-green-600' : 'text-gray-500'
                }`}>
                  평균 대비 {studio.average_rating > studio.overall_avg ? '+' : ''}
                  {(studio.average_rating - studio.overall_avg).toFixed(1)}
                </span>
              </div>
            </div>
          );
        })}
        </div>
      )}
    </div>
  );
}
