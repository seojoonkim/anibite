export default function GenreCombinationChart({ combinations }) {
  if (!combinations || combinations.length === 0) {
    return null;
  }

  const maxCount = Math.max(...combinations.map(c => c.count));

  return (
    <div className="bg-white rounded-2xl shadow-md p-6">
      <h3 className="text-lg font-bold mb-4 text-gray-800">좋아하는 장르 조합 Top 10</h3>

      <div className="space-y-2">
        {combinations.map((combo, index) => {
          const percentage = (combo.count / maxCount) * 100;

          return (
            <div key={`${combo.genre1}-${combo.genre2}`}>
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <span className="text-xs font-bold text-gray-400 w-5">#{index + 1}</span>
                  <div className="flex items-center gap-1.5 flex-1 min-w-0">
                    <span className="text-sm font-medium" style={{ color: '#8EC5FC' }}>{combo.genre1}</span>
                    <span className="text-xs text-gray-400">+</span>
                    <span className="text-sm font-medium" style={{ color: '#638CCC' }}>{combo.genre2}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-600">{combo.count}개</span>
                  <span className="text-xs text-yellow-600">★ {combo.average_rating?.toFixed(1)}</span>
                </div>
              </div>
              <div className="bg-gray-100 rounded-full h-1.5">
                <div
                  className="h-1.5 rounded-full transition-all duration-500"
                  style={{ width: `${percentage}%`, background: 'linear-gradient(to right, #8EC5FC, #638CCC, #90B2E4)' }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
