import { useLanguage } from '../../context/LanguageContext';

export default function StudioStats({ studios }) {
  const { language } = useLanguage();

  if (!studios || studios.length === 0) {
    return null;
  }

  const maxCount = Math.max(...studios.map(s => s.count));

  return (
    <div className="bg-surface rounded-xl shadow-lg border border-border p-6 w-full h-full flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-base font-semibold text-text-primary">
          {language === 'ko' ? '애니메이션 스튜디오 Top 10' : language === 'ja' ? 'スタジオ TOP 10' : 'Top 10 Studios'}
        </h3>
      </div>

      <div className="space-y-2.5">
        {studios.map((studio, index) => {
          const percentage = (studio.count / maxCount) * 100;

          return (
            <div key={studio.studio_name}>
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <span className="text-xs font-bold text-primary-light w-5">#{index + 1}</span>
                  <span className="text-sm font-bold text-text-primary truncate">
                    {studio.studio_name}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-text-secondary font-medium">
                    {studio.count}{language === 'ko' ? '개' : language === 'ja' ? '作品' : ' titles'}
                  </span>
                  <span className="text-xs text-accent font-bold">★ {studio.average_rating?.toFixed(1)}</span>
                </div>
              </div>
              <div className="bg-surface-elevated rounded-full h-2 overflow-hidden">
                <div
                  className="h-2 rounded-full transition-all duration-500 shadow-sm bg-primary"
                  style={{ width: `${percentage}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
