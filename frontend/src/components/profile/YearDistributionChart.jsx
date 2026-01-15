import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

export default function YearDistributionChart({ distribution }) {
  if (!distribution || distribution.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 w-full h-full flex flex-col">
        <h3 className="text-xl font-bold mb-4">연도별 시청 분포</h3>
        <p className="text-gray-600">아직 평가한 애니메이션이 없습니다.</p>
      </div>
    );
  }

  // 색상 그라데이션 (메인 테마 색상)
  const getColor = (year) => {
    if (year >= 2020) return '#8EC5FC'; // 진한 파랑
    if (year >= 2015) return '#638CCC'; // 중간 파랑
    if (year >= 2010) return '#90B2E4'; // 밝은 파랑
    if (year >= 2005) return '#638CCC'; // 중간 파랑
    if (year >= 2000) return '#8EC5FC'; // 진한 파랑
    return '#638CCC'; // 중간 파랑
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white border border-gray-200 rounded-lg shadow-lg px-3 py-2">
          <p className="font-medium">{data.year}년</p>
          <p className="text-sm text-gray-600">{data.count}개 작품</p>
          {data.average_rating && (
            <p className="text-sm text-yellow-500">
              평균 ★ {data.average_rating.toFixed(1)}
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  // 데이터를 연도순으로 정렬
  const sortedData = [...distribution].sort((a, b) => a.year - b.year);

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6 hover:shadow-xl transition-all duration-300 w-full h-full flex flex-col">
      <h3 className="text-xl font-bold mb-4 bg-gradient-to-r from-gray-700 to-gray-900 bg-clip-text text-transparent">연도별 시청 분포</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={sortedData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="year"
            tick={{ fontSize: 12 }}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fontSize: 12 }}
            allowDecimals={false}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="count" radius={[8, 8, 0, 0]}>
            {sortedData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getColor(entry.year)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div className="mt-4 text-center text-sm text-gray-600">
        {sortedData.length > 0 && (
          <>
            {Math.min(...sortedData.map(d => d.year))}년 ~ {Math.max(...sortedData.map(d => d.year))}년
          </>
        )}
      </div>
    </div>
  );
}
