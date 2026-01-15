export default function StudioStats({ studios }) {
  if (!studios || studios.length === 0) {
    return null;
  }

  const maxCount = Math.max(...studios.map(s => s.count));

  return (
    <div className="bg-gradient-to-br from-white to-pink-50/20 rounded-2xl shadow-md p-6 w-full h-full flex flex-col border border-pink-100/40">
      <h3 className="text-lg font-bold mb-4 bg-gradient-to-r from-[#638CCC] to-pink-500 bg-clip-text text-transparent">애니메이션 스튜디오 Top 10</h3>

      <div className="space-y-2.5">
        {studios.map((studio, index) => {
          const percentage = (studio.count / maxCount) * 100;

          return (
            <div key={studio.studio_name}>
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <span className="text-xs font-bold text-[#8EC5FC] w-5">#{index + 1}</span>
                  <span className="text-sm font-bold bg-gradient-to-r from-[#638CCC] to-[#8EC5FC] bg-clip-text text-transparent truncate">
                    {studio.studio_name}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-600 font-medium">{studio.count}개</span>
                  <span className="text-xs text-amber-500 font-bold">★ {studio.average_rating?.toFixed(1)}</span>
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
