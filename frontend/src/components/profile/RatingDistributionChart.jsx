import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

export default function RatingDistributionChart({ distribution }) {
  if (!distribution || distribution.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-xl font-bold mb-4">평점 분포</h3>
        <p className="text-gray-600">아직 평가한 애니메이션이 없습니다.</p>
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

  // 색상 그라데이션 (메인 테마 색상)
  const getColor = (rating) => {
    if (rating >= 4.5) return '#8EC5FC'; // 진한 파랑
    if (rating >= 4.0) return '#638CCC'; // 중간 파랑
    if (rating >= 3.5) return '#90B2E4'; // 밝은 파랑
    if (rating >= 3.0) return '#638CCC'; // 중간 파랑
    if (rating >= 2.5) return '#8EC5FC'; // 진한 파랑
    return '#638CCC'; // 중간 파랑
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white border border-gray-200 rounded-lg shadow-lg px-3 py-2">
          <p className="font-medium">★ {payload[0].payload.rating}</p>
          <p className="text-sm text-gray-600">{payload[0].value}개 작품</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6 hover:shadow-xl transition-all duration-300">
      <h3 className="text-xl font-bold mb-4 bg-gradient-to-r from-gray-700 to-gray-900 bg-clip-text text-transparent">평점 분포</h3>
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
        총 {distribution.reduce((sum, d) => sum + d.count, 0)}개 평가
      </div>
    </div>
  );
}
