import { useState } from 'react';
import { createPortal } from 'react-dom';
import { levels as otakuLevels, getCurrentLevelInfo as getOtakuLevelInfo } from '../../utils/otakuLevels';

export default function OtakuMeter({ score }) {
  const maxScore = 2000;
  const percentage = Math.min((score / maxScore) * 100, 100);
  const [showRoadmap, setShowRoadmap] = useState(false);

  // Use levels from otakuLevels.js
  const levels = otakuLevels;

  // Use getCurrentLevelInfo from otakuLevels.js
  const levelInfo = getOtakuLevelInfo(score);
  const progressToNext = levelInfo.nextThreshold
    ? ((score - levelInfo.currentThreshold) / (levelInfo.nextThreshold - levelInfo.currentThreshold)) * 100
    : 100;

  return (
    <>
      <div className="bg-white rounded-xl shadow-[0_2px_12px_rgba(0,0,0,0.08)] border border-gray-200 p-6 w-full h-full flex flex-col">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-base font-semibold text-gray-900">애니패스 등급</h3>
          <button
            onClick={() => setShowRoadmap(true)}
            className="text-sm font-medium text-[#3797F0] hover:text-[#2a7dc4] transition-colors"
          >
            자세히 보기
          </button>
        </div>

        {/* Current Level Info */}
        <div className="mb-5">
          <div className="flex items-center gap-3">
            <span
              className="text-3xl"
              style={{
                background: levelInfo.gradient,
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text'
              }}
            >
              {levelInfo.icon}
            </span>
            <div className="flex-1">
              <div className="flex items-baseline gap-2 mb-1">
                <span className="text-xl font-bold" style={{ color: levelInfo.color }}>{levelInfo.level}</span>
                <span className="text-xs text-gray-500">
                  ({levelInfo.rank}/{levelInfo.total} 등급)
                </span>
              </div>
              <div className="text-sm text-gray-600">
                현재 점수: <span className="font-semibold text-gray-900">{score.toFixed(0)}점</span>
              </div>
            </div>
          </div>
        </div>

        {/* Progress to Next Level */}
        {levelInfo.nextLevel && (
          <div className="mb-5">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600 flex items-center gap-1.5">
                다음 등급:
                <span
                  className="text-base font-bold"
                  style={{
                    background: levels[levelInfo.rank]?.gradient || levelInfo.gradient,
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text'
                  }}
                >
                  {levelInfo.nextIcon}
                </span>
                <span className="font-medium text-gray-900">{levelInfo.nextLevel}</span>
              </span>
              <span className="text-sm font-semibold text-gray-900">
                {Math.max(0, levelInfo.nextThreshold - score).toFixed(0)}점 남음
              </span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-2.5">
              <div
                className="h-2.5 rounded-full transition-all duration-500"
                style={{ width: `${Math.min(progressToNext, 100)}%`, backgroundColor: '#3797F0' }}
              />
            </div>
          </div>
        )}

        {levelInfo.nextLevel === null && (
          <div className="mb-5 p-3 bg-gradient-to-r from-yellow-50 to-orange-50 border border-yellow-200 rounded-lg">
            <p className="text-sm font-medium text-yellow-900">🎉 최고 등급 달성!</p>
          </div>
        )}

        {/* Calculation info */}
        <div className="pt-4 border-t border-gray-200 mt-auto">
          <p className="text-xs font-semibold text-gray-700 mb-2">점수 계산</p>
          <div className="text-xs text-gray-600 space-y-1">
            <p>• 애니 평가 1개 = 2점</p>
            <p>• 캐릭터 평가 1개 = 1점</p>
            <p>• 리뷰 1개 = 5점</p>
          </div>
        </div>
      </div>

      {/* Roadmap Modal */}
      {showRoadmap && createPortal(
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[95vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
              <h3 className="text-lg font-bold text-gray-900">애니패스 등급 로드맵</h3>
              <button
                onClick={() => setShowRoadmap(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="p-4">
              <div className="grid grid-cols-2 gap-3">
                {levels.map((level, index) => {
                  const isCurrentLevel = levelInfo.rank === index + 1;
                  const isPassed = score > level.max;

                  return (
                    <div
                      key={level.name}
                      className={`p-3 rounded-lg border-2 transition-all ${
                        isCurrentLevel
                          ? 'bg-gray-50'
                          : isPassed
                          ? 'bg-gray-50 border-gray-200'
                          : 'bg-white border-gray-200'
                      }`}
                      style={isCurrentLevel ? { borderColor: '#8EC5FC' } : {}}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <span
                          className="text-2xl font-bold"
                          style={{
                            background: level.gradient,
                            WebkitBackgroundClip: 'text',
                            WebkitTextFillColor: 'transparent',
                            backgroundClip: 'text'
                          }}
                        >
                          {level.icon}
                        </span>
                        <div className="flex-1">
                          <div className="flex items-center gap-1.5">
                            <span className="text-xs font-medium text-gray-500">
                              Lv.{index + 1}
                            </span>
                            <span className="font-bold text-sm" style={{ color: level.color }}>
                              {level.name}
                            </span>
                            {isCurrentLevel && (
                              <span className="text-xs text-white px-1.5 py-0.5 rounded" style={{ backgroundColor: '#8EC5FC' }}>현재</span>
                            )}
                            {isPassed && (
                              <span className="text-xs text-green-600">✓</span>
                            )}
                          </div>
                          <div className="text-xs text-gray-600 mt-0.5">
                            {level.threshold}점 ~ {level.max === Infinity ? '최고' : `${level.max}점`}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>,
        document.body
      )}
    </>
  );
}
