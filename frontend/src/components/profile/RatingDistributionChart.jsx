import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { useLanguage } from '../../contexts/LanguageContext';

export default function RatingDistributionChart({ distribution }) {
  const { language } = useLanguage();

  if (!distribution || distribution.length === 0) {
    return (
      <div className="bg-gradient-to-br from-white to-sky-50/30 rounded-xl shadow-md p-6 w-full h-full flex flex-col border border-sky-100/50">
        <h3 className="text-xl font-bold mb-4 text-[#638CCC]">
          {language === 'ko' ? '평점 분포' : language === 'ja' ? '評価分布' : 'Rating Distribution'}
        </h3>
        <p className="text-gray-600">
          {language === 'ko' ? '아직 평가한 애니메이션이 없습니다.' : language === 'ja' ? 'まだ評価したアニメがありません。' : 'No ratings yet.'}
        </p>
      </div>
    );
  }

  // 0.5 ~ 5.0 범위의 모든 평점을 포함하도록 데이터 준비
  const allRatings = [];
  for (let i = 0.5; i <= 5.0; i += 0.5) {
    const existing = distribution.find(d => d.rating === i);
    allRatings.push({
      rating: i,
      count: existing ? existing.count : 0
    });
  }

  // 색상 그라데이션 (메인 테마 색상) - 평점이 높을수록 진한 색
  const getColor = (rating) => {
    if (rating >= 4.5) return '#638CCC'; // 가장 진한 파랑
    if (rating >= 4.0) return '#8EC5FC'; // 진한 파랑
    if (rating >= 3.5) return '#90B2E4'; // 밝은 파랑
    if (rating >= 3.0) return '#8EC5FC'; // 진한 파랑
    if (rating >= 2.5) return '#90B2E4'; // 밝은 파랑
    return '#638CCC'; // 중간 파랑
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white border border-gray-200 rounded-lg shadow-lg px-3 py-2">
          <p className="font-medium">★ {payload[0].payload.rating}</p>
          <p className="text-sm text-gray-600">
            {payload[0].value}{language === 'ko' ? '개 작품' : language === 'ja' ? '作品' : ' titles'}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-gradient-to-br from-white to-sky-50/30 rounded-2xl shadow-lg p-6 hover:shadow-xl transition-all duration-300 w-full h-full flex flex-col border border-sky-100/50">
      <h3 className="text-xl font-bold mb-4 text-[#638CCC]">
        {language === 'ko' ? '평점 분포' : language === 'ja' ? '評価分布' : 'Rating Distribution'}
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={allRatings} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="rating"
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => `★${value}`}
          />
          <YAxis
            tick={{ fontSize: 12 }}
            allowDecimals={false}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="count" radius={[8, 8, 0, 0]}>
            {allRatings.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getColor(entry.rating)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div className="mt-4 text-center text-sm text-gray-600">
        {language === 'ko' ? '총 ' : language === 'ja' ? '合計 ' : 'Total '}
        {distribution.reduce((sum, d) => sum + d.count, 0)}
        {language === 'ko' ? '개 평가' : language === 'ja' ? '件の評価' : ' ratings'}
      </div>
    </div>
  );
}
