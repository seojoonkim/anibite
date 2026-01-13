export default function EpisodeLengthChart({ distribution }) {
  if (!distribution || distribution.length === 0) {
    return null;
  }

  const total = distribution.reduce((sum, item) => sum + item.count, 0);

  const lengthNames = {
    'SHORT': '단편 (1-12화)',
    'MEDIUM': '중편 (13-26화)',
    'LONG': '장편 (27화+)'
  };

  const lengthColors = {
    'SHORT': '#90B2E4',
    'MEDIUM': '#638CCC',
    'LONG': '#8EC5FC'
  };

  return (
    <div className="bg-white rounded-2xl shadow-md p-6">
      <h3 className="text-lg font-bold mb-4 text-gray-800">에피소드 길이 선호도</h3>

      <div className="space-y-3">
        {distribution.map((item) => {
          const percentage = ((item.count / total) * 100).toFixed(1);
          const color = lengthColors[item.length_category] || 'bg-gray-500';

          return (
            <div key={item.length_category}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium text-gray-700">
                  {lengthNames[item.length_category] || item.length_category}
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
