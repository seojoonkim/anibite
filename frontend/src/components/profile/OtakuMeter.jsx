import { useState } from 'react';
import { createPortal } from 'react-dom';
import { levels as otakuLevels, getCurrentLevelInfo as getOtakuLevelInfo } from '../../utils/otakuLevels';
import { useLanguage } from '../../context/LanguageContext';

export default function OtakuMeter({ score }) {
  const { language } = useLanguage();
  const maxScore = 2000;
  const percentage = Math.min((score / maxScore) * 100, 100);
  const [showRoadmap, setShowRoadmap] = useState(false);

  // Use levels from otakuLevels.js
  const levels = otakuLevels;

  // Use getCurrentLevelInfo from otakuLevels.js
  const levelInfo = getOtakuLevelInfo(score, language);
  const progressToNext = levelInfo.nextThreshold
    ? ((score - levelInfo.currentThreshold) / (levelInfo.nextThreshold - levelInfo.currentThreshold)) * 100
    : 100;

  return (
    <>
      <div className="bg-surface rounded-xl shadow-lg border border-border p-6 w-full h-full flex flex-col">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-base font-semibold text-text-primary">
            {language === 'ko' ? '애니바이트 등급' : language === 'ja' ? 'アニバイト等級' : 'AniBite Grade'}
          </h3>
          <button
            onClick={() => setShowRoadmap(true)}
            className="text-sm font-medium text-primary hover:text-primary-light transition-colors"
          >
            {language === 'ko' ? '자세히 보기' : language === 'ja' ? '詳しく見る' : 'View details'}
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
                <span className="text-xs text-text-tertiary">
                  ({levelInfo.rank}/{levelInfo.total} {language === 'ko' ? '등급' : language === 'ja' ? '等級' : 'grade'})
                </span>
              </div>
              <div className="text-sm text-text-secondary">
                {language === 'ko' ? '현재 점수' : language === 'ja' ? '現在のスコア' : 'Current score'}: <span className="font-semibold text-text-primary">{score.toFixed(0)}{language === 'ko' ? '점' : language === 'ja' ? '点' : ' pts'}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Progress to Next Level */}
        {levelInfo.nextLevel && (
          <div className="mb-5">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-text-secondary flex items-center gap-1.5">
                {language === 'ko' ? '다음 등급' : language === 'ja' ? '次の等級' : 'Next grade'}:
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
                <span className="font-medium text-text-primary">{levelInfo.nextLevel}</span>
              </span>
              <span className="text-sm font-semibold text-text-primary">
                {Math.max(0, levelInfo.nextThreshold - score).toFixed(0)}{language === 'ko' ? '점 남음' : language === 'ja' ? '点残り' : ' pts left'}
              </span>
            </div>
            <div className="w-full bg-surface-elevated rounded-full h-2.5">
              <div
                className="h-2.5 rounded-full transition-all duration-500 bg-primary"
                style={{ width: `${Math.min(progressToNext, 100)}%` }}
              />
            </div>
          </div>
        )}

        {levelInfo.nextLevel === null && (
          <div className="mb-5 p-3 bg-accent/10 border border-accent/30 rounded-lg">
            <p className="text-sm font-medium text-accent">
              🎉 {language === 'ko' ? '최고 등급 달성!' : language === 'ja' ? '最高等級達成！' : 'Max grade achieved!'}
            </p>
          </div>
        )}

        {/* Calculation info */}
        <div className="pt-4 border-t border-border mt-auto">
          <p className="text-xs font-semibold text-text-secondary mb-2">
            {language === 'ko' ? '점수 계산' : language === 'ja' ? 'スコア計算' : 'Score calculation'}
          </p>
          <div className="text-xs text-text-tertiary space-y-1">
            <p>
              • {language === 'ko' ? '애니 평가 1개 = 2점' : language === 'ja' ? 'アニメ評価 1件 = 2点' : 'Anime rating = 2 pts'}
            </p>
            <p>
              • {language === 'ko' ? '캐릭터 평가 1개 = 1점' : language === 'ja' ? 'キャラクター評価 1件 = 1点' : 'Character rating = 1 pt'}
            </p>
            <p>
              • {language === 'ko' ? '리뷰 1개 = 5점' : language === 'ja' ? 'レビュー 1件 = 5点' : 'Review = 5 pts'}
            </p>
          </div>
        </div>
      </div>

      {/* Roadmap Modal */}
      {showRoadmap && createPortal(
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-surface rounded-xl shadow-xl max-w-2xl w-full max-h-[95vh] overflow-y-auto border border-border">
            <div className="sticky top-0 bg-surface border-b border-border px-6 py-3 flex items-center justify-between">
              <h3 className="text-lg font-bold text-text-primary">
                {language === 'ko' ? '애니바이트 등급 로드맵' : language === 'ja' ? 'アニバイト等級ロードマップ' : 'AniBite Grade Roadmap'}
              </h3>
              <button
                onClick={() => setShowRoadmap(false)}
                className="text-text-tertiary hover:text-text-secondary"
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
                      className={`p-3 rounded-lg border-2 transition-all ${isCurrentLevel
                          ? 'bg-surface-elevated border-primary'
                          : isPassed
                            ? 'bg-surface-elevated border-border'
                            : 'bg-surface border-border'
                        }`}
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
                            <span className="text-xs font-medium text-text-tertiary">
                              Lv.{index + 1}
                            </span>
                            <span className="font-bold text-sm" style={{ color: level.color }}>
                              {language === 'ko' ? level.name : language === 'ja' ? level.nameJa : level.nameEn}
                            </span>
                            {isCurrentLevel && (
                              <span className="text-xs text-white px-1.5 py-0.5 rounded bg-primary">
                                {language === 'ko' ? '현재' : language === 'ja' ? '現在' : 'Current'}
                              </span>
                            )}
                            {isPassed && (
                              <span className="text-xs text-success">✓</span>
                            )}
                          </div>
                          <div className="text-xs text-text-secondary mt-0.5">
                            {level.threshold}{language === 'ko' ? '점' : language === 'ja' ? '点' : ' pts'} ~ {level.max === Infinity ? (language === 'ko' ? '최고' : language === 'ja' ? '最高' : 'Max') : `${level.max}${language === 'ko' ? '점' : language === 'ja' ? '点' : ' pts'}`}
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
