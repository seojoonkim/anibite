export default function StudioStats({ studios }) {
  if (!studios || studios.length === 0) {
    return null;
  }

  const maxCount = Math.max(...studios.map(s => s.count));

  return (
    <div className="bg-white rounded-2xl shadow-md p-6">
      <h3 className="text-lg font-bold mb-4 text-gray-800">애니메이션 스튜디오 Top 10</h3>

      <div className="space-y-2">
        {studios.map((studio, index) => {
          const percentage = (studio.count / maxCount) * 100;

          return (
            <div key={studio.studio_name}>
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <span className="text-xs font-bold text-gray-400 w-5">#{index + 1}</span>
                  <span className="text-sm font-medium text-gray-700 truncate">
                    {studio.studio_name}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-600">{studio.count}개</span>
                  <span className="text-xs text-yellow-600">★ {studio.average_rating?.toFixed(1)}</span>
                </div>
              </div>
              <div className="bg-gray-100 rounded-full h-1.5">
                <div
                  className="h-1.5 rounded-full transition-all duration-500"
                  style={{ width: `${percentage}%`, background: 'linear-gradient(to right, #8EC5FC, #638CCC)' }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
