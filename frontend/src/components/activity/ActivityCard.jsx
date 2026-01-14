/**
 * ActivityCard - Unified activity card component
 *
 * Displays all types of user activities with customizable layout
 *
 * Usage:
 * <ActivityCard
 *   activity={activity}
 *   context="feed"
 *   showOptions={{ showItemImage: true, showItemTitle: true }}
 *   onUpdate={() => refetch()}
 * />
 */
import { useState, useEffect, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import { useActivityLike, useActivityComments } from '../../hooks/useActivity';
import { getCurrentLevelInfo } from '../../utils/otakuLevels';
import ActivityComments from './ActivityComments';
import ContentMenu from '../common/ContentMenu';
import { ratingService } from '../../services/ratingService';
import { characterService } from '../../services/characterService';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const IMAGE_BASE_URL = import.meta.env.VITE_IMAGE_BASE_URL || API_BASE_URL;

/**
 * Context presets for common page layouts
 */
const CONTEXT_PRESETS = {
  feed: {
    showItemImage: true,
    showItemTitle: true,
    showUserInfo: true,
    compact: false
  },
  anime_page: {
    showItemImage: false,  // Already shown in page header
    showItemTitle: false,
    showUserInfo: true,
    compact: false
  },
  character_page: {
    showItemImage: false,
    showItemTitle: false,
    showUserInfo: true,
    compact: false
  },
  profile: {
    showItemImage: true,
    showItemTitle: true,
    showUserInfo: false,  // It's the user's own profile
    compact: false
  },
  notification: {
    showItemImage: true,
    showItemTitle: true,
    showUserInfo: true,
    compact: true  // Compact layout for notifications
  }
};

export default function ActivityCard({
  activity,
  context = 'feed',
  showOptions = {},
  onUpdate = null,
  notificationData = null  // Additional data for notification context
}) {
  const { language } = useLanguage();
  const { user } = useAuth();
  const navigate = useNavigate();

  // Merge context preset with custom showOptions
  const preset = CONTEXT_PRESETS[context] || CONTEXT_PRESETS.feed;
  const finalShowOptions = { ...preset, ...showOptions };

  // State
  const [showComments, setShowComments] = useState(activity.comments_count > 0);
  const [newCommentText, setNewCommentText] = useState('');
  const [replyingTo, setReplyingTo] = useState(null);
  const [replyText, setReplyText] = useState('');
  const [avatarError, setAvatarError] = useState(false);
  const [itemImageError, setItemImageError] = useState(false);
  const [bookmarked, setBookmarked] = useState(false);

  // Initialize bookmark state from localStorage
  useEffect(() => {
    const bookmarks = JSON.parse(localStorage.getItem('anipass_bookmarks') || '[]');
    setBookmarked(bookmarks.includes(activity.id));
  }, [activity.id]);

  // Hooks
  const { liked, likesCount, toggleLike } = useActivityLike(
    activity.id,
    activity.user_liked,
    activity.likes_count
  );

  const {
    comments,
    loading: commentsLoading,
    createComment,
    deleteComment
  } = useActivityComments(activity.id);

  // Helper functions
  const getImageUrl = (url) => {
    if (!url) return null;
    if (url.startsWith('http')) return url;
    return `${IMAGE_BASE_URL}${url}`;
  };

  const getAvatarUrl = (url) => {
    if (!url) return null;
    if (url.startsWith('http')) return url;
    return `${IMAGE_BASE_URL}${url}`;
  };

  const getActivityLink = () => {
    if (activity.activity_type === 'anime_rating') {
      return `/anime/${activity.item_id}`;
    } else if (activity.activity_type === 'character_rating') {
      return `/character/${activity.item_id}`;
    }
    return null;
  };

  const getActivityTypeMessage = () => {
    const hasReview = activity.review_title || activity.review_content;

    if (activity.activity_type === 'anime_rating') {
      if (hasReview) {
        return language === 'ko' ? '애니를 리뷰했어요' : 'reviewed an anime';
      }
      return language === 'ko' ? '애니를 평가했어요' : 'rated an anime';
    } else if (activity.activity_type === 'character_rating') {
      if (hasReview) {
        return language === 'ko' ? '캐릭터를 리뷰했어요' : 'reviewed a character';
      }
      return language === 'ko' ? '캐릭터를 평가했어요' : 'rated a character';
    } else if (activity.activity_type === 'user_post') {
      return language === 'ko' ? '포스트를 작성했어요' : 'created a post';
    }
    return '';
  };

  const toRoman = (num) => {
    const romanNumerals = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X'];
    return romanNumerals[num - 1] || num;
  };

  const getRelativeTime = (dateString) => {
    const now = new Date();

    // Backend sends UTC time without timezone info, so append 'Z' to parse as UTC
    const date = new Date(dateString.endsWith('Z') ? dateString : dateString.replace(' ', 'T') + 'Z');

    const diffMs = now - date;
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffSecs < 60) {
      return language === 'ko' ? '방금 전' : 'Just now';
    } else if (diffMins < 60) {
      return language === 'ko' ? `${diffMins}분 전` : `${diffMins}m ago`;
    } else if (diffHours < 24) {
      return language === 'ko' ? `${diffHours}시간 전` : `${diffHours}h ago`;
    } else if (diffDays < 7) {
      return language === 'ko' ? `${diffDays}일 전` : `${diffDays}d ago`;
    } else {
      return date.toLocaleDateString(language === 'ko' ? 'ko-KR' : 'en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    }
  };

  const levelInfo = getCurrentLevelInfo(activity.otaku_score || 0);

  // Reset error state when activity changes
  useEffect(() => {
    setItemImageError(false);
  }, [activity.id]);

  // Calculate item image src with useMemo - try R2 first, fallback to original on error
  const itemImageSrc = useMemo(() => {
    const url = activity.item_image;
    if (!url) return null;

    // If error occurred, use original URL
    if (itemImageError && url.startsWith('http')) {
      return url;
    }

    // If it's an AniList character image, try R2 first
    if (url.includes('anilist.co') && url.includes('/character/')) {
      const match = url.match(/\/b(\d+)-/);
      if (match && match[1]) {
        const characterId = match[1];
        return `${IMAGE_BASE_URL}/images/characters/${characterId}.jpg`;
      }
    }

    // If it's already a relative path, use IMAGE_BASE_URL
    if (!url.startsWith('http')) {
      return `${IMAGE_BASE_URL}${url}`;
    }

    // Otherwise use as-is
    return url;
  }, [activity.item_image, itemImageError]);

  // Handle item image load error - fallback to original AniList URL
  const handleItemImageError = () => {
    if (!itemImageError) {
      setItemImageError(true);
    }
  };

  // Handlers
  const handleLikeClick = async () => {
    if (!user) {
      alert(language === 'ko' ? '로그인이 필요합니다.' : 'Please login first.');
      return;
    }
    await toggleLike();
    // Don't call onUpdate() - let the hook handle optimistic updates
  };

  const handleBookmarkClick = () => {
    console.log('Bookmark button clicked!', { user, bookmarked, activityId: activity.id });

    if (!user) {
      alert(language === 'ko' ? '로그인이 필요합니다.' : 'Please login first.');
      return;
    }

    const bookmarks = JSON.parse(localStorage.getItem('anipass_bookmarks') || '[]');
    console.log('Current bookmarks:', bookmarks);

    if (bookmarked) {
      // Remove bookmark
      const newBookmarks = bookmarks.filter(id => id !== activity.id);
      localStorage.setItem('anipass_bookmarks', JSON.stringify(newBookmarks));
      setBookmarked(false);
      console.log('Bookmark removed. New bookmarks:', newBookmarks);
    } else {
      // Add bookmark
      const newBookmarks = [...bookmarks, activity.id];
      localStorage.setItem('anipass_bookmarks', JSON.stringify(newBookmarks));
      setBookmarked(true);
      console.log('Bookmark added. New bookmarks:', newBookmarks);
    }
  };

  const handleCommentSubmit = async () => {
    if (!user) {
      alert(language === 'ko' ? '로그인이 필요합니다.' : 'Please login first.');
      return;
    }

    if (!newCommentText.trim()) return;

    try {
      await createComment(newCommentText.trim());
      setNewCommentText('');
      // Don't call onUpdate() - useActivityComments already handles optimistic updates
    } catch (err) {
      console.error('Failed to create comment:', err);
      alert(language === 'ko' ? '댓글 작성에 실패했습니다.' : 'Failed to create comment.');
    }
  };

  const handleReplySubmit = async (parentCommentId) => {
    if (!user || !replyText.trim()) return;

    try {
      await createComment(replyText.trim(), parentCommentId);
      setReplyText('');
      setReplyingTo(null);
      // Don't call onUpdate() - useActivityComments already handles optimistic updates
    } catch (err) {
      console.error('Failed to create reply:', err);
      alert(language === 'ko' ? '답글 작성에 실패했습니다.' : 'Failed to create reply.');
    }
  };

  // ContentMenu handlers
  const handleEdit = () => {
    // Navigate to edit page or open edit modal
    if (activity.activity_type === 'anime_rating') {
      navigate(`/anime/${activity.item_id}`);
    } else if (activity.activity_type === 'character_rating') {
      navigate(`/character/${activity.item_id}`);
    }
  };

  const handleDelete = async () => {
    try {
      // Delete rating (which should also delete associated review)
      if (activity.activity_type === 'anime_rating') {
        await ratingService.deleteRating(activity.item_id);
      } else if (activity.activity_type === 'character_rating') {
        await characterService.deleteCharacterRating(activity.item_id);
      }

      // Refresh the feed
      if (onUpdate) {
        onUpdate();
      }
    } catch (err) {
      console.error('Failed to delete:', err);
      alert(language === 'ko' ? '삭제에 실패했습니다.' : 'Failed to delete.');
    }
  };

  const handleEditRating = () => {
    // Navigate to detail page where user can change rating
    if (activity.activity_type === 'anime_rating') {
      navigate(`/anime/${activity.item_id}`);
    } else if (activity.activity_type === 'character_rating') {
      navigate(`/character/${activity.item_id}`);
    }
  };

  const handleAddReview = () => {
    // Navigate to detail page where user can add review
    if (activity.activity_type === 'anime_rating') {
      navigate(`/anime/${activity.item_id}`);
    } else if (activity.activity_type === 'character_rating') {
      navigate(`/character/${activity.item_id}`);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-[0_2px_12px_rgba(0,0,0,0.08)] border border-gray-200 p-4 hover:shadow-[0_2px_12px_rgba(0,0,0,0.12)] transition-all">
      {/* Header: User Info + Activity Type + Timestamp */}
      {finalShowOptions.showUserInfo && (
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2.5">
            {/* User Avatar */}
            <Link to={`/user/${activity.user_id}`} className="flex-shrink-0">
              {activity.avatar_url && !avatarError ? (
                <img
                  src={getAvatarUrl(activity.avatar_url)}
                  alt={activity.display_name || activity.username}
                  className="w-9 h-9 rounded-full object-cover border border-gray-200"
                  onError={() => setAvatarError(true)}
                />
              ) : (
                <div
                  className="w-9 h-9 rounded-full flex items-center justify-center border border-gray-200"
                  style={{ background: 'linear-gradient(to bottom right, #90B2E4, #638CCC)' }}
                >
                  <span className="text-white text-sm font-bold">
                    {(activity.display_name || activity.username || '?').charAt(0).toUpperCase()}
                  </span>
                </div>
              )}
            </Link>

            {/* User Info + Activity Type */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <Link
                  to={`/user/${activity.user_id}`}
                  className="text-sm font-semibold text-gray-800 hover:text-[#3797F0] transition-colors"
                >
                  {activity.display_name || activity.username}
                </Link>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full font-semibold ${levelInfo.bgGradient} border ${levelInfo.borderColor}`}
                >
                  <span style={{ color: levelInfo.color }} className="font-bold">
                    {levelInfo.icon}
                  </span>{' '}
                  <span className="text-gray-700">
                    {levelInfo.level} - {toRoman(levelInfo.rank)}
                  </span>
                </span>
                <span className="text-sm text-gray-600">
                  {getActivityTypeMessage()}
                </span>
              </div>
            </div>
          </div>

          {/* Timestamp + Menu */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <span className="text-xs text-gray-400">
              {getRelativeTime(activity.activity_time)}
            </span>

            {/* ContentMenu */}
            <ContentMenu
              type={activity.activity_type}
              item={activity}
              onEdit={handleEdit}
              onDelete={handleDelete}
              onEditRating={handleEditRating}
              onAddReview={handleAddReview}
            />
          </div>
        </div>
      )}

      {/* Content: Item Image + Details */}
      <div className="flex gap-4">
        {/* Item Image (anime/character thumbnail) */}
        {finalShowOptions.showItemImage && activity.item_image && itemImageSrc && (
          <Link
            to={getActivityLink()}
            className="flex-shrink-0 hover:opacity-80 transition-opacity"
          >
            <img
              src={itemImageSrc}
              alt={activity.item_title || ''}
              className="w-16 h-24 object-cover rounded border-2 border-transparent hover:border-[#A8E6CF] transition-all"
              onError={handleItemImageError}
            />
          </Link>
        )}

        {/* Item Details */}
        <div className="flex-1 min-w-0">
          {/* Item Title */}
          {finalShowOptions.showItemTitle && activity.item_title && (
            <div className="mb-2">
              <Link
                to={getActivityLink()}
                className="block text-base font-semibold text-gray-800 hover:text-[#3797F0] transition-colors"
              >
                {activity.activity_type === 'character_rating' ? (
                  <>
                    {activity.item_title} <span className="text-gray-600">({activity.item_title_korean})</span>
                  </>
                ) : (
                  <>
                    {activity.item_title_korean || activity.item_title}
                  </>
                )}
              </Link>
              {activity.anime_title && (
                <Link
                  to={`/anime/${activity.anime_id}`}
                  className="text-xs text-gray-500 mt-0.5 hover:text-[#3797F0] transition-colors block"
                >
                  from: {activity.anime_title_korean || activity.anime_title}
                </Link>
              )}
            </div>
          )}

          {/* Rating */}
          {activity.rating && (
            <div className="flex items-center gap-px mb-2">
              {[...Array(5)].map((_, i) => {
                const starValue = i + 1;
                const fillPercentage =
                  activity.rating >= starValue
                    ? 100
                    : activity.rating > i
                    ? (activity.rating - i) * 100
                    : 0;

                return (
                  <div key={i} className="relative w-6 h-6">
                    <svg
                      className="w-6 h-6 text-gray-200"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                    {fillPercentage > 0 && (
                      <div
                        className="absolute top-0 left-0 overflow-hidden"
                        style={{ width: `${fillPercentage}%` }}
                      >
                        <svg
                          className="w-6 h-6"
                          fill="url(#star-gradient)"
                          viewBox="0 0 20 20"
                        >
                          <defs>
                            <linearGradient id="star-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                              <stop offset="0%" style={{ stopColor: '#FF6B6B', stopOpacity: 1 }} />
                              <stop offset="100%" style={{ stopColor: '#FF4757', stopOpacity: 1 }} />
                            </linearGradient>
                          </defs>
                          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                        </svg>
                      </div>
                    )}
                  </div>
                );
              })}
              <span className="ml-1.5 text-base font-bold text-gray-800">
                {activity.rating.toFixed(1)}
              </span>
            </div>
          )}

          {/* Review Title */}
          {activity.review_title && (
            <h3 className="text-base font-bold text-gray-900 mb-1">{activity.review_title}</h3>
          )}

          {/* Review Content */}
          {activity.review_content && (
            <div className="text-sm text-gray-700 whitespace-pre-wrap">
              {activity.is_spoiler ? (
                <details className="cursor-pointer">
                  <summary className="text-red-600 font-medium">
                    {language === 'ko' ? '스포일러 포함 (클릭하여 보기)' : 'Spoiler (Click to reveal)'}
                  </summary>
                  <p className="mt-2">{activity.review_content}</p>
                </details>
              ) : (
                <p>{activity.review_content}</p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Actions: Like, Comment, Bookmark */}
      <div className="mt-4 flex items-center justify-between">
            <div className="flex items-center gap-6">
              {/* Like Button */}
              <button
                onClick={handleLikeClick}
                className="flex items-center gap-2 transition-all hover:scale-110"
                style={{
                  color: liked ? '#DC2626' : '#6B7280'
                }}
              >
                {liked ? (
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
                  </svg>
                ) : (
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
                  </svg>
                )}
                <span className="text-sm font-medium">
                  {language === 'ko' ? '좋아요' : 'Like'}
                  {likesCount > 0 && <> {likesCount}</>}
                </span>
              </button>

              {/* Comment Button */}
              <button
                onClick={() => setShowComments(!showComments)}
                className="flex items-center gap-2 transition-all hover:scale-110 text-gray-600 hover:text-[#8EC5FC]"
              >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
                <span className="text-sm font-medium">
                  {language === 'ko' ? '댓글' : 'Comment'}
                  {activity.comments_count > 0 && <> {activity.comments_count}</>}
                </span>
              </button>
            </div>

            {/* Bookmark Button */}
            <button
              onClick={handleBookmarkClick}
              className="transition-all hover:scale-110"
            >
              {bookmarked ? (
                <svg width="24" height="24" viewBox="0 0 24 24">
                  <defs>
                    <linearGradient id="bookmark-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" style={{ stopColor: '#FF6B6B', stopOpacity: 1 }} />
                      <stop offset="100%" style={{ stopColor: '#FF4757', stopOpacity: 1 }} />
                    </linearGradient>
                  </defs>
                  <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" fill="url(#bookmark-gradient)" />
                </svg>
              ) : (
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#6B7280" strokeWidth="2">
                  <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
                </svg>
              )}
            </button>
      </div>

      {/* Comments Section */}
      {showComments && (
        <ActivityComments
          comments={comments}
          loading={commentsLoading}
          newCommentText={newCommentText}
          setNewCommentText={setNewCommentText}
          replyingTo={replyingTo}
          setReplyingTo={setReplyingTo}
          replyText={replyText}
          setReplyText={setReplyText}
          onCommentSubmit={handleCommentSubmit}
          onReplySubmit={handleReplySubmit}
          onDeleteComment={deleteComment}
          getAvatarUrl={getAvatarUrl}
          currentUser={user}
        />
      )}
    </div>
  );
}
