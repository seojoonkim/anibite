import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { useActivities } from '../hooks/useActivity';
import { activityService } from '../services/activityService';
import { notificationService } from '../services/notificationService';
import Navbar from '../components/common/Navbar';
import ActivityCard from '../components/activity/ActivityCard';
import NotificationCard from '../components/feed/NotificationCard';
import { getAvatarUrl as getAvatarUrlHelper } from '../utils/imageHelpers';

export default function Feed() {
  const { user } = useAuth();
  const { language } = useLanguage();
  const [searchParams, setSearchParams] = useSearchParams();

  const [feedFilter, setFeedFilter] = useState(searchParams.get('filter') || 'all');
  const [newPostContent, setNewPostContent] = useState('');
  const [savedActivities, setSavedActivities] = useState(new Set());
  const [notifications, setNotifications] = useState([]);
  const [notificationsLoading, setNotificationsLoading] = useState(false);

  // Use unified activities hook for all/following filters
  const {
    activities,
    loading,
    error,
    refetch
  } = useActivities(
    {
      followingOnly: feedFilter === 'following',
      limit: 50,
      offset: 0
    },
    {
      autoFetch: feedFilter === 'all' || feedFilter === 'following'
    }
  );

  // Load saved activities from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('savedActivities');
    if (saved) {
      setSavedActivities(new Set(JSON.parse(saved)));
    }
  }, []);

  // Update feedFilter when URL changes
  useEffect(() => {
    const filterParam = searchParams.get('filter') || 'all';
    if (filterParam !== feedFilter) {
      setFeedFilter(filterParam);
    }

    // Handle highlight parameter
    const highlightKey = searchParams.get('highlight');
    if (highlightKey) {
      setTimeout(() => {
        const element = document.getElementById(`activity-${highlightKey}`);
        if (element) {
          element.scrollIntoView({ behavior: 'smooth', block: 'center' });
          element.classList.add('highlight-animation');
          setTimeout(() => {
            element.classList.remove('highlight-animation');
          }, 3000);
        }
      }, 500);
    }
  }, [searchParams]);

  // Load notifications when filter is 'notifications'
  useEffect(() => {
    if (feedFilter === 'notifications') {
      loadNotifications();
    }
  }, [feedFilter]);

  // Reload saved feed from localStorage when filter changes to 'saved'
  useEffect(() => {
    if (feedFilter === 'saved') {
      const saved = localStorage.getItem('savedActivities');
      if (saved) {
        setSavedActivities(new Set(JSON.parse(saved)));
      }
    }
  }, [feedFilter]);

  const loadNotifications = async () => {
    try {
      setNotificationsLoading(true);
      const notificationData = await notificationService.getNotifications(50, 0);

      // Mark as read
      await notificationService.markAsRead();

      if (!notificationData.items || notificationData.items.length === 0) {
        setNotifications([]);
        setNotificationsLoading(false);
        return;
      }

      // Group notifications by item_id + activity_type
      const groupedNotifications = {};
      notificationData.items.forEach((notification) => {
        const key = `${notification.activity_type}_${notification.item_id}`;
        if (!groupedNotifications[key]) {
          groupedNotifications[key] = [];
        }
        groupedNotifications[key].push(notification);
      });

      // Transform to activities format
      const transformedActivities = Object.values(groupedNotifications).map(notificationGroup => {
        const latestNotification = notificationGroup[0];

        return {
          id: `notification-${latestNotification.activity_type}-${latestNotification.item_id}`,
          activity_type: latestNotification.activity_type,
          user_id: latestNotification.target_user_id,
          item_id: latestNotification.item_id,
          username: latestNotification.activity_username,
          display_name: latestNotification.activity_display_name,
          avatar_url: latestNotification.activity_avatar_url,
          otaku_score: latestNotification.activity_otaku_score || 0,
          item_title: latestNotification.item_title,
          item_title_korean: latestNotification.item_title,
          item_image: latestNotification.item_image,
          anime_id: latestNotification.anime_id,
          anime_title: latestNotification.anime_title,
          anime_title_korean: latestNotification.anime_title_korean,
          rating: latestNotification.my_rating,
          review_content: latestNotification.activity_text,
          review_title: null,
          is_spoiler: false,
          activity_time: latestNotification.activity_created_at,
          likes_count: latestNotification.activity_likes_count,
          comments_count: latestNotification.activity_comments_count,
          user_liked: Boolean(latestNotification.user_has_liked),
          _notifications: notificationGroup
        };
      });

      setNotifications(transformedActivities);
      setNotificationsLoading(false);
    } catch (err) {
      console.error('Failed to load notifications:', err);
      setNotifications([]);
      setNotificationsLoading(false);
    }
  };

  const handleSaveActivity = (activityId) => {
    setSavedActivities(prev => {
      const newSet = new Set(prev);
      if (newSet.has(activityId)) {
        newSet.delete(activityId);
      } else {
        newSet.add(activityId);
      }
      localStorage.setItem('savedActivities', JSON.stringify([...newSet]));
      return newSet;
    });
  };

  const handleCreatePost = async () => {
    if (!newPostContent || !newPostContent.trim()) return;

    try {
      await activityService.createActivity({
        activity_type: 'user_post',
        content: newPostContent.trim()
      });
      setNewPostContent('');
      refetch();
    } catch (err) {
      console.error('Failed to create post:', err);
      alert(language === 'ko' ? '게시 실패' : 'Failed to post');
    }
  };

  const getAvatarUrl = (avatarUrl) => {
    return getAvatarUrlHelper(avatarUrl) || '/placeholder-avatar.png';
  };

  const getTimeAgo = (timestamp) => {
    const now = new Date();
    // Backend sends UTC time without timezone info, so append 'Z' to parse as UTC
    const activityTime = new Date(timestamp.endsWith('Z') ? timestamp : timestamp.replace(' ', 'T') + 'Z');
    const diff = now - activityTime;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (language === 'ko') {
      if (minutes < 60) return `${Math.max(1, minutes)}분 전`;
      if (hours < 24) return `${hours}시간 전`;
      if (days < 7) return `${days}일 전`;
      return activityTime.toLocaleDateString('ko-KR');
    } else {
      if (minutes < 60) return `${Math.max(1, minutes)}m ago`;
      if (hours < 24) return `${hours}h ago`;
      if (days < 7) return `${days}d ago`;
      return activityTime.toLocaleDateString('en-US');
    }
  };

  // Get activities based on filter
  const getFilteredActivities = () => {
    if (feedFilter === 'notifications') {
      return notifications;
    } else if (feedFilter === 'saved') {
      return activities.filter(activity =>
        savedActivities.has(`${activity.activity_type}_${activity.user_id}_${activity.item_id}`)
      );
    }
    return activities;
  };

  const filteredActivities = getFilteredActivities();
  const isLoading = feedFilter === 'notifications' ? notificationsLoading : loading;

  return (
    <div className="min-h-screen pt-0 md:pt-16 bg-transparent">
      <Navbar />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8">
        <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-6">
          {/* Left Sidebar - Filter Menu */}
          <aside className="hidden lg:block">
            <div className="fixed top-24 w-[280px] z-40">
              <nav>
                <div className="flex flex-col gap-2">
                  <button
                    onClick={() => setSearchParams({ filter: 'all' })}
                    className={`w-full text-left px-4 py-2.5 rounded-lg text-sm font-medium transition-all flex items-center gap-3 ${
                      feedFilter === 'all'
                        ? 'bg-[#3797F0] text-white font-semibold'
                        : 'text-gray-600 hover:text-black hover:bg-gray-100'
                    }`}
                  >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="3" y="3" width="7" height="7"></rect>
                      <rect x="14" y="3" width="7" height="7"></rect>
                      <rect x="14" y="14" width="7" height="7"></rect>
                      <rect x="3" y="14" width="7" height="7"></rect>
                    </svg>
                    {language === 'ko' ? '전체 보기' : 'View All'}
                  </button>

                  <button
                    onClick={() => setSearchParams({ filter: 'following' })}
                    className={`w-full text-left px-4 py-2.5 rounded-lg text-sm font-medium transition-all flex items-center gap-3 ${
                      feedFilter === 'following'
                        ? 'bg-[#3797F0] text-white font-semibold'
                        : 'text-gray-600 hover:text-black hover:bg-gray-100'
                    }`}
                  >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                      <circle cx="9" cy="7" r="4"></circle>
                      <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                      <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                    </svg>
                    {language === 'ko' ? '팔로잉 보기' : 'Following'}
                  </button>

                  <button
                    onClick={() => setSearchParams({ filter: 'notifications' })}
                    className={`w-full text-left px-4 py-2.5 rounded-lg text-sm font-medium transition-all flex items-center gap-3 ${
                      feedFilter === 'notifications'
                        ? 'bg-[#3797F0] text-white font-semibold'
                        : 'text-gray-600 hover:text-black hover:bg-gray-100'
                    }`}
                  >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                      <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                    </svg>
                    {language === 'ko' ? '알림 보기' : 'Notifications'}
                  </button>

                  <button
                    onClick={() => setSearchParams({ filter: 'saved' })}
                    className={`w-full text-left px-4 py-2.5 rounded-lg text-sm font-medium transition-all flex items-center gap-3 ${
                      feedFilter === 'saved'
                        ? 'bg-[#3797F0] text-white font-semibold'
                        : 'text-gray-600 hover:text-black hover:bg-gray-100'
                    }`}
                  >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
                    </svg>
                    {language === 'ko' ? '저장한 피드' : 'Saved'}
                  </button>
                </div>
              </nav>
            </div>
          </aside>

          {/* Right Content - Feed */}
          <div>
            {/* Post Composer */}
            {user && (
              <div className="bg-white rounded-xl shadow-[0_2px_12px_rgba(0,0,0,0.08)] border border-gray-200 p-4 mb-6">
                <div className="flex gap-3">
                  {user.avatar_url ? (
                    <img
                      src={getAvatarUrl(user.avatar_url)}
                      alt={user.display_name || user.username}
                      className="w-12 h-12 rounded-full object-cover border border-gray-200"
                    />
                  ) : (
                    <div className="w-12 h-12 rounded-full flex items-center justify-center border border-gray-200" style={{ backgroundColor: '#364F6B' }}>
                      <span className="text-white text-base font-bold">
                        {(user.display_name || user.username || '?').charAt(0).toUpperCase()}
                      </span>
                    </div>
                  )}
                  <div className="flex-1">
                    <textarea
                      value={newPostContent}
                      onChange={(e) => setNewPostContent(e.target.value)}
                      placeholder={language === 'ko' ? '무슨 생각을 하고 계신가요?' : "What's on your mind?"}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                      rows="3"
                    />
                    <div className="flex justify-end mt-2">
                      <button
                        onClick={handleCreatePost}
                        disabled={!newPostContent.trim()}
                        className="px-4 py-2 text-white rounded-lg transition-colors disabled:bg-gray-300 disabled:text-gray-500 disabled:cursor-not-allowed"
                        style={newPostContent.trim() ? { backgroundColor: '#3797F0', fontWeight: '600' } : {}}
                      >
                        {language === 'ko' ? '게시' : 'Post'}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Activity Feed */}
            {isLoading ? (
              <div className="space-y-4">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className="bg-white rounded-xl shadow-[0_2px_12px_rgba(0,0,0,0.08)] border border-gray-200 p-4 animate-pulse">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full bg-gray-200"></div>
                        <div className="h-4 w-24 bg-gray-200 rounded"></div>
                        <div className="h-4 w-20 bg-gray-200 rounded"></div>
                      </div>
                      <div className="h-3 w-16 bg-gray-200 rounded"></div>
                    </div>
                    <div className="flex gap-4">
                      <div className="w-16 h-24 bg-gray-200 rounded"></div>
                      <div className="flex-1">
                        <div className="h-4 w-3/4 bg-gray-200 rounded mb-2"></div>
                        <div className="h-3 w-1/2 bg-gray-200 rounded mb-2"></div>
                        <div className="h-3 w-full bg-gray-200 rounded"></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : error ? (
              <div className="text-center py-12">
                <p className="text-red-600">{language === 'ko' ? '피드를 불러오는데 실패했습니다.' : 'Failed to load feed.'}</p>
              </div>
            ) : filteredActivities.length === 0 ? (
              <div className="text-center py-12">
                {feedFilter === 'notifications' ? (
                  <>
                    <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                    </svg>
                    <p className="text-gray-600 text-lg font-medium mb-2">
                      {language === 'ko' ? '알림이 없습니다' : 'No notifications yet'}
                    </p>
                    <p className="text-gray-500 text-sm">
                      {language === 'ko'
                        ? '다른 사용자가 회원님의 평가에 좋아요를 누르거나 댓글을 남기면 여기에 표시됩니다'
                        : 'When someone likes or comments on your ratings, you\'ll see it here'}
                    </p>
                  </>
                ) : (
                  <p className="text-gray-600">
                    {language === 'ko' ? '아직 활동이 없습니다.' : 'No activities yet.'}
                  </p>
                )}
              </div>
            ) : (
              <div className="space-y-4">
                {filteredActivities.map((activity) => {
                  const activityKey = `${activity.activity_type}_${activity.user_id}_${activity.item_id}`;
                  const isSaved = savedActivities.has(activityKey);

                  // Render notification-wrapped activity
                  if (activity._notifications) {
                    return (
                      <NotificationCard
                        key={activity.id}
                        notifications={activity._notifications}
                        getTimeAgo={getTimeAgo}
                        getAvatarUrl={getAvatarUrl}
                      >
                        <ActivityCard
                          activity={activity}
                          context="notification"
                          onUpdate={refetch}
                        />
                      </NotificationCard>
                    );
                  }

                  // Regular activity card
                  return (
                    <div key={activityKey} id={`activity-${activityKey}`}>
                      <ActivityCard
                        activity={activity}
                        context="feed"
                        onUpdate={refetch}
                      />
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Highlight Animation Styles */}
      <style>{`
        @keyframes highlightPulse {
          0%, 100% {
            box-shadow: 0 0 0 0 rgba(63, 193, 201, 0.7);
            border-color: rgba(63, 193, 201, 0.3);
          }
          50% {
            box-shadow: 0 0 0 10px rgba(63, 193, 201, 0);
            border-color: rgba(63, 193, 201, 1);
          }
        }

        .highlight-animation {
          animation: highlightPulse 1.5s ease-in-out 2;
          border: 2px solid #A8E6CF !important;
        }
      `}</style>
    </div>
  );
}
