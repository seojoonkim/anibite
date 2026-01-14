import { useState, useEffect } from 'react';
import { useLanguage } from '../../context/LanguageContext';
import StarRating from './StarRating';

const IMAGE_BASE_URL = import.meta.env.VITE_API_URL || 'https://anipass-production.up.railway.app';

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

  // Helper to convert relative URLs to absolute
  const getImageUrl = (url) => {
    if (!url) return '/placeholder-anime.svg';
    if (url.startsWith('http')) return url;
    return `${IMAGE_BASE_URL}${url}`;
  };

  useEffect(() => {
    if (isOpen && activity) {
      setFormData({
        rating: activity.rating || 0,
        content: activity.review_content || '',
        is_spoiler: activity.is_spoiler || false
      });
      setError('');
    }
  }, [isOpen, activity]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // 별점 필수
    if (formData.rating === 0) {
      setError(language === 'ko' ? '별점을 선택해주세요.' : 'Please select a rating.');
      return;
    }

    // 리뷰 내용 검증 (edit_rating 모드가 아니고 내용이 있을 경우에만)
    if (mode !== 'edit_rating' && formData.content.trim()) {
      if (formData.content.trim().length < 10) {
        setError(language === 'ko' ? '리뷰는 최소 10자 이상 작성해주세요.' : 'Review must be at least 10 characters.');
        return;
      }
    }

    // add_review 모드에서는 리뷰 내용 필수
    if (mode === 'add_review' && !formData.content.trim()) {
      setError(language === 'ko' ? '리뷰 내용을 입력해주세요.' : 'Please enter review content.');
      return;
    }

    setSaving(true);
    try {
      await onSave(formData);
      onClose();
    } catch (err) {
      setError(language === 'ko' ? '저장에 실패했습니다.' : 'Failed to save.');
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  const getTitle = () => {
    if (mode === 'edit_rating') {
      return language === 'ko' ? '별점 수정' : 'Edit Rating';
    }
    if (mode === 'add_review') {
      return language === 'ko' ? '리뷰 추가' : 'Add Review';
    }
    return language === 'ko' ? '리뷰 수정' : 'Edit Review';
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">{getTitle()}</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="p-6">
          {error && (
            <div className="mb-4 p-3 bg-red-100 border border-red-300 text-red-800 rounded-md text-sm">
              {error}
            </div>
          )}

          {/* Item Info */}
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-4">
              <img
                src={getImageUrl(activity?.item_image)}
                alt={activity?.item_title_korean || activity?.item_title || 'Item'}
                className="w-16 h-20 object-cover rounded bg-gray-200"
                onError={(e) => {
                  e.target.src = '/placeholder-anime.svg';
                }}
              />
              <div>
                <h3 className="font-semibold text-gray-900">
                  {activity?.item_title_korean || activity?.item_title || 'Unknown'}
                </h3>
                {activity?.item_title_korean && activity?.item_title && (
                  <p className="text-sm text-gray-600">{activity.item_title}</p>
                )}
              </div>
            </div>
          </div>

          {/* Rating */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {language === 'ko' ? '별점' : 'Rating'} *
            </label>
            <StarRating
              rating={formData.rating}
              onRatingChange={(rating) => setFormData({ ...formData, rating })}
              size="lg"
              showNumber={true}
            />
          </div>

          {/* Review Content */}
          {mode !== 'edit_rating' && (
            <>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {language === 'ko' ? '리뷰 내용' : 'Review Content'} *
                </label>
                <textarea
                  value={formData.content}
                  onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md h-40 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder={language === 'ko' ? '이 작품에 대한 당신의 생각을 공유해주세요...' : 'Share your thoughts about this...'}
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  {formData.content.length} / 5000 {language === 'ko' ? '자' : 'characters'}
                </p>
              </div>

              {/* Spoiler */}
              <div className="mb-6">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.is_spoiler}
                    onChange={(e) => setFormData({ ...formData, is_spoiler: e.target.checked })}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">
                    {language === 'ko' ? '스포일러 포함' : 'Contains spoilers'}
                  </span>
                </label>
              </div>
            </>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors font-medium"
              disabled={saving}
            >
              {language === 'ko' ? '취소' : 'Cancel'}
            </button>
            <button
              type="submit"
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:bg-gray-400"
              disabled={saving}
            >
              {saving
                ? (language === 'ko' ? '저장 중...' : 'Saving...')
                : (language === 'ko' ? '저장' : 'Save')
              }
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
