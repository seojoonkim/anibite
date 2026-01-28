import { useLanguage } from '../../context/LanguageContext';

export default function GenreCombinationChart({ combinations }) {
  const { language } = useLanguage();

  if (!combinations || combinations.length === 0) {
    return null;
  }

  const maxCount = Math.max(...combinations.map(c => c.count));

  return (
    <div className="bg-surface rounded-xl shadow-lg border border-border p-6 w-full h-full flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-base font-semibold text-text-primary">
          {language === 'ko' ? '좋아하는 장르 조합 Top 10' : language === 'ja' ? 'お気に入りのジャンル組み合わせTOP 10' : 'Top 10 Genre Combinations'}
        </h3>
      </div>

      <div className="space-y-2.5">
        {combinations.map((combo, index) => {
          const percentage = (combo.count / maxCount) * 100;

          return (
            <div key={`${combo.genre1}-${combo.genre2}`}>
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <span className="text-xs font-bold text-primary-light w-5">#{index + 1}</span>
                  <div className="flex items-center gap-1.5 flex-1 min-w-0">
                    <span className="text-sm font-bold text-primary-light">{combo.genre1}</span>
                    <span className="text-xs text-text-tertiary">+</span>
                    <span className="text-sm font-bold text-primary">{combo.genre2}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-text-secondary font-medium">
                    {combo.count}{language === 'ko' ? '개' : language === 'ja' ? '個' : ''}
                  </span>
                  <span className="text-xs text-accent font-bold">★ {combo.average_rating?.toFixed(1)}</span>
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
