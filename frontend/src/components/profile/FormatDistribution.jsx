import { useLanguage } from '../../context/LanguageContext';

export default function FormatDistribution({ distribution }) {
  const { language } = useLanguage();

  if (!distribution || distribution.length === 0) {
    return null;
  }

  const total = distribution.reduce((sum, item) => sum + item.count, 0);

  const formatNames = {
    'TV': language === 'ko' ? 'TV 시리즈' : language === 'ja' ? 'TVシリーズ' : 'TV Series',
    'MOVIE': language === 'ko' ? '영화' : language === 'ja' ? '映画' : 'Movie',
    'OVA': 'OVA',
    'ONA': 'ONA',
    'SPECIAL': language === 'ko' ? '스페셜' : language === 'ja' ? 'スペシャル' : 'Special',
    'MUSIC': language === 'ko' ? '뮤직' : language === 'ja' ? 'ミュージック' : 'Music'
  };

  const formatGradients = {
    'TV': 'linear-gradient(135deg, #8EC5FC 0%, #638CCC 100%)',
    'MOVIE': 'linear-gradient(135deg, #638CCC 0%, #90B2E4 100%)',
    'OVA': 'linear-gradient(135deg, #90B2E4 0%, #8EC5FC 100%)',
    'ONA': 'linear-gradient(135deg, #8EC5FC 0%, #90B2E4 100%)',
    'SPECIAL': 'linear-gradient(135deg, #638CCC 0%, #8EC5FC 100%)',
    'MUSIC': 'linear-gradient(135deg, #90B2E4 0%, #638CCC 100%)'
  };

  return (
    <div className="bg-gradient-to-br from-white to-blue-50/20 rounded-2xl shadow-md p-6 w-full h-full flex flex-col border border-blue-100/40">
      <h3 className="text-lg font-bold mb-4 text-[#638CCC]">
        {language === 'ko' ? '포맷 선호도' : language === 'ja' ? 'フォーマットの好み' : 'Format Preferences'}
      </h3>

      <div className="space-y-3">
        {distribution.map((item) => {
          const percentage = ((item.count / total) * 100).toFixed(1);
          const gradient = formatGradients[item.format] || 'linear-gradient(135deg, #8EC5FC 0%, #638CCC 100%)';

          return (
            <div key={item.format}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-bold text-[#638CCC]">
                  {formatNames[item.format] || item.format}
                </span>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600 font-medium">
                    {item.count}{language === 'ko' ? '개' : language === 'ja' ? '作品' : ' titles'}
                  </span>
                  <span className="text-sm font-bold text-[#638CCC]">{percentage}%</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className="flex-1 bg-gray-100 rounded-full h-2.5 overflow-hidden">
                  <div
                    className="h-2.5 rounded-full transition-all duration-500 shadow-sm"
                    style={{ width: `${percentage}%`, background: gradient }}
                  />
                </div>
                <span className="text-xs text-amber-500 font-bold">★ {item.average_rating?.toFixed(1)}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
