export default function GenrePreferences({ preferences }) {
  if (!preferences || preferences.length === 0) {
    return (
      <div className="bg-gradient-to-br from-white to-purple-50/30 rounded-xl shadow-sm border border-purple-100/50 p-6 w-full h-full flex flex-col">
        <h3 className="text-lg font-bold text-[#638CCC] mb-4">
          선호 장르
        </h3>
        <p className="text-sm text-gray-500">아직 충분한 데이터가 없습니다.</p>
      </div>
    );
  }

  const maxCount = Math.max(...preferences.map((p) => p.count));

  // 각 장르마다 다른 그라데이션 색상
  const getGradient = (index) => {
    const gradients = [
      'linear-gradient(135deg, #8EC5FC 0%, #638CCC 100%)',
      'linear-gradient(135deg, #90B2E4 0%, #8EC5FC 100%)',
      'linear-gradient(135deg, #638CCC 0%, #90B2E4 100%)',
      'linear-gradient(135deg, #8EC5FC 0%, #90B2E4 100%)',
      'linear-gradient(135deg, #638CCC 0%, #8EC5FC 100%)',
    ];
    return gradients[index % gradients.length];
  };

  return (
    <div className="bg-gradient-to-br from-white to-purple-50/30 rounded-xl shadow-sm border border-purple-100/50 p-6 w-full h-full flex flex-col">
      <h3 className="text-lg font-bold text-[#638CCC] mb-4">
        선호 장르 Top 5
      </h3>

      <div className="space-y-3">
        {preferences.slice(0, 5).map((pref, index) => {
          const percentage = (pref.count / maxCount) * 100;

          return (
            <div key={pref.genre}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-bold text-[#638CCC]">
                  {pref.genre}
                </span>
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-gray-600 font-medium">
                    {pref.count}작품
                  </span>
                  {pref.average_rating && (
                    <span className="font-bold flex items-center gap-0.5 text-amber-500">
                      <span>★</span>
                      <span>{pref.average_rating.toFixed(1)}</span>
                    </span>
                  )}
                </div>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                <div
                  className="h-2 rounded-full transition-all duration-500 shadow-sm"
                  style={{ width: `${percentage}%`, background: getGradient(index) }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
