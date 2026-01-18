import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { useVirtualGrid } from '../hooks/useVirtualGrid';
import { userService } from '../services/userService';
import { ratingService } from '../services/ratingService';
import { followService } from '../services/followService';
import { feedService } from '../services/feedService';
import { activityCommentService } from '../services/activityCommentService';
import { activityLikeService } from '../services/activityLikeService';
import { commentLikeService } from '../services/commentLikeService';
import { userPostService } from '../services/userPostService';
import * as ActivityUtils from '../utils/activityUtils';
import { reviewService } from '../services/reviewService';
import { characterReviewService } from '../services/characterReviewService';
import { characterService } from '../services/characterService';
import OtakuMeter from '../components/profile/OtakuMeter';
import GenrePreferences from '../components/profile/GenrePreferences';
import RatingDistributionChart from '../components/profile/RatingDistributionChart';
import YearDistributionChart from '../components/profile/YearDistributionChart';
import StarRating from '../components/common/StarRating';
import FormatDistribution from '../components/profile/FormatDistribution';
import EpisodeLengthChart from '../components/profile/EpisodeLengthChart';
import RatingStatsCard from '../components/profile/RatingStatsCard';
import StudioStats from '../components/profile/StudioStats';
import SeasonStats from '../components/profile/SeasonStats';
import GenreCombinationChart from '../components/profile/GenreCombinationChart';
import ActivityCard from '../components/activity/ActivityCard';
import EditReviewModal from '../components/common/EditReviewModal';
import MyAnimeCard from '../components/profile/MyAnimeCard';
import MyCharacterCard from '../components/profile/MyCharacterCard';
import api from '../services/api';
import { getCurrentLevelInfo } from '../utils/otakuLevels';
import { API_BASE_URL, IMAGE_BASE_URL } from '../config/api';
import { getCharacterImageUrl, getCharacterImageFallback, getCharacterDisplayName, getAvatarUrl as getAvatarUrlHelper, getAvatarFallback } from '../utils/imageHelpers';

export default function MyAniPass() {
  const { user } = useAuth();
  const { t, language } = useLanguage();
  const { userId } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const isOwnProfile = !userId || parseInt(userId) === user?.id;
  const [profileUser, setProfileUser] = useState(null);
  const displayUser = isOwnProfile ? user : profileUser;

  // Initialize activeTab from URL query parameter, default to 'feed'
  const [activeTab, setActiveTab] = useState(() => {
    const tabFromUrl = searchParams.get('tab');
    return ['feed', 'anipass', 'anime', 'character'].includes(tabFromUrl) ? tabFromUrl : 'feed';
  });

  const [animeSubMenu, setAnimeSubMenu] = useState('all'); // 애니 서브메뉴: all, 5, 4, 3, 2, 1, 0, watchlist, pass
  const [characterSubMenu, setCharacterSubMenu] = useState('all'); // 캐릭터 서브메뉴: all, 5, 4, 3, 2, 1, 0, want, pass

  // Edit modal state
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editingActivity, setEditingActivity] = useState(null);
  const [editMode, setEditMode] = useState('edit'); // 'edit' | 'add_review' | 'edit_rating'

  const toRoman = (num) => {
    const romanNumerals = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X'];
    return romanNumerals[num - 1] || num;
  };

  // Generate consistent avatar gradient based on username
  const getAvatarGradient = (username) => {
    if (!username) return 'linear-gradient(135deg, #833AB4 0%, #E1306C 40%, #F77737 70%, #FCAF45 100%)';

    // Hash username to get consistent colors
    let hash = 0;
    for (let i = 0; i < username.length; i++) {
      hash = username.charCodeAt(i) + ((hash << 5) - hash);
    }

    const gradients = [
      'linear-gradient(135deg, #833AB4 0%, #E1306C 40%, #F77737 70%, #FCAF45 100%)', // Instagram
      'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', // Purple
      'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', // Pink
      'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', // Blue
      'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)', // Green
      'linear-gradient(135deg, #fa709a 0%, #fee140 100%)', // Orange
      'linear-gradient(135deg, #30cfd0 0%, #330867 100%)', // Teal
      'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)', // Pastel
    ];

    return gradients[Math.abs(hash) % gradients.length];
  };
  const [stats, setStats] = useState({
    total_rated: 0,
    total_want_to_watch: 0,
    total_pass: 0,
    average_rating: null,
    total_reviews: 0,
    total_character_ratings: 0,
    total_watch_time_minutes: 0,
    otaku_score: 0,
    favorite_genre: null
  });
  const [genrePreferences, setGenrePreferences] = useState([]);
  const [ratingDistribution, setRatingDistribution] = useState([]);
  const [yearDistribution, setYearDistribution] = useState([]);
  const [allAnime, setAllAnime] = useState([]); // 모든 애니 (평가, 보고싶어요, 관심없어요 포함)
  const [displayedAnime, setDisplayedAnime] = useState([]); // 현재 표시되는 애니
  const [allCharacters, setAllCharacters] = useState([]); // 모든 캐릭터 (평가, 알고싶어요, 관심없어요 포함)
  const [displayedCharacters, setDisplayedCharacters] = useState([]); // 현재 표시되는 캐릭터
  const [allRatedCharacters, setAllRatedCharacters] = useState([]); // 평가한 캐릭터만
  const [wantCharacters, setWantCharacters] = useState([]); // 알고싶어요 캐릭터
  const [passCharacters, setPassCharacters] = useState([]); // 관심없어요 캐릭터
  const [ratedAnime, setRatedAnime] = useState([]);
  const [allRatedAnime, setAllRatedAnime] = useState([]); // 전체 평가 애니 캐시
  const [ratedFilter, setRatedFilter] = useState('all'); // 별점 필터
  const [watchlistAnime, setWatchlistAnime] = useState([]);
  const [passAnime, setPassAnime] = useState([]);
  const [watchTime, setWatchTime] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tabLoading, setTabLoading] = useState(false);
  // Phase 1 & 2 통계
  const [formatDistribution, setFormatDistribution] = useState([]);
  const [episodeLengthDistribution, setEpisodeLengthDistribution] = useState([]);
  const [ratingStats, setRatingStats] = useState(null);
  const [studioStats, setStudioStats] = useState([]);
  const [seasonStats, setSeasonStats] = useState([]);
  const [genreCombinations, setGenreCombinations] = useState([]);
  // 탭별 로드 완료 여부 추적
  const [statsLoaded, setStatsLoaded] = useState(false);
  const [loadedTabs, setLoadedTabs] = useState({
    anipass: false,
    anime: false,
    character: false,
    feed: false
  });
  // 팔로우 관련 상태
  const [followCounts, setFollowCounts] = useState({ followers_count: 0, following_count: 0 });
  const [isFollowing, setIsFollowing] = useState(false);
  const [showFollowModal, setShowFollowModal] = useState(false);
  const [followModalType, setFollowModalType] = useState('followers'); // 'followers' or 'following'
  const [followList, setFollowList] = useState([]);
  // 피드 관련 상태
  const [userActivities, setUserActivities] = useState([]);
  const [feedOffset, setFeedOffset] = useState(0);
  const [hasMoreFeed, setHasMoreFeed] = useState(true);
  const [loadingMoreFeed, setLoadingMoreFeed] = useState(false);
  const [activityLikes, setActivityLikes] = useState({});
  const [expandedComments, setExpandedComments] = useState(new Set());
  const [comments, setComments] = useState({});
  const [newCommentText, setNewCommentText] = useState({});
  const [commentLikes, setCommentLikes] = useState({});
  const [replyingTo, setReplyingTo] = useState({});
  const [newPostContent, setNewPostContent] = useState('');
  const [failedImages, setFailedImages] = useState(new Set());
  // 삭제 모달 상태
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [activityToDelete, setActivityToDelete] = useState(null);
  const [deleteMenuOpen, setDeleteMenuOpen] = useState(null);

  // Infinite scroll observer ref
  const observer = useRef();
  const loadMoreFeedRef = useRef();

  // Update URL when activeTab changes
  const changeTab = useCallback((newTab) => {
    setActiveTab(newTab);
    setSearchParams({ tab: newTab });
  }, [setSearchParams]);

  // Sync activeTab with URL query parameter (for browser back/forward)
  useEffect(() => {
    const tabFromUrl = searchParams.get('tab');
    const validTab = ['feed', 'anipass', 'anime', 'character'].includes(tabFromUrl) ? tabFromUrl : 'feed';
    if (validTab !== activeTab) {
      setActiveTab(validTab);
    }
  }, [searchParams, activeTab]);

  const loadFollowData = useCallback(async () => {
    try {
      const targetUserId = userId || user?.id;
      if (!targetUserId) return;

      // 팔로우 카운트 로드
      const counts = await followService.getFollowCounts(targetUserId);
      setFollowCounts(counts);

      // 다른 사용자의 프로필이면 팔로잉 여부 확인
      if (!isOwnProfile) {
        const followStatus = await followService.isFollowing(targetUserId);
        setIsFollowing(followStatus.is_following);
      }
    } catch (err) {
      console.error('Failed to load follow data:', err);
    }
  }, [userId, user, isOwnProfile]);

  const handleFollowToggle = async () => {
    try {
      const targetUserId = userId || user?.id;
      if (isFollowing) {
        await followService.unfollowUser(targetUserId);
        setIsFollowing(false);
        setFollowCounts(prev => ({ ...prev, followers_count: prev.followers_count - 1 }));
      } else {
        await followService.followUser(targetUserId);
        setIsFollowing(true);
        setFollowCounts(prev => ({ ...prev, followers_count: prev.followers_count + 1 }));
      }
    } catch (err) {
      console.error('Failed to toggle follow:', err);
    }
  };

  const openFollowModal = async (type) => {
    try {
      setFollowModalType(type);
      setShowFollowModal(true);

      const targetUserId = userId || user?.id;
      if (type === 'followers') {
        const data = await followService.getFollowers(targetUserId);
        setFollowList(data.items || []);
      } else {
        const data = await followService.getFollowing(targetUserId);
        setFollowList(data.items || []);
      }
    } catch (err) {
      console.error('Failed to load follow list:', err);
    }
  };

  // 애니 서브메뉴 필터링
  const filterAnimeBySubMenu = useCallback((animeData, submenu) => {
    let filtered = [];

    if (submenu === 'all') {
      // 모두 선택 시 모든 항목 포함 (평가한 것 + 보고싶어요 + 관심없어요)
      filtered = animeData;
    } else if (submenu === '5') {
      filtered = animeData.filter(a => a.category === 'rated' && a.rating === 5.0);
    } else if (submenu === '4') {
      filtered = animeData.filter(a => a.category === 'rated' && a.rating >= 4.0 && a.rating < 5.0);
    } else if (submenu === '3') {
      filtered = animeData.filter(a => a.category === 'rated' && a.rating >= 3.0 && a.rating < 4.0);
    } else if (submenu === '2') {
      filtered = animeData.filter(a => a.category === 'rated' && a.rating >= 2.0 && a.rating < 3.0);
    } else if (submenu === '1') {
      // 1점대 이하: 0.5~1.9
      filtered = animeData.filter(a => a.category === 'rated' && a.rating >= 0.5 && a.rating < 2.0);
    } else if (submenu === 'watchlist') {
      filtered = animeData.filter(a => a.category === 'watchlist');
    } else if (submenu === 'pass') {
      filtered = animeData.filter(a => a.category === 'pass');
    }

    setDisplayedAnime(filtered); // 전체 표시 (이미지는 lazy loading)
  }, []);

  // 캐릭터 서브메뉴 필터링
  const filterCharactersBySubMenu = useCallback((charactersData, submenu) => {
    let filtered = [];

    if (submenu === 'all') {
      // 모두 선택 시 모든 항목 포함
      filtered = charactersData;
    } else if (submenu === '5') {
      // RATED 상태이고 rating이 5.0인 것만
      filtered = charactersData.filter(c => c.status === 'RATED' && c.rating === 5.0);
    } else if (submenu === '4') {
      filtered = charactersData.filter(c => c.status === 'RATED' && c.rating >= 4.0 && c.rating < 5.0);
    } else if (submenu === '3') {
      filtered = charactersData.filter(c => c.status === 'RATED' && c.rating >= 3.0 && c.rating < 4.0);
    } else if (submenu === '2') {
      filtered = charactersData.filter(c => c.status === 'RATED' && c.rating >= 2.0 && c.rating < 3.0);
    } else if (submenu === '1') {
      // 1점대 이하: 0.5~1.9
      filtered = charactersData.filter(c => c.status === 'RATED' && c.rating >= 0.5 && c.rating < 2.0);
    } else if (submenu === 'want') {
      filtered = charactersData.filter(c => c.status === 'WANT_TO_KNOW');
    } else if (submenu === 'pass') {
      filtered = charactersData.filter(c => c.status === 'PASS');
    }

    setDisplayedCharacters(filtered); // 전체 표시 (이미지는 lazy loading)
  }, []);


  // 서브메뉴 변경 시 필터링
  useEffect(() => {
    if (activeTab === 'anime' && allAnime.length > 0) {
      filterAnimeBySubMenu(allAnime, animeSubMenu);
    }
  }, [animeSubMenu, allAnime, activeTab, filterAnimeBySubMenu]);

  useEffect(() => {
    if (activeTab === 'character' && allCharacters.length > 0) {
      filterCharactersBySubMenu(allCharacters, characterSubMenu);
    }
  }, [characterSubMenu, allCharacters, activeTab, filterCharactersBySubMenu]);

  // Edit modal handlers
  const handleEditContent = (activity, mode = 'edit') => {
    setEditingActivity(activity);
    setEditMode(mode);
    setEditModalOpen(true);
  };

  const handleSaveEdit = async (formData) => {
    if (!editingActivity) return;

    const isAnime = editingActivity.activity_type === 'anime_rating';

    try {
      if (editMode === 'edit_rating') {
        // 별점만 수정
        if (isAnime) {
          await ratingService.rateAnime(editingActivity.item_id, {
            rating: formData.rating,
            status: 'RATED'
          });
        } else {
          await characterService.rateCharacter(editingActivity.item_id, {
            rating: formData.rating
          });
        }
      } else if (editMode === 'add_review') {
        // 리뷰 추가
        if (isAnime) {
          await reviewService.createReview({
            anime_id: editingActivity.item_id,
            rating: formData.rating,
            content: formData.content,
            is_spoiler: formData.is_spoiler
          });
        } else {
          await characterReviewService.createReview({
            character_id: editingActivity.item_id,
            rating: formData.rating,
            content: formData.content,
            is_spoiler: formData.is_spoiler
          });
        }
      } else {
        // 리뷰 수정
        if (formData.content && formData.content.trim()) {
          let reviewId;
          if (isAnime) {
            const myReview = await reviewService.getMyReview(editingActivity.item_id);
            reviewId = myReview.review_id || myReview.id;
            await reviewService.updateReview(reviewId, {
              content: formData.content,
              is_spoiler: formData.is_spoiler,
              rating: formData.rating
            });
          } else {
            const myReview = await characterReviewService.getMyReview(editingActivity.item_id);
            reviewId = myReview.review_id || myReview.id;
            await characterReviewService.updateReview(reviewId, {
              content: formData.content,
              is_spoiler: formData.is_spoiler,
              rating: formData.rating
            });
          }
        } else if (formData.rating !== editingActivity.rating) {
          // 리뷰 내용 없이 별점만 변경된 경우
          if (isAnime) {
            await ratingService.rateAnime(editingActivity.item_id, {
              rating: formData.rating,
              status: 'RATED'
            });
          } else {
            await characterService.rateCharacter(editingActivity.item_id, {
              rating: formData.rating
            });
          }
        }
      }

      // Refresh data after edit
      loadData(true);
    } catch (err) {
      console.error('Failed to save:', err);
      throw err;
    }
  };

  const loadData = useCallback(async (forceRefresh = false) => {
    try {
      // 이미 로드한 탭이면 스킵 (anime, character, anipass 캐싱)
      // forceRefresh가 true면 캐시 무시
      if (!forceRefresh && loadedTabs[activeTab] && (activeTab === 'anime' || activeTab === 'character' || activeTab === 'anipass')) {
        return;
      }

      const targetUserId = isOwnProfile ? user?.id : userId;
      const cacheKey = `profile_${targetUserId}_${activeTab}`;

      // Try loading from cache first (unless forceRefresh)
      let cachedData = null;
      if (!forceRefresh) {
        try {
          const cached = sessionStorage.getItem(cacheKey);
          if (cached) {
            const { data, timestamp } = JSON.parse(cached);
            // Use cache if less than 2 minutes old
            if (Date.now() - timestamp < 120000) {
              cachedData = data;
            }
          }
        } catch (err) {
          console.error('Failed to load cache:', err);
        }
      }

      // If we have cached data, use it immediately
      if (cachedData) {
        if (activeTab === 'anime') {
          setAllAnime(cachedData.allAnime || []);
          setAllRatedAnime(cachedData.allRatedAnime || []);
          setWatchlistAnime(cachedData.watchlistAnime || []);
          setPassAnime(cachedData.passAnime || []);
          setStats(prev => ({ ...prev, ...cachedData.stats }));
          filterAnimeBySubMenu(cachedData.allAnime || [], animeSubMenu);
          setLoadedTabs(prev => ({ ...prev, anime: true }));
          setLoading(false);
          setTabLoading(false);
          return;
        } else if (activeTab === 'character') {
          setAllCharacters(cachedData.allCharacters || []);
          setAllRatedCharacters(cachedData.allRatedCharacters || []);
          setWantCharacters(cachedData.wantCharacters || []);
          setPassCharacters(cachedData.passCharacters || []);
          filterCharactersBySubMenu(cachedData.allCharacters || [], characterSubMenu);
          setLoadedTabs(prev => ({ ...prev, character: true }));

          // Load stats if not loaded yet (cache doesn't include stats)
          if (!statsLoaded) {
            const targetUserId = userId || user?.id;
            try {
              if (isOwnProfile) {
                const statsData = await userService.getStats();
                setStats(statsData);
                setStatsLoaded(true);
              } else {
                const profileData = await userService.getUserProfile(targetUserId);
                if (profileData) {
                  setProfileUser(profileData.user);
                  setStats(profileData.stats);
                  setStatsLoaded(true);
                }
              }
            } catch (error) {
              console.error('Failed to load stats:', error);
            }
          }

          setLoading(false);
          setTabLoading(false);
          return;
        } else if (activeTab === 'anipass') {
          setStats(cachedData.stats || stats);
          setGenrePreferences(cachedData.genrePreferences || []);
          setWatchTime(cachedData.watchTime || null);
          setRatingDistribution(cachedData.ratingDistribution || []);
          setYearDistribution(cachedData.yearDistribution || []);
          setFormatDistribution(cachedData.formatDistribution || []);
          setEpisodeLengthDistribution(cachedData.episodeLengthDistribution || []);
          setRatingStats(cachedData.ratingStats || null);
          setStudioStats(cachedData.studioStats || []);
          setSeasonStats(cachedData.seasonStats || []);
          setGenreCombinations(cachedData.genreCombinations || []);
          setLoadedTabs(prev => ({ ...prev, anipass: true }));
          setLoading(false);
          setTabLoading(false);
          return;
        } else if (activeTab === 'feed') {
          // Restore cached feed activities
          setUserActivities(cachedData.userActivities || []);
          setFeedOffset(10);
          setHasMoreFeed(cachedData.userActivities && cachedData.userActivities.length === 10);
          const likesState = {};
          const commentsState = {};
          (cachedData.userActivities || []).forEach(activity => {
            likesState[activity.id] = activity.user_liked || false;
            commentsState[activity.id] = [];
          });
          setActivityLikes(likesState);
          setComments(commentsState);

          // Load stats if not loaded yet (cache doesn't include stats)
          if (!statsLoaded) {
            const targetUserId = userId || user?.id;
            try {
              if (isOwnProfile) {
                const statsData = await userService.getStats();
                setStats(statsData);
                setStatsLoaded(true);
              } else {
                const profileData = await userService.getUserProfile(targetUserId);
                if (profileData) {
                  setProfileUser(profileData.user);
                  setStats(profileData.stats);
                  setStatsLoaded(true);
                }
              }
            } catch (error) {
              console.error('Failed to load stats:', error);
            }
          }

          setLoading(false);
          setTabLoading(false);
          return;
        }
      }

      // Only show full loading screen on initial load
      if (!statsLoaded && isOwnProfile) {
        setLoading(true);
      } else if (!profileUser && !isOwnProfile) {
        setLoading(true);
      } else {
        setTabLoading(true);
      }

      // 내 프로필일 때는 stats와 follow data를 병렬로 로드
      if (!statsLoaded && isOwnProfile && user?.id) {
        const [statsData, followCounts] = await Promise.all([
          userService.getStats(),
          followService.getFollowCounts(user.id).catch(() => ({ followers_count: 0, following_count: 0 }))
        ]);
        setStats(statsData);
        setStatsLoaded(true);
        setFollowCounts(followCounts);
      }

      // 다른 사용자 프로필 정보와 follow data를 병렬로 로드
      if (!isOwnProfile && !profileUser) {
        const targetUserId = parseInt(userId);
        const [profileData, genrePrefs, followCounts, followStatus] = await Promise.all([
          userService.getUserProfile(targetUserId).catch(() => null),
          userService.getUserGenrePreferences(targetUserId).catch(() => []),
          followService.getFollowCounts(targetUserId).catch(() => ({ followers_count: 0, following_count: 0 })),
          followService.isFollowing(targetUserId).catch(() => ({ is_following: false }))
        ]);
        if (profileData) {
          setProfileUser(profileData.user); // user 객체 설정
          setStats(profileData.stats); // stats 객체 설정
          setStatsLoaded(true);
        }
        setGenrePreferences(genrePrefs);
        setFollowCounts(followCounts);
        setIsFollowing(followStatus.is_following);
      }

      if (activeTab === 'anipass') {
        const [
          statsData,
          genreData,
          watchTimeData,
          ratingDist,
          yearDist,
          formatDist,
          episodeDist,
          ratingStat,
          studioDist,
          seasonDist,
          genreCombo
        ] = await Promise.all([
          isOwnProfile ? userService.getStats() : userService.getUserStats(userId),
          isOwnProfile ? userService.getGenrePreferences().catch(() => []) : userService.getUserGenrePreferences(userId).catch(() => []),
          isOwnProfile ? userService.getWatchTime().catch(() => ({ total_minutes: 0 })) : userService.getUserWatchTime(userId).catch(() => ({ total_minutes: 0 })),
          isOwnProfile ? userService.getRatingDistribution().catch(() => []) : userService.getUserRatingDistribution(userId).catch(() => []),
          isOwnProfile ? userService.getYearDistribution().catch(() => []) : userService.getUserYearDistribution(userId).catch(() => []),
          isOwnProfile ? userService.getFormatDistribution().catch(() => []) : userService.getUserFormatDistribution(userId).catch(() => []),
          isOwnProfile ? userService.getEpisodeLengthDistribution().catch(() => []) : userService.getUserEpisodeLengthDistribution(userId).catch(() => []),
          isOwnProfile ? userService.getRatingStats().catch(() => null) : userService.getUserRatingStats(userId).catch(() => null),
          isOwnProfile ? userService.getStudioStats().catch(() => []) : userService.getUserStudioStats(userId).catch(() => []),
          isOwnProfile ? userService.getSeasonStats().catch(() => []) : userService.getUserSeasonStats(userId).catch(() => []),
          isOwnProfile ? userService.getGenreCombinations().catch(() => []) : userService.getUserGenreCombinations(userId).catch(() => []),
        ]);

        // Ensure average_rating is always available from the start
        // If not in stats, calculate it from ratingStats
        if (statsData && !statsData.average_rating && ratingStat && ratingStat.average !== undefined) {
          statsData.average_rating = ratingStat.average;
        }

        setStats(statsData);
        setGenrePreferences(genreData);
        setWatchTime(watchTimeData);
        setRatingDistribution(ratingDist);
        setYearDistribution(yearDist);
        setFormatDistribution(formatDist);
        setEpisodeLengthDistribution(episodeDist);
        setRatingStats(ratingStat);
        setStudioStats(studioDist);
        setSeasonStats(seasonDist);
        setGenreCombinations(genreCombo);
        setLoadedTabs(prev => ({ ...prev, anipass: true }));

        // Save to cache
        try {
          sessionStorage.setItem(cacheKey, JSON.stringify({
            data: {
              stats: statsData,
              genrePreferences: genreData,
              watchTime: watchTimeData,
              ratingDistribution: ratingDist,
              yearDistribution: yearDist,
              formatDistribution: formatDist,
              episodeLengthDistribution: episodeDist,
              ratingStats: ratingStat,
              studioStats: studioDist,
              seasonStats: seasonDist,
              genreCombinations: genreCombo
            },
            timestamp: Date.now()
          }));
        } catch (err) {
          console.error('Failed to save cache:', err);
        }
      } else if (activeTab === 'anime') {
        // Load all anime (rated, watchlist, pass) - Single API call for 3x speed!
        const targetUserId = isOwnProfile ? null : parseInt(userId);
        const allRatingsData = isOwnProfile
          ? await ratingService.getAllMyRatings()
          : await ratingService.getAllUserRatings(targetUserId);

        const allAnimeData = [
          ...(allRatingsData.rated || []).map(item => ({ ...item, category: 'rated' })),
          ...(allRatingsData.watchlist || []).map(item => ({ ...item, category: 'watchlist' })),
          ...(allRatingsData.pass || []).map(item => ({ ...item, category: 'pass' }))
        ];

        setAllAnime(allAnimeData);
        setAllRatedAnime(allRatingsData.rated || []);
        setWatchlistAnime(allRatingsData.watchlist || []);
        setPassAnime(allRatingsData.pass || []);

        // Update stats
        setStats(prev => ({
          ...prev,
          average_rating: allRatingsData.average_rating,
          total_rated: allRatingsData.total_rated || 0,
          total_want_to_watch: allRatingsData.total_watchlist || 0,
          total_pass: allRatingsData.total_pass || 0
        }));

        filterAnimeBySubMenu(allAnimeData, animeSubMenu);
        setLoadedTabs(prev => ({ ...prev, anime: true }));

        // Save to cache
        try {
          sessionStorage.setItem(cacheKey, JSON.stringify({
            data: {
              allAnime: allAnimeData,
              allRatedAnime: allRatingsData.rated || [],
              watchlistAnime: allRatingsData.watchlist || [],
              passAnime: allRatingsData.pass || [],
              stats: {
                average_rating: allRatingsData.average_rating,
                total_rated: allRatingsData.total_rated || 0,
                total_watchlist: allRatingsData.total_watchlist || 0,
                total_pass: allRatingsData.total_pass || 0
              }
            },
            timestamp: Date.now()
          }));
        } catch (err) {
          console.error('Failed to save cache:', err);
        }
      } else if (activeTab === 'character') {
        // Load all characters (rated, want_to_know, not_interested) - Single API call for 3x speed!
        const targetUserId = isOwnProfile ? null : parseInt(userId);
        const allCharacterRatings = isOwnProfile
          ? await characterService.getAllMyRatings()
          : await characterService.getAllUserRatings(targetUserId);

        const allCharactersData = [
          ...(allCharacterRatings.rated || []).map(c => ({ ...c, category: 'rated' })),
          ...(allCharacterRatings.want_to_know || []).map(c => ({ ...c, category: 'want' })),
          ...(allCharacterRatings.not_interested || []).map(c => ({ ...c, category: 'pass' }))
        ];

        setAllCharacters(allCharactersData);
        setAllRatedCharacters(allCharacterRatings.rated || []);
        setWantCharacters(allCharacterRatings.want_to_know || []);
        setPassCharacters(allCharacterRatings.not_interested || []);

        filterCharactersBySubMenu(allCharactersData, characterSubMenu);
        setLoadedTabs(prev => ({ ...prev, character: true }));

        // Save to cache
        try {
          sessionStorage.setItem(cacheKey, JSON.stringify({
            data: {
              allCharacters: allCharactersData,
              allRatedCharacters: allCharacterRatings.rated || [],
              wantCharacters: allCharacterRatings.want_to_know || [],
              passCharacters: allCharacterRatings.not_interested || []
            },
            timestamp: Date.now()
          }));
        } catch (err) {
          console.error('Failed to save cache:', err);
        }
      } else if (activeTab === 'feed') {
        try {
          const targetUserId = userId || user?.id;

          // Load stats if not loaded yet
          if (!statsLoaded) {
            if (isOwnProfile) {
              const statsData = await userService.getStats();
              setStats(statsData);
              setStatsLoaded(true);
            } else {
              const profileData = await userService.getUserProfile(targetUserId);
              if (profileData) {
                setProfileUser(profileData.user);
                setStats(profileData.stats);
                setStatsLoaded(true);
              }
            }
          }

          const feedData = await feedService.getUserFeed(targetUserId, 10, 0);
          setUserActivities(feedData || []);
          setFeedOffset(10);
          setHasMoreFeed(feedData && feedData.length === 10);

          // Initialize likes and comments state
          const likesState = {};
          const commentsState = {};
          (feedData || []).forEach(activity => {
            const key = `${activity.activity_type}_${activity.user_id}_${activity.item_id}`;
            likesState[key] = {
              count: activity.likes_count || 0,
              liked: Boolean(activity.user_has_liked)
            };
            commentsState[key] = [];
          });
          setActivityLikes(likesState);
          setComments(commentsState);
          setExpandedComments(new Set());

          setLoadedTabs(prev => ({ ...prev, feed: true }));

          // Save to cache
          try {
            sessionStorage.setItem(cacheKey, JSON.stringify({
              data: {
                userActivities: feedData || []
              },
              timestamp: Date.now()
            }));
          } catch (err) {
            console.error('Failed to save cache:', err);
          }
        } catch (error) {
          console.error('Failed to load feed:', error);
          setUserActivities([]);
          setFeedOffset(0);
          setHasMoreFeed(false);
          setLoadedTabs(prev => ({ ...prev, feed: true }));
        }

        // 로딩 완료 (댓글은 사용자가 클릭할 때만 로드)
        setLoading(false);
        setTabLoading(false);
        return;
      }

      setLoading(false);
      setTabLoading(false);
    } catch (err) {
      console.error('Failed to load data:', err);
      setLoading(false);
      setTabLoading(false);
    }
  }, [isOwnProfile, activeTab, statsLoaded, profileUser, userId, user, filterAnimeBySubMenu, animeSubMenu, filterCharactersBySubMenu, characterSubMenu]);

  // Load data when tab or userId changes
  useEffect(() => {
    // Reset states when userId changes (switching between profiles)
    if (userId !== undefined) {
      setUserActivities([]);
      setFeedOffset(0);
      setHasMoreFeed(true);
      setLoadedTabs({
        anipass: false,
        anime: false,
        character: false,
        feed: false
      });
    }
    loadData();
  }, [activeTab, userId, loadData]);

  // 팔로우 카운트는 항상 로드 (페이지 진입 시, userId 변경 시)
  useEffect(() => {
    loadFollowData();
  }, [loadFollowData]);

  const formatWatchTime = (minutes) => {
    if (!minutes) return '0시간';
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours === 0) return `${mins}분`;
    if (mins === 0) return `${hours}시간`;
    return `${hours}시간 ${mins}분`;
  };

  // Wrapper for avatar URL helper
  const getAvatarUrl = (avatarUrl) => {
    return getAvatarUrlHelper(avatarUrl) || '/placeholder-avatar.png';
  };

  // Helper for anime cover images and character images
  const getImageUrl = (imageUrl) => {
    if (!imageUrl) return '/placeholder-anime.svg';

    // If it's an AniList character image, try R2 first
    if (imageUrl.includes('anilist.co') && imageUrl.includes('/character/')) {
      const match = imageUrl.match(/\/b(\d+)-/);
      if (match && match[1]) {
        const characterId = match[1];
        return `${IMAGE_BASE_URL}/images/characters/${characterId}.jpg`;
      }
    }

    if (imageUrl.startsWith('http')) return imageUrl;

    const processedUrl = imageUrl.includes('/covers/')
      ? imageUrl.replace('/covers/', '/covers_large/')
      : imageUrl;
    return `${IMAGE_BASE_URL}${processedUrl}`;
  };

  const getActivityText = (activity) => {
    const displayName = activity.display_name || activity.username;

    switch (activity.activity_type) {
      case 'anime_rating':
        return language === 'ko' ? `${displayName}님이 평가했어요` : language === 'ja' ? `${displayName}さんが評価しました` : `${displayName} rated an anime`;
      case 'character_rating':
        return language === 'ko' ? `${displayName}님이 캐릭터를 평가했어요` : language === 'ja' ? `${displayName}さんがキャラクターを評価しました` : `${displayName} rated a character`;
      case 'review':
        return language === 'ko' ? `${displayName}님이 리뷰를 남겼어요` : language === 'ja' ? `${displayName}さんがレビューを残しました` : `${displayName} left a review`;
      default:
        return language === 'ko' ? `${displayName}님의 활동` : language === 'ja' ? `${displayName}さんのアクティビティ` : `${displayName}'s activity`;
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
    // SQLite timestamp를 UTC로 파싱
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

  const getActivityKey = (activity) => {
    return `${activity.activity_type}_${activity.user_id}_${activity.item_id}`;
  };

  const toggleComments = async (activity) => {
    const key = getActivityKey(activity);

    if (expandedComments.has(key)) {
      setExpandedComments(prev => {
        const newSet = new Set(prev);
        newSet.delete(key);
        return newSet;
      });
    } else {
      setExpandedComments(prev => new Set(prev).add(key));
      await loadComments(activity);
    }
  };

  const loadMoreFeed = useCallback(async () => {
    if (loadingMoreFeed || !hasMoreFeed) return;

    try {
      setLoadingMoreFeed(true);
      const targetUserId = userId || user?.id;
      const feedData = await feedService.getUserFeed(targetUserId, 50, feedOffset);

      if (feedData && feedData.length > 0) {
        setUserActivities(prev => [...prev, ...feedData]);
        setFeedOffset(prev => prev + feedData.length);
        setHasMoreFeed(feedData.length === 50);

        // Add likes and comments state for new activities
        const likesState = {};
        const commentsState = {};
        feedData.forEach(activity => {
          const key = `${activity.activity_type}_${activity.user_id}_${activity.item_id}`;
          likesState[key] = {
            count: activity.likes_count || 0,
            liked: Boolean(activity.user_has_liked)
          };
          commentsState[key] = [];
        });
        setActivityLikes(prev => ({ ...prev, ...likesState }));
        setComments(prev => ({ ...prev, ...commentsState }));
      } else {
        setHasMoreFeed(false);
      }
    } catch (err) {
      console.error('Failed to load more feed:', err);
    } finally {
      setLoadingMoreFeed(false);
    }
  }, [loadingMoreFeed, hasMoreFeed, userId, user?.id, feedOffset]);

  // Keep ref updated with latest loadMoreFeed
  loadMoreFeedRef.current = loadMoreFeed;

  // Infinite scroll callback - uses ref to access latest loadMoreFeed
  const lastActivityElementRef = useCallback(node => {
    if (loadingMoreFeed) return;
    if (observer.current) observer.current.disconnect();

    observer.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && hasMoreFeed) {
        if (loadMoreFeedRef.current) {
          loadMoreFeedRef.current();
        }
      }
    });

    if (node) {
      observer.current.observe(node);
    }
  }, [loadingMoreFeed, hasMoreFeed]);

  const loadComments = async (activity) => {
    try {
      const key = getActivityKey(activity);
      const data = await ActivityUtils.loadComments(activity);

      // Initialize comment likes
      const likes = {};
      data.items?.forEach(comment => {
        likes[comment.id] = {
          count: comment.likes_count || 0,
          liked: Boolean(comment.user_liked)
        };
        // Also for replies
        comment.replies?.forEach(reply => {
          likes[reply.id] = {
            count: reply.likes_count || 0,
            liked: Boolean(reply.user_liked)
          };
        });
      });
      setCommentLikes(prev => ({ ...prev, ...likes }));
      setComments(prev => ({ ...prev, [key]: data.items || [] }));
    } catch (err) {
      console.error('Failed to load comments:', err);
    }
  };

  // 활동의 댓글 수를 업데이트하는 헬퍼 함수
  const updateActivityCommentsCount = (activity, delta) => {
    setUserActivities(prev => prev.map(act => {
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

  const handleSubmitComment = async (activity, parentCommentId = null) => {
    const key = getActivityKey(activity);
    const text = parentCommentId ? newCommentText[`${key}-${parentCommentId}`] : newCommentText[key];

    console.log('[MyAniPass] handleSubmitComment called', { activity, parentCommentId, text, key });

    if (!text?.trim()) {
      console.log('[MyAniPass] No text to submit');
      return;
    }

    try {
      if (parentCommentId) {
        console.log('[MyAniPass] Creating reply...');
        await ActivityUtils.createReply(activity, parentCommentId, text);
      } else {
        console.log('[MyAniPass] Creating comment...');
        await ActivityUtils.createComment(activity, text);
      }
      console.log('[MyAniPass] Comment/reply created successfully');

      // Clear input
      if (parentCommentId) {
        setNewCommentText(prev => ({ ...prev, [`${key}-${parentCommentId}`]: '' }));
        setReplyingTo(prev => ({ ...prev, [parentCommentId]: false }));
      } else {
        setNewCommentText(prev => ({ ...prev, [key]: '' }));
      }

      // Reload comments
      console.log('[MyAniPass] Reloading comments...');
      await loadComments(activity);
      updateActivityCommentsCount(activity, 1);
      console.log('[MyAniPass] Comments reloaded and count updated');
    } catch (err) {
      console.error('[MyAniPass] Failed to submit comment:', err);
      alert(language === 'ko' ? `댓글 작성에 실패했습니다: ${err.message}` : language === 'ja' ? `コメント投稿に失敗しました: ${err.message}` : `Failed to post comment: ${err.message}`);
    }
  };

  const handleToggleActivityLike = async (activity) => {
    try {
      const result = await activityLikeService.toggleLike(
        activity.activity_type,
        activity.user_id,
        activity.item_id
      );
      const key = getActivityKey(activity);
      setActivityLikes(prev => ({
        ...prev,
        [key]: { liked: result.liked, count: result.like_count }
      }));
    } catch (err) {
      console.error('Failed to toggle activity like:', err);
    }
  };

  const handleToggleCommentLike = async (commentId) => {
    try {
      const result = await commentLikeService.toggleLike(commentId);
      setCommentLikes(prev => ({
        ...prev,
        [commentId]: { liked: result.liked, count: result.like_count }
      }));
    } catch (err) {
      console.error('Failed to toggle comment like:', err);
    }
  };

  const handleReplyClick = (commentId) => {
    setReplyingTo(prev => ({ ...prev, [commentId]: !prev[commentId] }));
  };

  const handleSubmitReply = async (activity, parentCommentId) => {
    const key = getActivityKey(activity);
    const text = replyText[parentCommentId];

    if (!text?.trim()) return;

    try {
      await ActivityUtils.createReply(activity, parentCommentId, text);

      setReplyText(prev => ({ ...prev, [parentCommentId]: '' }));
      setReplyingTo(prev => ({ ...prev, [parentCommentId]: false }));
      await loadComments(activity);
      updateActivityCommentsCount(activity, 1);
    } catch (err) {
      console.error('Failed to submit reply:', err);
      alert(language === 'ko' ? '답글 작성에 실패했습니다.' : language === 'ja' ? '返信投稿に失敗しました' : 'Failed to post reply.');
    }
  };

  const handleDeleteComment = async (activity, commentId) => {
    if (!confirm(language === 'ko' ? '댓글을 삭제하시겠습니까?' : language === 'ja' ? 'このコメントを削除しますか？' : 'Delete this comment?')) return;

    try {
      await ActivityUtils.deleteComment(activity, commentId);
      await loadComments(activity);
      updateActivityCommentsCount(activity, -1);
    } catch (err) {
      console.error('Failed to delete comment:', err);
      alert(language === 'ko' ? '댓글 삭제에 실패했습니다.' : language === 'ja' ? 'コメント削除に失敗しました' : 'Failed to delete comment.');
    }
  };

  const handleOpenDeleteModal = (activity) => {
    setActivityToDelete(activity);
    setShowDeleteModal(true);
    setDeleteMenuOpen(null);
  };

  const handleDeleteActivity = async (deleteType) => {
    if (!activityToDelete) return;

    try {
      const activity = activityToDelete;
      const isAnime = activity.activity_type === 'anime_rating';
      const hasReview = activity.review_content && activity.review_content.trim();

      if (deleteType === 'review_only' && hasReview) {
        // 리뷰만 삭제 (별점은 유지)
        if (isAnime) {
          await reviewService.deleteReview(activity.id);
        } else {
          await characterReviewService.deleteReview(activity.id);
        }
      } else {
        // 별점까지 모두 삭제
        if (isAnime) {
          await ratingService.deleteRating(activity.item_id);
        } else {
          await characterService.deleteCharacterRating(activity.item_id);
        }
      }

      setShowDeleteModal(false);
      setActivityToDelete(null);

      // Update UI based on delete type
      if (deleteType === 'review_only') {
        // Remove review content but keep rating activity
        setUserActivities(prev => prev.map(a =>
          (a.activity_type === activity.activity_type &&
           a.user_id === activity.user_id &&
           a.item_id === activity.item_id)
            ? { ...a, review_content: '', review_id: null }
            : a
        ));
      } else {
        // Remove entire activity
        setUserActivities(prev => prev.filter(a =>
          !(a.activity_type === activity.activity_type &&
            a.user_id === activity.user_id &&
            a.item_id === activity.item_id)
        ));
      }

      // Reload stats
      if (isOwnProfile) {
        loadStats();
      }
    } catch (err) {
      console.error('Failed to delete activity:', err);
      alert(language === 'ko' ? '삭제에 실패했습니다.' : language === 'ja' ? '削除に失敗しました' : 'Failed to delete.');
    }
  };

  const handleAvatarError = (e, userId) => {
    if (failedImages.has(`avatar-${userId}`)) return;
    setFailedImages(prev => new Set(prev).add(`avatar-${userId}`));
    e.target.src = '/placeholder-avatar.png';
  };

  const handleImageError = (e, itemId) => {
    if (failedImages.has(`image-${itemId}`)) return;
    setFailedImages(prev => new Set(prev).add(`image-${itemId}`));
    e.target.src = '/placeholder-anime.svg';
  };

  const handleCreatePost = async () => {
    if (!newPostContent || !newPostContent.trim()) return;

    try {
      await userPostService.createPost(newPostContent);
      setNewPostContent('');
      // Reload feed data (최신 10개만)
      const targetUserId = userId || user?.id;
      const feedData = await feedService.getUserFeed(targetUserId, 10, 0);
      setUserActivities(feedData || []);
      setFeedOffset(10);
      setHasMoreFeed(feedData && feedData.length === 10);

      // Reinitialize likes and comments state
      const likesState = {};
      const commentsState = {};
      feedData.forEach(activity => {
        const key = `${activity.activity_type}_${activity.user_id}_${activity.item_id}`;
        likesState[key] = {
          count: activity.likes_count || 0,
          liked: Boolean(activity.user_has_liked)
        };
        commentsState[key] = [];
      });
      setActivityLikes(likesState);
      setComments(commentsState);
      setExpandedComments(new Set());
    } catch (err) {
      console.error('Failed to create post:', err);
      alert(language === 'ko' ? '게시물 작성에 실패했습니다.' : language === 'ja' ? '投稿作成に失敗しました' : 'Failed to create post.');
    }
  };


  // 평점별로 그룹화 (애니용)
  const groupAnimeByCategory = (items) => {
    const groups = {
      '5': items.filter(item => item.category === 'rated' && item.rating === 5.0),
      '4.5': items.filter(item => item.category === 'rated' && item.rating === 4.5),
      '4': items.filter(item => item.category === 'rated' && item.rating === 4.0),
      '3.5': items.filter(item => item.category === 'rated' && item.rating === 3.5),
      '3': items.filter(item => item.category === 'rated' && item.rating === 3.0),
      '2.5': items.filter(item => item.category === 'rated' && item.rating === 2.5),
      '2': items.filter(item => item.category === 'rated' && item.rating === 2.0),
      '1.5': items.filter(item => item.category === 'rated' && item.rating === 1.5),
      '1': items.filter(item => item.category === 'rated' && item.rating === 1.0),
      '0.5': items.filter(item => item.category === 'rated' && item.rating === 0.5),
      'watchlist': items.filter(item => item.category === 'watchlist'),
      'pass': items.filter(item => item.category === 'pass')
    };
    return groups;
  };

  // 평점별로 그룹화 (캐릭터용)
  const groupCharactersByCategory = (items) => {
    const groups = {
      '5': items.filter(item => item.rating === 5.0),
      '4.5': items.filter(item => item.rating === 4.5),
      '4': items.filter(item => item.rating === 4.0),
      '3.5': items.filter(item => item.rating === 3.5),
      '3': items.filter(item => item.rating === 3.0),
      '2.5': items.filter(item => item.rating === 2.5),
      '2': items.filter(item => item.rating === 2.0),
      '1.5': items.filter(item => item.rating === 1.5),
      '1': items.filter(item => item.rating === 1.0),
      '0.5': items.filter(item => item.rating === 0.5),
      'want': items.filter(item => item.status === 'WANT_TO_KNOW'),
      'pass': items.filter(item => item.status === 'PASS')
    };
    return groups;
  };

  // Prepare sections for virtual scrolling (anime)
  const animeSections = useMemo(() => {
    if (!['all', '4', '3', '2', '1'].includes(animeSubMenu) || displayedAnime.length === 0) {
      return [];
    }
    const groups = groupAnimeByCategory(displayedAnime);
    const categoryOrder = ['5', '4.5', '4', '3.5', '3', '2.5', '2', '1.5', '1', '0.5', 'watchlist', 'pass'];
    return categoryOrder
      .map((category) => ({
        id: `anime-${category}`,
        category,
        items: groups[category]
      }))
      .filter((section) => section.items.length > 0);
  }, [displayedAnime, animeSubMenu]);

  // Prepare sections for virtual scrolling (character)
  const characterSections = useMemo(() => {
    if (!['all', '4', '3', '2', '1'].includes(characterSubMenu) || displayedCharacters.length === 0) {
      return [];
    }
    const groups = groupCharactersByCategory(displayedCharacters);
    const categoryOrder = ['5', '4.5', '4', '3.5', '3', '2.5', '2', '1.5', '1', '0.5', 'want', 'pass'];
    return categoryOrder
      .map((category) => ({
        id: `character-${category}`,
        category,
        items: groups[category]
      }))
      .filter((section) => section.items.length > 0);
  }, [displayedCharacters, characterSubMenu]);

  // Virtual scrolling hooks
  const { getSectionRef: getAnimeSectionRef, isSectionVisible: isAnimeSectionVisible } = useVirtualGrid(animeSections);
  const { getSectionRef: getCharacterSectionRef, isSectionVisible: isCharacterSectionVisible } = useVirtualGrid(characterSections);

  if (loading) {
    return (
      <div className="min-h-screen pt-12 md:pt-16 bg-transparent">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8">
          {/* Header with Real User Data */}
          <div className="bg-white rounded-2xl shadow-[0_2px_12px_rgba(0,0,0,0.08)] p-6 mb-8">
            <div className="flex items-center gap-4 mb-6">
              {/* Real Avatar */}
              {displayUser?.avatar_url ? (
                <img
                  src={getAvatarUrl(displayUser.avatar_url)}
                  alt={displayUser.display_name || displayUser.username}
                  className="w-20 h-20 rounded-full object-cover border-2 border-gray-200"
                  onError={(e) => {
                    e.target.style.display = 'none';
                  }}
                />
              ) : (
                <div className="w-20 h-20 rounded-full flex items-center justify-center text-white text-3xl font-bold border-2 border-gray-200" style={{ background: getAvatarGradient(displayUser?.username) }}>
                  {(displayUser?.display_name || displayUser?.username || 'U')[0].toUpperCase()}
                </div>
              )}
              <div className="flex-1">
                {/* Real Name */}
                <div className="flex items-center gap-2 mb-1">
                  <h1 className="text-2xl font-bold">
                    {displayUser?.display_name || displayUser?.username}
                  </h1>
                </div>
                {/* Real Follow Counts */}
                <div className="flex items-center gap-4 mb-2">
                  <button
                    onClick={() => openFollowModal('followers')}
                    className="text-sm hover:text-[#737373] transition-colors"
                  >
                    <span className="font-bold">{followCounts.followers_count}</span> {language === 'ko' ? '팔로워' : language === 'ja' ? 'フォロワー' : 'Followers'}
                  </button>
                  <button
                    onClick={() => openFollowModal('following')}
                    className="text-sm hover:text-[#737373] transition-colors"
                  >
                    <span className="font-bold">{followCounts.following_count}</span> {language === 'ko' ? '팔로잉' : language === 'ja' ? 'フォロー中' : 'Following'}
                  </button>
                </div>
              </div>
            </div>

            {/* Tabs - Real and Clickable */}
            <div className="flex border-b border-gray-200 overflow-x-auto">
              <button
                onClick={() => changeTab('feed')}
                className={`px-3 sm:px-6 py-2 sm:py-3 text-sm sm:text-base font-medium transition-colors whitespace-nowrap ${
                  activeTab === 'feed'
                    ? 'border-b-2'
                    : 'text-gray-600 hover:text-gray-800'
                }`}
                style={activeTab === 'feed' ? { color: '#000000', borderColor: '#000000', fontWeight: '600' } : {}}
              >
                {language === 'ko' ? '피드' : language === 'ja' ? 'フィード' : 'Feed'}
              </button>
              <button
                onClick={() => changeTab('anipass')}
                className={`px-3 sm:px-6 py-2 sm:py-3 text-sm sm:text-base font-medium transition-colors whitespace-nowrap ${
                  activeTab === 'anipass'
                    ? 'border-b-2'
                    : 'text-gray-600 hover:text-gray-800'
                }`}
                style={activeTab === 'anipass' ? { color: '#000000', borderColor: '#000000', fontWeight: '600' } : {}}
              >
                {language === 'ko' ? '애니패스' : language === 'ja' ? 'AniPass' : 'AniPass'}
              </button>
              <button
                onClick={() => changeTab('anime')}
                className={`px-3 sm:px-6 py-2 sm:py-3 text-sm sm:text-base font-medium transition-colors whitespace-nowrap ${
                  activeTab === 'anime'
                    ? 'border-b-2'
                    : 'text-gray-600 hover:text-gray-800'
                }`}
                style={activeTab === 'anime' ? { color: '#000000', borderColor: '#000000', fontWeight: '600' } : {}}
              >
                {language === 'ko' ? '애니' : language === 'ja' ? 'アニメ' : 'Anime'}
              </button>
              <button
                onClick={() => changeTab('character')}
                className={`px-3 sm:px-6 py-2 sm:py-3 text-sm sm:text-base font-medium transition-colors whitespace-nowrap ${
                  activeTab === 'character'
                    ? 'border-b-2'
                    : 'text-gray-600 hover:text-gray-800'
                }`}
                style={activeTab === 'character' ? { color: '#000000', borderColor: '#000000', fontWeight: '600' } : {}}
              >
                {language === 'ko' ? '캐릭터' : language === 'ja' ? 'キャラクター' : 'Character'}
              </button>
            </div>
          </div>

          {/* Loading Indicator */}
          <div className="flex justify-center items-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-12 md:pt-16 bg-transparent">

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-[0_2px_12px_rgba(0,0,0,0.08)] p-6 mb-8">
          <div className="flex items-center gap-4 mb-6">
            {displayUser?.avatar_url ? (
              <img
                src={getAvatarUrl(displayUser.avatar_url)}
                alt={displayUser.display_name || displayUser.username}
                className="w-20 h-20 rounded-full object-cover border-2 border-gray-200"
                onError={(e) => {
                  e.target.style.display = 'none';
                }}
              />
            ) : (
              <div className="w-20 h-20 rounded-full flex items-center justify-center text-white text-3xl font-bold border-2 border-gray-200" style={{ background: getAvatarGradient(displayUser?.username) }}>
                {(displayUser?.display_name || displayUser?.username || 'U')[0].toUpperCase()}
              </div>
            )}
            <div>
              <div className="flex items-center gap-2 mb-1">
                <h1 className="text-2xl font-bold">
                  {displayUser?.display_name || displayUser?.username}
                </h1>
                {stats && (
                  (() => {
                    const levelInfo = getCurrentLevelInfo(stats.otaku_score || 0, language);
                    return (
                      <span className={`px-3 py-1 rounded-full text-sm font-semibold ${levelInfo.bgGradient} border ${levelInfo.borderColor}`}>
                        <span style={{ color: levelInfo.color }} className="font-bold">{levelInfo.icon}</span> <span className="text-gray-700">{levelInfo.level} - {toRoman(levelInfo.rank)}</span>
                      </span>
                    );
                  })()
                )}
              </div>
              <div className="flex items-center gap-4 mb-2">
                <button
                  onClick={() => openFollowModal('followers')}
                  className="text-sm hover:text-[#737373] transition-colors"
                >
                  <span className="font-bold">{followCounts.followers_count}</span> {language === 'ko' ? '팔로워' : language === 'ja' ? 'フォロワー' : 'Followers'}
                </button>
                <button
                  onClick={() => openFollowModal('following')}
                  className="text-sm hover:text-[#737373] transition-colors"
                >
                  <span className="font-bold">{followCounts.following_count}</span> {language === 'ko' ? '팔로잉' : language === 'ja' ? 'フォロー中' : 'Following'}
                </button>
              </div>
            </div>
            {!isOwnProfile && (
              <button
                onClick={handleFollowToggle}
                className={`ml-auto px-4 py-2 rounded-lg font-medium transition-colors ${
                  isFollowing
                    ? 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    : 'text-white'
                }`}
                style={!isFollowing ? { backgroundColor: '#3797F0', color: 'white', fontWeight: '600' } : {}}
                onMouseEnter={(e) => !isFollowing && (e.target.style.backgroundColor = '#1877F2')}
                onMouseLeave={(e) => !isFollowing && (e.target.style.backgroundColor = '#3797F0')}
              >
                {isFollowing ? (language === 'ko' ? '언팔로우' : language === 'ja' ? 'フォロー解除' : 'Unfollow') : (language === 'ko' ? '팔로우' : language === 'ja' ? 'フォロー' : 'Follow')}
              </button>
            )}
          </div>

          {/* Tabs */}
          <div className="flex border-b border-gray-200 overflow-x-auto">
            <button
              onClick={() => changeTab('feed')}
              className={`px-3 sm:px-6 py-2 sm:py-3 text-sm sm:text-base font-medium transition-colors whitespace-nowrap ${
                activeTab === 'feed'
                  ? 'border-b-2'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
              style={activeTab === 'feed' ? { color: '#000000', borderColor: '#000000', fontWeight: '600' } : {}}
            >
              {language === 'ko' ? '피드' : language === 'ja' ? 'フィード' : 'Feed'}
            </button>
            <button
              onClick={() => changeTab('anipass')}
              className={`px-3 sm:px-6 py-2 sm:py-3 text-sm sm:text-base font-medium transition-colors whitespace-nowrap ${
                activeTab === 'anipass'
                  ? 'border-b-2'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
              style={activeTab === 'anipass' ? { color: '#000000', borderColor: '#000000', fontWeight: '600' } : {}}
            >
              {language === 'ko' ? '애니패스' : language === 'ja' ? 'AniPass' : 'AniPass'}
            </button>
            <button
              onClick={() => changeTab('anime')}
              className={`px-3 sm:px-6 py-2 sm:py-3 text-sm sm:text-base font-medium transition-colors whitespace-nowrap ${
                activeTab === 'anime'
                  ? 'border-b-2'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
              style={activeTab === 'anime' ? { color: '#000000', borderColor: '#000000', fontWeight: '600' } : {}}
            >
              {language === 'ko' ? '애니' : language === 'ja' ? 'アニメ' : 'Anime'} {stats && <span className="text-xs sm:text-sm">({(stats.total_rated || 0) + (stats.total_want_to_watch || 0) + (stats.total_pass || 0)})</span>}
            </button>
            <button
              onClick={() => changeTab('character')}
              className={`px-3 sm:px-6 py-2 sm:py-3 text-sm sm:text-base font-medium transition-colors whitespace-nowrap ${
                activeTab === 'character'
                  ? 'border-b-2'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
              style={activeTab === 'character' ? { color: '#000000', borderColor: '#000000', fontWeight: '600' } : {}}
            >
              {language === 'ko' ? '캐릭터' : language === 'ja' ? 'キャラクター' : 'Character'} {stats && <span className="text-xs sm:text-sm">({stats.total_character_ratings || 0})</span>}
            </button>
          </div>
        </div>

        {/* Content */}
        {/* Show filters first for anime/character tabs, regardless of loading state */}
        {!loading && (activeTab === 'anime' || activeTab === 'character') && (
          <div className="mb-6">
            {activeTab === 'anime' && (
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => setAnimeSubMenu('all')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    animeSubMenu === 'all'
                      ? ''
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  style={animeSubMenu === 'all' ? { backgroundColor: '#3797F0', color: 'white', fontWeight: '600' } : {}}
                >
                  {language === 'ko' ? '모두' : language === 'ja' ? 'すべて' : 'All'}
                </button>
                <button
                  onClick={() => setAnimeSubMenu('5')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    animeSubMenu === '5'
                      ? ''
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  style={animeSubMenu === '5' ? { backgroundColor: '#3797F0', color: 'white', fontWeight: '600' } : {}}
                >
                  ⭐ 5{language === 'ko' ? '점' : language === 'ja' ? '点' : ''}
                </button>
                <button
                  onClick={() => setAnimeSubMenu('4')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    animeSubMenu === '4'
                      ? ''
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  style={animeSubMenu === '4' ? { backgroundColor: '#3797F0', color: 'white', fontWeight: '600' } : {}}
                >
                  ⭐ 4{language === 'ko' ? '점대' : language === 'ja' ? '点台' : '.0-4.5'}
                </button>
                <button
                  onClick={() => setAnimeSubMenu('3')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    animeSubMenu === '3'
                      ? 'text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  style={animeSubMenu === '3' ? { backgroundColor: '#3797F0', color: 'white', fontWeight: '600' } : {}}
                >
                  ⭐ 3{language === 'ko' ? '점대' : language === 'ja' ? '点台' : '.0-3.5'}
                </button>
                <button
                  onClick={() => setAnimeSubMenu('2')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    animeSubMenu === '2'
                      ? 'text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  style={animeSubMenu === '2' ? { backgroundColor: '#3797F0', color: 'white', fontWeight: '600' } : {}}
                >
                  ⭐ 2{language === 'ko' ? '점대' : language === 'ja' ? '点台' : '.0-2.5'}
                </button>
                <button
                  onClick={() => setAnimeSubMenu('1')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    animeSubMenu === '1'
                      ? 'text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  style={animeSubMenu === '1' ? { backgroundColor: '#3797F0', color: 'white', fontWeight: '600' } : {}}
                >
                  ⭐ {language === 'ko' ? '1점대 이하' : language === 'ja' ? '≤1.5' : '≤1.5'}
                </button>
                <button
                  onClick={() => setAnimeSubMenu('watchlist')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    animeSubMenu === 'watchlist'
                      ? 'text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  style={animeSubMenu === 'watchlist' ? { backgroundColor: '#3797F0', color: 'white', fontWeight: '600' } : {}}
                >
                  {language === 'ko' ? '보고싶어요' : language === 'ja' ? 'ウォッチリスト' : 'Watchlist'}
                </button>
                <button
                  onClick={() => setAnimeSubMenu('pass')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    animeSubMenu === 'pass'
                      ? 'text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  style={animeSubMenu === 'pass' ? { backgroundColor: '#3797F0', color: 'white', fontWeight: '600' } : {}}
                >
                  {language === 'ko' ? '관심없어요' : language === 'ja' ? '興味なし' : 'Pass'}
                </button>
              </div>
            )}
            {activeTab === 'character' && (
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => setCharacterSubMenu('all')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    characterSubMenu === 'all'
                      ? ''
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  style={characterSubMenu === 'all' ? { backgroundColor: '#3797F0', color: 'white', fontWeight: '600' } : {}}
                >
                  {language === 'ko' ? '모두' : language === 'ja' ? 'すべて' : 'All'}
                </button>
                <button
                  onClick={() => setCharacterSubMenu('5')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    characterSubMenu === '5'
                      ? ''
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  style={characterSubMenu === '5' ? { backgroundColor: '#3797F0', color: 'white', fontWeight: '600' } : {}}
                >
                  ⭐ 5{language === 'ko' ? '점' : language === 'ja' ? '点' : ''}
                </button>
                <button
                  onClick={() => setCharacterSubMenu('4')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    characterSubMenu === '4'
                      ? ''
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  style={characterSubMenu === '4' ? { backgroundColor: '#3797F0', color: 'white', fontWeight: '600' } : {}}
                >
                  ⭐ 4{language === 'ko' ? '점대' : language === 'ja' ? '点台' : '.0-4.5'}
                </button>
                <button
                  onClick={() => setCharacterSubMenu('3')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    characterSubMenu === '3'
                      ? 'text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  style={characterSubMenu === '3' ? { backgroundColor: '#3797F0', color: 'white', fontWeight: '600' } : {}}
                >
                  ⭐ 3{language === 'ko' ? '점대' : language === 'ja' ? '点台' : '.0-3.5'}
                </button>
                <button
                  onClick={() => setCharacterSubMenu('2')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    characterSubMenu === '2'
                      ? 'text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  style={characterSubMenu === '2' ? { backgroundColor: '#3797F0', color: 'white', fontWeight: '600' } : {}}
                >
                  ⭐ 2{language === 'ko' ? '점대' : language === 'ja' ? '点台' : ''}
                </button>
                <button
                  onClick={() => setCharacterSubMenu('1')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    characterSubMenu === '1'
                      ? 'text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  style={characterSubMenu === '1' ? { backgroundColor: '#3797F0', color: 'white', fontWeight: '600' } : {}}
                >
                  ⭐ {language === 'ko' ? '1점대 이하' : language === 'ja' ? '≤1.5' : '≤1.5'}
                </button>
                <button
                  onClick={() => setCharacterSubMenu('want')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    characterSubMenu === 'want'
                      ? 'text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  style={characterSubMenu === 'want' ? { backgroundColor: '#3797F0', color: 'white', fontWeight: '600' } : {}}
                >
                  {language === 'ko' ? '알고싶어요' : language === 'ja' ? '知りたい' : 'Want to Know'}
                </button>
                <button
                  onClick={() => setCharacterSubMenu('pass')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    characterSubMenu === 'pass'
                      ? 'text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  style={characterSubMenu === 'pass' ? { backgroundColor: '#3797F0', color: 'white', fontWeight: '600' } : {}}
                >
                  {language === 'ko' ? '관심없어요' : language === 'ja' ? '興味なし' : 'Pass'}
                </button>
              </div>
            )}
          </div>
        )}

        {/* Feed tab - show composer and sidebar immediately */}
        {activeTab === 'feed' && (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Left Sidebar - Profile Summary - Show when stats loaded */}
            {stats && (
              <div className="hidden lg:block lg:col-span-1">
                <div className="bg-white rounded-xl shadow-[0_2px_12px_rgba(0,0,0,0.08)] border border-gray-200 p-6 sticky top-4">
                  {/* Profile Picture */}
                  <div className="flex flex-col items-center mb-4">
                    {displayUser?.avatar_url ? (
                      <img
                        src={getAvatarUrl(displayUser.avatar_url)}
                        alt={displayUser?.display_name || displayUser?.username}
                        className="w-24 h-24 rounded-full object-cover border-2 border-gray-200 mb-3"
                      />
                    ) : (
                      <div className="w-24 h-24 rounded-full flex items-center justify-center border-2 border-gray-200 mb-3" style={{ background: 'linear-gradient(135deg, #833AB4 0%, #E1306C 40%, #F77737 70%, #FCAF45 100%)' }}>
                        <span className="text-white text-2xl font-bold">
                          {(displayUser?.display_name || displayUser?.username || '?').charAt(0).toUpperCase()}
                        </span>
                      </div>
                    )}

                    {/* Name */}
                    <h3 className="text-lg font-bold text-gray-900 text-center">
                      {displayUser?.display_name || displayUser?.username}
                    </h3>

                    {/* Badge */}
                    {(() => {
                      const levelInfo = getCurrentLevelInfo(stats.otaku_score || 0, language);
                      return (
                        <span className={`mt-2 text-sm px-3 py-1 rounded-full font-semibold ${levelInfo.bgGradient} border ${levelInfo.borderColor}`}>
                          <span style={{ color: levelInfo.color }} className="font-bold">{levelInfo.icon}</span> <span className="text-gray-700">{levelInfo.level} - {toRoman(levelInfo.rank)}</span>
                        </span>
                      );
                    })()}
                  </div>

                  {/* Stats Summary */}
                  <div className="space-y-3 pt-4 border-t border-gray-200">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">{language === 'ko' ? '오타쿠 점수' : language === 'ja' ? 'オタクスコア' : 'Otaku Score'}</span>
                      <span className="text-sm font-bold text-gray-900">{Math.round(stats.otaku_score)}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">{language === 'ko' ? '평가한 애니' : language === 'ja' ? '評価済みアニメ' : 'Rated Anime'}</span>
                      <span className="text-sm font-bold text-gray-900">{stats.total_rated}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">{language === 'ko' ? '평가한 캐릭터' : language === 'ja' ? '評価済みキャラ' : 'Rated Characters'}</span>
                      <span className="text-sm font-bold text-gray-900">{stats.total_character_ratings || 0}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">{language === 'ko' ? '작성한 리뷰' : language === 'ja' ? '作成レビュー' : 'Reviews Written'}</span>
                      <span className="text-sm font-bold text-gray-900">{stats.total_reviews}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">{language === 'ko' ? '평균 평점' : language === 'ja' ? '平均評価' : 'Avg Rating'}</span>
                      <span className="text-sm font-bold text-gray-900">{stats.average_rating?.toFixed(1) || 'N/A'}</span>
                    </div>
                    {displayUser?.created_at && (
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">{language === 'ko' ? '가입일' : language === 'ja' ? '登録日' : 'Joined'}</span>
                        <span className="text-sm font-bold text-gray-900">
                          {new Date(displayUser.created_at).toLocaleDateString(language === 'ko' ? 'ko-KR' : language === 'ja' ? 'ja-JP' : 'en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Follow Stats */}
                  <div className="flex gap-4 justify-center pt-4 border-t border-gray-200 mt-4">
                    <button
                      onClick={() => openFollowModal('followers')}
                      className="flex flex-col items-center hover:text-[#737373] transition-colors"
                    >
                      <span className="text-lg font-bold text-gray-900">{followCounts.followers_count}</span>
                      <span className="text-xs text-gray-600">{language === 'ko' ? '팔로워' : language === 'ja' ? 'フォロワー' : 'Followers'}</span>
                    </button>
                    <div className="w-px bg-gray-200"></div>
                    <button
                      onClick={() => openFollowModal('following')}
                      className="flex flex-col items-center hover:text-[#737373] transition-colors"
                    >
                      <span className="text-lg font-bold text-gray-900">{followCounts.following_count}</span>
                      <span className="text-xs text-gray-600">{language === 'ko' ? '팔로잉' : language === 'ja' ? 'フォロー中' : 'Following'}</span>
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Right Content - Feed */}
            <div className={stats ? "lg:col-span-3" : "lg:col-span-4"}>
              {/* Post Composer - Show immediately for own profile */}
              {isOwnProfile && displayUser && (
                <div className="bg-white rounded-xl shadow-[0_2px_12px_rgba(0,0,0,0.08)] border border-gray-200 p-4 mb-6">
                  <div className="flex gap-3">
                    {displayUser?.avatar_url ? (
                      <img
                        src={getAvatarUrl(displayUser.avatar_url)}
                        alt={displayUser.display_name || displayUser.username}
                        className="w-10 h-10 rounded-full object-cover border border-gray-200"
                      />
                    ) : (
                      <div className="w-10 h-10 rounded-full flex items-center justify-center border border-gray-200" style={{ background: getAvatarGradient(displayUser?.username) }}>
                        <span className="text-white text-sm font-bold">
                          {(displayUser?.display_name || displayUser?.username || '?').charAt(0).toUpperCase()}
                        </span>
                      </div>
                    )}
                    <div className="flex-1">
                      <textarea
                        value={newPostContent}
                        onChange={(e) => setNewPostContent(e.target.value)}
                        placeholder={language === 'ko' ? '무슨 생각을 하고 계신가요?' : language === 'ja' ? '今何を考えていますか？' : "What's on your mind?"}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none"
                        rows="3"
                      />
                      <div className="flex justify-end mt-2">
                        <button
                          onClick={handleCreatePost}
                          disabled={!newPostContent.trim()}
                          className="px-4 py-2 text-white rounded-lg transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
                          style={newPostContent.trim() ? { backgroundColor: '#3797F0', color: 'white', fontWeight: '600' } : {}}
                          onMouseEnter={(e) => !e.target.disabled && (e.target.style.backgroundColor = '#1877F2')}
                          onMouseLeave={(e) => !e.target.disabled && (e.target.style.backgroundColor = '#3797F0')}
                        >
                          {language === 'ko' ? '게시' : language === 'ja' ? '投稿' : 'Post'}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Feed Activities */}
              {loading ? (
                <div className="flex justify-center items-center h-64">
                  <div className="text-xl text-gray-600">{language === 'ko' ? '피드 로딩 중...' : language === 'ja' ? 'フィード読込中...' : 'Loading feed...'}</div>
                </div>
              ) : userActivities.length > 0 ? (
                <div className="space-y-4">
                  {userActivities.map((activity, index) => {
                    // Use displayUser for consistency
                    const displayAvatar = displayUser?.avatar_url;
                    const displayName = displayUser?.display_name || displayUser?.username;
                    const currentOtakuScore = stats?.otaku_score || 0;
                    const isLastActivity = userActivities.length === index + 1;

                    return (
                      <ActivityCard
                        key={`${activity.activity_type}-${activity.user_id}-${activity.item_id}-${index}`}
                        ref={isLastActivity ? lastActivityElementRef : null}
                        activity={activity}
                        context="feed"
                        onUpdate={() => {
                          // Reload feed after deletion/update - force refresh to bypass cache
                          loadData(true);
                        }}
                        onEditContent={activity.activity_type === 'user_post' ? null : handleEditContent}
                      />
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-12 text-gray-600">
                  {language === 'ko' ? '아직 활동이 없습니다.' : language === 'ja' ? 'まだ活動がありません' : 'No activity yet.'}
                </div>
              )}
            </div>
          </div>
        )}

        {loading && activeTab !== 'feed' ? (
          <div className="flex justify-center items-center h-64">
            <div className="text-xl text-gray-600">{language === 'ko' ? '로딩 중...' : language === 'ja' ? '読込中...' : 'Loading...'}</div>
          </div>
        ) : activeTab !== 'feed' && (
          <div className={tabLoading ? 'opacity-50 pointer-events-none' : ''}>
            {activeTab === 'anipass' && (
              <div className="space-y-6">
                {/* 상단 그리드: 오타쿠 미터, 통계, 장르 선호도 */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:items-stretch">
                  {/* 오타쿠 미터 */}
                  <div className="w-full">
                    {stats && <OtakuMeter score={stats.otaku_score || 0} language={language} />}
                  </div>

                  {/* 통계 */}
                  <div className="w-full">
                    {stats && (
                      <div className="bg-white rounded-xl shadow-[0_2px_12px_rgba(0,0,0,0.08)] border border-gray-200 p-6 h-full">
                        <div className="space-y-4">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#8EC5FC] to-[#638CCC] flex items-center justify-center text-white text-xl flex-shrink-0">
                              📺
                            </div>
                            <div className="flex-1">
                              <div className="text-xs font-semibold text-[#638CCC] uppercase tracking-wide mb-0.5">{language === 'ko' ? '평가한 애니' : language === 'ja' ? '評価済みアニメ' : 'Rated Anime'}</div>
                              <div className="text-2xl font-bold text-[#638CCC]">
                                {stats.total_rated || 0}
                              </div>
                            </div>
                          </div>

                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#90B2E4] to-[#8EC5FC] flex items-center justify-center text-white text-xl flex-shrink-0">
                              ⭐
                            </div>
                            <div className="flex-1">
                              <div className="text-xs font-semibold text-[#638CCC] uppercase tracking-wide mb-0.5">{language === 'ko' ? '보고싶어요' : language === 'ja' ? 'ウォッチリスト' : 'Watchlist'}</div>
                              <div className="text-2xl font-bold text-[#638CCC]">
                                {stats.total_want_to_watch || 0}
                              </div>
                            </div>
                          </div>

                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-amber-400 to-yellow-400 flex items-center justify-center text-white text-xl flex-shrink-0">
                              ✨
                            </div>
                            <div className="flex-1">
                              <div className="text-xs font-semibold text-amber-600 uppercase tracking-wide mb-0.5">{language === 'ko' ? '평균 평점' : language === 'ja' ? '平均評価' : 'Avg Rating'}</div>
                              <div className="text-2xl font-bold text-amber-600">
                                {stats.average_rating ? `★ ${stats.average_rating.toFixed(1)}` : '-'}
                              </div>
                            </div>
                          </div>

                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#638CCC] to-purple-400 flex items-center justify-center text-white text-xl flex-shrink-0">
                              ⏱️
                            </div>
                            <div className="flex-1">
                              <div className="text-xs font-semibold text-[#638CCC] uppercase tracking-wide mb-0.5">{language === 'ko' ? '시청 시간' : language === 'ja' ? '視聴時間' : 'Watch Time'}</div>
                              <div className="text-2xl font-bold text-[#638CCC]">
                                {formatWatchTime(watchTime?.total_minutes)}
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* 장르 선호도 */}
                  <div className="w-full">
                    <GenrePreferences preferences={genrePreferences} />
                  </div>
                </div>

                {/* Phase 1 통계 그리드: 포맷, 에피소드 길이, 평가 성향 */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:items-stretch">
                  <div className="w-full">
                    <FormatDistribution distribution={formatDistribution} />
                  </div>
                  <div className="w-full">
                    <EpisodeLengthChart distribution={episodeLengthDistribution} />
                  </div>
                  <div className="w-full">
                    <RatingStatsCard stats={ratingStats} />
                  </div>
                </div>

                {/* 차트 그리드: 평점 분포, 연도별 분포 */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:items-stretch">
                  <div className="w-full">
                    <RatingDistributionChart distribution={ratingDistribution} />
                  </div>
                  <div className="w-full">
                    <YearDistributionChart distribution={yearDistribution} />
                  </div>
                </div>

                {/* Phase 1 & 2 추가 통계: 스튜디오, 장르 조합, 시즌 */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:items-stretch">
                  <div className="w-full">
                    <StudioStats studios={studioStats} />
                  </div>
                  <div className="w-full">
                    <GenreCombinationChart combinations={genreCombinations} />
                  </div>
                  <div className="w-full">
                    <SeasonStats seasons={seasonStats} />
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'anime' && (
              <div>
                {/* Anime Grid */}
                {!loadedTabs.anime ? (
                  <div className="flex justify-center items-center py-20">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
                  </div>
                ) : displayedAnime.length > 0 ? (
                  ['all', '4', '3', '2', '1'].includes(animeSubMenu) ? (
                    // 모두 또는 범위 필터 선택 시 평점별로 그룹화 + Virtual Scrolling
                    <div className="space-y-8">
                      {animeSections.map((section, sectionIndex) => {
                        const categoryLabels = {
                          '5': language === 'ko' ? '⭐ 5점' : language === 'ja' ? '⭐ 5点' : '⭐ 5.0',
                          '4.5': language === 'ko' ? '⭐ 4.5점' : language === 'ja' ? '⭐ 4.5点' : '⭐ 4.5',
                          '4': language === 'ko' ? '⭐ 4점' : language === 'ja' ? '⭐ 4点' : '⭐ 4.0',
                          '3.5': language === 'ko' ? '⭐ 3.5점' : language === 'ja' ? '⭐ 3.5点' : '⭐ 3.5',
                          '3': language === 'ko' ? '⭐ 3점' : language === 'ja' ? '⭐ 3点' : '⭐ 3.0',
                          '2.5': language === 'ko' ? '⭐ 2.5점' : language === 'ja' ? '⭐ 2.5点' : '⭐ 2.5',
                          '2': language === 'ko' ? '⭐ 2점' : language === 'ja' ? '⭐ 2点' : '⭐ 2.0',
                          '1.5': language === 'ko' ? '⭐ 1.5점' : language === 'ja' ? '⭐ 1.5点' : '⭐ 1.5',
                          '1': language === 'ko' ? '⭐ 1점' : language === 'ja' ? '⭐ 1点' : '⭐ 1.0',
                          '0.5': language === 'ko' ? '⭐ 0.5점' : language === 'ja' ? '⭐ 0.5点' : '⭐ 0.5',
                          'watchlist': language === 'ko' ? '📋 보고싶어요' : language === 'ja' ? '📋 ウォッチリスト' : '📋 Watchlist',
                          'pass': language === 'ko' ? '🚫 관심없어요' : language === 'ja' ? '🚫 興味なし' : '🚫 Pass'
                        };

                        const isVisible = isAnimeSectionVisible(section.id);
                        const itemsPerRow = 6; // lg:grid-cols-6
                        const rows = Math.ceil(section.items.length / itemsPerRow);
                        const estimatedHeight = rows * 250; // Approximate card height

                        return (
                          <div
                            key={section.id}
                            ref={getAnimeSectionRef(section.id)}
                            data-section-id={section.id}
                          >
                            {sectionIndex > 0 && <div className="border-t-2 border-gray-300 my-6"></div>}
                            <h3 className="text-lg font-bold mb-4 text-gray-800">
                              {categoryLabels[section.category]} ({section.items.length})
                            </h3>
                            {isVisible ? (
                              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-6">
                                {section.items.map((anime) => (
                                  <MyAnimeCard key={anime.anime_id} anime={anime} />
                                ))}
                              </div>
                            ) : (
                              <div
                                className="w-full bg-gray-100 rounded-lg animate-pulse"
                                style={{ height: `${estimatedHeight}px` }}
                              />
                            )}
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    // 5점, 보고싶어요, 관심없어요는 섹션 헤더와 함께 표시
                    <div>
                      <h3 className="text-lg font-bold mb-4 text-gray-800">
                        {animeSubMenu === '5' && (language === 'ko' ? `⭐ 5점 (${displayedAnime.length})` : language === 'ja' ? `⭐ 5点 (${displayedAnime.length})` : `⭐ 5.0 (${displayedAnime.length})`)}
                        {animeSubMenu === 'watchlist' && (language === 'ko' ? `📋 보고싶어요 (${displayedAnime.length})` : language === 'ja' ? `📋 ウォッチリスト (${displayedAnime.length})` : `📋 Watchlist (${displayedAnime.length})`)}
                        {animeSubMenu === 'pass' && (language === 'ko' ? `🚫 관심없어요 (${displayedAnime.length})` : language === 'ja' ? `🚫 興味なし (${displayedAnime.length})` : `🚫 Pass (${displayedAnime.length})`)}
                      </h3>
                      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-6">
                        {displayedAnime.map((anime) => (
                          <MyAnimeCard key={anime.anime_id} anime={anime} />
                        ))}
                      </div>
                    </div>
                  )
                ) : (
                  <div className="text-center py-12 text-gray-600">
                    {language === 'ko' ? '아직 애니가 없습니다.' : language === 'ja' ? 'まだアニメがありません' : 'No anime yet.'}
                  </div>
                )}
              </div>
            )}

            {activeTab === 'character' && (
              <div>
                {/* Character Grid */}
                {!loadedTabs.character ? (
                  <div className="flex justify-center items-center py-20">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
                  </div>
                ) : displayedCharacters.length > 0 ? (
                  ['all', '4', '3', '2', '1'].includes(characterSubMenu) ? (
                    // 모두 선택 시 평점별로 그룹화 + Virtual Scrolling
                    <div className="space-y-8">
                      {characterSections.map((section, sectionIndex) => {
                        const categoryLabels = {
                          '5': language === 'ko' ? '⭐ 5점' : language === 'ja' ? '⭐ 5点' : '⭐ 5.0',
                          '4.5': language === 'ko' ? '⭐ 4.5점' : language === 'ja' ? '⭐ 4.5点' : '⭐ 4.5',
                          '4': language === 'ko' ? '⭐ 4점' : language === 'ja' ? '⭐ 4点' : '⭐ 4.0',
                          '3.5': language === 'ko' ? '⭐ 3.5점' : language === 'ja' ? '⭐ 3.5点' : '⭐ 3.5',
                          '3': language === 'ko' ? '⭐ 3점' : language === 'ja' ? '⭐ 3点' : '⭐ 3.0',
                          '2.5': language === 'ko' ? '⭐ 2.5점' : language === 'ja' ? '⭐ 2.5点' : '⭐ 2.5',
                          '2': language === 'ko' ? '⭐ 2점' : language === 'ja' ? '⭐ 2点' : '⭐ 2.0',
                          '1.5': language === 'ko' ? '⭐ 1.5점' : language === 'ja' ? '⭐ 1.5点' : '⭐ 1.5',
                          '1': language === 'ko' ? '⭐ 1점' : language === 'ja' ? '⭐ 1点' : '⭐ 1.0',
                          '0.5': language === 'ko' ? '⭐ 0.5점' : language === 'ja' ? '⭐ 0.5点' : '⭐ 0.5',
                          'want': language === 'ko' ? '💭 알고싶어요' : language === 'ja' ? '💭 知りたい' : '💭 Want to Know',
                          'pass': language === 'ko' ? '🚫 관심없어요' : language === 'ja' ? '🚫 興味なし' : '🚫 Pass'
                        };

                        const isVisible = isCharacterSectionVisible(section.id);
                        const itemsPerRow = 6; // lg:grid-cols-6
                        const rows = Math.ceil(section.items.length / itemsPerRow);
                        const estimatedHeight = rows * 300; // Character cards are taller

                        return (
                          <div
                            key={section.id}
                            ref={getCharacterSectionRef(section.id)}
                            data-section-id={section.id}
                          >
                            {sectionIndex > 0 && <div className="border-t-2 border-gray-300 my-6"></div>}
                            <h3 className="text-lg font-bold mb-4 text-gray-800">
                              {categoryLabels[section.category]} ({section.items.length})
                            </h3>
                            {isVisible ? (
                              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-6">
                                {section.items.map((character) => (
                                  <MyCharacterCard
                                    key={character.character_id}
                                    character={character}
                                    language={language}
                                  />
                                ))}
                              </div>
                            ) : (
                              <div
                                className="w-full bg-gray-100 rounded-lg animate-pulse"
                                style={{ height: `${estimatedHeight}px` }}
                              />
                            )}
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    // 5점, 알고싶어요, 관심없어요는 섹션 헤더와 함께 표시
                    <div>
                      <h3 className="text-lg font-bold mb-4 text-gray-800">
                        {characterSubMenu === '5' && (language === 'ko' ? `⭐ 5점 (${displayedCharacters.length})` : language === 'ja' ? `⭐ 5点 (${displayedCharacters.length})` : `⭐ 5.0 (${displayedCharacters.length})`)}
                        {characterSubMenu === 'want' && (language === 'ko' ? `💭 알고싶어요 (${displayedCharacters.length})` : language === 'ja' ? `💭 知りたい (${displayedCharacters.length})` : `💭 Want to Know (${displayedCharacters.length})`)}
                        {characterSubMenu === 'pass' && (language === 'ko' ? `🚫 관심없어요 (${displayedCharacters.length})` : language === 'ja' ? `🚫 興味なし (${displayedCharacters.length})` : `🚫 Pass (${displayedCharacters.length})`)}
                      </h3>
                      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-6">
                        {displayedCharacters.map((character) => (
                          <MyCharacterCard
                            key={character.character_id}
                            character={character}
                            language={language}
                          />
                        ))}
                      </div>
                    </div>
                  )
                ) : (
                  <div className="text-center py-12 text-gray-600">
                    {language === 'ko' ? '아직 캐릭터가 없습니다.' : language === 'ja' ? 'まだキャラクターがいません' : 'No characters yet.'}
                  </div>
                )}
              </div>
            )}

          </div>
        )}

        {/* Follow Modal */}
        {showFollowModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setShowFollowModal(false)}>
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 max-h-[80vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold">
                  {followModalType === 'followers' ? (language === 'ko' ? '팔로워' : language === 'ja' ? 'フォロワー' : 'Followers') : (language === 'ko' ? '팔로잉' : language === 'ja' ? 'フォロー中' : 'Following')}
                </h2>
                <button
                  onClick={() => setShowFollowModal(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  ✕
                </button>
              </div>

              {followList.length > 0 ? (
                <div className="space-y-3">
                  {followList.map((follower) => (
                    <Link
                      key={follower.id}
                      to={`/user/${follower.id}`}
                      className="flex items-center gap-3 p-2 hover:bg-gray-50 rounded-lg transition-colors"
                      onClick={() => setShowFollowModal(false)}
                    >
                      {follower.avatar_url ? (
                        <img
                          src={getAvatarUrl(follower.avatar_url)}
                          alt={follower.display_name || follower.username}
                          className="w-12 h-12 rounded-full object-cover border border-gray-200"
                        />
                      ) : (
                        <div className="w-12 h-12 rounded-full flex items-center justify-center border border-gray-200" style={{ background: getAvatarGradient(follower.username) }}>
                          <span className="text-white text-lg font-bold">
                            {(follower.display_name || follower.username || '?')[0].toUpperCase()}
                          </span>
                        </div>
                      )}
                      <div>
                        <div className="font-medium text-gray-900">
                          {follower.display_name || follower.username}
                        </div>
                        <div className="text-sm text-gray-500">@{follower.username}</div>
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-600">
                  {followModalType === 'followers'
                    ? (language === 'ko' ? '팔로워가 없습니다.' : language === 'ja' ? 'フォロワーがいません' : 'No followers yet.')
                    : (language === 'ko' ? '팔로잉하는 사용자가 없습니다.' : language === 'ja' ? 'フォロー中のユーザーがいません' : 'Not following anyone yet.')}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Delete Modal */}
        {showDeleteModal && activityToDelete && createPortal(
          <div
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center"
            style={{ zIndex: 9999, position: 'fixed', top: 0, left: 0, right: 0, bottom: 0 }}
            onClick={() => setShowDeleteModal(false)}
          >
            <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4" onClick={(e) => e.stopPropagation()}>
              <h3 className="text-xl font-bold mb-2 text-gray-900">
                {language === 'ko' ? '삭제 옵션' : language === 'ja' ? '削除オプション' : 'Delete Options'}
              </h3>

              {/* Show what's being deleted */}
              <div className="mb-4 p-3 bg-gray-50 rounded-lg border border-gray-200 flex gap-3">
                {activityToDelete.item_image && (
                  <img
                    src={getImageUrl(activityToDelete.item_image)}
                    alt={activityToDelete.item_title_korean || activityToDelete.item_title}
                    className="w-16 h-24 object-cover rounded flex-shrink-0"
                    onError={(e) => {
                      e.target.src = '/placeholder-anime.svg';
                    }}
                  />
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-gray-900 mb-1">
                    {activityToDelete.activity_type === 'character_rating' ? (
                      <>
                        {activityToDelete.item_title}{' '}
                        <span className="text-gray-600">({activityToDelete.item_title_korean})</span>
                      </>
                    ) : (
                      activityToDelete.item_title_korean || activityToDelete.item_title
                    )}
                  </p>
                  {activityToDelete.activity_type === 'character_rating' && activityToDelete.anime_title && (
                    <p className="text-xs text-gray-600 mb-1">
                      from: {activityToDelete.anime_title_korean || activityToDelete.anime_title}
                    </p>
                  )}
                  <p className="text-xs text-gray-500">
                    {activityToDelete.activity_type === 'character_rating'
                      ? (language === 'ko' ? '캐릭터' : language === 'ja' ? 'キャラクター' : 'Character')
                      : (language === 'ko' ? '애니메이션' : language === 'ja' ? 'アニメーション' : 'Anime')}
                  </p>
                </div>
              </div>

              {activityToDelete.review_content && activityToDelete.review_content.trim() ? (
                <>
                  <p className="text-sm text-gray-700 mb-6">
                    {language === 'ko'
                      ? '이 평가에는 리뷰가 포함되어 있습니다. 어떻게 삭제하시겠습니까?'
                      : 'This rating includes a review. How would you like to delete it?'}
                  </p>
                  <div className="flex flex-col gap-3">
                    <button
                      onClick={() => handleDeleteActivity('review_only')}
                      className="w-full px-4 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors"
                    >
                      {language === 'ko' ? '리뷰만 삭제 (별점 유지)' : language === 'ja' ? 'レビューのみ削除 (評価は保持)' : 'Delete review only (Keep rating)'}
                    </button>
                    <button
                      onClick={() => handleDeleteActivity('all')}
                      className="w-full px-4 py-3 bg-red-500 hover:bg-red-600 text-white rounded-lg font-medium transition-colors"
                    >
                      {language === 'ko' ? '별점까지 모두 삭제' : language === 'ja' ? '評価とレビューを削除' : 'Delete rating and review'}
                    </button>
                    <button
                      onClick={() => setShowDeleteModal(false)}
                      className="w-full px-4 py-3 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg font-medium transition-colors"
                    >
                      {language === 'ko' ? '취소' : language === 'ja' ? 'キャンセル' : 'Cancel'}
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <p className="text-sm text-gray-700 mb-6">
                    {language === 'ko'
                      ? '이 평가를 삭제하시겠습니까?'
                      : 'Are you sure you want to delete this rating?'}
                  </p>
                  <div className="flex gap-3">
                    <button
                      onClick={() => handleDeleteActivity('all')}
                      className="flex-1 px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg font-medium transition-colors"
                    >
                      {language === 'ko' ? '삭제' : language === 'ja' ? '削除' : 'Delete'}
                    </button>
                    <button
                      onClick={() => setShowDeleteModal(false)}
                      className="flex-1 px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg font-medium transition-colors"
                    >
                      {language === 'ko' ? '취소' : language === 'ja' ? 'キャンセル' : 'Cancel'}
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>,
          document.body
        )}

        {/* Edit Review Modal */}
        <EditReviewModal
          isOpen={editModalOpen}
          onClose={() => {
            setEditModalOpen(false);
            setEditingActivity(null);
            setEditMode('edit');
          }}
          onSave={handleSaveEdit}
          activity={editingActivity}
          mode={editMode}
        />
      </div>
    </div>
  );
}
