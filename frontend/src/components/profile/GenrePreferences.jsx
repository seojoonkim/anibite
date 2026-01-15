export default function GenrePreferences({ preferences }) {
  if (!preferences || preferences.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 w-full h-full flex flex-col">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          선호 장르
        </h3>
        <p className="text-sm text-gray-500">아직 충분한 데이터가 없습니다.</p>
      </div>
    );
  }

  const maxCount = Math.max(...preferences.map((p) => p.count));

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 w-full h-full flex flex-col">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        선호 장르 Top 5
      </h3>

      <div className="space-y-4">
        {preferences.slice(0, 5).map((pref) => {
          const percentage = (pref.count / maxCount) * 100;

          return (
            <div key={pref.genre}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-900">
                  {pref.genre}
                </span>
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-gray-500">
                    {pref.count}작품
                  </span>
                  {pref.average_rating && (
                    <span className="text-gray-900 font-medium flex items-center gap-0.5">
                      <span>★</span>
                      <span>{pref.average_rating.toFixed(1)}</span>
                    </span>
                  )}
                </div>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-1.5">
                <div
                  className="h-1.5 rounded-full transition-all duration-500"
                  style={{ width: `${percentage}%`, backgroundColor: '#8EC5FC' }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
