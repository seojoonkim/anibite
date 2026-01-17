import { useLanguage } from '../../context/LanguageContext';

export default function DirectorPreferences({ directors }) {
  const { language } = useLanguage();

  return (
    <div className="bg-white rounded-2xl shadow-md p-6">
      <h3 className="text-lg font-bold mb-4 text-gray-800">
        {language === 'ko' ? '선호하는 감독' : language === 'ja' ? 'お気に入りの監督' : 'Favorite Directors'}
      </h3>

      {!directors || !Array.isArray(directors) || directors.length === 0 ? (
        <div className="text-center py-8 text-gray-500 text-sm">
          {language === 'ko' ? '데이터가 없습니다' : language === 'ja' ? 'データがありません' : 'No data available'}
        </div>
      ) : (
        <div className="space-y-2">
          {directors.map((director, index) => {
          return (
            <div key={director.staff_id}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <span className="text-xs font-bold text-gray-400 w-5">#{index + 1}</span>
                  <span className="text-sm font-medium text-gray-700 truncate">
                    {director.staff_name}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-600">
                    {director.anime_count}{language === 'ko' ? '개' : language === 'ja' ? '作品' : ' titles'}
                  </span>
                  <span className="text-xs text-yellow-600">★ {director.average_rating?.toFixed(1)}</span>
                </div>
              </div>
            </div>
          );
        })}
        </div>
      )}
    </div>
  );
}
