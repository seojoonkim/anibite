import { useState, useEffect, useCallback, useMemo, memo } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { feedService } from '../services/feedService';
import * as ActivityUtils from '../utils/activityUtils';
import { activityLikeService } from '../services/activityLikeService';
import { commentLikeService } from '../services/commentLikeService';
import { userPostService } from '../services/userPostService';
import { ratingService } from '../services/ratingService';
import { reviewService } from '../services/reviewService';
import { reviewCommentService } from '../services/reviewCommentService';
import { characterService } from '../services/characterService';
import { characterReviewService } from '../services/characterReviewService';
import { notificationService } from '../services/notificationService';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { getCurrentLevelInfo } from '../utils/otakuLevels';
import Navbar from '../components/common/Navbar';
import StarRating from '../components/common/StarRating';
import NotificationCard from '../components/feed/NotificationCard';

export default function Feed() {
  const { user } = useAuth();
  const { t, getAnimeTitle, language } = useLanguage();
  const [searchParams, setSearchParams] = useSearchParams();

  // 필터별 독립적인 activities 상태
  const [activitiesByFilter, setActivitiesByFilter] = useState({
    all: [],
    following: [],
    notifications: [],
    saved: []
  });

  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [offset, setOffset] = useState(0);
  const [failedImages, setFailedImages] = useState(new Set());
  const [expandedComments, setExpandedComments] = useState(new Set());
  const [comments, setComments] = useState({});
  const [newComment, setNewComment] = useState({});
  const [feedFilter, setFeedFilter] = useState(searchParams.get('filter') || 'all'); // 'all', 'following', 'notifications', 'saved'
  const [notifications, setNotifications] = useState([]);
  const [activityLikes, setActivityLikes] = useState({});
  const [commentLikes, setCommentLikes] = useState({});
  const [savedActivities, setSavedActivities] = useState(new Set());
  const [replyingTo, setReplyingTo] = useState({});
  const [replyText, setReplyText] = useState({});
  const [newPostContent, setNewPostContent] = useState('');
  const [editingActivity, setEditingActivity] = useState(null);
  const [editRating, setEditRating] = useState(0);
  const [editReviewContent, setEditReviewContent] = useState('');
  const [showEditMenu, setShowEditMenu] = useState(null);
  const [deleteConfirmModal, setDeleteConfirmModal] = useState(null);

  const ITEMS_PER_PAGE = 20;

  // 현재 필터의 activities 가져오기
  const activities = activitiesByFilter[feedFilter] || [];

  // 필터별 activities 업데이트 헬퍼 함수
  const updateActivitiesForFilter = (filter, updater) => {
    setActivitiesByFilter(prev => ({
      ...prev,
      [filter]: typeof updater === 'function' ? updater(prev[filter] || []) : updater
    }));
  };

  const toRoman = (num) => {
    const romanNumerals = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X'];
    return romanNumerals[num - 1] || num;
  };

  // 스켈레톤 컴포넌트
  const FeedSkeleton = () => (
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
  );

  // URL 파라미터 변경 시 feedFilter 업데이트 및 하이라이트 처리
  useEffect(() => {
    const filterParam = searchParams.get('filter') || 'all';
    if (filterParam !== feedFilter) {
      setFeedFilter(filterParam);
    }

    // 하이라이트 처리
    const highlightKey = searchParams.get('highlight');
    if (highlightKey) {
      // 페이지 로딩이 완료된 후 스크롤
      setTimeout(() => {
        const element = document.getElementById(`activity-${highlightKey}`);
        if (element) {
          element.scrollIntoView({ behavior: 'smooth', block: 'center' });
          // 하이라이트 효과
          element.classList.add('highlight-animation');
          setTimeout(() => {
            element.classList.remove('highlight-animation');
          }, 3000);
        }
      }, 500);
    }
  }, [searchParams]);

  useEffect(() => {
    // feedFilter 변경 시 localStorage 다시 읽기 (저장하기 동기화)
    // Only update savedActivities when on 'saved' filter to avoid triggering unnecessary re-renders
    if (feedFilter === 'saved') {
      const saved = localStorage.getItem('savedActivities');
      if (saved) {
        const savedSet = new Set(JSON.parse(saved));
        // console.log('[Feed] Loaded saved activities from localStorage:', Array.from(savedSet));
        setSavedActivities(savedSet);
      }
    }

    // 필터별 독립 상태이므로 activities 초기화 불필요
    setOffset(0);
    setHasMore(true);

    // 해당 필터의 데이터가 없으면 로드
    if ((activitiesByFilter[feedFilter] || []).length === 0) {
      loadFeed(true);
    } else {
      // 이미 데이터가 있으면 로딩 상태만 false로
      setLoading(false);
    }
  }, [feedFilter]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showEditMenu && !event.target.closest('.relative')) {
        setShowEditMenu(null);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showEditMenu]);

  // savedActivities가 변경되고 saved 필터일 때 피드 다시 로드
  useEffect(() => {
    if (feedFilter === 'saved') {
      // console.log('[Feed] savedActivities changed, reloading saved feed');
      updateActivitiesForFilter('saved', []);
      setOffset(0);
      setHasMore(true);
      loadFeed(true);
    }
  }, [savedActivities]);

  const loadFeed = async () => {
    try {
      setLoading(true);

      // 점진적 로딩: 먼저 10개만 빠르게 로드
      const initialLimit = 10;
      const totalLimit = 30;

      if (feedFilter === 'saved') {
        // 저장된 피드만 필터링 (최적화: 30개만 가져오기)
        const allData = await feedService.getFeed(totalLimit, 0, false);
        const savedData = (allData || []).filter(activity => savedActivities.has(getActivityKey(activity)));
        updateActivitiesForFilter('saved', savedData);

        // 좋아요/댓글 정보 초기화
        const newActivityLikes = {};
        const newComments = {};
        const newExpandedComments = new Set();
        const commentsToLoad = [];
        savedData.forEach(activity => {
          const key = getActivityKey(activity);
          newActivityLikes[key] = {
            liked: Boolean(activity.user_liked),
            count: activity.likes_count || 0
          };
          newComments[key] = [];
          // Auto-expand comments for activities that have comments
          if (activity.comments_count > 0) {
            newExpandedComments.add(key);
            commentsToLoad.push(activity);
          }
        });
        setActivityLikes(newActivityLikes);
        setComments(newComments);
        setExpandedComments(newExpandedComments);

        // Load comments for activities with comments
        if (commentsToLoad.length > 0) {
          commentsToLoad.forEach(activity => loadComments(activity));
        }

        // 저장함 로딩 완료
        setLoading(false);
      } else if (feedFilter === 'notifications') {
        // 알림 데이터 로드 (최적화: 30개만)
        const notificationData = await notificationService.getNotifications(30, 0);
        setNotifications(notificationData.items || []);

        // 처음 로드할 때만 읽음 처리
        await notificationService.markAsRead();

        // Check if we have any notifications
        if (!notificationData.items || notificationData.items.length === 0) {
          updateActivitiesForFilter('notifications', []);
          setLoading(false);
          return;
        }

        // 알림을 item_id + activity_type별로 그룹화
        const groupedNotifications = {};
        (notificationData.items || []).forEach((notification) => {
          const key = `${notification.activity_type}_${notification.item_id}`;
          if (!groupedNotifications[key]) {
            groupedNotifications[key] = [];
          }
          groupedNotifications[key].push(notification);
        });

        // 각 그룹을 하나의 activity로 변환
        const transformedActivities = Object.values(groupedNotifications).map(notificationGroup => {
          // 가장 최근 알림을 기준으로 activity 생성
          const latestNotification = notificationGroup[0];

          return {
            // Activity 기본 정보
            activity_type: latestNotification.activity_type,
            user_id: latestNotification.target_user_id,
            item_id: latestNotification.item_id,

            // 사용자 정보 (activity 소유자)
            username: latestNotification.activity_username,
            display_name: latestNotification.activity_display_name,
            avatar_url: latestNotification.activity_avatar_url,
            otaku_score: latestNotification.activity_otaku_score || 0,

            // 아이템 정보
            item_title: latestNotification.item_title,
            item_title_korean: latestNotification.item_title,
            item_image: latestNotification.item_image,
            anime_id: latestNotification.anime_id,
            anime_title: latestNotification.anime_title,
            anime_title_korean: latestNotification.anime_title_korean,

            // Activity 컨텐츠
            rating: latestNotification.my_rating,
            review_content: latestNotification.activity_text,
            review_id: latestNotification.review_id, // For editing/deleting reviews
            activity_time: latestNotification.activity_created_at,

            // 카운트
            likes_count: latestNotification.activity_likes_count,
            comments_count: latestNotification.activity_comments_count,
            user_liked: Boolean(latestNotification.user_has_liked),
            user_has_liked: Boolean(latestNotification.user_has_liked),

            // 알림 메타데이터 보존 (NotificationCard에서 사용) - 배열로 전달
            _notifications: notificationGroup
          };
        });

        updateActivitiesForFilter('notifications', transformedActivities);

        // State 초기화 (백엔드 데이터 직접 사용, 별도 API 호출 제거)
        const newActivityLikes = {};
        const newComments = {};
        const newExpandedComments = new Set();

        const commentsToLoad = [];
        transformedActivities.forEach(activity => {
          const key = getActivityKey(activity);

          newActivityLikes[key] = {
            liked: Boolean(activity.user_has_liked),
            count: activity.likes_count || 0
          };
          newComments[key] = [];
          // Auto-expand comments for activities that have comments
          if (activity.comments_count > 0) {
            newExpandedComments.add(key);
            commentsToLoad.push(activity);
          }
        });

        setActivityLikes(newActivityLikes);
        setComments(newComments);
        setExpandedComments(newExpandedComments);

        // Load comments for activities with comments
        if (commentsToLoad.length > 0) {
          commentsToLoad.forEach(activity => loadComments(activity));
        }

        // 알림 로딩 완료
        setLoading(false);
      } else {
        // 전체 또는 팔로잉 - 점진적 로딩
        const showFollowing = feedFilter === 'following';
        const currentFilter = feedFilter; // Capture current filter for background loading

        // 1단계: 먼저 10개만 빠르게 로드
        const initialData = await feedService.getFeed(initialLimit, 0, showFollowing);
        console.log('[Feed] Initial data loaded:', initialData);
        const charActivities = initialData?.filter(a => a.activity_type === 'character_rating' || a.activity_type === 'character_review');
        console.log('[Feed] Character activities:', charActivities?.map(a => ({
          type: a.activity_type,
          user: a.user_id,
          item: a.item_id,
          review_id: a.review_id,
          comments_count: a.comments_count
        })));
        updateActivitiesForFilter(currentFilter, initialData || []);

        // 좋아요/댓글 정보 초기화 (첫 10개)
        const newActivityLikes = {};
        const newComments = {};
        const newExpandedComments = new Set();
        const commentsToLoad = [];
        (initialData || []).forEach(activity => {
          const key = getActivityKey(activity);
          newActivityLikes[key] = {
            liked: Boolean(activity.user_liked),
            count: activity.likes_count || 0
          };
          newComments[key] = [];
          // Auto-expand comments for activities that have comments
          if (activity.comments_count > 0) {
            newExpandedComments.add(key);
            commentsToLoad.push(activity);
          }
        });
        setActivityLikes(newActivityLikes);
        setComments(newComments);
        setExpandedComments(newExpandedComments);

        // Load comments for activities with comments
        if (commentsToLoad.length > 0) {
          commentsToLoad.forEach(activity => loadComments(activity));
        }

        // 즉시 로딩 완료 처리 (UI 표시)
        setLoading(false);

        // 2단계: 백그라운드에서 나머지 20개 로드
        if (initialData && initialData.length === initialLimit) {
          feedService.getFeed(totalLimit - initialLimit, initialLimit, showFollowing).then(additionalData => {
            if (!additionalData || additionalData.length === 0) return;

            // Update only the specific filter that started this load
            updateActivitiesForFilter(currentFilter, prev => [...prev, ...additionalData]);

            // 추가 데이터의 좋아요/댓글 정보 초기화
            const additionalLikes = {};
            const additionalComments = {};
            const additionalCommentsToLoad = [];
            additionalData.forEach(activity => {
              const key = getActivityKey(activity);
              additionalLikes[key] = {
                liked: Boolean(activity.user_liked),
                count: activity.likes_count || 0
              };
              additionalComments[key] = [];
              // Auto-expand comments for activities that have comments
              if (activity.comments_count > 0) {
                additionalCommentsToLoad.push({ key, activity });
              }
            });

            setActivityLikes(prevLikes => ({ ...prevLikes, ...additionalLikes }));
            setComments(prevComments => ({ ...prevComments, ...additionalComments }));

            // Load comments and expand for activities with comments
            if (additionalCommentsToLoad.length > 0) {
              setExpandedComments(prevExpanded => {
                const newSet = new Set(prevExpanded);
                additionalCommentsToLoad.forEach(({ key }) => newSet.add(key));
                return newSet;
              });
              additionalCommentsToLoad.forEach(({ activity }) => loadComments(activity));
            }
          }).catch(err => {
            console.error('Failed to load additional feed items:', err);
          });
        }

        return; // Early return to skip the setLoading(false) below
      }

      setLoading(false);
    } catch (err) {
      console.error('Failed to load feed:', err);
      alert(`피드 로드 실패: ${err.message}`);
      updateActivitiesForFilter(feedFilter, []);
      setLoading(false);
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
      // 로컬 스토리지에 저장
      localStorage.setItem('savedActivities', JSON.stringify([...newSet]));
      return newSet;
    });
  };

  // 컴포넌트 마운트 시 저장된 활동 로드
  useEffect(() => {
    const saved = localStorage.getItem('savedActivities');
    if (saved) {
      setSavedActivities(new Set(JSON.parse(saved)));
    }
  }, []);

  // Feed가 다시 활성화될 때 localStorage 다시 읽기 (저장하기 동기화)
  useEffect(() => {
    const handleFocus = () => {
      const saved = localStorage.getItem('savedActivities');
      if (saved) {
        setSavedActivities(new Set(JSON.parse(saved)));
      }
    };

    window.addEventListener('focus', handleFocus);

    // 탭 visibility 변경 감지
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        const saved = localStorage.getItem('savedActivities');
        if (saved) {
          setSavedActivities(new Set(JSON.parse(saved)));
        }
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      window.removeEventListener('focus', handleFocus);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  const getImageUrl = (imageUrl) => {
    if (!imageUrl) return '/placeholder-anime.png';
    if (imageUrl.startsWith('http')) return imageUrl;
    return `http://localhost:8000${imageUrl}`;
  };

  const getAvatarUrl = (avatarUrl) => {
    if (!avatarUrl) return '/placeholder-avatar.png';
    if (avatarUrl.startsWith('http')) return avatarUrl;
    return `http://localhost:8000${avatarUrl}`;
  };

  const handleAvatarError = (e, userId) => {
    // 이미 실패한 이미지는 다시 시도하지 않음 (무한 루프 방지)
    if (failedImages.has(`avatar-${userId}`)) return;

    setFailedImages(prev => new Set(prev).add(`avatar-${userId}`));
    e.target.src = '/placeholder-avatar.png';
  };

  const handleImageError = (e, itemId) => {
    // 이미 실패한 이미지는 다시 시도하지 않음 (무한 루프 방지)
    if (failedImages.has(`image-${itemId}`)) return;

    setFailedImages(prev => new Set(prev).add(`image-${itemId}`));
    e.target.src = '/placeholder-anime.png';
  };

  const getActivityText = (activity) => {
    const displayName = activity.display_name || activity.username;

    switch (activity.activity_type) {
      case 'anime_rating':
        return `${displayName}님이 평가했어요`;
      case 'character_rating':
        return `${displayName}님이 캐릭터를 평가했어요`;
      case 'review':
        return `${displayName}님이 리뷰를 남겼어요`;
      default:
        return `${displayName}님의 활동`;
    }
  };

  const getActivityIcon = (activityType) => {
    switch (activityType) {
      case 'anime_rating':
        return '⭐';
      case 'character_rating':
        return '👤';
      case 'review':
        return '✍️';
      default:
        return '📝';
    }
  };

  const getTimeAgo = (timestamp) => {
    const now = new Date();
    // SQLite timestamp를 UTC로 파싱 (타임존 정보가 없으면 'Z' 추가)
    const activityTime = new Date(timestamp.endsWith('Z') ? timestamp : timestamp + 'Z');
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

  const handleStartEdit = (activity) => {
    const activityKey = `${activity.activity_type}_${activity.user_id}_${activity.item_id}`;
    setEditingActivity(activityKey);
    setEditRating(activity.rating || 0);
    setEditReviewContent(activity.review_content || '');
    setShowEditMenu(null);
  };

  const handleCancelEdit = () => {
    setEditingActivity(null);
    setEditRating(0);
    setEditReviewContent('');
  };

  const handleSaveEdit = async (activity) => {
    try {
      // Save user post
      if (activity.activity_type === 'user_post') {
        if (!editReviewContent.trim()) {
          alert(language === 'ko' ? '내용을 입력해주세요.' : 'Please enter content.');
          return;
        }
        await userPostService.updatePost(activity.item_id, editReviewContent.trim());
      }
      // Save rating
      else if (activity.activity_type === 'anime_rating') {
        await ratingService.rateAnime(activity.item_id, {
          rating: editRating,
          status: 'RATED'
        });
      } else if (activity.activity_type === 'character_rating') {
        await characterService.rateCharacter(activity.item_id, editRating);
      }

      // Save review if content exists (for anime/character ratings only)
      if (activity.activity_type !== 'user_post' && editReviewContent.trim()) {
        if (editReviewContent.trim().length < 10) {
          alert(language === 'ko' ? '리뷰는 최소 10자 이상 작성해야 합니다.' : 'Review must be at least 10 characters.');
          return;
        }

        // Character rating review
        if (activity.activity_type === 'character_rating') {
          // Check if review exists using review_id from activity
          if (activity.review_id && activity.review_id > 0) {
            // Update existing character review
            await characterReviewService.updateReview(activity.review_id, {
              content: editReviewContent.trim()
            });
          } else {
            // Create new character review
            await characterReviewService.createReview({
              character_id: activity.item_id,
              content: editReviewContent.trim()
            });
          }
        }
        // Anime rating review
        else if (activity.activity_type === 'anime_rating') {
          // Check if review exists using review_id from activity
          if (activity.review_id && activity.review_id > 0) {
            // Update existing anime review
            await reviewService.updateReview(activity.review_id, {
              content: editReviewContent.trim()
            });
          } else {
            // Create new anime review
            await reviewService.createReview({
              anime_id: activity.item_id,
              content: editReviewContent.trim()
            });
          }
        }
      }

      // Update activity in state for current filter
      const activityKey = getActivityKey(activity);
      updateActivitiesForFilter(feedFilter, prev => prev.map(act => {
        if (getActivityKey(act) === activityKey) {
          return {
            ...act,
            rating: editRating,
            review_content: editReviewContent.trim(),
            post_content: activity.activity_type === 'user_post' ? editReviewContent.trim() : act.post_content
          };
        }
        return act;
      }));
      handleCancelEdit();
    } catch (err) {
      console.error('[Feed] Failed to save edit:', err);
      console.error('[Feed] Error details:', err.response?.data);
      alert(language === 'ko' ? `저장에 실패했습니다: ${err.response?.data?.detail || err.message}` : `Failed to save changes: ${err.response?.data?.detail || err.message}`);
    }
  };

  const handleDeleteActivity = async (activity) => {
    try {
      // Delete user post
      if (activity.activity_type === 'user_post') {
        await userPostService.deletePost(activity.item_id);
      }
      // Delete rating
      else if (activity.activity_type === 'anime_rating') {
        await ratingService.deleteRating(activity.item_id);
      } else if (activity.activity_type === 'character_rating') {
        // Delete character rating
        await characterService.deleteCharacterRating(activity.item_id);
      }

      // Delete review if exists (for anime/character ratings)
      if (activity.review_id && activity.review_id > 0 && activity.activity_type !== 'user_post') {
        if (activity.activity_type === 'character_rating') {
          // Delete character review
          await characterReviewService.deleteReview(activity.review_id);
        } else if (activity.activity_type === 'anime_rating') {
          // Delete anime review
          await reviewService.deleteReview(activity.review_id);
        }
      }

      // Remove activity from state for current filter
      const activityKey = getActivityKey(activity);
      updateActivitiesForFilter(feedFilter, prev => prev.filter(act => getActivityKey(act) !== activityKey));
      setDeleteConfirmModal(null);
    } catch (err) {
      console.error('Failed to delete activity:', err);
      alert(language === 'ko' ? '삭제에 실패했습니다.' : 'Failed to delete.');
    }
  };

  const handleShowDeleteConfirm = (activity) => {
    setDeleteConfirmModal(activity);
    setShowEditMenu(null);
  };

  const getActivityKey = (activity) => {
    const key = `${activity.activity_type}_${activity.user_id}_${activity.item_id}`;
    // Debug: Log character_rating keys
    // if (activity.activity_type === 'character_rating') {
    //   console.log('[Feed] Character rating key:', key);
    //   console.log('[Feed] Activity:', {
    //     type: activity.activity_type,
    //     user_id: activity.user_id,
    //     item_id: activity.item_id,
    //     character: activity.item_title
    //   });
    // }
    return key;
  };

  const toggleComments = async (activity) => {
    const key = getActivityKey(activity);
    // console.log('[Feed] toggleComments called:', { key, isCurrentlyExpanded: expandedComments.has(key) });

    if (expandedComments.has(key)) {
      // console.log('[Feed] Closing comments for:', key);
      setExpandedComments(prev => {
        const newSet = new Set(prev);
        newSet.delete(key);
        // console.log('[Feed] Comments closed, new set:', Array.from(newSet));
        return newSet;
      });
    } else {
      // console.log('[Feed] Opening comments for:', key);
      setExpandedComments(prev => {
        const newSet = new Set(prev).add(key);
        // console.log('[Feed] Comments opened, new set:', Array.from(newSet));
        return newSet;
      });
      await loadComments(activity);
    }
  };

  const loadComments = async (activity) => {
    try {
      const key = getActivityKey(activity);

      // 캐릭터인지 애니인지 확인
      const isCharacter = activity.activity_type === 'character_rating' || activity.activity_type === 'character_review';
      const reviewType = isCharacter ? 'character' : 'anime';
      const reviewId = activity.review_id;

      console.log('[Feed] loadComments:', 'KEY=' + key, 'REVIEW_ID=' + reviewId, 'TYPE=' + reviewType);

      if (!reviewId || reviewId <= 0) {
        console.log('[Feed] No review_id, skipping');
        return;
      }

      // 직접 API 호출
      const data = await reviewCommentService.getReviewComments(reviewId, reviewType);

      console.log('[Feed] GOT COMMENTS:', 'COUNT=' + (data.items?.length || 0));
      console.log('[Feed] RAW COMMENT DATA:', JSON.stringify(data.items?.map(c => ({
        id: c.id,
        parent_comment_id: c.parent_comment_id,
        content: c.content?.substring(0, 20),
        replies: c.replies?.map(r => ({ id: r.id, parent_comment_id: r.parent_comment_id }))
      })), null, 2));

      let topLevelComments = [];

      // 백엔드가 이미 중첩 구조로 반환하는지 확인
      const hasNestedReplies = data.items?.some(comment =>
        comment.replies && Array.isArray(comment.replies) && comment.replies.length > 0
      );

      if (hasNestedReplies) {
        // 이미 중첩 구조 - 그대로 사용
        console.log('[Feed] Using nested structure from backend');
        topLevelComments = data.items || [];
      } else {
        // 평평한 구조 - 중첩 구조로 변환
        console.log('[Feed] Converting flat structure to nested');
        const commentsMap = new Map();
        const tempTopLevel = [];

        // 먼저 모든 댓글을 Map에 저장
        (data.items || []).forEach(comment => {
          commentsMap.set(comment.id, { ...comment, replies: [] });
        });

        // 부모-자식 관계 설정
        (data.items || []).forEach(comment => {
          const commentObj = commentsMap.get(comment.id);
          if (comment.parent_comment_id) {
            // 대댓글인 경우 부모 댓글의 replies에 추가
            const parent = commentsMap.get(comment.parent_comment_id);
            if (parent) {
              parent.replies.push(commentObj);
            } else {
              // 부모를 찾을 수 없으면 최상위 댓글로 처리
              tempTopLevel.push(commentObj);
            }
          } else {
            // 최상위 댓글
            tempTopLevel.push(commentObj);
          }
        });

        topLevelComments = tempTopLevel;
      }

      console.log('[Feed] FINAL STRUCTURE:', topLevelComments.map(c => ({
        id: c.id,
        replies_count: c.replies?.length || 0
      })));

      // 댓글과 답글의 좋아요 정보 초기화
      const newCommentLikes = {};
      topLevelComments.forEach(comment => {
        // 댓글의 좋아요 정보
        newCommentLikes[comment.id] = {
          liked: Boolean(comment.user_liked),
          count: comment.likes_count || 0
        };

        // 답글의 좋아요 정보
        if (comment.replies && comment.replies.length > 0) {
          comment.replies.forEach(reply => {
            newCommentLikes[reply.id] = {
              liked: Boolean(reply.user_liked),
              count: reply.likes_count || 0
            };
          });
        }
      });

      setComments(prev => ({
        ...prev,
        [key]: topLevelComments
      }));

      // 좋아요 정보 업데이트
      setCommentLikes(prev => ({
        ...prev,
        ...newCommentLikes
      }));
    } catch (err) {
      console.error('[Feed] loadComments ERROR:', err);
    }
  };

  // 활동의 댓글 수를 업데이트하는 헬퍼 함수
  const updateActivityCommentsCount = (activity, delta) => {
    updateActivitiesForFilter(feedFilter, prev => prev.map(act => {
      const actKey = getActivityKey(act);
      const targetKey = getActivityKey(activity);
      if (actKey === targetKey) {
        return {
          ...act,
          comments_count: Math.max(0, (act.comments_count || 0) + delta)
        };
      }
      return act;
    }));
  };

  const handleSubmitComment = async (activity) => {
    const key = getActivityKey(activity);
    const content = newComment[key];

    if (!content || !content.trim()) return;

    try {
      // 통합 유틸리티 사용
      await ActivityUtils.createComment(activity, content);

      setNewComment(prev => ({ ...prev, [key]: '' }));

      // Ensure comment section is expanded
      setExpandedComments(prev => {
        const newSet = new Set(prev).add(key);
        return newSet;
      });

      // Reload comments and update count
      await loadComments(activity);
      updateActivityCommentsCount(activity, 1);
    } catch (err) {
      console.error('[Feed] Failed to submit comment:', err);
      console.error('[Feed] Error details:', err.response?.data);
    }
  };

  const handleDeleteComment = async (activity, commentId) => {
    try {
      // 통합 유틸리티 사용
      await ActivityUtils.deleteComment(activity, commentId);

      // Reload comments and update count
      await loadComments(activity);
      updateActivityCommentsCount(activity, -1);
    } catch (err) {
      console.error('[Feed] Failed to delete comment:', err);
    }
  };

  const handleToggleActivityLike = async (activity) => {
    if (!user) {
      alert(language === 'ko' ? '로그인이 필요합니다.' : 'Please login first.');
      return;
    }

    try {
      const key = getActivityKey(activity);

      const result = await activityLikeService.toggleLike(
        activity.activity_type,
        activity.user_id,
        activity.item_id
      );

      setActivityLikes(prev => {
        const newState = {
          ...prev,
          [key]: { liked: result.liked, count: result.like_count }
        };
        return newState;
      });
    } catch (err) {
      console.error('[Feed] Failed to toggle activity like:', err);
      console.error('[Feed] Error details:', err.response?.data);
    }
  };

  const handleToggleCommentLike = async (commentId) => {
    try {
      // 통합 유틸리티 사용 (댓글 좋아요는 모든 경우에 동일)
      const result = await ActivityUtils.toggleCommentLike(commentId);

      setCommentLikes(prev => ({
        ...prev,
        [commentId]: { liked: result.liked, count: result.like_count }
      }));
    } catch (err) {
      console.error('[Feed] Failed to toggle comment like:', err);
    }
  };

  const handleReplyClick = (commentId) => {
    setReplyingTo(prev => ({ ...prev, [commentId]: !prev[commentId] }));
  };

  const handleSubmitReply = async (activity, parentCommentId) => {
    const content = replyText[parentCommentId];
    if (!content || !content.trim()) return;

    try {
      // 통합 유틸리티 사용
      await ActivityUtils.createReply(activity, parentCommentId, content);

      setReplyText(prev => ({ ...prev, [parentCommentId]: '' }));
      setReplyingTo(prev => ({ ...prev, [parentCommentId]: false }));
      await loadComments(activity);
      updateActivityCommentsCount(activity, 1);
    } catch (err) {
      console.error('[Feed] Failed to submit reply:', err);
    }
  };

  const handleCreatePost = async () => {
    if (!newPostContent || !newPostContent.trim()) return;

    try {
      await userPostService.createPost(newPostContent);
      setNewPostContent('');
      await loadFeed();
    } catch (err) {
      console.error('Failed to create post:', err);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen pt-0 md:pt-16 bg-transparent">
        <Navbar />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8">
          <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-6">
            {/* Left Sidebar - Real Filter Menu (Clickable) */}
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
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
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
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
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
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
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
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
                    </svg>
                    {language === 'ko' ? '저장한 피드' : 'Saved Feed'}
                  </button>
                </div>
              </nav>
              </div>
            </aside>
            {/* Main Content */}
            <div>
              {/* Post Composer - Always visible */}
              <div className="bg-white rounded-xl shadow-[0_2px_12px_rgba(0,0,0,0.08)] border border-gray-200 p-4 mb-6">
                <div className="flex gap-3">
                  {user?.avatar_url && !failedImages.has(`avatar-${user.id}`) ? (
                    <img
                      src={getAvatarUrl(user.avatar_url)}
                      alt={user.display_name || user.username}
                      className="w-12 h-12 rounded-full object-cover border border-gray-200"
                      onError={(e) => handleAvatarError(e, user.id)}
                    />
                  ) : (
                    <div className="w-12 h-12 rounded-full flex items-center justify-center border border-gray-200" style={{ backgroundColor: '#364F6B' }}>
                      <span className="text-white text-base font-bold">
                        {(user?.display_name || user?.username || '?').charAt(0).toUpperCase()}
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
                        onMouseEnter={(e) => !e.target.disabled && (e.target.style.backgroundColor = '#1877F2')}
                        onMouseLeave={(e) => !e.target.disabled && (e.target.style.backgroundColor = '#3797F0')}
                      >
                        {language === 'ko' ? '게시' : 'Post'}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
              {/* Feed Skeleton while loading */}
              <FeedSkeleton />
            </div>
          </div>
        </div>
      </div>
    );
  }

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
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
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
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
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
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
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
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
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
            <div className="bg-white rounded-xl shadow-[0_2px_12px_rgba(0,0,0,0.08)] border border-gray-200 p-4 mb-6">
              <div className="flex gap-3">
                {user?.avatar_url && !failedImages.has(`avatar-${user.id}`) ? (
                  <img
                    src={getAvatarUrl(user.avatar_url)}
                    alt={user.display_name || user.username}
                    className="w-12 h-12 rounded-full object-cover border border-gray-200"
                    onError={(e) => handleAvatarError(e, user.id)}
                  />
                ) : (
                  <div className="w-12 h-12 rounded-full flex items-center justify-center border border-gray-200" style={{ backgroundColor: '#364F6B' }}>
                    <span className="text-white text-base font-bold">
                      {(user?.display_name || user?.username || '?').charAt(0).toUpperCase()}
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
                      onMouseEnter={(e) => !e.target.disabled && (e.target.style.backgroundColor = '#1877F2')}
                      onMouseLeave={(e) => !e.target.disabled && (e.target.style.backgroundColor = '#3797F0')}
                    >
                      {language === 'ko' ? '게시' : 'Post'}
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Activity Feed */}
            {(
              <div className="space-y-4">
                {activities.length === 0 && feedFilter === 'notifications' ? (
                  <div className="text-center py-12">
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
                  </div>
                ) : null}
                {activities.map((activity, index) => {
                  const activityKey = getActivityKey(activity);

                  // Activity card content
                  const activityCardContent = (
                  <div
                    id={`activity-${activityKey}`}
                    className={activity._notifications ? '' : "bg-white rounded-xl shadow-[0_2px_12px_rgba(0,0,0,0.08)] border border-gray-200 p-4 hover:shadow-[0_4px_16px_rgba(0,0,0,0.12)] transition-all"}
                  >
                    {/* Header - Profile info at the top */}
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-2">
                        {/* User Avatar */}
                        <Link to={`/user/${activity.user_id}`} className="flex-shrink-0">
                          {activity.avatar_url ? (
                            <img
                              src={getAvatarUrl(activity.avatar_url)}
                              alt={activity.display_name || activity.username}
                              className="w-8 h-8 rounded-full object-cover border border-gray-200"
                              onError={(e) => handleAvatarError(e, activity.user_id)}
                            />
                          ) : (
                            <div className="w-8 h-8 rounded-full flex items-center justify-center border border-gray-200" style={{ background: 'linear-gradient(to bottom right, #90B2E4, #638CCC)' }}>
                              <span className="text-white text-xs font-bold">
                                {(activity.display_name || activity.username || '?').charAt(0).toUpperCase()}
                              </span>
                            </div>
                          )}
                        </Link>
                        <Link
                          to={`/user/${activity.user_id}`}
                          className="text-base font-medium text-gray-700 hover:text-[#737373] transition-colors"
                        >
                          {activity.display_name || activity.username}
                        </Link>
                        {(() => {
                          const levelInfo = getCurrentLevelInfo(activity.otaku_score || 0);
                          return (
                            <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${levelInfo.bgGradient} border ${levelInfo.borderColor}`}>
                              <span style={{ color: levelInfo.color }} className="font-bold">{levelInfo.icon}</span> <span className="text-gray-700">{levelInfo.level} - {toRoman(levelInfo.rank)}</span>
                            </span>
                          );
                        })()}
                        {activity.activity_type !== 'user_post' && (
                          <span className="text-sm text-gray-600">
                            {activity.activity_type === 'anime_rating' && (language === 'ko' ? '애니를 평가했어요' : 'rated an anime')}
                            {activity.activity_type === 'character_rating' && (language === 'ko' ? '캐릭터를 평가했어요' : 'rated a character')}
                            {activity.activity_type === 'review' && (language === 'ko' ? '리뷰를 남겼어요' : 'left a review')}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-500">
                          {getTimeAgo(activity.activity_time)}
                        </span>
                        {/* Edit Menu for own activities */}
                        {activity.user_id === user?.id && (
                          <div className="relative">
                            <button
                              onClick={() => setShowEditMenu(showEditMenu === activityKey ? null : activityKey)}
                              className="text-gray-400 hover:text-gray-600 p-1 rounded-full hover:bg-gray-100"
                            >
                              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
                              </svg>
                            </button>
                            {showEditMenu === activityKey && (
                              <div className="absolute right-0 mt-1 w-32 bg-white rounded-md shadow-[0_2px_12px_rgba(0,0,0,0.08)] z-10 border border-gray-200">
                                <button
                                  onClick={() => handleStartEdit(activity)}
                                  className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-t-md"
                                >
                                  {language === 'ko' ? '수정' : 'Edit'}
                                </button>
                                <button
                                  onClick={() => handleShowDeleteConfirm(activity)}
                                  className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded-b-md border-t border-gray-200"
                                >
                                  {language === 'ko' ? '삭제' : 'Delete'}
                                </button>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Main Content Wrapper */}
                    <div>
                      {/* Content area - Image and info side by side for non-post activities */}
                      {activity.activity_type !== 'user_post' ? (
                      <div className="flex gap-4">
                        {/* Image */}
                        <Link
                          to={activity.activity_type === 'character_rating' ? `/character/${activity.item_id}` : `/anime/${activity.item_id}`}
                          className="flex-shrink-0 hover:opacity-80 transition-opacity cursor-pointer"
                        >
                          <div className="w-20 h-28 rounded overflow-hidden border-2 border-transparent hover:border-[#A8E6CF] transition-all">
                            <img
                              src={getImageUrl(activity.item_image)}
                              alt={activity.item_title}
                              className="w-full h-full object-cover"
                              style={{ objectPosition: 'center top' }}
                              onError={(e) => handleImageError(e, activity.item_id)}
                            />
                          </div>
                        </Link>

                        {/* Info */}
                        <div className="flex-1 min-w-0">
                          {/* Title */}
                          <Link
                            to={activity.activity_type === 'character_rating' ? `/character/${activity.item_id}` : `/anime/${activity.item_id}`}
                            className="block group cursor-pointer"
                          >
                            <h3 className="font-semibold text-gray-900 group-hover:text-[#737373] transition-colors mb-1 group-hover:underline">
                              {activity.activity_type === 'character_rating' ? (
                                <>
                                  {activity.item_title}
                                  {activity.item_title_korean && activity.item_title_korean !== activity.item_title && (
                                    <span className="text-sm text-gray-500 ml-2">({activity.item_title_korean})</span>
                                  )}
                                </>
                              ) : (
                                language === 'ko' ? (activity.item_title_korean || activity.item_title) : activity.item_title
                              )}
                            </h3>
                          </Link>

                          {/* Anime title for character ratings */}
                          {activity.activity_type === 'character_rating' && activity.anime_title && (
                            <p className="text-xs text-gray-500 mb-2">
                              from:{' '}
                              <Link
                                to={`/anime/${activity.anime_id}`}
                                className="hover:text-[#737373] hover:underline transition-colors"
                              >
                                {language === 'ko' ? (activity.anime_title_korean || activity.anime_title) : activity.anime_title}
                              </Link>
                            </p>
                          )}

                          {/* Rating */}
                          {editingActivity === activityKey ? (
                            <div className="mb-4 p-4 bg-gray-50 rounded-lg">
                              <div className="mb-3">
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                  {language === 'ko' ? '별점' : 'Rating'}
                                </label>
                                <StarRating
                                  rating={editRating}
                                  onRatingChange={setEditRating}
                                  size="md"
                                  showNumber={true}
                                />
                              </div>
                              <div className="mb-3">
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                  {language === 'ko' ? '리뷰' : 'Review'}
                                </label>
                                <textarea
                                  value={editReviewContent}
                                  onChange={(e) => setEditReviewContent(e.target.value)}
                                  className="w-full p-2 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                                  rows="4"
                                  placeholder={language === 'ko' ? '리뷰를 작성하세요 (최소 10자)' : 'Write a review (minimum 10 characters)'}
                                />
                                <p className="text-xs text-gray-500 mt-1">
                                  {editReviewContent.length} / 5000
                                </p>
                              </div>
                              <div className="flex gap-2">
                                <button
                                  onClick={() => handleSaveEdit(activity)}
                                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                                >
                                  {language === 'ko' ? '저장' : 'Save'}
                                </button>
                                <button
                                  onClick={handleCancelEdit}
                                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors text-sm font-medium"
                                >
                                  {language === 'ko' ? '취소' : 'Cancel'}
                                </button>
                              </div>
                            </div>
                          ) : (
                            <>
                              {activity.rating && (
                                <div className="mb-2">
                                  <StarRating rating={activity.rating} readonly size="sm" />
                                </div>
                              )}

                              {/* Review Content */}
                              {activity.review_content && (
                                <p className="text-sm text-gray-700 line-clamp-2">
                                  {activity.review_content}
                                </p>
                              )}
                            </>
                          )}
                        </div>
                      </div>
                    ) : (
                      // User post content
                      <div>
                        {editingActivity === activityKey ? (
                          <div className="mb-4 p-4 bg-gray-50 rounded-lg">
                            <div className="mb-3">
                              <label className="block text-sm font-medium text-gray-700 mb-2">
                                {language === 'ko' ? '내용' : 'Content'}
                              </label>
                              <textarea
                                value={editReviewContent}
                                onChange={(e) => setEditReviewContent(e.target.value)}
                                className="w-full p-2 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                                rows="4"
                                placeholder={language === 'ko' ? '내용을 입력하세요' : 'Write content'}
                              />
                              <p className="text-xs text-gray-500 mt-1">
                                {editReviewContent.length} / 5000
                              </p>
                            </div>
                            <div className="flex gap-2">
                              <button
                                onClick={() => handleSaveEdit(activity)}
                                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                              >
                                {language === 'ko' ? '저장' : 'Save'}
                              </button>
                              <button
                                onClick={handleCancelEdit}
                                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors text-sm font-medium"
                              >
                                {language === 'ko' ? '취소' : 'Cancel'}
                              </button>
                            </div>
                          </div>
                        ) : (
                          activity.post_content && (
                            <p className="text-sm text-gray-700 whitespace-pre-wrap mb-3">
                              {activity.post_content}
                            </p>
                          )
                        )}
                      </div>
                      )}

                      {/* Like, Comment and Save Buttons */}
                      <div className="mt-3 flex items-center justify-between">
                      <div className="flex items-center gap-6">
                        <button
                          onClick={() => handleToggleActivityLike(activity)}
                          className="flex items-center gap-2 transition-all hover:scale-110"
                        >
                          {activityLikes[activityKey]?.liked ? (
                            <svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                              <defs>
                                <linearGradient id="heartGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                                  <stop offset="0%" style={{ stopColor: '#833AB4' }} />
                                  <stop offset="40%" style={{ stopColor: '#E1306C' }} />
                                  <stop offset="70%" style={{ stopColor: '#F77737' }} />
                                  <stop offset="100%" style={{ stopColor: '#FCAF45' }} />
                                </linearGradient>
                              </defs>
                              <path fill="url(#heartGradient)" d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                            </svg>
                          ) : (
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#8E8E8E" strokeWidth="2" xmlns="http://www.w3.org/2000/svg">
                              <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                            </svg>
                          )}
                          <span className="text-sm font-medium" style={{
                            color: activityLikes[activityKey]?.liked ? '#000000' : '#8E8E8E'
                          }}>
                            {language === 'ko' ? '좋아요' : 'Like'}
                            {activityLikes[activityKey]?.count > 0 && (
                              <> {activityLikes[activityKey].count}</>
                            )}
                          </span>
                        </button>
                        <button
                          onClick={() => toggleComments(activity)}
                          className="flex items-center gap-2 transition-all hover:scale-110"
                          style={{ color: '#6B7280' }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.color = '#737373';
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.color = '#6B7280';
                          }}
                        >
                          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" xmlns="http://www.w3.org/2000/svg">
                            <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>
                          </svg>
                          <span className="text-sm font-medium">
                            {language === 'ko' ? '댓글 달기' : 'Comment'}
                            {activity.comments_count > 0 && (
                              <> {activity.comments_count}</>
                            )}
                          </span>
                        </button>
                      </div>
  
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleSaveActivity(activityKey);
                        }}
                        className="flex items-center gap-2 transition-all hover:scale-110"
                        style={{
                          color: savedActivities.has(activityKey) ? '#000000' : '#737373'
                        }}
                      >
                        {savedActivities.has(activityKey) ? (
                          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                            <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
                          </svg>
                        ) : (
                          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" xmlns="http://www.w3.org/2000/svg">
                            <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
                          </svg>
                        )}
                        {savedActivities.has(activityKey) && (
                          <span className="text-sm font-medium">1</span>
                        )}
                      </button>
                    </div>
  
                    {/* Comments Section */}
                    {expandedComments.has(activityKey) && (() => {
                      // 로그는 댓글이 로드되지 않은 경우에만
                      if (!comments[activityKey] || comments[activityKey].length === 0) {
                        console.log('[Feed] RENDER: NO COMMENTS',
                          'KEY=' + activityKey,
                          'HAS_KEY=' + comments.hasOwnProperty(activityKey),
                          'ALL_KEYS=', Object.keys(comments)
                        );
                      }
                      return true;
                    })() && (
                      <div className="mt-3 pt-3 border-t border-gray-200">
                        {/* Comments List */}
                        {comments[activityKey]?.length > 0 && (
                          <div className="space-y-3 mb-3">
                            {comments[activityKey].map((comment) => {
                              // Debug log for each comment
                              if (comment.replies && comment.replies.length > 0) {
                                console.log(`[Feed Render] Comment ${comment.id} has ${comment.replies.length} replies:`, comment.replies.map(r => r.id));
                              }
                              return (
                              <div key={comment.id} className="space-y-2">
                                {/* Main Comment */}
                                <div className="flex gap-2">
                                  {comment.avatar_url ? (
                                    <img
                                      src={getAvatarUrl(comment.avatar_url)}
                                      alt={comment.display_name || comment.username}
                                      className="w-6 h-6 rounded-full object-cover"
                                    />
                                  ) : (
                                    <div className="w-6 h-6 rounded-full gradient-custom-profile flex items-center justify-center">
                                      <span className="text-white text-[10px] font-bold">
                                        {(comment.display_name || comment.username || '?')[0].toUpperCase()}
                                      </span>
                                    </div>
                                  )}
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2">
                                      <Link
                                        to={`/user/${comment.user_id}`}
                                        className="text-xs font-medium text-gray-700 hover:text-[#737373]"
                                      >
                                        {comment.display_name || comment.username}
                                      </Link>
                                      {(() => {
                                        const commentLevelInfo = getCurrentLevelInfo(comment.otaku_score || 0);
                                        return (
                                          <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-semibold ${commentLevelInfo.bgGradient} border ${commentLevelInfo.borderColor}`}>
                                            <span style={{ color: commentLevelInfo.color }} className="font-bold">{commentLevelInfo.icon}</span> <span className="text-gray-700">{commentLevelInfo.level} - {toRoman(commentLevelInfo.rank)}</span>
                                          </span>
                                        );
                                      })()}
                                      <span className="text-[10px] text-gray-400">
                                        {getTimeAgo(comment.created_at)}
                                      </span>
                                      {comment.user_id === user?.id && (
                                        <button
                                          onClick={() => handleDeleteComment(activity, comment.id)}
                                          className="text-[10px] text-red-500 hover:text-red-700"
                                        >
                                          {language === 'ko' ? '삭제' : 'Delete'}
                                        </button>
                                      )}
                                    </div>
                                    <p className="text-sm text-gray-700 mb-1">{comment.content}</p>
                                    <div className="flex items-center gap-3">
                                      <button
                                        onClick={() => handleToggleCommentLike(comment.id)}
                                        className="flex items-center gap-1 transition-all hover:scale-110"
                                        style={{
                                          color: commentLikes[comment.id]?.liked ? '#DC2626' : '#9CA3AF'
                                        }}
                                      >
                                        {commentLikes[comment.id]?.liked ? (
                                          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                                            <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                                          </svg>
                                        ) : (
                                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" xmlns="http://www.w3.org/2000/svg">
                                            <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                                          </svg>
                                        )}
                                        {commentLikes[comment.id]?.count > 0 && (
                                          <span className="text-xs">{commentLikes[comment.id].count}</span>
                                        )}
                                      </button>
                                      <button
                                        onClick={() => handleReplyClick(comment.id)}
                                        className="text-[10px]"
                                        style={{ color: '#9CA3AF' }}
                                        onMouseEnter={(e) => e.target.style.color = '#737373'}
                                        onMouseLeave={(e) => e.target.style.color = '#9CA3AF'}
                                      >
                                        {language === 'ko' ? '답글' : 'Reply'}
                                      </button>
                                    </div>
                                  </div>
                                </div>
  
                                {/* Replies */}
                                {comment.replies && comment.replies.length > 0 && (
                                  <div className="ml-12 space-y-2">
                                    {comment.replies.map((reply) => (
                                      <div key={reply.id} className="flex gap-2">
                                        {reply.avatar_url ? (
                                          <img
                                            src={getAvatarUrl(reply.avatar_url)}
                                            alt={reply.display_name || reply.username}
                                            className="w-5 h-5 rounded-full object-cover"
                                          />
                                        ) : (
                                          <div className="w-5 h-5 rounded-full flex items-center justify-center" style={{ background: 'linear-gradient(to bottom right, #90B2E4, #638CCC)' }}>
                                            <span className="text-white text-[8px] font-bold">
                                              {(reply.display_name || reply.username || '?')[0].toUpperCase()}
                                            </span>
                                          </div>
                                        )}
                                        <div className="flex-1 min-w-0">
                                          <div className="flex items-center gap-2">
                                            <Link
                                              to={`/user/${reply.user_id}`}
                                              className="text-xs font-medium text-gray-700 hover:text-[#737373]"
                                            >
                                              {reply.display_name || reply.username}
                                            </Link>
                                            {(() => {
                                              const replyLevelInfo = getCurrentLevelInfo(reply.otaku_score || 0);
                                              return (
                                                <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-semibold ${replyLevelInfo.bgGradient} border ${replyLevelInfo.borderColor}`}>
                                                  <span style={{ color: replyLevelInfo.color }} className="font-bold">{replyLevelInfo.icon}</span> <span className="text-gray-700">{toRoman(replyLevelInfo.rank)}</span>
                                                </span>
                                              );
                                            })()}
                                            <span className="text-[10px] text-gray-400">
                                              {getTimeAgo(reply.created_at)}
                                            </span>
                                            {reply.user_id === user?.id && (
                                              <button
                                                onClick={() => handleDeleteComment(activity, reply.id)}
                                                className="text-[10px] text-red-500 hover:text-red-700"
                                              >
                                                {language === 'ko' ? '삭제' : 'Delete'}
                                              </button>
                                            )}
                                          </div>
                                          <p className="text-sm text-gray-700 mb-1">{reply.content}</p>
                                          <button
                                            onClick={() => handleToggleCommentLike(reply.id)}
                                            className="flex items-center gap-1 transition-all hover:scale-110"
                                            style={{
                                              color: commentLikes[reply.id]?.liked ? '#DC2626' : '#9CA3AF'
                                            }}
                                          >
                                            {commentLikes[reply.id]?.liked ? (
                                              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                                                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                                              </svg>
                                            ) : (
                                              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" xmlns="http://www.w3.org/2000/svg">
                                                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                                              </svg>
                                            )}
                                            {commentLikes[reply.id]?.count > 0 && (
                                              <span className="text-xs">{commentLikes[reply.id].count}</span>
                                            )}
                                          </button>
                                        </div>
                                      </div>
                                    ))}
                                  </div>
                                )}
  
                                {/* Reply Input */}
                                {replyingTo[comment.id] && (
                                  <div className="ml-12 flex gap-2">
                                    <input
                                      type="text"
                                      value={replyText[comment.id] || ''}
                                      onChange={(e) => setReplyText(prev => ({ ...prev, [comment.id]: e.target.value }))}
                                      onKeyPress={(e) => {
                                        if (e.key === 'Enter') {
                                          handleSubmitReply(activity, comment.id);
                                        }
                                      }}
                                      placeholder={language === 'ko' ? '답글을 입력하세요...' : 'Write a reply...'}
                                      className="flex-1 px-2 py-1 text-xs border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                      autoFocus
                                    />
                                    <button
                                      onClick={() => handleSubmitReply(activity, comment.id)}
                                      disabled={!replyText[comment.id] || !replyText[comment.id].trim()}
                                      className="px-2 py-1 text-xs rounded-lg transition-colors disabled:bg-gray-300 disabled:text-gray-500 disabled:cursor-not-allowed"
                                      style={(replyText[comment.id] && replyText[comment.id].trim()) ? { backgroundColor: '#3797F0', color: 'white', fontWeight: '600' } : {}}
                                      onMouseEnter={(e) => !e.target.disabled && (e.target.style.backgroundColor = '#1877F2')}
                                      onMouseLeave={(e) => !e.target.disabled && (e.target.style.backgroundColor = '#3797F0')}
                                    >
                                      {language === 'ko' ? '작성' : 'Submit'}
                                    </button>
                                  </div>
                                )}
                              </div>
                              );
                            })}
                          </div>
                        )}
  
                        {/* Comment Input */}
                        <div className="flex gap-2">
                          <input
                            type="text"
                            value={newComment[activityKey] || ''}
                            onChange={(e) => setNewComment(prev => ({ ...prev, [activityKey]: e.target.value }))}
                            onKeyPress={(e) => {
                              if (e.key === 'Enter') {
                                handleSubmitComment(activity);
                              }
                            }}
                            placeholder={language === 'ko' ? '댓글을 입력하세요...' : 'Write a comment...'}
                            className="flex-1 px-3 py-1.5 text-xs border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                          <button
                            onClick={() => handleSubmitComment(activity)}
                            disabled={!newComment[activityKey] || !newComment[activityKey].trim()}
                            className="px-3 py-1.5 text-xs rounded-lg transition-colors disabled:bg-gray-300 disabled:text-gray-500 disabled:cursor-not-allowed"
                            style={(newComment[activityKey] && newComment[activityKey].trim()) ? { backgroundColor: '#3797F0', color: 'white', fontWeight: '600' } : {}}
                            onMouseEnter={(e) => !e.target.disabled && (e.target.style.backgroundColor = '#1877F2')}
                            onMouseLeave={(e) => !e.target.disabled && (e.target.style.backgroundColor = '#3797F0')}
                          >
                            {language === 'ko' ? '작성' : 'Submit'}
                          </button>
                        </div>
                      </div>
                    )}
                    </div>
                  </div>
                  );

                  // Wrap with NotificationCard if this is a notification
                  return activity._notifications ? (
                    <NotificationCard
                      key={`notification-${index}`}
                      notifications={activity._notifications}
                      getTimeAgo={getTimeAgo}
                      getAvatarUrl={getAvatarUrl}
                    >
                      {activityCardContent}
                    </NotificationCard>
                  ) : (
                    activityCardContent
                  );
                })}

                {activities.length === 0 && (
                  <div className="text-center py-12">
                    <p className="text-gray-600">{language === 'ko' ? '아직 활동이 없습니다.' : 'No activities yet.'}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {deleteConfirmModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setDeleteConfirmModal(null)}>
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-gray-900 mb-4">
              {language === 'ko' ? '삭제 확인' : 'Confirm Delete'}
            </h3>
            <p className="text-gray-700 mb-6">
              {language === 'ko' ? (
                <>
                  이 활동을 삭제하시겠습니까?<br/>
                  <span className="text-sm text-gray-500">
                    {deleteConfirmModal.activity_type === 'anime_rating' && '평점과 리뷰가 모두 삭제됩니다.'}
                    {deleteConfirmModal.activity_type === 'character_rating' && '캐릭터 평가가 삭제됩니다.'}
                    {deleteConfirmModal.activity_type === 'review' && '리뷰가 삭제됩니다.'}
                  </span>
                </>
              ) : (
                <>
                  Are you sure you want to delete this activity?<br/>
                  <span className="text-sm text-gray-500">
                    {deleteConfirmModal.activity_type === 'anime_rating' && 'Your rating and review will be deleted.'}
                    {deleteConfirmModal.activity_type === 'character_rating' && 'Your character rating will be deleted.'}
                    {deleteConfirmModal.activity_type === 'review' && 'Your review will be deleted.'}
                  </span>
                </>
              )}
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setDeleteConfirmModal(null)}
                className="px-4 py-2 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors font-medium"
              >
                {language === 'ko' ? '취소' : 'Cancel'}
              </button>
              <button
                onClick={() => handleDeleteActivity(deleteConfirmModal)}
                className="px-4 py-2 text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors font-medium"
              >
                {language === 'ko' ? '삭제' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}

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
