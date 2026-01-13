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
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import { useActivityLike, useActivityComments } from '../../hooks/useActivity';
import { getCurrentLevelInfo } from '../../utils/otakuLevels';
import ActivityComments from './ActivityComments';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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

  // Merge context preset with custom showOptions
  const preset = CONTEXT_PRESETS[context] || CONTEXT_PRESETS.feed;
  const finalShowOptions = { ...preset, ...showOptions };

  // State
  const [showComments, setShowComments] = useState(false);
  const [newCommentText, setNewCommentText] = useState('');
  const [replyingTo, setReplyingTo] = useState(null);
  const [replyText, setReplyText] = useState('');

  // Hooks
  const { liked, likesCount, toggleLike } = useActivityLike(
    activity.id,
    activity.user_liked,
    activity.likes_count
  );

  const {
    comments,
    loading: commentsLoading,
    createComment
  } = useActivityComments(activity.id);

  // Helper functions
  const getImageUrl = (url) => {
    if (!url) return null;
    if (url.startsWith('http')) return url;
    return `${API_BASE_URL}${url}`;
  };

  const getAvatarUrl = (url) => {
    if (!url) return null;
    if (url.startsWith('http')) return url;
    return `${API_BASE_URL}${url}`;
  };

  const getActivityLink = () => {
    if (activity.activity_type === 'anime_rating') {
      return `/anime/${activity.item_id}`;
    } else if (activity.activity_type === 'character_rating') {
      return `/character/${activity.item_id}`;
    }
    return null;
  };

  const toRoman = (num) => {
    const romanNumerals = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X'];
    return romanNumerals[num - 1] || num;
  };

  const levelInfo = getCurrentLevelInfo(activity.otaku_score || 0);

  // Handlers
  const handleLikeClick = async () => {
    if (!user) {
      alert(language === 'ko' ? '로그인이 필요합니다.' : 'Please login first.');
      return;
    }
    await toggleLike();
    if (onUpdate) onUpdate();
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
      if (onUpdate) onUpdate();
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
      if (onUpdate) onUpdate();
    } catch (err) {
      console.error('Failed to create reply:', err);
      alert(language === 'ko' ? '답글 작성에 실패했습니다.' : 'Failed to create reply.');
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-[0_2px_12px_rgba(0,0,0,0.08)] border border-gray-200 p-4 hover:shadow-[0_2px_12px_rgba(0,0,0,0.12)] transition-all">
      <div className={finalShowOptions.showItemImage ? 'flex gap-4' : ''}>
        {/* Item Image (anime/character thumbnail) */}
        {finalShowOptions.showItemImage && activity.item_image && (
          <Link
            to={getActivityLink()}
            className="flex-shrink-0 hover:opacity-80 transition-opacity"
          >
            <img
              src={getImageUrl(activity.item_image)}
              alt={activity.item_title || ''}
              className="w-16 h-24 object-cover rounded border-2 border-transparent hover:border-[#A8E6CF] transition-all"
              onError={(e) => {
                e.target.src = '/placeholder-anime.svg';
              }}
            />
          </Link>
        )}

        {/* Main Content */}
        <div className="flex-1 min-w-0">
          {/* User Info Header */}
          {finalShowOptions.showUserInfo && (
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                {/* User Avatar */}
                <Link to={`/user/${activity.user_id}`} className="flex-shrink-0">
                  {activity.avatar_url ? (
                    <img
                      src={getAvatarUrl(activity.avatar_url)}
                      alt={activity.display_name || activity.username}
                      className="w-8 h-8 rounded-full object-cover border border-gray-200"
                    />
                  ) : (
                    <div
                      className="w-8 h-8 rounded-full flex items-center justify-center border border-gray-200"
                      style={{ background: 'linear-gradient(to bottom right, #90B2E4, #638CCC)' }}
                    >
                      <span className="text-white text-xs font-bold">
                        {(activity.display_name || activity.username || '?').charAt(0).toUpperCase()}
                      </span>
                    </div>
                  )}
                </Link>

                {/* Username & Level */}
                <div className="flex items-center gap-2">
                  <Link
                    to={`/user/${activity.user_id}`}
                    className="text-sm font-medium text-gray-700 hover:text-[#A8E6CF] transition-colors"
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
                </div>
              </div>

              {/* Timestamp */}
              <span className="text-xs text-gray-400 ml-2">
                {new Date(activity.activity_time).toLocaleDateString(language === 'ko' ? 'ko-KR' : 'en-US')}
              </span>
            </div>
          )}

          {/* Item Title (for context where it should be shown) */}
          {finalShowOptions.showItemTitle && activity.item_title && (
            <Link
              to={getActivityLink()}
              className="block mb-2 text-sm font-medium text-gray-800 hover:text-[#A8E6CF] transition-colors"
            >
              {activity.item_title_korean || activity.item_title}
              {activity.anime_title && (
                <span className="text-xs text-gray-500 ml-1">
                  ({activity.anime_title_korean || activity.anime_title})
                </span>
              )}
            </Link>
          )}

          {/* Rating */}
          {activity.rating && (
            <div className="flex items-center gap-1 mb-2">
              {[...Array(5)].map((_, i) => {
                const starValue = i + 1;
                const fillPercentage =
                  activity.rating >= starValue
                    ? 100
                    : activity.rating > i
                    ? (activity.rating - i) * 100
                    : 0;

                return (
                  <div key={i} className="relative w-5 h-5">
                    <svg
                      className="w-5 h-5 text-gray-200"
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
                          className="w-5 h-5 text-[#FFD700]"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                        </svg>
                      </div>
                    )}
                  </div>
                );
              })}
              <span className="ml-1 text-sm font-semibold text-gray-700">
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

          {/* Like, Comment Buttons */}
          <div className="mt-3 flex items-center justify-between">
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
              getAvatarUrl={getAvatarUrl}
            />
          )}
        </div>
      </div>
    </div>
  );
}
