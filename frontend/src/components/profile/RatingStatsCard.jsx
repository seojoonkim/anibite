import { useLanguage } from '../../context/LanguageContext';

export default function RatingStatsCard({ stats }) {
  const { language } = useLanguage();

  if (!stats) {
    return null;
  }

  // 2D 분석: 엄격도 (표준편차) + 관대함 (평균 평점)
  const getRatingTendency = (meanRating, stdDev) => {
    const isGenerous = meanRating >= 3.5; // 3.5 이상이면 관대
    const isConsistent = stdDev < 1.0; // 표준편차 1.0 미만이면 일관성 있음

    if (isGenerous && isConsistent) {
      return {
        label: language === 'ko' ? '호평형' : language === 'ja' ? '好評型' : 'Generous',
        color: '#8EC5FC',
        bgColor: '#EBF2FA',
        desc: language === 'ko' ? '평점을 후하게 주되, 일관성 있게 평가' : language === 'ja' ? '評価が高く、一貫性のある評価' : 'Generous and consistent ratings',
        icon: '😊'
      };
    } else if (isGenerous && !isConsistent) {
      return {
        label: language === 'ko' ? '관대형' : language === 'ja' ? '寛大型' : 'Lenient',
        color: '#638CCC',
        bgColor: '#EBF2FA',
        desc: language === 'ko' ? '평점을 후하게 주며, 다양한 점수 활용' : language === 'ja' ? '評価が高く、様々なスコアを活用' : 'Generous with varied scores',
        icon: '🌟'
      };
    } else if (!isGenerous && isConsistent) {
      return {
        label: language === 'ko' ? '냉정형' : language === 'ja' ? '冷静型' : 'Critical',
        color: '#8EC5FC',
        bgColor: '#EBF2FA',
        desc: language === 'ko' ? '낮은 점수를 일관되게 부여' : language === 'ja' ? '低いスコアを一貫して付与' : 'Consistently lower ratings',
        icon: '🤔'
      };
    } else {
      return {
        label: language === 'ko' ? '신중형' : language === 'ja' ? '慎重型' : 'Cautious',
        color: '#638CCC',
        bgColor: '#EBF2FA',
        desc: language === 'ko' ? '평점을 신중하게 부여하며, 넓은 범위 활용' : language === 'ja' ? '評価を慎重に付与し、広範囲を活用' : 'Cautious with wide range',
        icon: '⚖️'
      };
    }
  };

  const tendency = getRatingTendency(stats.mean_rating, stats.std_dev);

  // 일관성 점수 (0-100)
  const consistencyScore = Math.max(0, Math.min(100, (1.5 - stats.std_dev) * 50));

  // 관대함 점수 (0-100, 3.0을 중심으로)
  const generosityScore = Math.max(0, Math.min(100, ((stats.mean_rating - 1.0) / 4.0) * 100));

  return (
    <div className="bg-surface rounded-xl shadow-lg border border-border p-6 w-full h-full flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-base font-semibold text-text-primary">
          {language === 'ko' ? '평가 성향' : language === 'ja' ? '評価傾向' : 'Rating Tendency'}
        </h3>
      </div>

      <div className="space-y-4">
        {/* 평가 유형 */}
        <div className="p-5 rounded-xl bg-surface-elevated border border-border">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <span className="text-2xl">{tendency.icon}</span>
              <span className="text-sm text-primary font-semibold">
                {language === 'ko' ? '평가 유형' : language === 'ja' ? '評価タイプ' : 'Rating Type'}
              </span>
            </div>
            <span className="text-xl font-bold text-primary">{tendency.label}</span>
          </div>
          <p className="text-sm text-text-secondary">{tendency.desc}</p>
        </div>

        {/* 세부 지표 */}
        <div className="grid grid-cols-2 gap-4">
          {/* 관대함 지표 */}
          <div>
            <div className="text-xs text-primary font-semibold mb-1">
              {language === 'ko' ? '관대함' : language === 'ja' ? '寛大さ' : 'Generosity'}
            </div>
            <div className="text-2xl font-bold mb-2 text-primary">{generosityScore.toFixed(0)}%</div>
            <div className="w-full bg-surface-elevated rounded-full h-2 overflow-hidden">
              <div
                className="h-2 rounded-full transition-all shadow-sm bg-primary"
                style={{ width: `${generosityScore}%` }}
              ></div>
            </div>
            <div className="text-xs text-text-secondary mt-1 font-medium">
              {language === 'ko' ? '평균' : language === 'ja' ? '平均' : 'Average'} ★{stats.mean_rating.toFixed(1)}
            </div>
          </div>

          {/* 일관성 지표 */}
          <div>
            <div className="text-xs text-primary font-semibold mb-1">
              {language === 'ko' ? '일관성' : language === 'ja' ? '一貫性' : 'Consistency'}
            </div>
            <div className="text-2xl font-bold mb-2 text-primary-light">{consistencyScore.toFixed(0)}%</div>
            <div className="w-full bg-surface-elevated rounded-full h-2 overflow-hidden">
              <div
                className="h-2 rounded-full transition-all shadow-sm bg-primary-light"
                style={{ width: `${consistencyScore}%` }}
              ></div>
            </div>
            <div className="text-xs text-text-secondary mt-1 font-medium">
              {language === 'ko' ? '표준편차' : language === 'ja' ? '標準偏差' : 'Std Dev'} {stats.std_dev.toFixed(2)}
            </div>
          </div>
        </div>

        {/* 통계 */}
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-xs text-text-secondary mb-1">
              {language === 'ko' ? '평균' : language === 'ja' ? '平均' : 'Average'}
            </div>
            <div className="text-lg font-bold text-text-primary">
              <span style={{
                background: 'linear-gradient(135deg, #FFD700 0%, #FFA500 50%, #FF8C00 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text'
              }}>★</span> {stats.mean_rating.toFixed(1)}
            </div>
          </div>
          <div className="text-center">
            <div className="text-xs text-text-secondary mb-1">
              {language === 'ko' ? '최고' : language === 'ja' ? '最高' : 'Highest'}
            </div>
            <div className="text-lg font-bold text-accent">
              <span style={{
                background: 'linear-gradient(135deg, #FFD700 0%, #FFA500 50%, #FF8C00 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text'
              }}>★</span> {stats.max_rating.toFixed(1)}
            </div>
          </div>
          <div className="text-center">
            <div className="text-xs text-text-secondary mb-1">
              {language === 'ko' ? '최저' : language === 'ja' ? '最低' : 'Lowest'}
            </div>
            <div className="text-lg font-bold text-primary">
              <span style={{
                background: 'linear-gradient(135deg, #FFD700 0%, #FFA500 50%, #FF8C00 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text'
              }}>★</span> {stats.min_rating.toFixed(1)}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
