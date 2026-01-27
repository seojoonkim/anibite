import { useLanguage } from '../../context/LanguageContext';

export default function GenrePreferences({ preferences }) {
  const { language } = useLanguage();

  if (!preferences || preferences.length === 0) {
    return (
      <div className="bg-surface rounded-xl shadow-lg border border-border p-6 w-full h-full flex flex-col">
        <h3 className="text-lg font-bold text-primary mb-4">
          {language === 'ko' ? '선호 장르' : language === 'ja' ? 'お気に入りのジャンル' : 'Favorite Genres'}
        </h3>
        <p className="text-sm text-text-secondary">
          {language === 'ko' ? '아직 충분한 데이터가 없습니다.' : language === 'ja' ? 'まだ十分なデータがありません。' : 'Not enough data yet.'}
        </p>
      </div>
    );
  }

  const maxCount = Math.max(...preferences.map((p) => p.count));

  // 각 장르마다 다른 그라데이션 색상 - Neon terminal style
  const getGradient = (index) => {
    const gradients = [
      'linear-gradient(135deg, #58a6ff 0%, #388bfd 100%)', // Primary blue
      'linear-gradient(135deg, #f778ba 0%, #db61a2 100%)', // Secondary pink
      'linear-gradient(135deg, #3fb950 0%, #2ea043 100%)', // Tertiary green
      'linear-gradient(135deg, #f0b429 0%, #d29922 100%)', // Accent gold
      'linear-gradient(135deg, #79c0ff 0%, #58a6ff 100%)', // Light blue
    ];
    return gradients[index % gradients.length];
  };

  return (
    <div className="bg-surface rounded-xl shadow-lg border border-border p-6 w-full h-full flex flex-col">
      <h3 className="text-lg font-bold text-primary mb-4">
        {language === 'ko' ? '선호 장르 Top 5' : language === 'ja' ? 'お気に入りのジャンルTOP 5' : 'Top 5 Favorite Genres'}
      </h3>

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
