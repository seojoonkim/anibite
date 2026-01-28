import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { useLanguage } from '../../context/LanguageContext';

export default function YearDistributionChart({ distribution }) {
  const { language } = useLanguage();

  if (!distribution || distribution.length === 0) {
    return (
      <div className="bg-surface rounded-xl shadow-lg border border-border p-6 w-full h-full flex flex-col">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-base font-semibold text-text-primary">
            {language === 'ko' ? '연도별 시청 분포' : language === 'ja' ? '年別視聴分布' : 'Year Distribution'}
          </h3>
        </div>
        <p className="text-text-secondary">
          {language === 'ko' ? '아직 평가한 애니메이션이 없습니다.' : language === 'ja' ? 'まだ評価したアニメがありません。' : 'No ratings yet.'}
        </p>
      </div>
    );
  }

  // 색상 그라데이션 (메인 테마 색상) - 최신 작품일수록 밝은 색
  const getColor = (year) => {
    if (year >= 2020) return '#8EC5FC'; // 밝은 파랑
    if (year >= 2015) return '#90B2E4'; // 연한 파랑
    if (year >= 2010) return '#638CCC'; // 중간 파랑
    if (year >= 2005) return '#90B2E4'; // 연한 파랑
    if (year >= 2000) return '#8EC5FC'; // 밝은 파랑
    return '#638CCC'; // 중간 파랑
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white border border-gray-200 rounded-lg shadow-lg px-3 py-2">
          <p className="font-medium">
            {data.year}{language === 'ko' ? '년' : language === 'ja' ? '年' : ''}
          </p>
          <p className="text-sm text-gray-600">
            {data.count}{language === 'ko' ? '개 작품' : language === 'ja' ? '作品' : ' titles'}
          </p>
          {data.average_rating && (
            <p className="text-sm text-yellow-500">
              {language === 'ko' ? '평균 ' : language === 'ja' ? '平均 ' : 'Avg '}★ {data.average_rating.toFixed(1)}
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
    <div className="bg-surface rounded-xl shadow-lg border border-border p-6 w-full h-full flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-base font-semibold text-text-primary">
          {language === 'ko' ? '연도별 시청 분포' : language === 'ja' ? '年別視聴分布' : 'Year Distribution'}
        </h3>
      </div>
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
      <div className="mt-4 text-center text-sm text-text-secondary">
        {sortedData.length > 0 && (
          <>
            {Math.min(...sortedData.map(d => d.year))}{language === 'ko' ? '년' : language === 'ja' ? '年' : ''} ~ {Math.max(...sortedData.map(d => d.year))}{language === 'ko' ? '년' : language === 'ja' ? '年' : ''}
          </>
        )}
      </div>
    </div>
  );
}
