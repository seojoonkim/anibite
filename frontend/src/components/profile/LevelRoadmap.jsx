import { levels as otakuLevels } from '../../utils/otakuLevels';

export default function LevelRoadmap({ currentScore }) {
  // Gradient colors for progress bars (visual only)
  const gradientColors = [
    'from-gray-400 to-gray-500',        // 루키
    'from-green-400 to-emerald-500',    // 헌터
    'from-blue-400 to-cyan-500',        // 워리어
    'from-indigo-400 to-blue-500',      // 나이트
    'from-purple-400 to-violet-500',    // 마스터
    'from-orange-400 to-amber-500',     // 하이마스터
    'from-red-400 to-rose-500',         // 그랜드마스터
    'from-pink-400 to-fuchsia-500',     // 오타쿠
    'from-yellow-400 via-amber-500 to-orange-500', // 오타쿠 킹
    'from-purple-500 via-pink-500 to-yellow-500',  // 오타쿠 갓
  ];

  // Map otakuLevels to LevelRoadmap format
  const levels = otakuLevels.map((level, index) => ({
    name: level.name,
    min: level.threshold,
    max: level.max,
    color: gradientColors[index],
    icon: level.icon
  }));

  const getCurrentLevel = () => {
    return levels.findIndex(level => currentScore >= level.min && currentScore < level.max);
  };

  const currentLevelIndex = getCurrentLevel();

  return (
    <div className="bg-white rounded-2xl shadow-lg p-5 hover:shadow-xl transition-all duration-300">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold bg-gradient-to-r from-gray-700 to-gray-900 bg-clip-text text-transparent">
          레벨 로드맵
        </h3>
        {/* 점수 획득 방법 - 인라인 */}
        <div className="flex items-center gap-3 text-xs">
          <div className="flex items-center gap-1">
            <span>⭐</span>
            <span className="font-bold text-blue-600">+2</span>
          </div>
          <div className="flex items-center gap-1">
            <span>👤</span>
            <span className="font-bold text-green-600">+1</span>
          </div>
          <div className="flex items-center gap-1">
            <span>✍️</span>
            <span className="font-bold text-purple-600">+5</span>
          </div>
        </div>
      </div>

      {/* 레벨 진행 바 */}
      <div className="space-y-2">
        {levels.map((level, index) => {
          const isCompleted = currentScore >= level.max;
          const isCurrent = index === currentLevelIndex;
          const isLocked = currentScore < level.min;

          let progress = 0;
          if (isCompleted) {
            progress = 100;
          } else if (isCurrent) {
            const range = level.max - level.min;
            const current = currentScore - level.min;
            progress = (current / range) * 100;
          }

          return (
            <div
              key={level.name}
              className={`relative rounded-lg p-2.5 transition-all duration-300 ${
                isCurrent
                  ? 'ring-2 ring-blue-500 bg-blue-50 shadow-md'
                  : isCompleted
                  ? 'bg-gray-50'
                  : 'bg-gray-50 opacity-50'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <span className="text-xl">{level.icon}</span>
                  <div>
                    <div className={`text-sm font-bold ${isCurrent ? 'text-blue-600' : 'text-gray-700'}`}>
                      {level.name}
                    </div>
                    <div className="text-xs text-gray-500">
                      {level.min}~{level.max}점
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {isCurrent && (
                    <div className="text-xs font-bold text-blue-600">
                      {Math.floor(progress)}%
                    </div>
                  )}
                  {isCompleted && (
                    <div className="text-green-500 text-lg">✓</div>
                  )}
                  {isLocked && (
                    <div className="text-gray-400 text-lg">🔒</div>
                  )}
                </div>
              </div>

              {/* 프로그레스 바 */}
              <div className="w-full bg-gray-200 rounded-full h-1.5 overflow-hidden">
                <div
                  className={`bg-gradient-to-r ${level.color} h-1.5 rounded-full transition-all duration-700 ease-out`}
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* 예상 레벨업 정보 - 현재 레벨만 */}
      {currentLevelIndex >= 0 && currentLevelIndex < levels.length - 1 && (
        <div className="mt-3 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg p-3">
          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-600">다음 레벨까지</span>
            {(() => {
              const pointsNeeded = levels[currentLevelIndex].max - currentScore;
              const animeRatingsNeeded = Math.ceil(pointsNeeded / 2);
              const characterRatingsNeeded = Math.ceil(pointsNeeded / 1);
              const reviewsNeeded = Math.ceil(pointsNeeded / 5);

              return (
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-1">
                    <span className="font-bold text-blue-600">{animeRatingsNeeded}</span>
                    <span className="text-gray-600">작품평가</span>
                  </div>
                  <span className="text-gray-400">또는</span>
                  <div className="flex items-center gap-1">
                    <span className="font-bold text-green-600">{characterRatingsNeeded}</span>
                    <span className="text-gray-600">캐릭터평가</span>
                  </div>
                  <span className="text-gray-400">또는</span>
                  <div className="flex items-center gap-1">
                    <span className="font-bold text-purple-600">{reviewsNeeded}</span>
                    <span className="text-gray-600">리뷰</span>
                  </div>
                </div>
              );
            })()}
          </div>
        </div>
      )}

      {currentScore >= 1800 && (
        <div className="mt-3 text-center p-3 bg-gradient-to-r from-pink-100 via-yellow-100 to-purple-100 rounded-lg">
          <span className="text-xl mr-2">🎉</span>
          <span className="font-bold bg-gradient-to-r from-purple-600 via-pink-600 to-yellow-600 bg-clip-text text-transparent">최고 레벨 달성! 오타쿠 갓!</span>
        </div>
      )}
    </div>
  );
}
