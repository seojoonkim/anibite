import { useState, useRef, useEffect } from 'react';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';

/**
 * ContentMenu - 컨텐츠 카드 우상단 ... 메뉴
 *
 * @param {object} props
 * @param {string} props.type - 'anime_rating' | 'character_rating'
 * @param {object} props.item - 컨텐츠 아이템 (rating, review 등)
 * @param {function} props.onEdit - 수정 콜백
 * @param {function} props.onDelete - 삭제 콜백
 * @param {function} props.onEditRating - 별점 수정 콜백 (리뷰 없을 때)
 * @param {function} props.onAddReview - 리뷰 추가 콜백 (리뷰 없을 때)
 */
export default function ContentMenu({
  type,
  item,
  onEdit,
  onDelete,
  onEditRating,
  onAddReview
}) {
  const { language } = useLanguage();
  const { user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef(null);

  const hasReview = item.review_content && item.review_content.trim();

  // Only show menu for own content
  const isOwnContent = user && item.user_id && user.id === item.user_id;

  // Debug log
  console.log('ContentMenu Debug:', {
    user: user?.id,
    item_user_id: item.user_id,
    isOwnContent,
    type,
    item
  });

  if (!isOwnContent) {
    return null;
  }

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleMenuClick = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsOpen(!isOpen);
  };

  const handleAction = (action) => {
    setIsOpen(false);
    action();
  };

  const handleDelete = () => {
    const itemName = type === 'anime_rating'
      ? (item.item_title_korean || item.item_title || item.anime_title)
      : (item.item_title_korean || item.item_title || item.character_name);

    const message = language === 'ko'
      ? `"${itemName}"의 평가와 리뷰를 모두 삭제하시겠습니까?`
      : `Delete rating and review for "${itemName}"?`;

    if (window.confirm(message)) {
      onDelete();
    }
  };

  return (
    <div ref={menuRef} className="relative">
      {/* ... 버튼 */}
      <button
        onClick={handleMenuClick}
        className="p-2 rounded-full hover:bg-gray-200 transition-colors"
        aria-label="More options"
      >
        <svg
          className="w-5 h-5 text-gray-600"
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
        </svg>
      </button>

      {/* 드롭다운 메뉴 */}
      {isOpen && (
        <div className="absolute right-0 mt-1 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50">
          {hasReview ? (
            // 리뷰가 있는 경우
            <>
              <button
                onClick={() => handleAction(onEdit)}
                className="w-full text-left px-4 py-2 hover:bg-gray-100 transition-colors text-sm"
              >
                {language === 'ko' ? '리뷰 수정' : 'Edit Review'}
              </button>
            </>
          ) : (
            // 리뷰가 없는 경우 (평가만 있음)
            <>
              <button
                onClick={() => handleAction(onEditRating)}
                className="w-full text-left px-4 py-2 hover:bg-gray-100 transition-colors text-sm"
              >
                {language === 'ko' ? '별점 수정' : 'Edit Rating'}
              </button>
              <button
                onClick={() => handleAction(onAddReview)}
                className="w-full text-left px-4 py-2 hover:bg-gray-100 transition-colors text-sm"
              >
                {language === 'ko' ? '리뷰 추가' : 'Add Review'}
              </button>
            </>
          )}

          <div className="border-t border-gray-200 my-1"></div>

          <button
            onClick={() => handleAction(handleDelete)}
            className="w-full text-left px-4 py-2 hover:bg-red-50 transition-colors text-sm text-red-600"
          >
            {language === 'ko' ? '삭제' : 'Delete'}
          </button>
        </div>
      )}
    </div>
  );
}
