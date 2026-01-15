export default function GenreCombinationChart({ combinations }) {
  if (!combinations || combinations.length === 0) {
    return null;
  }

  const maxCount = Math.max(...combinations.map(c => c.count));

  return (
    <div className="bg-gradient-to-br from-white to-violet-50/20 rounded-2xl shadow-md p-6 w-full h-full flex flex-col border border-violet-100/40">
      <h3 className="text-lg font-bold mb-4 bg-gradient-to-r from-[#638CCC] to-violet-500 bg-clip-text text-transparent">좋아하는 장르 조합 Top 10</h3>

      <div className="space-y-2.5">
        {combinations.map((combo, index) => {
          const percentage = (combo.count / maxCount) * 100;

          return (
            <div key={`${combo.genre1}-${combo.genre2}`}>
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <span className="text-xs font-bold text-[#8EC5FC] w-5">#{index + 1}</span>
                  <div className="flex items-center gap-1.5 flex-1 min-w-0">
                    <span className="text-sm font-bold bg-gradient-to-r from-[#8EC5FC] to-[#638CCC] bg-clip-text text-transparent">{combo.genre1}</span>
                    <span className="text-xs text-gray-400">+</span>
                    <span className="text-sm font-bold bg-gradient-to-r from-[#638CCC] to-[#90B2E4] bg-clip-text text-transparent">{combo.genre2}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-600 font-medium">{combo.count}개</span>
                  <span className="text-xs text-amber-500 font-bold">★ {combo.average_rating?.toFixed(1)}</span>
                </div>
              </div>
              <div className="bg-gray-100 rounded-full h-2 overflow-hidden">
                <div
                  className="h-2 rounded-full transition-all duration-500 shadow-sm"
                  style={{ width: `${percentage}%`, background: 'linear-gradient(90deg, #8EC5FC, #638CCC, #90B2E4)' }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
