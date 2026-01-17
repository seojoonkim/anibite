import { useLanguage } from '../../contexts/LanguageContext';

export default function EpisodeLengthChart({ distribution }) {
  const { language } = useLanguage();

  if (!distribution || distribution.length === 0) {
    return null;
  }

  const total = distribution.reduce((sum, item) => sum + item.count, 0);

  const lengthNames = {
    'SHORT': language === 'ko' ? '단편 (1-12화)' : language === 'ja' ? '短編 (1-12話)' : 'Short (1-12 episodes)',
    'MEDIUM': language === 'ko' ? '중편 (13-26화)' : language === 'ja' ? '中編 (13-26話)' : 'Medium (13-26 episodes)',
    'LONG': language === 'ko' ? '장편 (27화+)' : language === 'ja' ? '長編 (27話+)' : 'Long (27+ episodes)'
  };

  const lengthGradients = {
    'SHORT': 'linear-gradient(135deg, #90B2E4 0%, #8EC5FC 100%)',
    'MEDIUM': 'linear-gradient(135deg, #638CCC 0%, #90B2E4 100%)',
    'LONG': 'linear-gradient(135deg, #8EC5FC 0%, #638CCC 100%)'
  };

  return (
    <div className="bg-gradient-to-br from-white to-indigo-50/20 rounded-2xl shadow-md p-6 w-full h-full flex flex-col border border-indigo-100/40">
      <h3 className="text-lg font-bold mb-4 text-[#638CCC]">
        {language === 'ko' ? '에피소드 길이 선호도' : language === 'ja' ? 'エピソード長の好み' : 'Episode Length Preferences'}
      </h3>

      <div className="space-y-3">
        {distribution.map((item) => {
          const percentage = ((item.count / total) * 100).toFixed(1);
          const gradient = lengthGradients[item.length_category] || 'linear-gradient(135deg, #8EC5FC 0%, #638CCC 100%)';

          return (
            <div key={item.length_category}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-bold text-[#638CCC]">
                  {lengthNames[item.length_category] || item.length_category}
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
