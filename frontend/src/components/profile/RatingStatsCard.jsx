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
    <div className="bg-gradient-to-br from-white to-cyan-50/20 rounded-2xl shadow-md p-6 w-full h-full flex flex-col border border-cyan-100/40">
      <h3 className="text-lg font-bold mb-4 text-[#638CCC]">
        {language === 'ko' ? '평가 성향' : language === 'ja' ? '評価傾向' : 'Rating Tendency'}
      </h3>

      <div className="space-y-4">
        {/* 평가 유형 */}
        <div className="p-5 rounded-xl bg-gradient-to-br from-[#8EC5FC]/15 to-[#638CCC]/15 border border-[#8EC5FC]/30">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <span className="text-2xl">{tendency.icon}</span>
              <span className="text-sm text-[#638CCC] font-semibold">
                {language === 'ko' ? '평가 유형' : language === 'ja' ? '評価タイプ' : 'Rating Type'}
              </span>
            </div>
            <span className="text-xl font-bold text-[#638CCC]">{tendency.label}</span>
          </div>
          <p className="text-sm text-gray-600">{tendency.desc}</p>
        </div>

        {/* 세부 지표 */}
        <div className="grid grid-cols-2 gap-4">
          {/* 관대함 지표 */}
          <div>
            <div className="text-xs text-[#638CCC] font-semibold mb-1">
              {language === 'ko' ? '관대함' : language === 'ja' ? '寛大さ' : 'Generosity'}
            </div>
            <div className="text-2xl font-bold mb-2 text-[#638CCC]">{generosityScore.toFixed(0)}%</div>
            <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
              <div
                className="h-2 rounded-full transition-all shadow-sm"
                style={{ width: `${generosityScore}%`, background: 'linear-gradient(90deg, #638CCC 0%, #8EC5FC 100%)' }}
              ></div>
            </div>
            <div className="text-xs text-gray-600 mt-1 font-medium">
              {language === 'ko' ? '평균' : language === 'ja' ? '平均' : 'Average'} ★{stats.mean_rating.toFixed(1)}
            </div>
          </div>

          {/* 일관성 지표 */}
          <div>
            <div className="text-xs text-[#638CCC] font-semibold mb-1">
              {language === 'ko' ? '일관성' : language === 'ja' ? '一貫性' : 'Consistency'}
            </div>
            <div className="text-2xl font-bold mb-2 text-[#8EC5FC]">{consistencyScore.toFixed(0)}%</div>
            <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
              <div
                className="h-2 rounded-full transition-all shadow-sm"
                style={{ width: `${consistencyScore}%`, background: 'linear-gradient(90deg, #8EC5FC 0%, #90B2E4 100%)' }}
              ></div>
            </div>
            <div className="text-xs text-gray-600 mt-1 font-medium">
              {language === 'ko' ? '표준편차' : language === 'ja' ? '標準偏差' : 'Std Dev'} {stats.std_dev.toFixed(2)}
            </div>
          </div>
        </div>

        {/* 통계 */}
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-xs text-gray-600 mb-1">
              {language === 'ko' ? '평균' : language === 'ja' ? '平均' : 'Average'}
            </div>
            <div className="text-lg font-bold text-gray-700">★ {stats.mean_rating.toFixed(1)}</div>
          </div>
          <div className="text-center">
            <div className="text-xs text-gray-600 mb-1">
              {language === 'ko' ? '최고' : language === 'ja' ? '最高' : 'Highest'}
            </div>
            <div className="text-lg font-bold" style={{ color: '#8EC5FC' }}>★ {stats.max_rating.toFixed(1)}</div>
          </div>
          <div className="text-center">
            <div className="text-xs text-gray-600 mb-1">
              {language === 'ko' ? '최저' : language === 'ja' ? '最低' : 'Lowest'}
            </div>
            <div className="text-lg font-bold" style={{ color: '#638CCC' }}>★ {stats.min_rating.toFixed(1)}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
