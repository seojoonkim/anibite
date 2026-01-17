import { useLanguage } from '../../context/LanguageContext';

export default function SeasonStats({ seasons }) {
  const { language } = useLanguage();

  if (!seasons || seasons.length === 0) {
    return null;
  }

  const total = seasons.reduce((sum, item) => sum + item.count, 0);

  const seasonNames = {
    'SPRING': language === 'ko' ? '봄' : language === 'ja' ? '春' : 'Spring',
    'SUMMER': language === 'ko' ? '여름' : language === 'ja' ? '夏' : 'Summer',
    'FALL': language === 'ko' ? '가을' : language === 'ja' ? '秋' : 'Fall',
    'WINTER': language === 'ko' ? '겨울' : language === 'ja' ? '冬' : 'Winter'
  };

  const seasonEmojis = {
    'SPRING': '🌸',
    'SUMMER': '☀️',
    'FALL': '🍂',
    'WINTER': '❄️'
  };

  const seasonGradients = {
    'SPRING': 'linear-gradient(135deg, #90B2E4 0%, #8EC5FC 100%)',
    'SUMMER': 'linear-gradient(135deg, #638CCC 0%, #8EC5FC 100%)',
    'FALL': 'linear-gradient(135deg, #8EC5FC 0%, #90B2E4 100%)',
    'WINTER': 'linear-gradient(135deg, #638CCC 0%, #90B2E4 100%)'
  };

  return (
    <div className="bg-gradient-to-br from-white to-emerald-50/20 rounded-2xl shadow-md p-6 w-full h-full flex flex-col border border-emerald-100/40">
      <h3 className="text-lg font-bold mb-4 text-[#638CCC]">
        {language === 'ko' ? '시즌 선호도' : language === 'ja' ? 'シーズンの好み' : 'Season Preferences'}
      </h3>

      <div className="space-y-3">
        {seasons.map((item) => {
          const percentage = ((item.count / total) * 100).toFixed(1);
          const gradient = seasonGradients[item.season] || 'linear-gradient(135deg, #8EC5FC 0%, #638CCC 100%)';

          return (
            <div key={item.season}>
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <span className="text-lg">{seasonEmojis[item.season]}</span>
                  <span className="text-sm font-bold text-[#638CCC]">
                    {seasonNames[item.season] || item.season}
                  </span>
                </div>
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
