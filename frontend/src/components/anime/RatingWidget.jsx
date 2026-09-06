import { useState, useRef } from 'react';
import RatingEditor from '../common/RatingEditor';
import Dialog from '../common/Dialog';
import { seriesService } from '../../services/seriesService';
import { useLanguage } from '../../context/LanguageContext';

export default function RatingWidget({ animeId, currentRating, onRate, onStatusChange }) {
  const { t } = useLanguage();
  const [showSeriesModal, setShowSeriesModal] = useState(false);
  const [seriesInfo, setSeriesInfo] = useState(null);
  const [pendingStatus, setPendingStatus] = useState(null);
  const [showSuccessMessage, setShowSuccessMessage] = useState(false);
  const [successText, setSuccessText] = useState('');

  const [busy, setBusy] = useState(false);
  const inFlight = useRef(false);
  const [failedAction, setFailedAction] = useState(null);
  const { language } = useLanguage();

  const runStatusAction = async (action) => {
    if (inFlight.current) return;
    inFlight.current = true;
    setBusy(true);
    setFailedAction(null);
    try {
      await action();
    } catch {
      setFailedAction(() => action);
    } finally {
      inFlight.current = false;
      setBusy(false);
    }
  };

  const handleStatusClick = (status) => runStatusAction(async () => {
    if (currentRating?.status === status) {
      await onStatusChange(null);
      return;
    }
    const series = await seriesService.getAnimeSequels(animeId);
    if (series?.sequels?.length) {
      setSeriesInfo(series);
      setPendingStatus(status);
      setShowSeriesModal(true);
      return;
    }
    await onStatusChange(status);
  });

  const handleSeriesConfirm = (applyToAll) => runStatusAction(async () => {
    if (applyToAll && seriesInfo) {
      await seriesService.bulkRateSeries([animeId, ...seriesInfo.sequels.map(s => s.id)], pendingStatus);
    }
    await onStatusChange(pendingStatus);
    setShowSeriesModal(false);
    setSeriesInfo(null);
    setPendingStatus(null);
    if (applyToAll) {
      setSuccessText(language === 'ko' ? '시리즈 상태를 저장했습니다.' : 'Series status saved.');
      setShowSuccessMessage(true);
      setTimeout(() => setShowSuccessMessage(false), 3000);
    }
  });

  const saveRating = async (value) => {
    if (inFlight.current) throw new Error('A save is already pending');
    inFlight.current = true;
    setBusy(true);
    setFailedAction(null);
    try {
      await (value === 0 ? onStatusChange(null) : onRate(value, 'RATED'));
    } finally {
      inFlight.current = false;
      setBusy(false);
    }
  };

  const handleSeriesCancel = () => {
    if (inFlight.current) return;
    setFailedAction(null);
    setShowSeriesModal(false);
    setSeriesInfo(null);
    setPendingStatus(null);
  };

  const statusError = failedAction && <div role="alert"><p>{language === 'ko' ? '저장하지 못했습니다. 다시 시도해주세요.' : 'Not saved. Please retry.'}</p><button disabled={busy} onClick={() => runStatusAction(failedAction)}>{language === 'ko' ? '다시 시도' : 'Retry'}</button></div>;

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-lg font-bold mb-4">내 평가</h3>

      <RatingEditor rating={currentRating?.rating || 0} disabled={busy || showSeriesModal} onSave={saveRating}/>
      {!showSeriesModal && statusError}

      {/* Status Text Links */}
      <div className="flex items-center justify-center gap-4 text-sm pt-2">
        <button
          disabled={busy || showSeriesModal}
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
          disabled={busy || showSeriesModal}
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
        <Dialog title="시리즈 일괄 처리" onClose={handleSeriesCancel}>
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

            {statusError}
            <div className="flex gap-3">
              <button
                disabled={busy}
                onClick={() => handleSeriesConfirm(true)}
                className="flex-1 bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded font-medium transition-colors"
              >
                모두 적용 ({seriesInfo.sequels.length + 1}개)
              </button>
              <button
                disabled={busy}
                onClick={() => handleSeriesConfirm(false)}
                className="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-700 py-2 px-4 rounded font-medium transition-colors"
              >
                현재만
              </button>
              <button
                disabled={busy}
                onClick={handleSeriesCancel}
                className="bg-gray-200 hover:bg-gray-300 text-gray-700 py-2 px-4 rounded font-medium transition-colors"
              >
                취소
              </button>
            </div>
          </div>
        </Dialog>
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
