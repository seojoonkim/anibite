import { useState } from 'react';
import Dialog from './Dialog';
import { useLanguage } from '../../context/LanguageContext';
import StarRating from './StarRating';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const IMAGE_BASE_URL = import.meta.env.VITE_IMAGE_BASE_URL || API_BASE_URL;

/**
 * EditReviewModal - 리뷰 수정 모달
 *
 * @param {object} props
 * @param {boolean} props.isOpen - 모달 열림 상태
 * @param {function} props.onClose - 모달 닫기 콜백
 * @param {object} props.activity - 수정할 activity 객체
 * @param {function} props.onSave - 저장 콜백
 * @param {string} props.mode - 'edit' | 'add_review' | 'edit_rating'
 */
export default function EditReviewModal({ isOpen, onClose, activity, onSave, mode = 'edit' }) {
  const { language } = useLanguage();
  const [formData, setFormData] = useState({
    rating: 0,
    content: '',
    is_spoiler: false
  });
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  // Helper to convert relative URLs to absolute - same logic as ActivityCard
  const getImageUrl = (url, activityType = null, itemId = null) => {
    // 캐릭터 평가의 경우 itemId를 직접 사용 (가장 안정적)
    if (activityType === 'character_rating' && itemId) {
      return `${API_BASE_URL}/api/images/characters/${itemId}.jpg`;
    }

    if (!url) return '/placeholder-anime.svg';

    // Normalize URL: ensure it starts with / if it's a relative path
    if (!url.startsWith('http') && !url.startsWith('/')) {
      url = `/${url}`;
    }

    // For character images from R2 paths - use backend API proxy
    if (url.includes('/characters/')) {
      // Extract character ID from path like "/images/characters/8485.jpg"
      const match = url.match(/\/characters\/(\d+)\./);
      if (match && match[1]) {
        return `${API_BASE_URL}/api/images/characters/${match[1]}.jpg`;
      }
    }

    // If it's an AniList character image, use API proxy
    if (url.includes('anilist.co') && url.includes('/character/')) {
      const match = url.match(/\/[bn](\d+)-/);
      if (match && match[1]) {
        return `${API_BASE_URL}/api/images/characters/${match[1]}.jpg`;
      }
    }

    // If it's an AniList anime cover image, try R2 first
    if (url.includes('anilist.co') && url.includes('/media/')) {
      // Extract anime ID from URL patterns like /b123456- or /n123456-
      const match = url.match(/\/[bn](\d+)-/);
      if (match && match[1]) {
        const animeId = match[1];
        return `${IMAGE_BASE_URL}/images/covers_large/${animeId}.jpg`;
      }
    }

    // If it's a relative path, use IMAGE_BASE_URL
    if (!url.startsWith('http')) {
      return `${IMAGE_BASE_URL}${url}`;
    }

    // External URLs - try to use them directly, fallback to placeholder on error
    return url;
  };

  // Keep a draft across close/reopen for this item; never persist private text to storage.
  const draftKey = `${activity?.id ?? activity?.item_id}:${mode}`;
  const [loadedKey, setLoadedKey] = useState(null);
  if (activity && loadedKey !== draftKey) {
    setLoadedKey(draftKey);
    setFormData({ rating: activity.rating || 0, content: activity.review_content || '', is_spoiler: activity.is_spoiler || false });
    setError('');
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (saving) return;
    if (formData.content.length > 5000) { setError(language === 'ko' ? '리뷰는 5000자 이하여야 합니다.' : 'Review must be at most 5000 characters.'); return; }

    // 별점 필수
    if (formData.rating === 0) {
      setError(language === 'ko' ? '별점을 선택해주세요.' : language === 'ja' ? '評価を選択してください。' : 'Please select a rating.');
      return;
    }

    // 리뷰 내용 검증 (edit_rating 모드가 아니고 내용이 있을 경우에만)
    if (mode !== 'edit_rating' && formData.content.trim()) {
      if (formData.content.trim().length < 10) {
        setError(language === 'ko' ? '리뷰는 최소 10자 이상 작성해주세요.' : language === 'ja' ? 'レビューは10文字以上で入力してください。' : 'Review must be at least 10 characters.');
        return;
      }
    }

    // add_review 모드에서는 리뷰 내용 필수
    if (mode === 'add_review' && !formData.content.trim()) {
      setError(language === 'ko' ? '리뷰 내용을 입력해주세요.' : language === 'ja' ? 'レビュー内容を入力してください。' : 'Please enter review content.');
      return;
    }

    setSaving(true);
    try {
      await onSave(formData);
      onClose();
    } catch {
      setError(language === 'ko' ? '저장에 실패했습니다.' : language === 'ja' ? '保存に失敗しました。' : 'Failed to save.');
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  const getTitle = () => {
    // 통일된 제목 - 별점과 리뷰를 함께 수정 가능
    return language === 'ko' ? '평가 수정' : language === 'ja' ? '評価を編集' : 'Edit Rating';
  };

  const modalContent = (
    <Dialog title={getTitle()} onClose={onClose} busy={saving}>
      <div
        className="bg-white rounded-xl shadow-xl max-w-xl w-full max-h-[90vh] overflow-y-auto"
        style={{ position: 'relative', zIndex: 10000 }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-2.5 border-b border-gray-200">
          <h2 className="text-base font-semibold text-gray-900">{getTitle()}</h2>
          <button
            onClick={onClose}
            disabled={saving}
            aria-label={language === 'ko' ? '닫기 (초안 유지)' : 'Close (keep draft)'}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="p-4">
          {error && (
            <div role="alert" className="mb-3 p-2.5 bg-red-100 border border-red-300 text-red-800 rounded-md text-sm">
              {error}
            </div>
          )}

          {/* Item Info */}
          <div className="mb-4">
            <div className="flex items-center gap-3">
              <img
                src={getImageUrl(activity?.item_image, activity?.activity_type, activity?.item_id)}
                alt={activity?.item_title_korean || activity?.item_title || 'Item'}
                className="w-[84px] h-[105px] object-cover rounded bg-gray-200 flex-shrink-0"
                onError={(e) => {
                  e.target.src = '/placeholder-anime.svg';
                }}
              />
              <div className="min-w-0 flex-1">
                <h3 className="font-semibold text-gray-900 text-xl">
                  {activity?.activity_type === 'character_rating' ? (
                    <>
                      {activity?.item_title}{' '}
                      <span className="text-gray-600">({activity?.item_title_korean})</span>
                    </>
                  ) : (
                    activity?.item_title_korean || activity?.item_title || 'Unknown'
                  )}
                </h3>
                {activity?.activity_type === 'character_rating' && (activity?.anime_title || activity?.anime_title_korean) && (
                  <p className="text-sm text-gray-600 mt-0.5">
                    from: {activity.anime_title_korean || activity.anime_title}
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Rating */}
          <div className="mb-3">
            <div className="flex items-center gap-2 mb-1.5">
              <label className="text-sm font-medium text-gray-700">
                {language === 'ko' ? '별점' : language === 'ja' ? '評価' : 'Rating'}
              </label>
              <span className="text-xs text-gray-500 font-normal">
                ({language === 'ko' ? '클릭하여 수정' : language === 'ja' ? 'クリックして編集' : 'Click to edit'})
              </span>
            </div>
            <div className="flex items-center gap-4">
              <StarRating
                rating={formData.rating}
                onRatingChange={(rating) => setFormData({ ...formData, rating })}
                size="xl"
                showNumber={false}
              />
              {formData.rating > 0 && (
                <span className="text-2xl font-bold text-gray-700">{formData.rating.toFixed(1)}</span>
              )}
            </div>
          </div>

          {/* Review Content */}
          <div className="mb-3">
            <label htmlFor="review-content" className="block text-sm font-medium text-gray-700 mb-1.5">
              {language === 'ko' ? '리뷰 내용' : language === 'ja' ? 'レビュー内容' : 'Review Content'}{' '}
              {mode === 'add_review' ? '*' : (
                <span className="text-gray-500 font-normal text-xs">
                  ({language === 'ko' ? '선택' : language === 'ja' ? 'オプション' : 'Optional'})
                </span>
              )}
            </label>
            <textarea
              id="review-content"
              maxLength={5000}
              aria-invalid={!!error}
              value={formData.content}
              onChange={(e) => setFormData({ ...formData, content: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md h-28 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
              placeholder={language === 'ko' ? '이 작품에 대한 당신의 생각을 공유해주세요...' : language === 'ja' ? 'この作品についてのあなたの考えを共有してください...' : 'Share your thoughts about this...'}
              required={mode === 'add_review'}
            />
            <p className="text-xs text-gray-500 mt-1">
              {formData.content.length} / 5000 {language === 'ko' ? '자' : language === 'ja' ? '文字' : 'characters'}
            </p>
          </div>

          {/* Spoiler */}
          <div className="mb-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                id="spoiler-checkbox"
                checked={formData.is_spoiler}
                onChange={(e) => setFormData({ ...formData, is_spoiler: e.target.checked })}
                className="mr-2"
              />
              <span className="text-sm text-gray-700">
                {language === 'ko' ? '스포일러 포함' : language === 'ja' ? 'ネタバレを含む' : 'Contains spoilers'}
              </span>
            </label>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-5 py-1.5 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors font-medium text-sm"
              disabled={saving}
            >
              {language === 'ko' ? '취소' : language === 'ja' ? 'キャンセル' : 'Cancel'}
            </button>
            <button
              type="submit"
              className="px-5 py-1.5 text-white rounded-lg transition-colors text-sm disabled:bg-gray-400"
              style={{ backgroundColor: '#47B5FF' }}
              onMouseEnter={(e) => !e.target.disabled && (e.target.style.backgroundColor = '#2DA0ED')}
              onMouseLeave={(e) => !e.target.disabled && (e.target.style.backgroundColor = '#47B5FF')}
              disabled={saving}
            >
              {saving
                ? (language === 'ko' ? '저장 중...' : language === 'ja' ? '保存中...' : 'Saving...')
                : (language === 'ko' ? '저장' : language === 'ja' ? '保存' : 'Save')
              }
            </button>
          </div>
        </form>
      </div>
    </Dialog>
  );

  return modalContent;
}
