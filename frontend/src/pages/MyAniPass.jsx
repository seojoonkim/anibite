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
import { activityService } from '../services/activityService';
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
import DefaultAvatar, { getAvatarGradient } from '../components/common/DefaultAvatar';

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

  const [animeSubMenu, setAnimeSubMenu] = useState('all'); // ?†Îãà ?úÎ∏åÎ©îÎâ¥: all, 5, 4, 3, 2, 1, 0, watchlist, pass
  const [characterSubMenu, setCharacterSubMenu] = useState('all'); // Ï∫êÎ¶≠???úÎ∏åÎ©îÎâ¥: all, 5, 4, 3, 2, 1, 0, want, pass

  // Edit modal state
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editingActivity, setEditingActivity] = useState(null);
  const [editMode, setEditMode] = useState('edit'); // 'edit' | 'add_review' | 'edit_rating'

  const toRoman = (num) => {
    const romanNumerals = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X'];
    return romanNumerals[num - 1] || num;
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
  const [allAnime, setAllAnime] = useState([]); // Î™®Îì† ?†Îãà (?âÍ?, Î≥¥Í≥†?∂Ïñ¥?? Í¥Ä?¨ÏóÜ?¥Ïöî ?¨Ìï®)
  const [displayedAnime, setDisplayedAnime] = useState([]); // ?ÑÏû¨ ?úÏãú?òÎäî ?†Îãà
  const [allCharacters, setAllCharacters] = useState([]); // Î™®Îì† Ï∫êÎ¶≠??(?âÍ?, ?åÍ≥†?∂Ïñ¥?? Í¥Ä?¨ÏóÜ?¥Ïöî ?¨Ìï®)
  const [displayedCharacters, setDisplayedCharacters] = useState([]); // ?ÑÏû¨ ?úÏãú?òÎäî Ï∫êÎ¶≠??
  const [allRatedCharacters, setAllRatedCharacters] = useState([]); // ?âÍ???Ï∫êÎ¶≠?∞Îßå
  const [wantCharacters, setWantCharacters] = useState([]); // ?åÍ≥†?∂Ïñ¥??Ï∫êÎ¶≠??
  const [passCharacters, setPassCharacters] = useState([]); // Í¥Ä?¨ÏóÜ?¥Ïöî Ï∫êÎ¶≠??
  const [ratedAnime, setRatedAnime] = useState([]);
  const [allRatedAnime, setAllRatedAnime] = useState([]); // ?ÑÏ≤¥ ?âÍ? ?†Îãà Ï∫êÏãú
  const [ratedFilter, setRatedFilter] = useState('all'); // Î≥ÑÏ†ê ?ÑÌÑ∞
  const [watchlistAnime, setWatchlistAnime] = useState([]);
  const [passAnime, setPassAnime] = useState([]);
  const [watchTime, setWatchTime] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tabLoading, setTabLoading] = useState(false);
  // Phase 1 & 2 ?µÍ≥Ñ
  const [formatDistribution, setFormatDistribution] = useState([]);
  const [episodeLengthDistribution, setEpisodeLengthDistribution] = useState([]);
  const [ratingStats, setRatingStats] = useState(null);
  const [studioStats, setStudioStats] = useState([]);
  const [seasonStats, setSeasonStats] = useState([]);
  const [genreCombinations, setGenreCombinations] = useState([]);
  // ??≥Ñ Î°úÎìú ?ÑÎ£å ?¨Î? Ï∂îÏ†Å
  const [statsLoaded, setStatsLoaded] = useState(false);
  const [loadedTabs, setLoadedTabs] = useState({
    anipass: false,
    anime: false,
    character: false,
    feed: false
  });
  // ?îÎ°ú??Í¥Ä???ÅÌÉú
  const [followCounts, setFollowCounts] = useState({ followers_count: 0, following_count: 0 });
  const [isFollowing, setIsFollowing] = useState(false);
  const [showFollowModal, setShowFollowModal] = useState(false);
  const [followModalType, setFollowModalType] = useState('followers'); // 'followers' or 'following'
  const [followList, setFollowList] = useState([]);
  // ?ºÎìú Í¥Ä???ÅÌÉú
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
  // ??†ú Î™®Îã¨ ?ÅÌÉú
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

      // ?îÎ°ú??Ïπ¥Ïö¥??Î°úÎìú
      const counts = await followService.getFollowCounts(targetUserId);
      setFollowCounts(counts);

      // ?§Î•∏ ?¨Ïö©?êÏùò ?ÑÎ°ú?ÑÏù¥Î©??îÎ°ú???¨Î? ?ïÏù∏
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

  // ?†Îãà ?úÎ∏åÎ©îÎâ¥ ?ÑÌÑ∞Îß?
  const filterAnimeBySubMenu = useCallback((animeData, submenu) => {
    let filtered = [];

    if (submenu === 'all') {
      // Î™®Îëê ?†ÌÉù ??Î™®Îì† ??™© ?¨Ìï® (?âÍ???Í≤?+ Î≥¥Í≥†?∂Ïñ¥??+ Í¥Ä?¨ÏóÜ?¥Ïöî)
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
      // 1?êÎ? ?¥Ìïò: 0.5~1.9
      filtered = animeData.filter(a => a.category === 'rated' && a.rating >= 0.5 && a.rating < 2.0);
    } else if (submenu === 'watchlist') {
      filtered = animeData.filter(a => a.category === 'watchlist');
    } else if (submenu === 'pass') {
      filtered = animeData.filter(a => a.category === 'pass');
    }

    setDisplayedAnime(filtered); // ?ÑÏ≤¥ ?úÏãú (?¥Î?ÏßÄ??lazy loading)
  }, []);

  // Ï∫êÎ¶≠???úÎ∏åÎ©îÎâ¥ ?ÑÌÑ∞Îß?
  const filterCharactersBySubMenu = useCallback((charactersData, submenu) => {
    let filtered = [];

    if (submenu === 'all') {
      // Î™®Îëê ?†ÌÉù ??Î™®Îì† ??™© ?¨Ìï®
      filtered = charactersData;
    } else if (submenu === '5') {
      // RATED ?ÅÌÉú?¥Í≥† rating??5.0??Í≤ÉÎßå
      filtered = charactersData.filter(c => c.status === 'RATED' && c.rating === 5.0);
    } else if (submenu === '4') {
      filtered = charactersData.filter(c => c.status === 'RATED' && c.rating >= 4.0 && c.rating < 5.0);
    } else if (submenu === '3') {
      filtered = charactersData.filter(c => c.status === 'RATED' && c.rating >= 3.0 && c.rating < 4.0);
    } else if (submenu === '2') {
      filtered = charactersData.filter(c => c.status === 'RATED' && c.rating >= 2.0 && c.rating < 3.0);
    } else if (submenu === '1') {
      // 1?êÎ? ?¥Ìïò: 0.5~1.9
      filtered = charactersData.filter(c => c.status === 'RATED' && c.rating >= 0.5 && c.rating < 2.0);
    } else if (submenu === 'want') {
      filtered = charactersData.filter(c => c.status === 'WANT_TO_KNOW');
    } else if (submenu === 'pass') {
      filtered = charactersData.filter(c => c.status === 'PASS');
    }

    setDisplayedCharacters(filtered); // ?ÑÏ≤¥ ?úÏãú (?¥Î?ÏßÄ??lazy loading)
  }, []);


  // ?úÎ∏åÎ©îÎâ¥ Î≥ÄÍ≤????ÑÌÑ∞Îß?
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
        // Î≥ÑÏ†êÎß??òÏ†ï
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
        // Î¶¨Î∑∞ Ï∂îÍ?
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
        // Î¶¨Î∑∞ ?òÏ†ï
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
          // Î¶¨Î∑∞ ?¥Ïö© ?ÜÏù¥ Î≥ÑÏ†êÎß?Î≥ÄÍ≤ΩÎêú Í≤ΩÏö∞
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
      // ?¥Î? Î°úÎìú????ù¥Î©??§ÌÇµ (anime, character, anipass Ï∫êÏã±)
      // forceRefreshÍ∞Ä trueÎ©?Ï∫êÏãú Î¨¥Ïãú
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

      // ???ÑÎ°ú?ÑÏùº ?åÎäî stats?Ä follow dataÎ•?Î≥ëÎ†¨Î°?Î°úÎìú
      if (!statsLoaded && isOwnProfile && user?.id) {
        const [statsData, followCounts] = await Promise.all([
          userService.getStats(),
          followService.getFollowCounts(user.id).catch(() => ({ followers_count: 0, following_count: 0 }))
        ]);
        setStats(statsData);
        setStatsLoaded(true);
        setFollowCounts(followCounts);
      }

      // ?§Î•∏ ?¨Ïö©???ÑÎ°ú???ïÎ≥¥?Ä follow dataÎ•?Î≥ëÎ†¨Î°?Î°úÎìú
      if (!isOwnProfile && !profileUser) {
        const targetUserId = parseInt(userId);
        const [profileData, genrePrefs, followCounts, followStatus] = await Promise.all([
          userService.getUserProfile(targetUserId).catch(() => null),
          userService.getUserGenrePreferences(targetUserId).catch(() => []),
          followService.getFollowCounts(targetUserId).catch(() => ({ followers_count: 0, following_count: 0 })),
          followService.isFollowing(targetUserId).catch(() => ({ is_following: false }))
        ]);
        if (profileData) {
          setProfileUser(profileData.user); // user Í∞ùÏ≤¥ ?§Ï†ï
          setStats(profileData.stats); // stats Í∞ùÏ≤¥ ?§Ï†ï
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

        // Î°úÎî© ?ÑÎ£å (?ìÍ??Ä ?¨Ïö©?êÍ? ?¥Î¶≠???åÎßå Î°úÎìú)
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

  // ?îÎ°ú??Ïπ¥Ïö¥?∏Îäî ??ÉÅ Î°úÎìú (?òÏù¥ÏßÄ ÏßÑÏûÖ ?? userId Î≥ÄÍ≤???
  useEffect(() => {
    loadFollowData();
  }, [loadFollowData]);

  const formatWatchTime = (minutes) => {
    if (!minutes) return '0?úÍ∞Ñ';
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours === 0) return `${mins}Î∂?;
    if (mins === 0) return `${hours}?úÍ∞Ñ`;
    return `${hours}?úÍ∞Ñ ${mins}Î∂?;
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

    // External URLs (AniList, etc) - use placeholder
    if (imageUrl.startsWith('http')) return '/placeholder-anime.svg';

    const processedUrl = imageUrl.includes('/covers/')
      ? imageUrl.replace('/covers/', '/covers_large/')
      : imageUrl;
    return `${IMAGE_BASE_URL}${processedUrl}`;
  };

  const getActivityText = (activity) => {
    const displayName = activity.display_name || activity.username;

    switch (activity.activity_type) {
      case 'anime_rating':
        return language === 'ko' ? `${displayName}?òÏù¥ ?âÍ??àÏñ¥?? : language === 'ja' ? `${displayName}?ï„Çì?åË©ï‰æ°„Åó?æ„Åó?? : `${displayName} rated an anime`;
      case 'character_rating':
        return language === 'ko' ? `${displayName}?òÏù¥ Ï∫êÎ¶≠?∞Î? ?âÍ??àÏñ¥?? : language === 'ja' ? `${displayName}?ï„Çì?å„Ç≠?£„É©??Çø?º„ÇíË©ï‰æ°?ó„Åæ?ó„Åü` : `${displayName} rated a character`;
      case 'review':
        return language === 'ko' ? `${displayName}?òÏù¥ Î¶¨Î∑∞Î•??®Í≤º?¥Ïöî` : language === 'ja' ? `${displayName}?ï„Çì?å„É¨?ì„É•?º„ÇíÊÆã„Åó?æ„Åó?? : `${displayName} left a review`;
      default:
        return language === 'ko' ? `${displayName}?òÏùò ?úÎèô` : language === 'ja' ? `${displayName}?ï„Çì??Ç¢??ÉÜ?£„Éì?Ü„Ç£` : `${displayName}'s activity`;
    }
  };

  const getActivityIcon = (activityType) => {
    switch (activityType) {
      case 'anime_rating':
        return '‚≠?;
      case 'character_rating':
        return '?ë§';
      case 'review':
        return '?çÔ∏è';
      default:
        return '?ìù';
    }
  };

  const getTimeAgo = (timestamp) => {
    const now = new Date();
    // SQLite timestampÎ•?UTCÎ°??åÏã±
    const activityTime = new Date(timestamp.endsWith('Z') ? timestamp : timestamp + 'Z');
    const diff = now - activityTime;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (language === 'ko') {
      if (minutes < 60) return `${Math.max(1, minutes)}Î∂???;
      if (hours < 24) return `${hours}?úÍ∞Ñ ??;
      if (days < 7) return `${days}????;
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

  // ?úÎèô???ìÍ? ?òÎ? ?ÖÎç∞?¥Ìä∏?òÎäî ?¨Ìçº ?®Ïàò
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
      alert(language === 'ko' ? `?ìÍ? ?ëÏÑ±???§Ìå®?àÏäµ?àÎã§: ${err.message}` : language === 'ja' ? `?≥„É°?≥„Éà?ïÁ®ø?´Â§±?ó„Åó?æ„Åó?? ${err.message}` : `Failed to post comment: ${err.message}`);
    }
  };

  const handleToggleActivityLike = async (activity) => {
    try {
      const result = await activityService.toggleLike(activity.id);
      const key = getActivityKey(activity);
      setActivityLikes(prev => ({
        ...prev,
        [key]: { liked: result.liked, count: result.likes_count }
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
      alert(language === 'ko' ? '?µÍ? ?ëÏÑ±???§Ìå®?àÏäµ?àÎã§.' : language === 'ja' ? 'Ëøî‰ø°?ïÁ®ø?´Â§±?ó„Åó?æ„Åó?? : 'Failed to post reply.');
    }
  };

  const handleDeleteComment = async (activity, commentId) => {
    if (!confirm(language === 'ko' ? '?ìÍ?????†ú?òÏãúÍ≤†Ïäµ?àÍπå?' : language === 'ja' ? '?ì„ÅÆ?≥„É°?≥„Éà?íÂâä?§„Åó?æ„Åô?ãÔºü' : 'Delete this comment?')) return;

    try {
      await ActivityUtils.deleteComment(activity, commentId);
      await loadComments(activity);
      updateActivityCommentsCount(activity, -1);
    } catch (err) {
      console.error('Failed to delete comment:', err);
      alert(language === 'ko' ? '?ìÍ? ??†ú???§Ìå®?àÏäµ?àÎã§.' : language === 'ja' ? '?≥„É°?≥„Éà?äÈô§?´Â§±?ó„Åó?æ„Åó?? : 'Failed to delete comment.');
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
        // Î¶¨Î∑∞Îß???†ú (Î≥ÑÏ†ê?Ä ?†Ï?)
        if (isAnime) {
          await reviewService.deleteReview(activity.id);
        } else {
          await characterReviewService.deleteReview(activity.id);
        }
      } else {
        // Î≥ÑÏ†êÍπåÏ? Î™®Îëê ??†ú
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
      alert(language === 'ko' ? '??†ú???§Ìå®?àÏäµ?àÎã§.' : language === 'ja' ? '?äÈô§?´Â§±?ó„Åó?æ„Åó?? : 'Failed to delete.');
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
      // Reload feed data (ÏµúÏã† 10Í∞úÎßå)
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
      alert(language === 'ko' ? 'Í≤åÏãúÎ¨??ëÏÑ±???§Ìå®?àÏäµ?àÎã§.' : language === 'ja' ? '?ïÁ®ø‰ΩúÊàê?´Â§±?ó„Åó?æ„Åó?? : 'Failed to create post.');
    }
  };


  // ?âÏ†êÎ≥ÑÎ°ú Í∑∏Î£π??(?†Îãà??
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

  // ?âÏ†êÎ≥ÑÎ°ú Í∑∏Î£π??(Ï∫êÎ¶≠?∞Ïö©)
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
      <div className="min-h-screen pt-10 md:pt-12 bg-transparent">
        <div className="max-w-[1180px] mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8">
          {/* Header with Real User Data */}
          <div className="bg-white rounded-2xl shadow-[0_2px_12px_rgba(0,0,0,0.08)] p-5 mb-6">
            <div className="flex items-center gap-4 mb-4">
              {/* Real Avatar */}
              {displayUser?.avatar_url ? (
                <img
                  src={getAvatarUrl(displayUser.avatar_url)}
                  alt={displayUser.display_name || displayUser.username}
                  className="w-16 h-16 rounded-full object-cover border-2 border-border"
                  onError={(e) => {
                    e.target.style.display = 'none';
                  }}
                />
              ) : (
                <div className="w-16 h-16 rounded-full flex items-center justify-center text-white text-2xl font-bold border-2 border-border" style={{ background: getAvatarGradient(displayUser?.username) }}>
                  {(displayUser?.display_name || displayUser?.username || 'U')[0].toUpperCase()}
                </div>
              )}
              <div className="flex-1">
                {/* Real Name */}
                <div className="flex items-center gap-2.5 mb-1">
                  <h1 className="text-[22px] font-bold">
                    {displayUser?.display_name || displayUser?.username}
                  </h1>
                </div>
                {/* Real Follow Counts */}
                <div className="flex items-center gap-4">
                  <button
                    onClick={() => openFollowModal('followers')}
                    className="text-sm hover:text-[#737373] transition-colors"
                  >
                    <span className="font-semibold">{followCounts.followers_count}</span> {language === 'ko' ? '?îÎ°ú?? : language === 'ja' ? '?ï„Ç©??ÉØ?? : 'Followers'}
                  </button>
                  <button
                    onClick={() => openFollowModal('following')}
                    className="text-sm hover:text-[#737373] transition-colors"
                  >
                    <span className="font-semibold">{followCounts.following_count}</span> {language === 'ko' ? '?îÎ°ú?? : language === 'ja' ? '?ï„Ç©??Éº‰∏? : 'Following'}
                  </button>
                </div>
              </div>
            </div>

            {/* Tabs - Real and Clickable */}
            <div className="flex border-b border-border overflow-x-auto">
              <button
                onClick={() => changeTab('feed')}
                className={`px-2 sm:px-4 py-1.5 sm:py-2 text-xs sm:text-sm font-normal transition-colors whitespace-nowrap ${activeTab === 'feed'
                  ? 'border-b-2'
                  : 'text-text-secondary hover:text-text-primary'
                  }`}
                style={activeTab === 'feed' ? { color: 'var(--color-primary)', borderColor: 'var(--color-primary)', fontWeight: '500' } : {}}
              >
                {language === 'ko' ? '?ºÎìú' : language === 'ja' ? '?ï„Ç£?º„Éâ' : 'Feed'}
              </button>
              <button
                onClick={() => changeTab('anipass')}
                className={`px-2 sm:px-4 py-1.5 sm:py-2 text-xs sm:text-sm font-normal transition-colors whitespace-nowrap ${activeTab === 'anipass'
                  ? 'border-b-2'
                  : 'text-text-secondary hover:text-text-primary'
                  }`}
                style={activeTab === 'anipass' ? { color: 'var(--color-primary)', borderColor: 'var(--color-primary)', fontWeight: '500' } : {}}
              >
                {language === 'ko' ? 'Î∂ÑÏÑù' : language === 'ja' ? '?ÜÊûê' : 'Analysis'}
              </button>
              <button
                onClick={() => changeTab('anime')}
                className={`px-2 sm:px-4 py-1.5 sm:py-2 text-xs sm:text-sm font-normal transition-colors whitespace-nowrap ${activeTab === 'anime'
                  ? 'border-b-2'
                  : 'text-text-secondary hover:text-text-primary'
                  }`}
                style={activeTab === 'anime' ? { color: 'var(--color-primary)', borderColor: 'var(--color-primary)', fontWeight: '500' } : {}}
              >
                {language === 'ko' ? '?†Îãà' : language === 'ja' ? '?¢„Éã?? : 'Anime'}
              </button>
              <button
                onClick={() => changeTab('character')}
                className={`px-2 sm:px-4 py-1.5 sm:py-2 text-xs sm:text-sm font-normal transition-colors whitespace-nowrap ${activeTab === 'character'
                  ? 'border-b-2'
                  : 'text-text-secondary hover:text-text-primary'
                  }`}
                style={activeTab === 'character' ? { color: 'var(--color-primary)', borderColor: 'var(--color-primary)', fontWeight: '500' } : {}}
              >
                {language === 'ko' ? 'Ï∫êÎ¶≠?? : language === 'ja' ? '??É£?©„ÇØ?ø„Éº' : 'Character'}
              </button>
            </div>
          </div>

          {/* Loading Indicator */}
          <div className="flex justify-center items-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-10 md:pt-12 bg-transparent">

      <div className="max-w-[1180px] mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8">
        {/* Header */}
        <div className="bg-surface rounded-2xl shadow-lg border border-border p-5 mb-6">
          <div className="flex items-center gap-4 mb-4">
            {displayUser?.avatar_url ? (
              <img
                src={getAvatarUrl(displayUser.avatar_url)}
                alt={displayUser.display_name || displayUser.username}
                className="w-16 h-16 rounded-full object-cover border-2 border-border"
                onError={(e) => {
                  e.target.style.display = 'none';
                }}
              />
            ) : (
              <div className="w-16 h-16 rounded-full flex items-center justify-center text-text-primary text-2xl font-bold border-2 border-border" style={{ background: getAvatarGradient(displayUser?.username) }}>
                {(displayUser?.display_name || displayUser?.username || 'U')[0].toUpperCase()}
              </div>
            )}
            <div>
              <div className="flex items-center gap-2.5 mb-1">
                <h1 className="text-[22px] font-bold text-text-primary">
                  {displayUser?.display_name || displayUser?.username}
                </h1>
                {stats && (
                  (() => {
                    const levelInfo = getCurrentLevelInfo(stats.otaku_score || 0, language);
                    return (
                      <span
                        className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold"
                        style={{ backgroundColor: levelInfo.bgColor, border: `1px solid ${levelInfo.borderColorHex}` }}
                      >
                        <span style={{ color: levelInfo.color }} className="font-bold">{levelInfo.icon}</span> <span style={{ color: levelInfo.color }}>{levelInfo.level} - {toRoman(levelInfo.rank)}</span>
                      </span>
                    );
                  })()
                )}
              </div>
              <div className="flex items-center gap-4">
                <button
                  onClick={() => openFollowModal('followers')}
                  className="text-sm text-text-secondary hover:text-primary transition-colors"
                >
                  <span className="font-semibold text-text-primary">{followCounts.followers_count}</span> {language === 'ko' ? '?îÎ°ú?? : language === 'ja' ? '?ï„Ç©??ÉØ?? : 'Followers'}
                </button>
                <button
                  onClick={() => openFollowModal('following')}
                  className="text-sm text-text-secondary hover:text-primary transition-colors"
                >
                  <span className="font-semibold text-text-primary">{followCounts.following_count}</span> {language === 'ko' ? '?îÎ°ú?? : language === 'ja' ? '?ï„Ç©??Éº‰∏? : 'Following'}
                </button>
              </div>
            </div>
            {!isOwnProfile && (
              <button
                onClick={handleFollowToggle}
                className={`ml-auto px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${isFollowing
                  ? 'bg-transparent border-2 border-gray-300 text-text-secondary hover:border-red-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20'
                  : 'text-white'
                  }`}
                style={!isFollowing ? { backgroundColor: '#4EEAF7', fontWeight: '500' } : {}}
                onMouseEnter={(e) => !isFollowing && (e.target.style.backgroundColor = '#1877F2')}
                onMouseLeave={(e) => !isFollowing && (e.target.style.backgroundColor = '#4EEAF7')}
              >
                {isFollowing ? (language === 'ko' ? '?îÎ°ú?? : language === 'ja' ? '?ï„Ç©??Éº‰∏? : 'Following') : (language === 'ko' ? '?îÎ°ú?? : language === 'ja' ? '?ï„Ç©??Éº' : 'Follow')}
              </button>
            )}
          </div>

          {/* Tabs */}
          <div className="flex border-b border-border overflow-x-auto">
            <button
              onClick={() => changeTab('feed')}
              className={`px-2 sm:px-4 py-1.5 sm:py-2 text-xs sm:text-sm font-normal transition-colors whitespace-nowrap ${activeTab === 'feed'
                ? 'border-b-2'
                : 'text-text-secondary hover:text-text-primary'
                }`}
              style={activeTab === 'feed' ? { color: 'var(--color-primary)', borderColor: 'var(--color-primary)', fontWeight: '500' } : {}}
            >
              {language === 'ko' ? '?ºÎìú' : language === 'ja' ? '?ï„Ç£?º„Éâ' : 'Feed'}
            </button>
            <button
              onClick={() => changeTab('anipass')}
              className={`px-2 sm:px-4 py-1.5 sm:py-2 text-xs sm:text-sm font-normal transition-colors whitespace-nowrap ${activeTab === 'anipass'
                ? 'border-b-2'
                : 'text-text-secondary hover:text-text-primary'
                }`}
              style={activeTab === 'anipass' ? { color: 'var(--color-primary)', borderColor: 'var(--color-primary)', fontWeight: '500' } : {}}
            >
              {language === 'ko' ? 'Î∂ÑÏÑù' : language === 'ja' ? '?ÜÊûê' : 'Analysis'}
            </button>
            <button
              onClick={() => changeTab('anime')}
              className={`px-2 sm:px-4 py-1.5 sm:py-2 text-xs sm:text-sm font-normal transition-colors whitespace-nowrap ${activeTab === 'anime'
                ? 'border-b-2'
                : 'text-text-secondary hover:text-text-primary'
                }`}
              style={activeTab === 'anime' ? { color: 'var(--color-primary)', borderColor: 'var(--color-primary)', fontWeight: '500' } : {}}
            >
              {language === 'ko' ? '?†Îãà' : language === 'ja' ? '?¢„Éã?? : 'Anime'} {stats && <span className="text-[10px] sm:text-xs">({(stats.total_rated || 0) + (stats.total_want_to_watch || 0) + (stats.total_pass || 0)})</span>}
            </button>
            <button
              onClick={() => changeTab('character')}
              className={`px-2 sm:px-4 py-1.5 sm:py-2 text-xs sm:text-sm font-normal transition-colors whitespace-nowrap ${activeTab === 'character'
                ? 'border-b-2'
                : 'text-text-secondary hover:text-text-primary'
                }`}
              style={activeTab === 'character' ? { color: 'var(--color-primary)', borderColor: 'var(--color-primary)', fontWeight: '500' } : {}}
            >
              {language === 'ko' ? 'Ï∫êÎ¶≠?? : language === 'ja' ? '??É£?©„ÇØ?ø„Éº' : 'Character'} {stats && <span className="text-[10px] sm:text-xs">({stats.total_character_ratings || 0})</span>}
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
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${animeSubMenu === 'all'
                    ? ''
                    : 'bg-surface-elevated text-text-secondary hover:bg-surface-hover'
                    }`}
                  style={animeSubMenu === 'all' ? { backgroundColor: 'var(--color-primary)', color: 'var(--color-text-primary)', fontWeight: '600' } : {}}
                >
                  {language === 'ko' ? 'Î™®Îëê' : language === 'ja' ? '?ô„Åπ?? : 'All'}
                </button>
                <button
                  onClick={() => setAnimeSubMenu('5')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${animeSubMenu === '5'
                    ? ''
                    : 'bg-surface-elevated text-text-secondary hover:bg-surface-hover'
                    }`}
                  style={animeSubMenu === '5' ? { backgroundColor: 'var(--color-primary)', color: 'var(--color-text-primary)', fontWeight: '600' } : {}}
                >
                  ‚≠?5{language === 'ko' ? '?? : language === 'ja' ? '?? : ''}
                </button>
                <button
                  onClick={() => setAnimeSubMenu('4')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${animeSubMenu === '4'
                    ? ''
                    : 'bg-surface-elevated text-text-secondary hover:bg-surface-hover'
                    }`}
                  style={animeSubMenu === '4' ? { backgroundColor: 'var(--color-primary)', color: 'var(--color-text-primary)', fontWeight: '600' } : {}}
                >
                  ‚≠?4{language === 'ko' ? '?êÎ?' : language === 'ja' ? '?πÂè∞' : '.0-4.5'}
                </button>
                <button
                  onClick={() => setAnimeSubMenu('3')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${animeSubMenu === '3'
                    ? 'text-white'
                    : 'bg-surface-elevated text-text-secondary hover:bg-surface-hover'
                    }`}
                  style={animeSubMenu === '3' ? { backgroundColor: 'var(--color-primary)', color: 'var(--color-text-primary)', fontWeight: '600' } : {}}
                >
                  ‚≠?3{language === 'ko' ? '?êÎ?' : language === 'ja' ? '?πÂè∞' : '.0-3.5'}
                </button>
                <button
                  onClick={() => setAnimeSubMenu('2')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${animeSubMenu === '2'
                    ? 'text-white'
                    : 'bg-surface-elevated text-text-secondary hover:bg-surface-hover'
                    }`}
                  style={animeSubMenu === '2' ? { backgroundColor: 'var(--color-primary)', color: 'var(--color-text-primary)', fontWeight: '600' } : {}}
                >
                  ‚≠?2{language === 'ko' ? '?êÎ?' : language === 'ja' ? '?πÂè∞' : '.0-2.5'}
                </button>
                <button
                  onClick={() => setAnimeSubMenu('1')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${animeSubMenu === '1'
                    ? 'text-white'
                    : 'bg-surface-elevated text-text-secondary hover:bg-surface-hover'
                    }`}
                  style={animeSubMenu === '1' ? { backgroundColor: 'var(--color-primary)', color: 'var(--color-text-primary)', fontWeight: '600' } : {}}
                >
                  ‚≠?{language === 'ko' ? '1?êÎ? ?¥Ìïò' : language === 'ja' ? '??.5' : '??.5'}
                </button>
                <button
                  onClick={() => setAnimeSubMenu('watchlist')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${animeSubMenu === 'watchlist'
                    ? 'text-white'
                    : 'bg-surface-elevated text-text-secondary hover:bg-surface-hover'
                    }`}
                  style={animeSubMenu === 'watchlist' ? { backgroundColor: 'var(--color-primary)', color: 'var(--color-text-primary)', fontWeight: '600' } : {}}
                >
                  {language === 'ko' ? 'Î≥¥Í≥†?∂Ïñ¥?? : language === 'ja' ? '?¶„Ç©?É„ÉÅ?™„Çπ?? : 'Watchlist'}
                </button>
                <button
                  onClick={() => setAnimeSubMenu('pass')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${animeSubMenu === 'pass'
                    ? 'text-white'
                    : 'bg-surface-elevated text-text-secondary hover:bg-surface-hover'
                    }`}
                  style={animeSubMenu === 'pass' ? { backgroundColor: 'var(--color-primary)', color: 'var(--color-text-primary)', fontWeight: '600' } : {}}
                >
                  {language === 'ko' ? 'Í¥Ä?¨ÏóÜ?¥Ïöî' : language === 'ja' ? '?àÂë≥?™„Åó' : 'Pass'}
                </button>
              </div>
            )}
            {activeTab === 'character' && (
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => setCharacterSubMenu('all')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${characterSubMenu === 'all'
                    ? ''
                    : 'bg-surface-elevated text-text-secondary hover:bg-surface-hover'
                    }`}
                  style={characterSubMenu === 'all' ? { backgroundColor: 'var(--color-primary)', color: 'var(--color-text-primary)', fontWeight: '600' } : {}}
                >
                  {language === 'ko' ? 'Î™®Îëê' : language === 'ja' ? '?ô„Åπ?? : 'All'}
                </button>
                <button
                  onClick={() => setCharacterSubMenu('5')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${characterSubMenu === '5'
                    ? ''
                    : 'bg-surface-elevated text-text-secondary hover:bg-surface-hover'
                    }`}
                  style={characterSubMenu === '5' ? { backgroundColor: 'var(--color-primary)', color: 'var(--color-text-primary)', fontWeight: '600' } : {}}
                >
                  ‚≠?5{language === 'ko' ? '?? : language === 'ja' ? '?? : ''}
                </button>
                <button
                  onClick={() => setCharacterSubMenu('4')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${characterSubMenu === '4'
                    ? ''
                    : 'bg-surface-elevated text-text-secondary hover:bg-surface-hover'
                    }`}
                  style={characterSubMenu === '4' ? { backgroundColor: 'var(--color-primary)', color: 'var(--color-text-primary)', fontWeight: '600' } : {}}
                >
                  ‚≠?4{language === 'ko' ? '?êÎ?' : language === 'ja' ? '?πÂè∞' : '.0-4.5'}
                </button>
                <button
                  onClick={() => setCharacterSubMenu('3')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${characterSubMenu === '3'
                    ? 'text-white'
                    : 'bg-surface-elevated text-text-secondary hover:bg-surface-hover'
                    }`}
                  style={characterSubMenu === '3' ? { backgroundColor: 'var(--color-primary)', color: 'var(--color-text-primary)', fontWeight: '600' } : {}}
                >
                  ‚≠?3{language === 'ko' ? '?êÎ?' : language === 'ja' ? '?πÂè∞' : '.0-3.5'}
                </button>
                <button
                  onClick={() => setCharacterSubMenu('2')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${characterSubMenu === '2'
                    ? 'text-white'
                    : 'bg-surface-elevated text-text-secondary hover:bg-surface-hover'
                    }`}
                  style={characterSubMenu === '2' ? { backgroundColor: 'var(--color-primary)', color: 'var(--color-text-primary)', fontWeight: '600' } : {}}
                >
                  ‚≠?2{language === 'ko' ? '?êÎ?' : language === 'ja' ? '?πÂè∞' : ''}
                </button>
                <button
                  onClick={() => setCharacterSubMenu('1')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${characterSubMenu === '1'
                    ? 'text-white'
                    : 'bg-surface-elevated text-text-secondary hover:bg-surface-hover'
                    }`}
                  style={characterSubMenu === '1' ? { backgroundColor: 'var(--color-primary)', color: 'var(--color-text-primary)', fontWeight: '600' } : {}}
                >
                  ‚≠?{language === 'ko' ? '1?êÎ? ?¥Ìïò' : language === 'ja' ? '??.5' : '??.5'}
                </button>
                <button
                  onClick={() => setCharacterSubMenu('want')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${characterSubMenu === 'want'
                    ? 'text-white'
                    : 'bg-surface-elevated text-text-secondary hover:bg-surface-hover'
                    }`}
                  style={characterSubMenu === 'want' ? { backgroundColor: 'var(--color-primary)', color: 'var(--color-text-primary)', fontWeight: '600' } : {}}
                >
                  {language === 'ko' ? '?åÍ≥†?∂Ïñ¥?? : language === 'ja' ? '?•„Çä?ü„ÅÑ' : 'Want to Know'}
                </button>
                <button
                  onClick={() => setCharacterSubMenu('pass')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${characterSubMenu === 'pass'
                    ? 'text-white'
                    : 'bg-surface-elevated text-text-secondary hover:bg-surface-hover'
                    }`}
                  style={characterSubMenu === 'pass' ? { backgroundColor: 'var(--color-primary)', color: 'var(--color-text-primary)', fontWeight: '600' } : {}}
                >
                  {language === 'ko' ? 'Í¥Ä?¨ÏóÜ?¥Ïöî' : language === 'ja' ? '?àÂë≥?™„Åó' : 'Pass'}
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
                <div className="bg-surface rounded-xl shadow-lg border border-border p-6 sticky top-4">
                  {/* Profile Picture */}
                  <div className="flex flex-col items-center mb-4">
                    {displayUser?.avatar_url ? (
                      <img
                        src={getAvatarUrl(displayUser.avatar_url)}
                        alt={displayUser?.display_name || displayUser?.username}
                        className="w-24 h-24 rounded-full object-cover border-2 border-border mb-3"
                      />
                    ) : (
                      <div className="w-24 h-24 rounded-full flex items-center justify-center border-2 border-border mb-3" style={{ background: 'linear-gradient(135deg, #833AB4 0%, #E1306C 40%, #F77737 70%, #FCAF45 100%)' }}>
                        <span className="text-white text-2xl font-bold">
                          {(displayUser?.display_name || displayUser?.username || '?').charAt(0).toUpperCase()}
                        </span>
                      </div>
                    )}

                    {/* Name */}
                    <h3 className="text-lg font-bold text-text-primary text-center">
                      {displayUser?.display_name || displayUser?.username}
                    </h3>

                    {/* Badge */}
                    {(() => {
                      const levelInfo = getCurrentLevelInfo(stats.otaku_score || 0, language);
                      return (
                        <span
                          className="mt-2 text-xs px-3 py-1 rounded-full font-semibold"
                          style={{ backgroundColor: levelInfo.bgColor, border: `1px solid ${levelInfo.borderColorHex}` }}
                        >
                          <span style={{ color: levelInfo.color }} className="font-bold">{levelInfo.icon}</span> <span style={{ color: levelInfo.color }}>{levelInfo.level} - {toRoman(levelInfo.rank)}</span>
                        </span>
                      );
                    })()}
                  </div>

                  {/* Stats Summary */}
                  <div className="space-y-3 pt-4 border-t border-border">
                    <h3 className="text-base font-bold text-text-primary mb-3">
                      {language === 'ko' ? '?µÍ≥Ñ' : language === 'ja' ? 'Áµ±Ë®à' : 'Statistics'}
                    </h3>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-text-secondary">{language === 'ko' ? '?§Ì?Ïø??êÏàò' : language === 'ja' ? '?™„Çø??Çπ?≥„Ç¢' : 'Otaku Score'}</span>
                      <span className="text-sm font-bold text-text-primary">{Math.round(stats.otaku_score)}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-text-secondary">{language === 'ko' ? '?âÍ????†Îãà' : language === 'ja' ? 'Ë©ï‰æ°Ê∏à„Åø?¢„Éã?? : 'Rated Anime'}</span>
                      <span className="text-sm font-bold text-text-primary">{stats.total_rated}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-text-secondary">{language === 'ko' ? '?âÍ???Ï∫êÎ¶≠?? : language === 'ja' ? 'Ë©ï‰æ°Ê∏à„Åø??É£?? : 'Rated Characters'}</span>
                      <span className="text-sm font-bold text-text-primary">{stats.total_character_ratings || 0}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-text-secondary">{language === 'ko' ? '?ëÏÑ±??Î¶¨Î∑∞' : language === 'ja' ? '‰ΩúÊàê?¨„Éì?•„Éº' : 'Reviews Written'}</span>
                      <span className="text-sm font-bold text-text-primary">{stats.total_reviews}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-text-secondary">{language === 'ko' ? '?âÍ∑† ?âÏ†ê' : language === 'ja' ? 'Âπ≥ÂùáË©ï‰æ°' : 'Avg Rating'}</span>
                      <span className="text-sm font-bold text-text-primary">{stats.average_rating?.toFixed(1) || 'N/A'}</span>
                    </div>
                    {displayUser?.created_at && (
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-text-secondary">{language === 'ko' ? 'Í∞Ä?ÖÏùº' : language === 'ja' ? '?ªÈå≤?? : 'Joined'}</span>
                        <span className="text-sm font-bold text-text-primary">
                          {new Date(displayUser.created_at).toLocaleDateString(language === 'ko' ? 'ko-KR' : language === 'ja' ? 'ja-JP' : 'en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Follow Stats */}
                  <div className="flex gap-4 justify-center pt-4 border-t border-border mt-4">
                    <button
                      onClick={() => openFollowModal('followers')}
                      className="flex flex-col items-center hover:text-[#737373] transition-colors"
                    >
                      <span className="text-lg font-bold text-text-primary">{followCounts.followers_count}</span>
                      <span className="text-xs text-text-secondary">{language === 'ko' ? '?îÎ°ú?? : language === 'ja' ? '?ï„Ç©??ÉØ?? : 'Followers'}</span>
                    </button>
                    <div className="w-px bg-gray-200"></div>
                    <button
                      onClick={() => openFollowModal('following')}
                      className="flex flex-col items-center hover:text-[#737373] transition-colors"
                    >
                      <span className="text-lg font-bold text-text-primary">{followCounts.following_count}</span>
                      <span className="text-xs text-text-secondary">{language === 'ko' ? '?îÎ°ú?? : language === 'ja' ? '?ï„Ç©??Éº‰∏? : 'Following'}</span>
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Right Content - Feed */}
            <div className={stats ? "lg:col-span-3" : "lg:col-span-4"}>
              {/* Post Composer - Show immediately for own profile */}
              {isOwnProfile && displayUser && (
                <div className="bg-surface rounded-xl shadow-lg border border-border p-4 mb-6">
                  <div className="flex gap-3">
                    {displayUser?.avatar_url ? (
                      <img
                        src={getAvatarUrl(displayUser.avatar_url)}
                        alt={displayUser.display_name || displayUser.username}
                        className="w-10 h-10 rounded-full object-cover border border-border"
                      />
                    ) : (
                      <div className="w-10 h-10 rounded-full flex items-center justify-center border border-border" style={{ background: getAvatarGradient(displayUser?.username) }}>
                        <span className="text-white text-sm font-bold">
                          {(displayUser?.display_name || displayUser?.username || '?').charAt(0).toUpperCase()}
                        </span>
                      </div>
                    )}
                    <div className="flex-1">
                      <textarea
                        value={newPostContent}
                        onChange={(e) => setNewPostContent(e.target.value)}
                        placeholder={language === 'ko' ? 'Î¨¥Ïä® ?ùÍ∞Å???òÍ≥† Í≥ÑÏã†Í∞Ä??' : language === 'ja' ? '‰ªä‰Ωï?íËÄÉ„Åà?¶„ÅÑ?æ„Åô?ãÔºü' : "What's on your mind?"}
                        className="w-full px-4 py-2 border border-border rounded-lg bg-input focus:outline-none focus:ring-1 focus:ring-primary focus:bg-input-focus text-text-primary resize-none"
                        rows="3"
                      />
                      <div className="flex justify-end mt-2">
                        <button
                          onClick={handleCreatePost}
                          disabled={!newPostContent.trim()}
                          className="px-4 py-2 text-white rounded-lg transition-all disabled:bg-gray-300 disabled:cursor-not-allowed font-semibold"
                          style={newPostContent.trim() ? {
                            background: 'linear-gradient(135deg, #E1306C 0%, #F77737 50%, #FCAF45 100%)',
                            color: 'white'
                          } : {}}
                        >
                          {language === 'ko' ? 'Í≤åÏãú' : language === 'ja' ? '?ïÁ®ø' : 'Post'}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Feed Activities */}
              {loading ? (
                <div className="flex justify-center items-center h-64">
                  <div className="text-xl text-text-secondary">{language === 'ko' ? '?ºÎìú Î°úÎî© Ï§?..' : language === 'ja' ? '?ï„Ç£?º„ÉâË™?æº‰∏?..' : 'Loading feed...'}</div>
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
                <div className="text-center py-12 text-text-secondary">
                  {language === 'ko' ? '?ÑÏßÅ ?úÎèô???ÜÏäµ?àÎã§.' : language === 'ja' ? '?æ„Å†Ê¥ªÂãï?å„ÅÇ?ä„Åæ?õ„Çì' : 'No activity yet.'}
                </div>
              )}
            </div>
          </div>
        )}

        {loading && activeTab !== 'feed' ? (
          <div className="flex justify-center items-center h-64">
            <div className="text-xl text-text-secondary">{language === 'ko' ? 'Î°úÎî© Ï§?..' : language === 'ja' ? 'Ë™?æº‰∏?..' : 'Loading...'}</div>
          </div>
        ) : activeTab !== 'feed' && (
          <div className={tabLoading ? 'opacity-50 pointer-events-none' : ''}>
            {activeTab === 'anipass' && (
              <div className="space-y-6">
                {/* ?ÅÎã® Í∑∏Î¶¨?? ?§Ì?Ïø?ÎØ∏ÌÑ∞, ?µÍ≥Ñ, ?•Î•¥ ?†Ìò∏??*/}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:items-stretch">
                  {/* ?§Ì?Ïø?ÎØ∏ÌÑ∞ */}
                  <div className="w-full">
                    {stats && <OtakuMeter score={stats.otaku_score || 0} language={language} />}
                  </div>

                  {/* ?µÍ≥Ñ */}
                  <div className="w-full">
                    {stats && (
                      <div className="bg-surface rounded-xl shadow-lg border border-border p-6 h-full">
                        <h3 className="text-base font-semibold text-text-primary mb-4">
                          {language === 'ko' ? '?µÍ≥Ñ' : language === 'ja' ? 'Áµ±Ë®à' : 'Statistics'}
                        </h3>
                        <div className="space-y-4">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary to-primary-dark flex items-center justify-center text-text-primary text-xl flex-shrink-0">
                              ?ì∫
                            </div>
                            <div className="flex-1">
                              <div className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-0.5">{language === 'ko' ? '?âÍ????†Îãà' : language === 'ja' ? 'Ë©ï‰æ°Ê∏à„Åø?¢„Éã?? : 'Rated Anime'}</div>
                              <div className="text-2xl font-bold text-primary">
                                {stats.total_rated || 0}
                              </div>
                            </div>
                          </div>

                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-secondary to-secondary-dark flex items-center justify-center text-text-primary text-xl flex-shrink-0">
                              ‚≠?
                            </div>
                            <div className="flex-1">
                              <div className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-0.5">{language === 'ko' ? 'Î≥¥Í≥†?∂Ïñ¥?? : language === 'ja' ? '?¶„Ç©?É„ÉÅ?™„Çπ?? : 'Watchlist'}</div>
                              <div className="text-2xl font-bold text-secondary">
                                {stats.total_want_to_watch || 0}
                              </div>
                            </div>
                          </div>

                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-accent to-accent-dark flex items-center justify-center text-text-primary text-xl flex-shrink-0">
                              ??
                            </div>
                            <div className="flex-1">
                              <div className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-0.5">{language === 'ko' ? '?âÍ∑† ?âÏ†ê' : language === 'ja' ? 'Âπ≥ÂùáË©ï‰æ°' : 'Avg Rating'}</div>
                              <div className="text-2xl font-bold text-accent">
                                {stats.average_rating ? `??${stats.average_rating.toFixed(1)}` : '-'}
                              </div>
                            </div>
                          </div>

                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-tertiary to-tertiary-dark flex items-center justify-center text-text-primary text-xl flex-shrink-0">
                              ?±Ô∏è
                            </div>
                            <div className="flex-1">
                              <div className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-0.5">{language === 'ko' ? '?úÏ≤≠ ?úÍ∞Ñ' : language === 'ja' ? 'Ë¶ñËÅ¥?ÇÈñì' : 'Watch Time'}</div>
                              <div className="text-2xl font-bold text-tertiary">
                                {formatWatchTime(watchTime?.total_minutes)}
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* ?•Î•¥ ?†Ìò∏??*/}
                  <div className="w-full">
                    <GenrePreferences preferences={genrePreferences} />
                  </div>
                </div>

                {/* Phase 1 ?µÍ≥Ñ Í∑∏Î¶¨?? ?¨Îß∑, ?êÌîº?åÎìú Í∏∏Ïù¥, ?âÍ? ?±Ìñ• */}
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

                {/* Ï∞®Ìä∏ Í∑∏Î¶¨?? ?âÏ†ê Î∂ÑÌè¨, ?∞ÎèÑÎ≥?Î∂ÑÌè¨ */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:items-stretch">
                  <div className="w-full">
                    <RatingDistributionChart distribution={ratingDistribution} />
                  </div>
                  <div className="w-full">
                    <YearDistributionChart distribution={yearDistribution} />
                  </div>
                </div>

                {/* Phase 1 & 2 Ï∂îÍ? ?µÍ≥Ñ: ?§Ìäú?îÏò§, ?•Î•¥ Ï°∞Ìï©, ?úÏ¶å */}
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
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
                  </div>
                ) : displayedAnime.length > 0 ? (
                  ['all', '4', '3', '2', '1'].includes(animeSubMenu) ? (
                    // Î™®Îëê ?êÎäî Î≤îÏúÑ ?ÑÌÑ∞ ?†ÌÉù ???âÏ†êÎ≥ÑÎ°ú Í∑∏Î£π??+ Virtual Scrolling
                    <div className="space-y-8">
                      {animeSections.map((section, sectionIndex) => {
                        const categoryLabels = {
                          '5': language === 'ko' ? '‚≠?5?? : language === 'ja' ? '‚≠?5?? : '‚≠?5.0',
                          '4.5': language === 'ko' ? '‚≠?4.5?? : language === 'ja' ? '‚≠?4.5?? : '‚≠?4.5',
                          '4': language === 'ko' ? '‚≠?4?? : language === 'ja' ? '‚≠?4?? : '‚≠?4.0',
                          '3.5': language === 'ko' ? '‚≠?3.5?? : language === 'ja' ? '‚≠?3.5?? : '‚≠?3.5',
                          '3': language === 'ko' ? '‚≠?3?? : language === 'ja' ? '‚≠?3?? : '‚≠?3.0',
                          '2.5': language === 'ko' ? '‚≠?2.5?? : language === 'ja' ? '‚≠?2.5?? : '‚≠?2.5',
                          '2': language === 'ko' ? '‚≠?2?? : language === 'ja' ? '‚≠?2?? : '‚≠?2.0',
                          '1.5': language === 'ko' ? '‚≠?1.5?? : language === 'ja' ? '‚≠?1.5?? : '‚≠?1.5',
                          '1': language === 'ko' ? '‚≠?1?? : language === 'ja' ? '‚≠?1?? : '‚≠?1.0',
                          '0.5': language === 'ko' ? '‚≠?0.5?? : language === 'ja' ? '‚≠?0.5?? : '‚≠?0.5',
                          'watchlist': language === 'ko' ? '?ìã Î≥¥Í≥†?∂Ïñ¥?? : language === 'ja' ? '?ìã ?¶„Ç©?É„ÉÅ?™„Çπ?? : '?ìã Watchlist',
                          'pass': language === 'ko' ? '?ö´ Í¥Ä?¨ÏóÜ?¥Ïöî' : language === 'ja' ? '?ö´ ?àÂë≥?™„Åó' : '?ö´ Pass'
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
                    // 5?? Î≥¥Í≥†?∂Ïñ¥?? Í¥Ä?¨ÏóÜ?¥Ïöî???πÏÖò ?§Îçî?Ä ?®Íªò ?úÏãú
                    <div>
                      <h3 className="text-lg font-bold mb-4 text-gray-800">
                        {animeSubMenu === '5' && (language === 'ko' ? `‚≠?5??(${displayedAnime.length})` : language === 'ja' ? `‚≠?5??(${displayedAnime.length})` : `‚≠?5.0 (${displayedAnime.length})`)}
                        {animeSubMenu === 'watchlist' && (language === 'ko' ? `?ìã Î≥¥Í≥†?∂Ïñ¥??(${displayedAnime.length})` : language === 'ja' ? `?ìã ?¶„Ç©?É„ÉÅ?™„Çπ??(${displayedAnime.length})` : `?ìã Watchlist (${displayedAnime.length})`)}
                        {animeSubMenu === 'pass' && (language === 'ko' ? `?ö´ Í¥Ä?¨ÏóÜ?¥Ïöî (${displayedAnime.length})` : language === 'ja' ? `?ö´ ?àÂë≥?™„Åó (${displayedAnime.length})` : `?ö´ Pass (${displayedAnime.length})`)}
                      </h3>
                      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-6">
                        {displayedAnime.map((anime) => (
                          <MyAnimeCard key={anime.anime_id} anime={anime} />
                        ))}
                      </div>
                    </div>
                  )
                ) : (
                  <div className="text-center py-12 text-text-secondary">
                    {language === 'ko' ? '?ÑÏßÅ ?†ÎãàÍ∞Ä ?ÜÏäµ?àÎã§.' : language === 'ja' ? '?æ„Å†?¢„Éã?°„Åå?Ç„Çä?æ„Åõ?? : 'No anime yet.'}
                  </div>
                )}
              </div>
            )}

            {activeTab === 'character' && (
              <div>
                {/* Character Grid */}
                {!loadedTabs.character ? (
                  <div className="flex justify-center items-center py-20">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
                  </div>
                ) : displayedCharacters.length > 0 ? (
                  ['all', '4', '3', '2', '1'].includes(characterSubMenu) ? (
                    // Î™®Îëê ?†ÌÉù ???âÏ†êÎ≥ÑÎ°ú Í∑∏Î£π??+ Virtual Scrolling
                    <div className="space-y-8">
                      {characterSections.map((section, sectionIndex) => {
                        const categoryLabels = {
                          '5': language === 'ko' ? '‚≠?5?? : language === 'ja' ? '‚≠?5?? : '‚≠?5.0',
                          '4.5': language === 'ko' ? '‚≠?4.5?? : language === 'ja' ? '‚≠?4.5?? : '‚≠?4.5',
                          '4': language === 'ko' ? '‚≠?4?? : language === 'ja' ? '‚≠?4?? : '‚≠?4.0',
                          '3.5': language === 'ko' ? '‚≠?3.5?? : language === 'ja' ? '‚≠?3.5?? : '‚≠?3.5',
                          '3': language === 'ko' ? '‚≠?3?? : language === 'ja' ? '‚≠?3?? : '‚≠?3.0',
                          '2.5': language === 'ko' ? '‚≠?2.5?? : language === 'ja' ? '‚≠?2.5?? : '‚≠?2.5',
                          '2': language === 'ko' ? '‚≠?2?? : language === 'ja' ? '‚≠?2?? : '‚≠?2.0',
                          '1.5': language === 'ko' ? '‚≠?1.5?? : language === 'ja' ? '‚≠?1.5?? : '‚≠?1.5',
                          '1': language === 'ko' ? '‚≠?1?? : language === 'ja' ? '‚≠?1?? : '‚≠?1.0',
                          '0.5': language === 'ko' ? '‚≠?0.5?? : language === 'ja' ? '‚≠?0.5?? : '‚≠?0.5',
                          'want': language === 'ko' ? '?í≠ ?åÍ≥†?∂Ïñ¥?? : language === 'ja' ? '?í≠ ?•„Çä?ü„ÅÑ' : '?í≠ Want to Know',
                          'pass': language === 'ko' ? '?ö´ Í¥Ä?¨ÏóÜ?¥Ïöî' : language === 'ja' ? '?ö´ ?àÂë≥?™„Åó' : '?ö´ Pass'
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
                    // 5?? ?åÍ≥†?∂Ïñ¥?? Í¥Ä?¨ÏóÜ?¥Ïöî???πÏÖò ?§Îçî?Ä ?®Íªò ?úÏãú
                    <div>
                      <h3 className="text-lg font-bold mb-4 text-gray-800">
                        {characterSubMenu === '5' && (language === 'ko' ? `‚≠?5??(${displayedCharacters.length})` : language === 'ja' ? `‚≠?5??(${displayedCharacters.length})` : `‚≠?5.0 (${displayedCharacters.length})`)}
                        {characterSubMenu === 'want' && (language === 'ko' ? `?í≠ ?åÍ≥†?∂Ïñ¥??(${displayedCharacters.length})` : language === 'ja' ? `?í≠ ?•„Çä?ü„ÅÑ (${displayedCharacters.length})` : `?í≠ Want to Know (${displayedCharacters.length})`)}
                        {characterSubMenu === 'pass' && (language === 'ko' ? `?ö´ Í¥Ä?¨ÏóÜ?¥Ïöî (${displayedCharacters.length})` : language === 'ja' ? `?ö´ ?àÂë≥?™„Åó (${displayedCharacters.length})` : `?ö´ Pass (${displayedCharacters.length})`)}
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
                  <div className="text-center py-12 text-text-secondary">
                    {language === 'ko' ? '?ÑÏßÅ Ï∫êÎ¶≠?∞Í? ?ÜÏäµ?àÎã§.' : language === 'ja' ? '?æ„Å†??É£?©„ÇØ?ø„Éº?å„ÅÑ?æ„Åõ?? : 'No characters yet.'}
                  </div>
                )}
              </div>
            )}

          </div>
        )}

        {/* Follow Modal */}
        {showFollowModal && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50" onClick={() => setShowFollowModal(false)}>
            <div className="bg-white dark:bg-surface rounded-lg p-6 max-w-md w-full mx-4 max-h-[80vh] overflow-y-auto border border-border shadow-2xl" onClick={(e) => e.stopPropagation()}>
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold text-text-primary">
                  {followModalType === 'followers' ? (language === 'ko' ? '?îÎ°ú?? : language === 'ja' ? '?ï„Ç©??ÉØ?? : 'Followers') : (language === 'ko' ? '?îÎ°ú?? : language === 'ja' ? '?ï„Ç©??Éº‰∏? : 'Following')}
                </h2>
                <button
                  onClick={() => setShowFollowModal(false)}
                  className="text-text-tertiary hover:text-text-primary"
                >
                  ??
                </button>
              </div>

              {followList.length > 0 ? (
                <div className="space-y-3">
                  {followList.map((follower) => (
                    <Link
                      key={follower.id}
                      to={`/user/${follower.id}`}
                      className="flex items-center gap-3 p-2 hover:bg-surface-hover rounded-lg transition-colors"
                      onClick={() => setShowFollowModal(false)}
                    >
                      {follower.avatar_url ? (
                        <img
                          src={getAvatarUrl(follower.avatar_url)}
                          alt={follower.display_name || follower.username}
                          className="w-12 h-12 rounded-full object-cover border border-border"
                        />
                      ) : (
                        <div className="w-12 h-12 rounded-full flex items-center justify-center border border-border" style={{ background: getAvatarGradient(follower.username) }}>
                          <span className="text-white text-lg font-bold">
                            {(follower.display_name || follower.username || '?')[0].toUpperCase()}
                          </span>
                        </div>
                      )}
                      <div>
                        <div className="font-medium text-text-primary">
                          {follower.display_name || follower.username}
                        </div>
                        <div className="text-sm text-text-tertiary">@{follower.username}</div>
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-text-secondary">
                  {followModalType === 'followers'
                    ? (language === 'ko' ? '?îÎ°ú?åÍ? ?ÜÏäµ?àÎã§.' : language === 'ja' ? '?ï„Ç©??ÉØ?º„Åå?Ñ„Åæ?õ„Çì' : 'No followers yet.')
                    : (language === 'ko' ? '?îÎ°ú?âÌïò???¨Ïö©?êÍ? ?ÜÏäµ?àÎã§.' : language === 'ja' ? '?ï„Ç©??Éº‰∏?ÅÆ?¶„Éº?∂„Éº?å„ÅÑ?æ„Åõ?? : 'Not following anyone yet.')}
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
              <h3 className="text-xl font-bold mb-2 text-text-primary">
                {language === 'ko' ? '??†ú ?µÏÖò' : language === 'ja' ? '?äÈô§?™„Éó?∑„Éß?? : 'Delete Options'}
              </h3>

              {/* Show what's being deleted */}
              <div className="mb-4 p-3 bg-gray-50 rounded-lg border border-border flex gap-3">
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
                  <p className="text-sm font-semibold text-text-primary mb-1">
                    {activityToDelete.activity_type === 'character_rating' ? (
                      <>
                        {activityToDelete.item_title}{' '}
                        <span className="text-text-secondary">({activityToDelete.item_title_korean})</span>
                      </>
                    ) : (
                      activityToDelete.item_title_korean || activityToDelete.item_title
                    )}
                  </p>
                  {activityToDelete.activity_type === 'character_rating' && activityToDelete.anime_title && (
                    <p className="text-xs text-text-secondary mb-1">
                      from: {activityToDelete.anime_title_korean || activityToDelete.anime_title}
                    </p>
                  )}
                  <p className="text-xs text-gray-500">
                    {activityToDelete.activity_type === 'character_rating'
                      ? (language === 'ko' ? 'Ï∫êÎ¶≠?? : language === 'ja' ? '??É£?©„ÇØ?ø„Éº' : 'Character')
                      : (language === 'ko' ? '?†ÎãàÎ©îÏù¥?? : language === 'ja' ? '?¢„Éã?°„Éº?∑„Éß?? : 'Anime')}
                  </p>
                </div>
              </div>

              {activityToDelete.review_content && activityToDelete.review_content.trim() ? (
                <>
                  <p className="text-sm text-text-secondary mb-6">
                    {language === 'ko'
                      ? '???âÍ??êÎäî Î¶¨Î∑∞Í∞Ä ?¨Ìï®?òÏñ¥ ?àÏäµ?àÎã§. ?¥ÎñªÍ≤???†ú?òÏãúÍ≤†Ïäµ?àÍπå?'
                      : 'This rating includes a review. How would you like to delete it?'}
                  </p>
                  <div className="flex flex-col gap-3">
                    <button
                      onClick={() => handleDeleteActivity('review_only')}
                      className="w-full px-4 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors"
                    >
                      {language === 'ko' ? 'Î¶¨Î∑∞Îß???†ú (Î≥ÑÏ†ê ?†Ï?)' : language === 'ja' ? '?¨„Éì?•„Éº??Åø?äÈô§ (Ë©ï‰æ°??øù??' : 'Delete review only (Keep rating)'}
                    </button>
                    <button
                      onClick={() => handleDeleteActivity('all')}
                      className="w-full px-4 py-3 bg-red-500 hover:bg-red-600 text-white rounded-lg font-medium transition-colors"
                    >
                      {language === 'ko' ? 'Î≥ÑÏ†êÍπåÏ? Î™®Îëê ??†ú' : language === 'ja' ? 'Ë©ï‰æ°?®„É¨?ì„É•?º„Çí?äÈô§' : 'Delete rating and review'}
                    </button>
                    <button
                      onClick={() => setShowDeleteModal(false)}
                      className="w-full px-4 py-3 bg-gray-200 hover:bg-gray-300 text-text-secondary rounded-lg font-medium transition-colors"
                    >
                      {language === 'ko' ? 'Ï∑®ÏÜå' : language === 'ja' ? '??É£?≥„Çª?? : 'Cancel'}
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <p className="text-sm text-text-secondary mb-6">
                    {language === 'ko'
                      ? '???âÍ?Î•???†ú?òÏãúÍ≤†Ïäµ?àÍπå?'
                      : 'Are you sure you want to delete this rating?'}
                  </p>
                  <div className="flex gap-3">
                    <button
                      onClick={() => handleDeleteActivity('all')}
                      className="flex-1 px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg font-medium transition-colors"
                    >
                      {language === 'ko' ? '??†ú' : language === 'ja' ? '?äÈô§' : 'Delete'}
                    </button>
                    <button
                      onClick={() => setShowDeleteModal(false)}
                      className="flex-1 px-4 py-2 bg-gray-200 hover:bg-gray-300 text-text-secondary rounded-lg font-medium transition-colors"
                    >
                      {language === 'ko' ? 'Ï∑®ÏÜå' : language === 'ja' ? '??É£?≥„Çª?? : 'Cancel'}
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
