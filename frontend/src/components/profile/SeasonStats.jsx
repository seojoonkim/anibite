export default function SeasonStats({ seasons }) {
  if (!seasons || seasons.length === 0) {
    return null;
  }

  const total = seasons.reduce((sum, item) => sum + item.count, 0);

  const seasonNames = {
    'SPRING': '봄',
    'SUMMER': '여름',
    'FALL': '가을',
    'WINTER': '겨울'
  };

  const seasonEmojis = {
    'SPRING': '🌸',
    'SUMMER': '☀️',
    'FALL': '🍂',
    'WINTER': '❄️'
  };

  const seasonColors = {
    'SPRING': '#90B2E4',
    'SUMMER': '#638CCC',
    'FALL': '#8EC5FC',
    'WINTER': '#638CCC'
  };

  return (
    <div className="bg-white rounded-2xl shadow-md p-6">
      <h3 className="text-lg font-bold mb-4 text-gray-800">시즌 선호도</h3>

      <div className="space-y-3">
        {seasons.map((item) => {
          const percentage = ((item.count / total) * 100).toFixed(1);
          const color = seasonColors[item.season] || 'bg-gray-500';

          return (
            <div key={item.season}>
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <span className="text-lg">{seasonEmojis[item.season]}</span>
                  <span className="text-sm font-medium text-gray-700">
                    {seasonNames[item.season] || item.season}
                  </span>
                </div>
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
