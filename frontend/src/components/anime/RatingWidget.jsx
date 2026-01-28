import { useState, useEffect } from 'react';
import StarRating from '../common/StarRating';
import { seriesService } from '../../services/seriesService';
import { useLanguage } from '../../context/LanguageContext';

export default function RatingWidget({ animeId, currentRating, onRate, onStatusChange }) {
  const { t } = useLanguage();
  const [tempRating, setTempRating] = useState(currentRating?.rating || 0);
  const [showSeriesModal, setShowSeriesModal] = useState(false);
  const [seriesInfo, setSeriesInfo] = useState(null);
  const [pendingStatus, setPendingStatus] = useState(null);
  const [showSuccessMessage, setShowSuccessMessage] = useState(false);
  const [successText, setSuccessText] = useState('');

  useEffect(() => {
    setTempRating(currentRating?.rating || 0);
  }, [currentRating]);

  const handleRatingChange = (newRating) => {
    setTempRating(newRating);
    // 바로 저장
    if (newRating > 0) {
      onRate(newRating, 'RATED');
    }
  };

  const handleStatusClick = async (status) => {
    console.log('handleStatusClick called:', { status, animeId, currentStatus: currentRating?.status });

    if (currentRating?.status === status) {
      // Remove status if clicking the same one
      onStatusChange(null);
      return;
    }

    // WANT_TO_WATCH나 PASS 상태일 때만 시리즈 확인
    if (status === 'WANT_TO_WATCH' || status === 'PASS') {
      console.log('Checking for series...');
      try {
        const series = await seriesService.getAnimeSequels(animeId);
        console.log('Series response:', series);
        if (series && series.sequels && series.sequels.length > 0) {
          // 시리즈가 있으면 팝업 표시
          console.log('Series found, showing modal');
          setSeriesInfo(series);
          setPendingStatus(status);
          setShowSeriesModal(true);
          return;
        } else {
          console.log('No sequels found');
        }
      } catch (err) {
        console.error('Failed to check series:', err);
      }
    }

    // 시리즈가 없거나 에러 발생 시 바로 처리
    console.log('Directly calling onStatusChange');
    onStatusChange(status);
  };

  const handleSeriesConfirm = async (applyToAll) => {
    setShowSeriesModal(false);

    if (applyToAll && seriesInfo) {
      // 현재 애니 + 모든 후속작에 상태 적용
      const animeIds = [animeId, ...seriesInfo.sequels.map(s => s.id)];
      try {
        await seriesService.bulkRateSeries(animeIds, pendingStatus);
        // 현재 애니 상태 업데이트
        onStatusChange(pendingStatus);

        // 성공 메시지 표시
        setSuccessText(`${seriesInfo.sequels.length + 1}개 작품에 ${pendingStatus === 'WANT_TO_WATCH' ? t('watchLater') : t('notInterested')}를 적용했습니다.`);
        setShowSuccessMessage(true);
        setTimeout(() => setShowSuccessMessage(false), 3000);
      } catch (err) {
        console.error('Failed to bulk rate series:', err);
        setSuccessText('일괄 처리 중 오류가 발생했습니다.');
        setShowSuccessMessage(true);
        setTimeout(() => setShowSuccessMessage(false), 3000);
      }
    } else {
      // 현재 애니에만 적용
      onStatusChange(pendingStatus);
    }

    setSeriesInfo(null);
    setPendingStatus(null);
  };

  const handleSeriesCancel = () => {
    setShowSeriesModal(false);
    setSeriesInfo(null);
    setPendingStatus(null);
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-lg font-bold mb-4">내 평가</h3>

      {/* Rating Display/Input */}
      <div className="mb-6 flex flex-col items-center w-full">
        <div className="w-full">
          <StarRating
            rating={tempRating}
            onRatingChange={handleRatingChange}
            size="xl"
            align="center"
            showNumber={false}
            dynamicSize={true}
          />
        </div>
        {tempRating > 0 && (
          <div className="mt-2 text-lg text-gray-600">
            {tempRating.toFixed(1)}
          </div>
        )}

        {!currentRating?.rating && (
          <p className="text-sm text-gray-500 text-center mt-2">
            별을 클릭하여 평가해보세요
          </p>
        )}
      </div>

      {/* Status Text Links */}
      <div className="flex items-center justify-center gap-4 text-sm pt-2">
        <button
          onClick={() => handleStatusClick('WANT_TO_WATCH')}
          className={`transition-colors underline-offset-2 hover:underline ${
            currentRating?.status === 'WANT_TO_WATCH'
              ? 'text-blue-600 font-semibold'
              : 'text-gray-600 hover:text-blue-500'
          }`}
        >
          {t('watchLater')}
        </button>
        <span className="text-gray-400">|</span>
        <button
          onClick={() => handleStatusClick('PASS')}
          className={`transition-colors underline-offset-2 hover:underline ${
            currentRating?.status === 'PASS'
              ? 'text-gray-800 font-semibold'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          {t('notInterested')}
        </button>
      </div>

      {currentRating && (
        <div className="mt-4 text-sm text-gray-600 text-center">
          평가일: {new Date(currentRating.created_at).toLocaleDateString('ko-KR')}
        </div>
      )}

      {/* 시리즈 일괄 처리 모달 */}
      {showSeriesModal && seriesInfo && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={handleSeriesCancel}>
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-xl font-bold mb-4">시리즈 일괄 처리</h3>

            <div className="mb-4">
              <p className="text-gray-700 mb-3">
                이 작품은 {seriesInfo.sequels.length}개의 후속작이 있습니다.
              </p>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-3">
                <p className="text-sm font-medium text-blue-900 mb-2">
                  후속작 목록:
                </p>
                <div className="max-h-32 overflow-y-auto space-y-1">
                  {seriesInfo.sequels.map((sequel, index) => (
                    <p key={sequel.id} className="text-sm text-gray-700">
                      {index + 1}. {sequel.title_korean || sequel.title_romaji}
                    </p>
                  ))}
                </div>
              </div>

              <p className="text-gray-700 mb-2">
                이 작품과 모든 후속작에 <strong className="text-blue-600">
                  {pendingStatus === 'WANT_TO_WATCH' ? t('watchLater') : t('notInterested')}
                </strong>를 적용하시겠습니까?
              </p>

              <p className="text-sm text-gray-500 bg-gray-50 p-3 rounded">
                💡 이전 시즌은 영향받지 않습니다. (이미 보셨거나 다른 평가를 했을 수 있으므로)
              </p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => handleSeriesConfirm(true)}
                className="flex-1 bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded font-medium transition-colors"
              >
                모두 적용 ({seriesInfo.sequels.length + 1}개)
              </button>
              <button
                onClick={() => handleSeriesConfirm(false)}
                className="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-700 py-2 px-4 rounded font-medium transition-colors"
              >
                현재만
              </button>
              <button
                onClick={handleSeriesCancel}
                className="bg-gray-200 hover:bg-gray-300 text-gray-700 py-2 px-4 rounded font-medium transition-colors"
              >
                취소
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 성공 메시지 토스트 */}
      {showSuccessMessage && (
        <div className="fixed bottom-8 left-1/2 transform -translate-x-1/2 z-50 animate-fade-in">
          <div className="bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg flex items-center gap-2">
            <span className="text-xl">✓</span>
            <span>{successText}</span>
          </div>
        </div>
      )}
    </div>
  );
}
