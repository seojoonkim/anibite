import { useLanguage } from '../../context/LanguageContext';

export default function GenrePreferences({ preferences }) {
  const { language } = useLanguage();

  if (!preferences || preferences.length === 0) {
    return (
      <div className="bg-surface rounded-xl shadow-lg border border-border p-6 w-full h-full flex flex-col">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-base font-semibold text-text-primary">
            {language === 'ko' ? '선호 장르' : language === 'ja' ? '人気入りのジャンル' : 'Favorite Genres'}
          </h3>
        </div>
        <p className="text-sm text-text-secondary">
          {language === 'ko' ? '아직 충분한 데이터가 없습니다.' : language === 'ja' ? 'まだ十分なデータがありません。' : 'Not enough data yet.'}
        </p>
      </div>
    );
  }

  const maxCount = Math.max(...preferences.map((p) => p.count));

  // 각 장르마다 다른 그라디언트 색상 - Neon terminal style
  const getGradient = (index) => {
    const gradients = [
      'linear-gradient(135deg, #4A8AC9 0%, #2DD4E4 100%)', // Primary cyan
      'linear-gradient(135deg, #f778ba 0%, #db61a2 100%)', // Secondary pink
      'linear-gradient(135deg, #3fb950 0%, #2ea043 100%)', // Tertiary green
      'linear-gradient(135deg, #f0b429 0%, #d29922 100%)', // Accent gold
      'linear-gradient(135deg, #6FF4FF 0%, #4A8AC9 100%)', // Light cyan
    ];
    return gradients[index % gradients.length];
  };

  return (
    <div className="bg-surface rounded-xl shadow-lg border border-border p-6 w-full h-full flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-base font-semibold text-text-primary">
          {language === 'ko' ? '선호 장르 Top 5' : language === 'ja' ? '人気入りのジャンルTOP 5' : 'Top 5 Favorite Genres'}
        </h3>
      </div>

      <div className="space-y-3">
        {preferences.slice(0, 5).map((pref, index) => {
          const percentage = (pref.count / maxCount) * 100;

          return (
            <div key={pref.genre}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-bold text-text-primary">
                  {pref.genre}
                </span>
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-text-secondary font-medium">
                    {pref.count}{language === 'ko' ? '작품' : language === 'ja' ? '作品' : ' works'}
                  </span>
                  {pref.average_rating && (
                    <span className="font-bold flex items-center gap-0.5 text-accent">
                      <span>★</span>
                      <span>{pref.average_rating.toFixed(1)}</span>
                    </span>
                  )}
                </div>
              </div>
              <div className="w-full bg-surface-elevated rounded-full h-2 overflow-hidden">
                <div
                  className="h-2 rounded-full transition-all duration-500 shadow-sm"
                  style={{ width: `${percentage}%`, background: getGradient(index) }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
