import { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { characterService } from '../services/characterService';
import { characterReviewService } from '../services/characterReviewService';
import { activityService } from '../services/activityService';
import { useActivities } from '../hooks/useActivity';
import { useLanguage } from '../context/LanguageContext';
import { useAuth } from '../context/AuthContext';
import { getPrefetchedData } from '../hooks/usePrefetch';
import { getCurrentLevelInfo } from '../utils/otakuLevels';
import * as ActivityUtils from '../utils/activityUtils';
import StarRating from '../components/common/StarRating';
import CharacterRatingWidget from '../components/character/CharacterRatingWidget';
import ActivityCard from '../components/activity/ActivityCard';
import { API_BASE_URL, IMAGE_BASE_URL } from '../config/api';
import { getCharacterImageUrl, getCharacterImageFallback, getAvatarUrl } from '../utils/imageHelpers';

export default function CharacterDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { language, getAnimeTitle } = useLanguage();
  const { user } = useAuth();
  const [character, setCharacter] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [myReview, setMyReview] = useState(null);
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [isEditingReview, setIsEditingReview] = useState(false);
  const [reviewData, setReviewData] = useState({ content: '', is_spoiler: false, rating: 0 });
  const [reviewError, setReviewError] = useState('');
  const [reviewSuccess, setReviewSuccess] = useState('');
  const [showEditMenu, setShowEditMenu] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [reviewLikes, setReviewLikes] = useState({});
  const [comments, setComments] = useState({});
  const [expandedComments, setExpandedComments] = useState(new Set());
  const [savedActivities, setSavedActivities] = useState(new Set());
  const [newComment, setNewComment] = useState({});
  const [commentLikes, setCommentLikes] = useState({});
  const [replyingTo, setReplyingTo] = useState({});
  const [myReviewComments, setMyReviewComments] = useState([]);

  // Use unified activities hook
  const {
    activities: otherActivities,
    loading: activitiesLoading,
    refetch: refetchActivities
  } = useActivities(
    {
      activityType: 'character_rating',
      itemId: id,
      limit: 50,
      offset: 0
    },
    {
      autoFetch: true
    }
  );

  // Combine myReview with other activities
  const activities = useMemo(() => {
    const allActivities = [...otherActivities];

    // If user has rating/review, add it to the top (if not already in the list)
    if (myReview && user) {
      const myActivityIndex = allActivities.findIndex(a => a.user_id === user.id);

      if (myActivityIndex === -1) {
        // Create activity object for my rating/review
        const myActivity = {
          id: `my-activity-${id}`,
          user_id: user.id,
          username: user.username || myReview.username,
          display_name: user.display_name || myReview.display_name,
          avatar_url: user.avatar_url || myReview.avatar_url,
          activity_type: 'character_rating',
          item_id: parseInt(id),
          item_title: character?.name_full,
          item_title_korean: character?.name_native,
          item_image: character?.image_url,
          rating: myReview.user_rating || character?.my_rating,
          review_content: myReview.content || null,
          review_title: myReview.title || null,
          is_spoiler: myReview.is_spoiler || false,
          activity_time: myReview.created_at || new Date().toISOString(),
          likes_count: myReview.likes_count || 0,
          comments_count: myReview.comments_count || 0,
          user_liked: false,
          otaku_score: myReview.otaku_score || user.otaku_score || 0
        };

        // Add to the beginning
        allActivities.unshift(myActivity);
      }
    }

    return allActivities;
  }, [otherActivities, myReview, user, id, character]);

  useEffect(() => {
    loadAllData();
  }, [id, user]);

  const loadAllData = async () => {
    setLoading(true);
    try {
      // Check for prefetched data first
      const prefetched = getPrefetchedData('character', id, user?.id);

      if (prefetched) {
        // Use prefetched data for instant display
        if (prefetched.character) {
          setCharacter(prefetched.character);
          setError(null);
          setLoading(false);
        }
        if (prefetched.reviews) {
          processReviews(prefetched.reviews);
        }
        if (prefetched.myReview) {
          processMyReview(prefetched.myReview);
        }
        return; // Skip API calls, data is already fresh from prefetch
      }

      // 1?¨ê³„: ìºë¦­??ê¸°ë³¸ ?•ë³´ ë¨¼ì? ë¡œë“œ?˜ê³  ì¦‰ì‹œ ?œì‹œ
      const characterData = await characterService.getCharacterDetail(id);

      if (characterData) {
        setCharacter(characterData);
        setError(null);
        setLoading(false); // ?¬ê¸°??ë¡œë”© ?´ì œ - ê¸°ë³¸ ?•ë³´ ë°”ë¡œ ?œì‹œ
      } else {
        setError(language === 'ko' ? 'ìºë¦­???•ë³´ë¥?ë¶ˆëŸ¬?¤ì? ëª»í–ˆ?µë‹ˆ??' : 'Failed to load character.');
        setLoading(false);
        return;
      }

      // 2?¨ê³„: ë¦¬ë·°?€ ??ë¦¬ë·°??ë°±ê·¸?¼ìš´?œì—??ë¡œë“œ (?”ë©´?€ ?´ë? ?œì‹œ ì¤?
      const reviewPromises = [
        characterReviewService.getCharacterReviews(id, { page: 1, page_size: 10 }).catch(() => null)
      ];

      if (user) {
        reviewPromises.push(characterReviewService.getMyReview(id).catch(() => null));
      }

      const reviewResults = await Promise.all(reviewPromises);

      // ë¦¬ë·° ëª©ë¡
      if (reviewResults[0]) {
        processReviews(reviewResults[0]);
      }

      // ??ë¦¬ë·°
      if (user && reviewResults[1]) {
        processMyReview(reviewResults[1]);
      }

      // 3?¨ê³„: ?¤ë¥¸ ?¬ëŒ?¤ì˜ ?œë™?€ useActivities hook?ì„œ ?ë™?¼ë¡œ ë¡œë“œ??
    } catch (err) {
      console.error('Failed to load character data:', err);
      setError(language === 'ko' ? '?°ì´?°ë? ë¶ˆëŸ¬?¤ì? ëª»í–ˆ?µë‹ˆ??' : 'Failed to load data.');
      setLoading(false);
    }
  };

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showEditMenu && !event.target.closest('.relative')) {
        setShowEditMenu(null);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showEditMenu]);

  // Load saved activities from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('savedActivities');
    if (saved) {
      setSavedActivities(new Set(JSON.parse(saved)));
    }
  }, []);

  const processReviews = (data) => {
    // ??ë¦¬ë·°??myReviewë¡??°ë¡œ ?œì‹œ?˜ë?ë¡? reviews?ì„œ???œì™¸
    const otherReviews = (data.items || []).filter(review => review.user_id !== user?.id);
    setReviews(otherReviews);

    // Load like information for each review
    const likesData = {};
    const newExpandedSet = new Set();
    const newComments = {};
    const commentsToLoad = [];

    otherReviews.forEach(review => {
      likesData[review.id] = {
        liked: review.user_liked || false,
        count: review.likes_count || 0
      };
      newComments[review.id] = [];

      // ?“ê????ˆìœ¼ë©??ë™?¼ë¡œ ?¼ì¹˜ê¸?
      if (review.comments_count > 0) {
        newExpandedSet.add(review.id);
        commentsToLoad.push(review);
      }
    });

    setReviewLikes(prev => ({ ...prev, ...likesData }));
    setComments(prev => ({ ...prev, ...newComments }));
    setExpandedComments(prev => new Set([...prev, ...newExpandedSet]));

    // ?“ê? ë³‘ë ¬ ë¡œë“œ
    if (commentsToLoad.length > 0) {
      Promise.all(commentsToLoad.map(review => loadComments(review)));
    }
  };

  const processMyReview = (data) => {
    setMyReview(data);

    // ì¢‹ì•„???íƒœ ?¤ì •
    if (data) {
      setReviewLikes(prev => ({
        ...prev,
        [data.id]: {
          liked: data.user_liked || false,
          count: data.likes_count || 0
        }
      }));

      // ??ë¦¬ë·°???“ê????ˆìœ¼ë©??ë™?¼ë¡œ ?¼ì¹˜ê³?ë¡œë“œ
      if (data.comments_count > 0) {
        setExpandedComments(prev => new Set([...prev, data.id]));
        loadComments(data);
      }
    }
  };

  const handleRatingChange = async (rating) => {
    try {
      if (rating === 0) {
        await characterService.deleteCharacterRating(id);
        setCharacter({ ...character, my_rating: null });
        setMyReview(null);
      } else {
        // rateCharacter expects an object, not a direct rating value
        await characterService.rateCharacter(id, { rating });
        setCharacter({ ...character, my_rating: rating });
        // ?‰ì  ?…ë ¥ ????ë¦¬ë·° ?¹ì…˜??ë°”ë¡œ ?œì‹œ
        const myReviewData = await characterReviewService.getMyReview(id).catch(() => null);
        if (myReviewData) processMyReview(myReviewData);

        // Update myReview rating if it exists
        if (myReview) {
          setMyReview({
            ...myReview,
            user_rating: rating
          });
        }
      }

      // ë³‘ë ¬ë¡??°ì´???ˆë¡œê³ ì¹¨ (BUT preserve the locally updated my_rating)
      const [charData, reviewData] = await Promise.all([
        characterService.getCharacterDetail(id),
        characterReviewService.getCharacterReviews(id, { page: 1, page_size: 10 })
      ]);

      // Preserve the locally updated my_rating to prevent overwrite with stale data
      if (charData) {
        setCharacter({ ...charData, my_rating: rating === 0 ? null : rating });
      }
      if (reviewData) processReviews(reviewData);
    } catch (err) {
      console.error('Failed to rate character:', err);
      console.error('Error response:', err.response?.data);
      console.error('Error status:', err.response?.status);

      const errorDetail = err.response?.data?.detail || err.message || 'Unknown error';
      const errorStatus = err.response?.status ? ` (${err.response.status})` : '';

      alert(
        language === 'ko'
          ? `?‰ê?ë¥??€?¥í•˜?”ë° ?¤íŒ¨?ˆìŠµ?ˆë‹¤${errorStatus}\n${errorDetail}`
          : language === 'ja'
            ? `è©•ä¾¡??¿å­˜ã«å¤±æ•—?—ã¾?—ãŸ${errorStatus}\n${errorDetail}`
            : `Failed to save rating${errorStatus}\n${errorDetail}`
      );
    }
  };

  const handleStatusChange = async (status) => {
    try {
      // rateCharacter expects an object with status property
      await characterService.rateCharacter(id, { status });
      setCharacter({ ...character, my_status: status });
      const charData = await characterService.getCharacterDetail(id);
      if (charData) setCharacter(charData);
    } catch (err) {
      console.error('Failed to change status:', err);
      alert(language === 'ko' ? '?íƒœ ë³€ê²½ì— ?¤íŒ¨?ˆìŠµ?ˆë‹¤.' : language === 'ja' ? '?¹ãƒ†?¼ã‚¿?¹å¤‰?´ã«å¤±æ•—?—ã¾?—ãŸ?? : 'Failed to change status.');
    }
  };

  const handleSubmitReview = async (e) => {
    e.preventDefault();
    setReviewError('');
    setReviewSuccess('');

    if (reviewData.rating === 0 || !reviewData.rating) {
      setReviewError(language === 'ko' ? 'ë³„ì ??? íƒ?´ì£¼?¸ìš”.' : language === 'ja' ? 'è©•ä¾¡?’é¸?ã—?¦ã? ã•?„ã€? : 'Please select a rating.');
      return;
    }

    if (!reviewData.content.trim()) {
      setReviewError(language === 'ko' ? 'ë¦¬ë·° ?´ìš©???…ë ¥?´ì£¼?¸ìš”.' : language === 'ja' ? '?¬ãƒ“?¥ãƒ¼?…å??’å…¥?›ã—?¦ã? ã•?„ã€? : 'Please enter review content.');
      return;
    }

    if (reviewData.content.trim().length < 10) {
      setReviewError(language === 'ko' ? 'ë¦¬ë·°??ìµœì†Œ 10???´ìƒ ?‘ì„±?´ì£¼?¸ìš”.' : language === 'ja' ? '?¬ãƒ“?¥ãƒ¼???ä½?0?‡å­—ä»¥ä¸Š?¥åŠ›?—ã¦?ã ?•ã„?? : 'Review must be at least 10 characters.');
      return;
    }

    try {
      if (isEditingReview && myReview && myReview.id) {
        // ?˜ì • ?? rating??ë¦¬ë·° API???¨ê»˜ ?„ì†¡
        await characterReviewService.updateReview(myReview.id, {
          content: reviewData.content,
          is_spoiler: reviewData.is_spoiler,
          rating: reviewData.rating  // ë³„ì ???¨ê»˜ ?„ì†¡
        });
        setReviewSuccess(language === 'ko' ? 'ë¦¬ë·°ê°€ ?˜ì •?˜ì—ˆ?µë‹ˆ??' : language === 'ja' ? '?¬ãƒ“?¥ãƒ¼?Œç·¨?†ã•?Œã¾?—ãŸ?? : 'Review updated successfully.');
      } else {
        // ?ˆë¡œ ?‘ì„±: ë³„ì ê³?ë¦¬ë·°ë¥???ë²ˆì— ?„ì†¡
        await characterReviewService.createReview({
          character_id: parseInt(id),
          content: reviewData.content,
          is_spoiler: reviewData.is_spoiler,
          rating: reviewData.rating  // ë³„ì ??ë¦¬ë·° API???¨ê»˜ ?„ì†¡
        });

        // ë¦¬ë·° ?ì„± ??ìºë¦­???°ì´???ˆë¡œê³ ì¹¨?˜ì—¬ ë³„ì  ?íƒœ ë°˜ì˜
        setCharacter({ ...character, my_rating: reviewData.rating });

        setReviewSuccess(language === 'ko' ? 'ë¦¬ë·°ê°€ ?‘ì„±?˜ì—ˆ?µë‹ˆ??' : language === 'ja' ? '?¬ãƒ“?¥ãƒ¼?Œä½œ?ã•?Œã¾?—ãŸ?? : 'Review submitted successfully.');
      }

      setReviewData({ content: '', is_spoiler: false, rating: 0 });
      setShowReviewForm(false);
      setIsEditingReview(false);

      // ë¡œì»¬ stateë§??…ë°?´íŠ¸ (?„ì²´ ë¦¬í”„?ˆì‹œ ?†ì´)
      if (isEditingReview) {
        // ë¦¬ë·° ?˜ì •: myReview?€ character ?…ë°?´íŠ¸
        const [updatedMyReview, updatedCharacter] = await Promise.all([
          characterReviewService.getMyReview(id).catch(() => null),
          characterService.getCharacterDetail(id).catch(() => null)
        ]);

        if (updatedMyReview) {
          setMyReview(updatedMyReview);
        }
        if (updatedCharacter) {
          setCharacter(updatedCharacter);
        }

        // Refresh activities list to update review list immediately
        await refetchActivities();
      } else {
        // ??ë¦¬ë·° ?‘ì„±: myReview?€ character statsë§??…ë°?´íŠ¸
        const [myReviewData, charData] = await Promise.all([
          characterReviewService.getMyReview(id).catch(() => null),
          characterService.getCharacterDetail(id)
        ]);

        if (myReviewData) setMyReview(myReviewData);
        if (charData) setCharacter(charData);
      }

      setTimeout(() => setReviewSuccess(''), 3000);
    } catch (err) {
      console.error('Failed to submit review:', err);
      setReviewError(
        language === 'ko'
          ? err.response?.data?.detail || 'ë¦¬ë·° ?‘ì„±???¤íŒ¨?ˆìŠµ?ˆë‹¤.'
          : language === 'ja'
            ? err.response?.data?.detail || '?¬ãƒ“?¥ãƒ¼ä½œæˆ?«å¤±?—ã—?¾ã—?Ÿã€?
            : err.response?.data?.detail || 'Failed to submit review.'
      );
    }
  };

  const handleEditReview = () => {
    // ?‰ì ë§??ˆëŠ” ê²½ìš° ë¦¬ë·° ?‘ì„± ?¼ì„ ?´ì–´ì¤?
    if (ActivityUtils.isRatingsOnly(myReview)) {
      setReviewData({
        content: '',
        is_spoiler: false,
        rating: myReview?.user_rating || character?.my_rating || 0
      });
      setIsEditingReview(false); // ?ˆë¡œ ?‘ì„±?˜ëŠ” ê²ƒì´ë¯€ë¡?editing???„ë‹˜
      setShowReviewForm(true);
    } else {
      setReviewData({
        content: myReview.content,
        is_spoiler: myReview.is_spoiler,
        rating: myReview?.user_rating || character?.my_rating || 0
      });
      setIsEditingReview(true);
      setShowReviewForm(true);
    }
  };

  const handleDeleteReview = async () => {
    // ?‰ì ë§??ˆëŠ” ê²½ìš°?€ ë¦¬ë·°ê°€ ?ˆëŠ” ê²½ìš° ?¤ë¥´ê²?ì²˜ë¦¬
    const isRatingOnly = ActivityUtils.isRatingsOnly(myReview);
    const confirmMessage = isRatingOnly
      ? (language === 'ko' ? '?‰ì ???? œ?˜ì‹œê² ìŠµ?ˆê¹Œ?' : language === 'ja' ? '?“ã®è©•ä¾¡?’å‰Š?¤ã—?¾ã™?‹ï¼Ÿ' : 'Are you sure you want to delete this rating?')
      : (language === 'ko' ? 'ë¦¬ë·°ë¥??? œ?˜ì‹œê² ìŠµ?ˆê¹Œ?' : language === 'ja' ? '?“ã®?¬ãƒ“?¥ãƒ¼?’å‰Š?¤ã—?¾ã™?‹ï¼Ÿ' : 'Are you sure you want to delete this review?');

    if (!window.confirm(confirmMessage)) {
      return;
    }

    try {
      if (isRatingOnly) {
        // ?‰ì ë§??ˆëŠ” ê²½ìš° - character rating ?? œ
        await characterService.deleteCharacterRating(id);
        setCharacter({ ...character, my_rating: null });
      } else {
        // ë¦¬ë·°ê°€ ?ˆëŠ” ê²½ìš° - review ?? œ
        await characterReviewService.deleteReview(myReview.id);
      }

      setMyReview(null);
      const successMessage = isRatingOnly
        ? (language === 'ko' ? '?‰ì ???? œ?˜ì—ˆ?µë‹ˆ??' : language === 'ja' ? 'è©•ä¾¡?Œå‰Š?¤ã•?Œã¾?—ãŸ?? : 'Rating deleted successfully.')
        : (language === 'ko' ? 'ë¦¬ë·°ê°€ ?? œ?˜ì—ˆ?µë‹ˆ??' : language === 'ja' ? '?¬ãƒ“?¥ãƒ¼?Œå‰Š?¤ã•?Œã¾?—ãŸ?? : 'Review deleted successfully.');
      setReviewSuccess(successMessage);

      // character statsë§??…ë°?´íŠ¸ (?„ì²´ ë¦¬í”„?ˆì‹œ ?†ì´)
      const charData = await characterService.getCharacterDetail(id);
      if (charData) setCharacter(charData);

      // Refresh activities list
      await refetchActivities();

      setTimeout(() => setReviewSuccess(''), 3000);
    } catch (err) {
      console.error('Failed to delete:', err);
      alert(language === 'ko' ? '?? œ???¤íŒ¨?ˆìŠµ?ˆë‹¤.' : language === 'ja' ? '?Šé™¤?«å¤±?—ã—?¾ã—?Ÿã€? : 'Failed to delete.');
    }
  };

  // Helper function to get review by ID
  const getReviewById = (reviewId) => {
    if (myReview && myReview.id === reviewId) {
      return myReview;
    }
    return reviews.find(r => r.id === reviewId);
  };

  // ?“ê? ê´€???¨ìˆ˜
  const loadComments = async (reviewOrId) => {
    try {
      // review ê°ì²´ê°€ ì§ì ‘ ?„ë‹¬?˜ì—ˆ?”ì?, IDë§??„ë‹¬?˜ì—ˆ?”ì? ?•ì¸
      const review = typeof reviewOrId === 'object' ? reviewOrId : getReviewById(reviewOrId);
      const reviewId = typeof reviewOrId === 'object' ? reviewOrId.id : reviewOrId;

      if (!review) {
        console.error('[CharacterDetail] Review not found:', reviewOrId);
        return;
      }

      console.log('[CharacterDetail] loadComments - review object:', review);
      console.log('[CharacterDetail] loadComments - isRatingsOnly:', ActivityUtils.isRatingsOnly(review));
      console.log('[CharacterDetail] loadComments - activityType:', ActivityUtils.getActivityType(review));

      // ?µí•© ? í‹¸ë¦¬í‹° ?¬ìš©
      const data = await ActivityUtils.loadComments(review);

      console.log('[CharacterDetail] loadComments - data received:', data);
      console.log('[CharacterDetail] loadComments - First comment sample:', data.items?.[0]);

      setComments(prev => ({ ...prev, [reviewId]: data.items || [] }));

      // ê°??“ê???ì¢‹ì•„???íƒœ ë¡œë“œ
      const likes = {};
      (data.items || []).forEach(comment => {
        console.log('[CharacterDetail] loadComments - Processing comment:', {
          id: comment.id,
          user_id: comment.user_id,
          username: comment.username,
          avatar_url: comment.avatar_url,
          content: comment.content?.substring(0, 20)
        });
        likes[comment.id] = {
          liked: comment.user_liked || false,
          count: comment.likes_count || 0
        };
        if (comment.replies) {
          comment.replies.forEach(reply => {
            likes[reply.id] = {
              liked: reply.user_liked || false,
              count: reply.likes_count || 0
            };
          });
        }
      });
      setCommentLikes(prev => ({ ...prev, ...likes }));
    } catch (err) {
      console.error('[CharacterDetail] Failed to load comments:', err);
      console.error('[CharacterDetail] Error details:', err);
    }
  };

  // ë¦¬ë·°???“ê? ?˜ë? ?…ë°?´íŠ¸?˜ëŠ” ?¬í¼ ?¨ìˆ˜
  const updateReviewCommentsCount = (reviewId, delta) => {
    // myReview ?…ë°?´íŠ¸
    if (myReview && myReview.id === reviewId) {
      setMyReview(prev => ({
        ...prev,
        comments_count: Math.max(0, (prev.comments_count || 0) + delta)
      }));
    }

    // reviews ë°°ì—´ ?…ë°?´íŠ¸
    setReviews(prev => prev.map(review =>
      review.id === reviewId
        ? { ...review, comments_count: Math.max(0, (review.comments_count || 0) + delta) }
        : review
    ));
  };

  const handleSubmitComment = async (reviewId) => {
    const content = newComment[reviewId];
    if (!content || !content.trim()) return;

    try {
      const review = getReviewById(reviewId);
      if (!review) {
        console.error('[CharacterDetail] Review not found:', reviewId);
        return;
      }

      console.log('[CharacterDetail] handleSubmitComment - review object:', review);
      console.log('[CharacterDetail] handleSubmitComment - content:', content);
      console.log('[CharacterDetail] handleSubmitComment - isRatingsOnly:', ActivityUtils.isRatingsOnly(review));
      console.log('[CharacterDetail] handleSubmitComment - activityType:', ActivityUtils.getActivityType(review));

      // ?µí•© ? í‹¸ë¦¬í‹° ?¬ìš©
      await ActivityUtils.createComment(review, content);

      console.log('[CharacterDetail] handleSubmitComment - comment created successfully');

      setNewComment(prev => ({ ...prev, [reviewId]: '' }));
      await loadComments(reviewId);
      updateReviewCommentsCount(reviewId, 1);
    } catch (err) {
      console.error('[CharacterDetail] Failed to submit comment:', err);
      console.error('[CharacterDetail] Error details:', err);
      alert(language === 'ko' ? '?“ê? ?‘ì„±???¤íŒ¨?ˆìŠµ?ˆë‹¤.' : language === 'ja' ? '?³ãƒ¡?³ãƒˆä½œæˆ?«å¤±?—ã—?¾ã—?Ÿã€? : 'Failed to submit comment.');
    }
  };

  const handleSubmitReply = async (reviewId, parentCommentId) => {
    const content = replyText[parentCommentId];
    if (!content || !content.trim()) return;

    try {
      const review = getReviewById(reviewId);
      if (!review) {
        console.error('[CharacterDetail] Review not found:', reviewId);
        return;
      }

      // ?µí•© ? í‹¸ë¦¬í‹° ?¬ìš©
      await ActivityUtils.createReply(review, parentCommentId, content);

      setReplyText(prev => ({ ...prev, [parentCommentId]: '' }));
      setReplyingTo(prev => ({ ...prev, [parentCommentId]: false }));
      await loadComments(reviewId);
      updateReviewCommentsCount(reviewId, 1);
    } catch (err) {
      console.error('Failed to submit reply:', err);
      alert(language === 'ko' ? '?µê? ?‘ì„±???¤íŒ¨?ˆìŠµ?ˆë‹¤.' : language === 'ja' ? 'è¿”ä¿¡ä½œæˆ?«å¤±?—ã—?¾ã—?Ÿã€? : 'Failed to submit reply.');
    }
  };

  const handleDeleteComment = async (reviewId, commentId) => {
    if (!window.confirm(language === 'ko' ? '?“ê????? œ?˜ì‹œê² ìŠµ?ˆê¹Œ?' : language === 'ja' ? '?“ã®?³ãƒ¡?³ãƒˆ?’å‰Š?¤ã—?¾ã™?‹ï¼Ÿ' : 'Are you sure you want to delete this comment?')) {
      return;
    }

    try {
      const review = getReviewById(reviewId);
      if (!review) {
        console.error('[CharacterDetail] Review not found:', reviewId);
        return;
      }

      console.log('[CharacterDetail] handleDeleteComment - deleting comment:', commentId, 'from review:', review);

      // ?µí•© ? í‹¸ë¦¬í‹° ?¬ìš©
      await ActivityUtils.deleteComment(review, commentId);

      console.log('[CharacterDetail] handleDeleteComment - comment deleted successfully');

      await loadComments(review);  // review ê°ì²´ ?„ë‹¬
      updateReviewCommentsCount(reviewId, -1);
    } catch (err) {
      console.error('[CharacterDetail] Failed to delete comment:', err);
      console.error('[CharacterDetail] Error details:', err.response?.data || err.message);
      alert(language === 'ko' ? '?“ê? ?? œ???¤íŒ¨?ˆìŠµ?ˆë‹¤.' : language === 'ja' ? '?³ãƒ¡?³ãƒˆ?Šé™¤?«å¤±?—ã—?¾ã—?Ÿã€? : 'Failed to delete comment.');
    }
  };

  const handleToggleCommentLike = async (commentId) => {
    if (!user) {
      alert(language === 'ko' ? 'ë¡œê·¸?¸ì´ ?„ìš”?©ë‹ˆ??' : language === 'ja' ? '??‚°?¤ãƒ³?Œå¿…è¦ã§?™ã€? : 'Please login first.');
      return;
    }

    try {
      // Find which review this comment belongs to
      let reviewId = null;
      let currentComment = null;

      for (const rId of Object.keys(comments)) {
        const allComments = comments[rId] || [];

        // Check main comments
        const mainComment = allComments.find(c => c.id === commentId);
        if (mainComment) {
          reviewId = rId;
          currentComment = mainComment;
          break;
        }

        // Check replies
        for (const comment of allComments) {
          if (comment.replies) {
            const reply = comment.replies.find(r => r.id === commentId);
            if (reply) {
              reviewId = rId;
              currentComment = reply;
              break;
            }
          }
        }
        if (currentComment) break;
      }

      if (!reviewId || !currentComment) return;

      if (currentComment.user_liked) {
        await commentLikeService.unlikeComment(commentId);
      } else {
        await commentLikeService.likeComment(commentId);
      }

      loadComments(reviewId);
    } catch (err) {
      console.error('Failed to toggle comment like:', err);
    }
  };

  const handleReplyClick = (reviewId, commentId) => {
    setReplyingTo(prev => ({
      ...prev,
      [reviewId]: prev[reviewId] === commentId ? null : commentId
    }));
  };

  const toggleComments = (reviewId) => {
    const newExpanded = new Set(expandedComments);
    if (newExpanded.has(reviewId)) {
      newExpanded.delete(reviewId);
    } else {
      newExpanded.add(reviewId);
      // ?“ê????„ì§ ë¡œë“œ?˜ì? ?Šì•˜?¼ë©´ ë¡œë“œ
      if (!comments[reviewId] || comments[reviewId].length === 0) {
        loadComments(reviewId);
      }
    }
    setExpandedComments(newExpanded);
  };

  const handleToggleReviewLike = async (reviewId) => {
    if (!user) {
      alert(language === 'ko' ? 'ë¡œê·¸?¸ì´ ?„ìš”?©ë‹ˆ??' : language === 'ja' ? '??‚°?¤ãƒ³?Œå¿…è¦ã§?™ã€? : 'Please login first.');
      return;
    }

    try {
      const review = getReviewById(reviewId);
      if (!review) {
        console.error('[CharacterDetail] Review not found:', reviewId);
        return;
      }

      // ?„ì¬ ì¢‹ì•„???íƒœ ê°€?¸ì˜¤ê¸?(?†ìœ¼ë©?ê¸°ë³¸ê°?
      const currentLike = reviewLikes[reviewId] || { liked: false, count: 0 };
      const newLiked = !currentLike.liked;

      // Use activityService with activity_id
      const { activityService } = await import('../services/activityService');
      await activityService.toggleLike(reviewId);

      setReviewLikes(prev => ({
        ...prev,
        [reviewId]: {
          liked: newLiked,
          count: currentLike.count + (newLiked ? 1 : -1)
        }
      }));
    } catch (err) {
      console.error('Failed to toggle review like:', err);
    }
  };

  const handleToggleSaveReview = (review) => {
    // Feed?€ ?™ì¼???•ì‹?¼ë¡œ activity key ?ì„± (character_rating ?¬ìš©!)
    const activityKey = `character_rating_${review.user_id}_${id}`;
    console.log('[CharacterDetail] Toggling save for key:', activityKey);
    console.log('[CharacterDetail] Review user_id:', review.user_id, 'Character ID:', id);

    setSavedActivities(prev => {
      const newSet = new Set(prev);
      if (newSet.has(activityKey)) {
        newSet.delete(activityKey);
        console.log('[CharacterDetail] Removed from saved');
      } else {
        newSet.add(activityKey);
        console.log('[CharacterDetail] Added to saved');
      }
      // ë¡œì»¬ ?¤í† ë¦¬ì????€??(?¼ë“œ?€ ?™ê¸°??
      const savedArray = [...newSet];
      localStorage.setItem('savedActivities', JSON.stringify(savedArray));
      console.log('[CharacterDetail] Saved to localStorage:', savedArray);
      return newSet;
    });
  };

  // Using imported getAvatarUrl from imageHelpers

  const toRoman = (num) => {
    const romanNumerals = ['I', 'II', 'III', 'IV', 'V'];
    return romanNumerals[num - 1] || num.toString();
  };

  const getTimeAgo = (dateString) => {
    // SQLite timestampë¥?UTCë¡??Œì‹±
    const date = new Date(dateString.endsWith('Z') ? dateString : dateString + 'Z');
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);

    if (diffInSeconds < 3600) return language === 'ko' ? `${Math.max(1, Math.floor(diffInSeconds / 60))}ë¶??? : language === 'ja' ? `${Math.max(1, Math.floor(diffInSeconds / 60))}?†å‰` : `${Math.max(1, Math.floor(diffInSeconds / 60))}m ago`;
    if (diffInSeconds < 86400) return language === 'ko' ? `${Math.floor(diffInSeconds / 3600)}?œê°„ ?? : language === 'ja' ? `${Math.floor(diffInSeconds / 3600)}?‚é–“?? : `${Math.floor(diffInSeconds / 3600)}h ago`;
    if (diffInSeconds < 2592000) return language === 'ko' ? `${Math.floor(diffInSeconds / 86400)}???? : language === 'ja' ? `${Math.floor(diffInSeconds / 86400)}?¥å‰` : `${Math.floor(diffInSeconds / 86400)}d ago`;
    return date.toLocaleDateString(language === 'ko' ? 'ko-KR' : language === 'ja' ? 'ja-JP' : 'en-US');
  };

  // Use imageHelpers function for consistency with list pages
  // This ensures proper fallback chain: R2 .jpg ??R2 .png ??external URL

  const getCoverUrl = (coverUrl) => {
    if (!coverUrl) return '/placeholder-anime.svg';
    if (coverUrl.startsWith('http')) return coverUrl;
    // Use covers_large for better quality
    const processedUrl = coverUrl.includes('/covers/')
      ? coverUrl.replace('/covers/', '/covers_large/')
      : coverUrl;
    return `${IMAGE_BASE_URL}${processedUrl}`;
  };

  // SVG Star icon component
  const StarIcon = ({ className = "w-6 h-6", filled = true }) => (
    <svg className={className} viewBox="0 0 20 20" fill={filled ? "url(#star-gradient-char)" : "currentColor"}>
      <defs>
        <linearGradient id="star-gradient-char" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style={{ stopColor: '#FFD700', stopOpacity: 1 }} />
          <stop offset="50%" style={{ stopColor: '#FFA500', stopOpacity: 1 }} />
          <stop offset="100%" style={{ stopColor: '#FF8C00', stopOpacity: 1 }} />
        </linearGradient>
      </defs>
      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
    </svg>
  );

  const getBirthday = () => {
    const { date_of_birth_year, date_of_birth_month, date_of_birth_day } = character;
    if (!date_of_birth_month || !date_of_birth_day) return null;

    const parts = [];
    if (date_of_birth_month) parts.push(`${date_of_birth_month}${language === 'ko' ? '?? : language === 'ja' ? '?? : '/'}`);
    if (date_of_birth_day) parts.push(`${date_of_birth_day}${language === 'ko' ? '?? : language === 'ja' ? '?? : ''}`);
    if (date_of_birth_year) parts.unshift(`${date_of_birth_year}${language === 'ko' ? '??' : language === 'ja' ? 'å¹? : '-'}`);

    return parts.join(language === 'ko' ? ' ' : language === 'ja' ? '' : '');
  };

  if (loading) {
    return (
      <div className="min-h-screen pt-10 md:pt-12 bg-transparent">
        <div className="max-w-[1180px] mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8">
          <div className="flex flex-col lg:flex-row gap-8 animate-pulse">
            {/* Character Image Skeleton */}
            <div className="lg:w-80 flex-shrink-0">
              <div className="w-full h-96 bg-gray-200 rounded-xl"></div>
            </div>
            {/* Info Skeleton */}
            <div className="flex-1">
              <div className="h-8 w-3/4 bg-gray-200 rounded mb-4"></div>
              <div className="h-6 w-1/2 bg-gray-200 rounded mb-6"></div>
              <div className="space-y-3 mb-6">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-4 w-full bg-gray-200 rounded"></div>
                ))}
              </div>
              <div className="flex gap-2 mb-6">
                {[1, 2].map((i) => (
                  <div key={i} className="h-10 w-32 bg-gray-200 rounded"></div>
                ))}
              </div>
            </div>
          </div>
          {/* Anime Appearances Skeleton */}
          <div className="mt-8">
            <div className="h-6 w-48 bg-gray-200 rounded mb-4"></div>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="bg-white rounded-lg p-2">
                  <div className="w-full h-48 bg-gray-200 rounded mb-2"></div>
                  <div className="h-4 bg-gray-200 rounded"></div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !character) {
    return (
      <div className="min-h-screen pt-10 md:pt-12 bg-transparent">
        <div className="max-w-[1180px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center py-12">
            <div className="text-xl text-red-600 mb-4">{error || (language === 'ko' ? 'ìºë¦­?°ë? ì°¾ì„ ???†ìŠµ?ˆë‹¤.' : language === 'ja' ? '??ƒ£?©ã‚¯?¿ãƒ¼?Œè¦‹?¤ã‹?Šã¾?›ã‚“?? : 'Character not found.')}</div>
            <button
              onClick={() => navigate(-1)}
              className="text-[#A8E6CF] hover:text-blue-700 font-medium"
            >
              ??{language === 'ko' ? '?¤ë¡œ ê°€ê¸? : language === 'ja' ? '?»ã‚‹' : 'Go Back'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-10 md:pt-12 bg-transparent">

      <div className="max-w-[1180px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Mobile Title - Show first on mobile */}
        <div className="lg:hidden mb-6">
          <div className="bg-white rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] p-6">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {language === 'ko' && character.name_korean ? character.name_korean : character.name_full}
            </h1>
            {language === 'ko' && character.name_korean ? (
              <p className="text-xl text-gray-600">{character.name_full}</p>
            ) : (
              character.name_native && character.name_native !== character.name_full && (
                <p className="text-xl text-gray-600">{character.name_native}</p>
              )
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column: Image and Rating Widget */}
          <div className="lg:col-span-1 space-y-6">
            {/* Character Image */}
            <div className="bg-white rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] overflow-hidden">
              <img
                src={getCharacterImageUrl(character.id, character.image_url)}
                alt={character.name_full}
                className="w-full"
                onError={(e) => {
                  // Fallback chain: R2 .jpg ??R2 .png ??external URL ??placeholder
                  if (!e.target.dataset.fallbackAttempt) {
                    e.target.dataset.fallbackAttempt = '1';
                    // Try .png if .jpg failed
                    e.target.src = `${IMAGE_BASE_URL}/images/characters/${character.id}.png`;
                  } else if (e.target.dataset.fallbackAttempt === '1') {
                    e.target.dataset.fallbackAttempt = '2';
                    // Try external URL
                    const fallbackUrl = getCharacterImageFallback(character.image_url);
                    if (fallbackUrl !== '/placeholder-anime.svg') {
                      e.target.src = fallbackUrl;
                    } else {
                      e.target.src = '/placeholder-anime.svg';
                    }
                  } else {
                    e.target.src = '/placeholder-anime.svg';
                  }
                }}
              />
            </div>

            {/* Rating Widget */}
            <CharacterRatingWidget
              characterId={id}
              currentRating={{
                rating: character.my_rating,
                status: character.my_status,
                created_at: character.rating_created_at
              }}
              onRate={handleRatingChange}
              onStatusChange={handleStatusChange}
            />
          </div>

          {/* Right Column: Details and Reviews */}
          <div className="lg:col-span-2 space-y-6">
            {/* Character Info - Desktop only */}
            <div className="hidden lg:block bg-white rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] p-6">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                {language === 'ko' && character.name_korean ? character.name_korean : character.name_full}
              </h1>
              {language === 'ko' && character.name_korean ? (
                <p className="text-xl text-gray-600 mb-4">{character.name_full}</p>
              ) : (
                character.name_native && character.name_native !== character.name_full && (
                  <p className="text-xl text-gray-600 mb-4">{character.name_native}</p>
                )
              )}

              {/* Community Rating */}
              <div className="mb-6 flex gap-8 items-center justify-center">
                {/* ?¼ìª½: ì¢…í•© ?‰ì  */}
                <div className="flex flex-col items-center">
                  <div className="text-sm font-medium text-gray-600 mb-3">
                    {language === 'ko' ? 'ì¢…í•© ?‰ì ' : language === 'ja' ? 'ç·åˆè©•ä¾¡' : 'Overall Rating'}
                  </div>
                  <div className="flex items-center gap-3">
                    <StarIcon className={`w-14 h-14 ${character.site_rating_count > 0 ? '' : 'text-gray-300'}`} filled={character.site_rating_count > 0} />
                    <div>
                      <div className="text-5xl font-bold">
                        {character.site_rating_count > 0 ? character.site_average_rating?.toFixed(1) : '--'}
                      </div>
                      <div className="text-base text-gray-600 mt-1">
                        {character.site_rating_count > 0
                          ? (language === 'ko' ? `${character.site_rating_count}ëª??‰ê?` : language === 'ja' ? `${character.site_rating_count}ä»¶ã®è©•ä¾¡` : `${character.site_rating_count} ratings`)
                          : (language === 'ko' ? '?„ì§ ?‰ê? ?†ìŒ' : language === 'ja' ? '?¾ã è©•ä¾¡?Œã‚?Šã¾?›ã‚“' : 'No ratings yet')
                        }
                      </div>
                    </div>
                  </div>
                </div>

                {/* ?¤ë¥¸ìª? ë³„ì  ?ˆìŠ¤? ê·¸??(ì»´íŒ©?? */}
                <div className="flex-1 max-w-md space-y-0.5">
                  {[5, 4.5, 4, 3.5, 3, 2.5, 2, 1.5, 1, 0.5].map((star) => {
                    const dist = character.site_rating_distribution?.find(d => d.rating === star);
                    const count = dist ? dist.count : 0;
                    const percentage = character.site_rating_count > 0 ? (count / character.site_rating_count) * 100 : 0;

                    return (
                      <div key={star} className="flex items-center gap-1.5 text-xs">
                        <span className={`w-12 text-right font-medium flex items-center justify-end gap-0.5 ${character.site_rating_count > 0 ? '' : 'text-gray-400'}`}>
                          <StarIcon className="w-3 h-3" filled={character.site_rating_count > 0} />
                          <span>{star.toFixed(1)}</span>
                        </span>
                        <div className="flex-1 bg-gray-200 rounded-full h-2 overflow-hidden">
                          <div
                            className={`h-2 rounded-full transition-all duration-500 ${character.site_rating_count > 0 ? 'bg-yellow-500' : 'bg-gray-300'}`}
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                        <span className="text-gray-600 w-8 text-right text-[10px]">
                          {percentage > 0 ? `${percentage.toFixed(0)}%` : ''}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Character Details */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                {character.gender && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '?±ë³„:' : language === 'ja' ? '?§åˆ¥:' : 'Gender:'}</span> {character.gender === 'Male' ? (language === 'ko' ? '?¨ì„±' : language === 'ja' ? '?·æ€? : 'Male') : character.gender === 'Female' ? (language === 'ko' ? '?¬ì„±' : language === 'ja' ? 'å¥³æ€? : 'Female') : character.gender}
                  </div>
                )}

                {getBirthday() && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '?ì¼:' : language === 'ja' ? 'èª•ç”Ÿ??' : 'Birthday:'}</span> {getBirthday()}
                  </div>
                )}

                {character.age && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '?˜ì´:' : language === 'ja' ? 'å¹´é½¢:' : 'Age:'}</span> {character.age}
                  </div>
                )}

                {character.blood_type && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '?ˆì•¡??' : language === 'ja' ? 'è¡€æ¶²å‹:' : 'Blood Type:'}</span> {character.blood_type}
                  </div>
                )}
              </div>

              {/* Description */}
              {character.description && (
                <div className="mt-6">
                  <h3 className="text-xl font-bold mb-4">
                    {language === 'ko' ? '?¤ëª…' : language === 'ja' ? 'èª¬æ˜' : 'Description'}
                  </h3>
                  <p className="text-gray-700 whitespace-pre-wrap">{character.description}</p>
                </div>
              )}
            </div>

            {/* Character Info - Mobile only (without title) */}
            <div className="lg:hidden bg-white rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] p-6">
              {/* Community Rating */}
              <div className="mb-6 flex gap-8 items-center justify-center">
                {/* ?¼ìª½: ì¢…í•© ?‰ì  */}
                <div className="flex flex-col items-center">
                  <div className="text-sm font-medium text-gray-600 mb-3">
                    {language === 'ko' ? 'ì¢…í•© ?‰ì ' : language === 'ja' ? 'ç·åˆè©•ä¾¡' : 'Overall Rating'}
                  </div>
                  <div className="flex items-center gap-3">
                    <StarIcon className={`w-14 h-14 ${character.site_rating_count > 0 ? '' : 'text-gray-300'}`} filled={character.site_rating_count > 0} />
                    <div>
                      <div className="text-5xl font-bold">
                        {character.site_rating_count > 0 ? character.site_average_rating?.toFixed(1) : '--'}
                      </div>
                      <div className="text-base text-gray-600 mt-1">
                        {character.site_rating_count > 0
                          ? (language === 'ko' ? `${character.site_rating_count}ëª??‰ê?` : language === 'ja' ? `${character.site_rating_count}ä»¶ã®è©•ä¾¡` : `${character.site_rating_count} ratings`)
                          : (language === 'ko' ? '?„ì§ ?‰ê? ?†ìŒ' : language === 'ja' ? '?¾ã è©•ä¾¡?Œã‚?Šã¾?›ã‚“' : 'No ratings yet')
                        }
                      </div>
                    </div>
                  </div>
                </div>

                {/* ?¤ë¥¸ìª? ë³„ì  ?ˆìŠ¤? ê·¸??(ì»´íŒ©?? */}
                <div className="flex-1 max-w-md space-y-0.5">
                  {[5, 4.5, 4, 3.5, 3, 2.5, 2, 1.5, 1, 0.5].map((star) => {
                    const dist = character.site_rating_distribution?.find(d => d.rating === star);
                    const count = dist ? dist.count : 0;
                    const percentage = character.site_rating_count > 0 ? (count / character.site_rating_count) * 100 : 0;

                    return (
                      <div key={star} className="flex items-center gap-1.5 text-xs">
                        <span className={`w-12 text-right font-medium flex items-center justify-end gap-0.5 ${character.site_rating_count > 0 ? '' : 'text-gray-400'}`}>
                          <StarIcon className="w-3 h-3" filled={character.site_rating_count > 0} />
                          <span>{star.toFixed(1)}</span>
                        </span>
                        <div className="flex-1 bg-gray-200 rounded-full h-2 overflow-hidden">
                          <div
                            className={`h-2 rounded-full transition-all duration-500 ${character.site_rating_count > 0 ? 'bg-yellow-500' : 'bg-gray-300'}`}
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                        <span className="text-gray-600 w-8 text-right text-[10px]">
                          {percentage > 0 ? `${percentage.toFixed(0)}%` : ''}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Character Details */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                {character.gender && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '?±ë³„:' : language === 'ja' ? '?§åˆ¥:' : 'Gender:'}</span> {character.gender === 'Male' ? (language === 'ko' ? '?¨ì„±' : language === 'ja' ? '?·æ€? : 'Male') : character.gender === 'Female' ? (language === 'ko' ? '?¬ì„±' : language === 'ja' ? 'å¥³æ€? : 'Female') : character.gender}
                  </div>
                )}
                {character.age && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '?˜ì´:' : language === 'ja' ? 'å¹´é½¢:' : 'Age:'}</span> {character.age}
                  </div>
                )}
                {character.date_of_birth && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '?ì¼:' : 'Birthday:'}</span> {character.date_of_birth}
                  </div>
                )}
                {character.blood_type && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '?ˆì•¡??' : language === 'ja' ? 'è¡€æ¶²å‹:' : 'Blood Type:'}</span> {character.blood_type}
                  </div>
                )}
                {character.favourites && character.favourites > 0 && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? 'ì¢‹ì•„??' : 'Favorites:'}</span> {character.favourites.toLocaleString()}
                  </div>
                )}
              </div>

              {/* Description */}
              {character.description && (
                <div className="mt-6">
                  <h3 className="text-xl font-bold mb-4">
                    {language === 'ko' ? '?¤ëª…' : language === 'ja' ? 'èª¬æ˜' : 'Description'}
                  </h3>
                  <p className="text-gray-700 whitespace-pre-wrap">{character.description}</p>
                </div>
              )}
            </div>

            {/* Anime Appearances */}
            <div className="bg-white rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] p-6">
              <h3 className="text-xl font-bold mb-4">
                {language === 'ko' ? 'ì¶œì—° ?‘í’ˆ' : language === 'ja' ? '?ºæ¼”ä½œå“' : 'Appearances'}
              </h3>

              {character.anime && character.anime.length > 0 ? (
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {character.anime.map((anime) => (
                    <Link
                      key={anime.anime_id}
                      to={`/anime/${anime.anime_id}`}
                      className="group"
                    >
                      <div className="bg-gray-100 rounded-lg overflow-hidden hover:shadow-[0_2px_12px_rgba(0,0,0,0.08)] transition-all duration-300">
                        <div className="aspect-[2/3] bg-gray-200 relative">
                          <img
                            src={getCoverUrl(anime.cover_image)}
                            alt={getAnimeTitle(anime)}
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                            onError={(e) => {
                              e.target.src = '/placeholder-anime.svg';
                            }}
                          />
                          {/* Role Badge */}
                          <div className={`absolute top-2 left-2 px-2 py-1 rounded text-xs font-bold ${anime.role === 'MAIN'
                              ? 'bg-red-500 text-white'
                              : 'bg-blue-500 text-white'
                            }`}>
                            {anime.role === 'MAIN' ? (language === 'ko' ? 'ë©”ì¸' : language === 'ja' ? '?¡ã‚¤?? : 'Main') : (language === 'ko' ? '?œë¸Œ' : language === 'ja' ? '?µãƒ?¼ãƒˆ' : 'Supporting')}
                          </div>
                          {/* My Rating Badge */}
                          {anime.my_anime_rating && (
                            <div className="absolute top-2 right-2 bg-yellow-400 text-gray-900 px-2 py-1 rounded text-xs font-bold flex items-center gap-0.5">
                              <StarIcon className="w-3 h-3" filled={true} />
                              <span>{anime.my_anime_rating.toFixed(1)}</span>
                            </div>
                          )}
                        </div>
                        <div className="p-2">
                          <h4 className="font-medium text-sm line-clamp-2 group-hover:text-[#00E5FF] transition-colors">
                            {getAnimeTitle(anime)}
                          </h4>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <p className="text-gray-600">
                  {language === 'ko' ? 'ì¶œì—° ?‘í’ˆ???†ìŠµ?ˆë‹¤.' : language === 'ja' ? '?ºæ¼”ä½œå“?Œè¦‹?¤ã‹?Šã¾?›ã‚“?? : 'No anime appearances found.'}
                </p>
              )}
            </div>

            {/* Reviews Section */}
            <div className="bg-white rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-bold">
                  {language === 'ko' ? 'ë¦¬ë·°' : language === 'ja' ? '?¬ãƒ“?¥ãƒ¼' : 'Reviews'} ({activities.length})
                </h3>
                {!myReview && (
                  <button
                    onClick={() => {
                      if (!showReviewForm) {
                        setReviewData({
                          content: '',
                          is_spoiler: false,
                          rating: character.my_rating || 0
                        });
                        setIsEditingReview(false);
                      }
                      setShowReviewForm(!showReviewForm);
                    }}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                  >
                    {showReviewForm
                      ? (language === 'ko' ? 'ì·¨ì†Œ' : language === 'ja' ? '??ƒ£?³ã‚»?? : 'Cancel')
                      : (language === 'ko' ? 'ë¦¬ë·° ?‘ì„±' : language === 'ja' ? '?¬ãƒ“?¥ãƒ¼ä½œæˆ' : 'Write Review')
                    }
                  </button>
                )}
              </div>

              {/* Review Form */}
              {showReviewForm && (
                <form onSubmit={handleSubmitReview} className="mb-6 p-4 bg-gray-50 rounded-lg">
                  {reviewError && (
                    <div className="mb-4 p-3 bg-red-100 border border-red-300 text-red-800 rounded-md text-sm">
                      {reviewError}
                    </div>
                  )}

                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      {language === 'ko' ? 'ë³„ì ' : language === 'ja' ? 'è©•ä¾¡' : 'Rating'} *
                    </label>
                    <div className="flex items-center gap-4">
                      <StarRating
                        rating={reviewData.rating}
                        onRatingChange={(rating) => setReviewData({ ...reviewData, rating })}
                        size="xl"
                        showNumber={false}
                      />
                      {reviewData.rating > 0 && (
                        <span className="text-2xl font-bold text-gray-700">{reviewData.rating.toFixed(1)}</span>
                      )}
                    </div>
                  </div>

                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {language === 'ko' ? 'ë¦¬ë·° ?´ìš©' : language === 'ja' ? '?¬ãƒ“?¥ãƒ¼?…å?' : 'Review Content'} *
                    </label>
                    <textarea
                      value={reviewData.content}
                      onChange={(e) => setReviewData({ ...reviewData, content: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md h-32"
                      placeholder={language === 'ko' ? '??ìºë¦­?°ì— ?€???¹ì‹ ???ê°??ê³µìœ ?´ì£¼?¸ìš”...' : language === 'ja' ? '?“ã®??ƒ£?©ã‚¯?¿ãƒ¼?«ã¤?„ã¦??‚?ªãŸ??„Ÿ?³ã‚’?·ã‚§?¢ã—?¦ã? ã•??..' : 'Share your thoughts about this character...'}
                      required
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      {reviewData.content.length} / 5000 {language === 'ko' ? '?? : language === 'ja' ? '?‡å­—' : 'characters'}
                    </p>
                  </div>

                  <div className="mb-4">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={reviewData.is_spoiler}
                        onChange={(e) => setReviewData({ ...reviewData, is_spoiler: e.target.checked })}
                        className="mr-2"
                      />
                      <span className="text-sm text-gray-700">
                        {language === 'ko' ? '?¤í¬?¼ëŸ¬ ?¬í•¨' : language === 'ja' ? '?ã‚¿?ãƒ¬?’å«?€' : 'Contains spoilers'}
                      </span>
                    </label>
                  </div>

                  <button
                    type="submit"
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                  >
                    {isEditingReview
                      ? (language === 'ko' ? 'ë¦¬ë·° ?˜ì •' : language === 'ja' ? '?¬ãƒ“?¥ãƒ¼ç·¨é›†' : 'Update Review')
                      : (language === 'ko' ? 'ë¦¬ë·° ?±ë¡' : language === 'ja' ? '?¬ãƒ“?¥ãƒ¼ä½œæˆ' : 'Submit Review')
                    }
                  </button>
                </form>
              )}

              {reviewSuccess && (
                <div className="mb-4 p-3 bg-green-100 border border-green-300 text-green-800 rounded-md text-sm">
                  {reviewSuccess}
                </div>
              )}

              {/* Reviews */}
              {activities.length > 0 ? (
                <div className="space-y-4">
                  {activities.map((activity) => {
                    // Hide the activity card if it's the user's review and the review form is open for editing
                    const isMyActivity = user && activity.user_id === user.id;
                    const hideWhileEditing = isMyActivity && showReviewForm && isEditingReview;

                    if (hideWhileEditing) {
                      return null;
                    }

                    return (
                      <ActivityCard
                        key={activity.id}
                        activity={activity}
                        context="character_page"
                        onUpdate={refetchActivities}
                        onEditContent={(activity, mode) => {
                          // Only allow editing own content
                          if (user && activity.user_id === user.id) {
                            if (mode === 'add_review' || !myReview || !myReview.content) {
                              // Open review form for adding review
                              setReviewData({
                                content: '',
                                is_spoiler: false,
                                rating: character?.my_rating || 0
                              });
                              setIsEditingReview(false);
                              setShowReviewForm(true);
                            } else {
                              // Open review form for editing
                              handleEditReview();
                            }
                          }
                        }}
                        onDeleteContent={async (activity) => {
                          // Only allow deleting own content
                          if (user && activity.user_id === user.id) {
                            await handleDeleteReview();
                          }
                        }}
                      />
                    );
                  })}
                </div>
              ) : (
                <p className="text-gray-600">{language === 'ko' ? '?„ì§ ë¦¬ë·°ê°€ ?†ìŠµ?ˆë‹¤.' : language === 'ja' ? '?¾ã ?¬ãƒ“?¥ãƒ¼?Œã‚?Šã¾?›ã‚“?? : 'No reviews yet.'}</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
