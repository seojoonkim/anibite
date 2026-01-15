export default function FormatDistribution({ distribution }) {
  if (!distribution || distribution.length === 0) {
    return null;
  }

  const total = distribution.reduce((sum, item) => sum + item.count, 0);

  const formatNames = {
    'TV': 'TV 시리즈',
    'MOVIE': '영화',
    'OVA': 'OVA',
    'ONA': 'ONA',
    'SPECIAL': '스페셜',
    'MUSIC': '뮤직'
  };

  const formatColors = {
    'TV': '#8EC5FC',
    'MOVIE': '#638CCC',
    'OVA': '#90B2E4',
    'ONA': '#8EC5FC',
    'SPECIAL': '#638CCC',
    'MUSIC': '#90B2E4'
  };

  return (
    <div className="bg-white rounded-2xl shadow-md p-6 w-full h-full flex flex-col">
      <h3 className="text-lg font-bold mb-4 text-gray-800">포맷 선호도</h3>

      <div className="space-y-3">
        {distribution.map((item) => {
          const percentage = ((item.count / total) * 100).toFixed(1);
          const color = formatColors[item.format] || 'bg-gray-500';

          return (
            <div key={item.format}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium text-gray-700">
                  {formatNames[item.format] || item.format}
                </span>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600">{item.count}개</span>
                  <span className="text-sm font-bold text-gray-900">{percentage}%</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className="flex-1 bg-gray-100 rounded-full h-2">
                  <div
                    className="h-2 rounded-full transition-all duration-500"
                    style={{ width: `${percentage}%`, backgroundColor: color }}
                  />
                </div>
                <span className="text-xs text-yellow-600">★ {item.average_rating?.toFixed(1)}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
