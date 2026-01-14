import { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { characterService } from '../services/characterService';
import { characterReviewService } from '../services/characterReviewService';
import { activityService } from '../services/activityService';
import { useActivities } from '../hooks/useActivity';
import { useLanguage } from '../context/LanguageContext';
import { useAuth } from '../context/AuthContext';
import { getCurrentLevelInfo } from '../utils/otakuLevels';
import * as ActivityUtils from '../utils/activityUtils';
import Navbar from '../components/common/Navbar';
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
      // 병렬로 모든 데이터 로드
      const promises = [
        characterService.getCharacterDetail(id),
        characterReviewService.getCharacterReviews(id, { page: 1, page_size: 10 })
      ];

      if (user) {
        promises.push(characterReviewService.getMyReview(id));
      }

      const results = await Promise.all(promises.map(p => p.catch(e => null)));

      // 캐릭터 상세 정보
      if (results[0]) {
        setCharacter(results[0]);
        setError(null);
      } else {
        setError(language === 'ko' ? '캐릭터 정보를 불러오지 못했습니다.' : 'Failed to load character.');
      }

      // 리뷰 목록
      if (results[1]) {
        processReviews(results[1]);
      }

      // 내 리뷰
      if (user && results[2]) {
        processMyReview(results[2]);
      }
    } catch (err) {
      console.error('Failed to load character data:', err);
      setError(language === 'ko' ? '데이터를 불러오지 못했습니다.' : 'Failed to load data.');
    } finally {
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
    // 내 리뷰는 myReview로 따로 표시하므로, reviews에서는 제외
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

      // 댓글이 있으면 자동으로 펼치기
      if (review.comments_count > 0) {
        newExpandedSet.add(review.id);
        commentsToLoad.push(review);
      }
    });

    setReviewLikes(prev => ({ ...prev, ...likesData }));
    setComments(prev => ({ ...prev, ...newComments }));
    setExpandedComments(prev => new Set([...prev, ...newExpandedSet]));

    // 댓글 병렬 로드
    if (commentsToLoad.length > 0) {
      Promise.all(commentsToLoad.map(review => loadComments(review)));
    }
  };

  const processMyReview = (data) => {
    setMyReview(data);

    // 좋아요 상태 설정
    if (data) {
      setReviewLikes(prev => ({
        ...prev,
        [data.id]: {
          liked: data.user_liked || false,
          count: data.likes_count || 0
        }
      }));

      // 내 리뷰에 댓글이 있으면 자동으로 펼치고 로드
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
        // 평점 입력 후 내 리뷰 섹션에 바로 표시
        const myReviewData = await characterReviewService.getMyReview(id).catch(() => null);
        if (myReviewData) processMyReview(myReviewData);
      }

      // 병렬로 데이터 새로고침 (BUT preserve the locally updated my_rating)
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
      alert(language === 'ko' ? '평가를 저장하는데 실패했습니다.' : 'Failed to save rating.');
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
      alert(language === 'ko' ? '상태 변경에 실패했습니다.' : 'Failed to change status.');
    }
  };

  const handleSubmitReview = async (e) => {
    e.preventDefault();
    setReviewError('');
    setReviewSuccess('');

    if (reviewData.rating === 0 || !reviewData.rating) {
      setReviewError(language === 'ko' ? '별점을 선택해주세요.' : 'Please select a rating.');
      return;
    }

    if (!reviewData.content.trim()) {
      setReviewError(language === 'ko' ? '리뷰 내용을 입력해주세요.' : 'Please enter review content.');
      return;
    }

    if (reviewData.content.trim().length < 10) {
      setReviewError(language === 'ko' ? '리뷰는 최소 10자 이상 작성해주세요.' : 'Review must be at least 10 characters.');
      return;
    }

    try {
      if (isEditingReview && myReview && myReview.review_id) {
        // 수정 시: 별점은 별도로 저장하고 리뷰만 수정
        if (!character.my_rating || character.my_rating !== reviewData.rating) {
          await characterService.rateCharacter(parseInt(id), reviewData.rating);
          setCharacter({ ...character, my_rating: reviewData.rating });
        }

        await characterReviewService.updateReview(myReview.review_id, {
          content: reviewData.content,
          is_spoiler: reviewData.is_spoiler
        });
        setReviewSuccess(language === 'ko' ? '리뷰가 수정되었습니다.' : 'Review updated successfully.');
      } else {
        // 새로 작성: 별점과 리뷰를 한 번에 전송
        await characterReviewService.createReview({
          character_id: parseInt(id),
          content: reviewData.content,
          is_spoiler: reviewData.is_spoiler,
          rating: reviewData.rating  // 별점을 리뷰 API에 함께 전송
        });

        // 리뷰 생성 후 캐릭터 데이터 새로고침하여 별점 상태 반영
        setCharacter({ ...character, my_rating: reviewData.rating });

        setReviewSuccess(language === 'ko' ? '리뷰가 작성되었습니다.' : 'Review submitted successfully.');
      }

      setReviewData({ content: '', is_spoiler: false, rating: 0 });
      setShowReviewForm(false);
      setIsEditingReview(false);

      // 로컬 state만 업데이트 (전체 리프레시 없이)
      if (isEditingReview) {
        // 리뷰 수정: myReview 업데이트만
        const updatedMyReview = await characterReviewService.getMyReview(id).catch(() => null);
        if (updatedMyReview) {
          setMyReview(updatedMyReview);
        }
      } else {
        // 새 리뷰 작성: myReview와 character stats만 업데이트
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
          ? err.response?.data?.detail || '리뷰 작성에 실패했습니다.'
          : err.response?.data?.detail || 'Failed to submit review.'
      );
    }
  };

  const handleEditReview = () => {
    // 평점만 있는 경우 리뷰 작성 폼을 열어줌
    if (ActivityUtils.isRatingsOnly(myReview)) {
      setReviewData({
        content: '',
        is_spoiler: false,
        rating: character.my_rating || 0
      });
      setIsEditingReview(false); // 새로 작성하는 것이므로 editing이 아님
      setShowReviewForm(true);
    } else {
      setReviewData({
        content: myReview.content,
        is_spoiler: myReview.is_spoiler,
        rating: character.my_rating || 0
      });
      setIsEditingReview(true);
      setShowReviewForm(true);
    }
  };

  const handleDeleteReview = async () => {
    // 평점만 있는 경우와 리뷰가 있는 경우 다르게 처리
    const isRatingOnly = ActivityUtils.isRatingsOnly(myReview);
    const confirmMessage = isRatingOnly
      ? (language === 'ko' ? '평점을 삭제하시겠습니까?' : 'Are you sure you want to delete this rating?')
      : (language === 'ko' ? '리뷰를 삭제하시겠습니까?' : 'Are you sure you want to delete this review?');

    if (!window.confirm(confirmMessage)) {
      return;
    }

    try {
      if (isRatingOnly) {
        // 평점만 있는 경우 - character rating 삭제
        await characterService.deleteCharacterRating(id);
        setCharacter({ ...character, my_rating: null });
      } else {
        // 리뷰가 있는 경우 - review 삭제
        await characterReviewService.deleteReview(myReview.id);
      }

      setMyReview(null);
      const successMessage = isRatingOnly
        ? (language === 'ko' ? '평점이 삭제되었습니다.' : 'Rating deleted successfully.')
        : (language === 'ko' ? '리뷰가 삭제되었습니다.' : 'Review deleted successfully.');
      setReviewSuccess(successMessage);

      // character stats만 업데이트 (전체 리프레시 없이)
      const charData = await characterService.getCharacterDetail(id);
      if (charData) setCharacter(charData);

      // Refresh activities list
      await refetchActivities();

      setTimeout(() => setReviewSuccess(''), 3000);
    } catch (err) {
      console.error('Failed to delete:', err);
      alert(language === 'ko' ? '삭제에 실패했습니다.' : 'Failed to delete.');
    }
  };

  // Helper function to get review by ID
  const getReviewById = (reviewId) => {
    if (myReview && myReview.id === reviewId) {
      return myReview;
    }
    return reviews.find(r => r.id === reviewId);
  };

  // 댓글 관련 함수
  const loadComments = async (reviewOrId) => {
    try {
      // review 객체가 직접 전달되었는지, ID만 전달되었는지 확인
      const review = typeof reviewOrId === 'object' ? reviewOrId : getReviewById(reviewOrId);
      const reviewId = typeof reviewOrId === 'object' ? reviewOrId.id : reviewOrId;

      if (!review) {
        console.error('[CharacterDetail] Review not found:', reviewOrId);
        return;
      }

      console.log('[CharacterDetail] loadComments - review object:', review);
      console.log('[CharacterDetail] loadComments - isRatingsOnly:', ActivityUtils.isRatingsOnly(review));
      console.log('[CharacterDetail] loadComments - activityType:', ActivityUtils.getActivityType(review));

      // 통합 유틸리티 사용
      const data = await ActivityUtils.loadComments(review);

      console.log('[CharacterDetail] loadComments - data received:', data);
      console.log('[CharacterDetail] loadComments - First comment sample:', data.items?.[0]);

      setComments(prev => ({ ...prev, [reviewId]: data.items || [] }));

      // 각 댓글의 좋아요 상태 로드
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

  // 리뷰의 댓글 수를 업데이트하는 헬퍼 함수
  const updateReviewCommentsCount = (reviewId, delta) => {
    // myReview 업데이트
    if (myReview && myReview.id === reviewId) {
      setMyReview(prev => ({
        ...prev,
        comments_count: Math.max(0, (prev.comments_count || 0) + delta)
      }));
    }

    // reviews 배열 업데이트
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

      // 통합 유틸리티 사용
      await ActivityUtils.createComment(review, content);

      console.log('[CharacterDetail] handleSubmitComment - comment created successfully');

      setNewComment(prev => ({ ...prev, [reviewId]: '' }));
      await loadComments(reviewId);
      updateReviewCommentsCount(reviewId, 1);
    } catch (err) {
      console.error('[CharacterDetail] Failed to submit comment:', err);
      console.error('[CharacterDetail] Error details:', err);
      alert(language === 'ko' ? '댓글 작성에 실패했습니다.' : 'Failed to submit comment.');
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

      // 통합 유틸리티 사용
      await ActivityUtils.createReply(review, parentCommentId, content);

      setReplyText(prev => ({ ...prev, [parentCommentId]: '' }));
      setReplyingTo(prev => ({ ...prev, [parentCommentId]: false }));
      await loadComments(reviewId);
      updateReviewCommentsCount(reviewId, 1);
    } catch (err) {
      console.error('Failed to submit reply:', err);
      alert(language === 'ko' ? '답글 작성에 실패했습니다.' : 'Failed to submit reply.');
    }
  };

  const handleDeleteComment = async (reviewId, commentId) => {
    if (!window.confirm(language === 'ko' ? '댓글을 삭제하시겠습니까?' : 'Are you sure you want to delete this comment?')) {
      return;
    }

    try {
      const review = getReviewById(reviewId);
      if (!review) {
        console.error('[CharacterDetail] Review not found:', reviewId);
        return;
      }

      console.log('[CharacterDetail] handleDeleteComment - deleting comment:', commentId, 'from review:', review);

      // 통합 유틸리티 사용
      await ActivityUtils.deleteComment(review, commentId);

      console.log('[CharacterDetail] handleDeleteComment - comment deleted successfully');

      await loadComments(review);  // review 객체 전달
      updateReviewCommentsCount(reviewId, -1);
    } catch (err) {
      console.error('[CharacterDetail] Failed to delete comment:', err);
      console.error('[CharacterDetail] Error details:', err.response?.data || err.message);
      alert(language === 'ko' ? '댓글 삭제에 실패했습니다.' : 'Failed to delete comment.');
    }
  };

  const handleToggleCommentLike = async (commentId) => {
    if (!user) {
      alert(language === 'ko' ? '로그인이 필요합니다.' : 'Please login first.');
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
      // 댓글이 아직 로드되지 않았으면 로드
      if (!comments[reviewId] || comments[reviewId].length === 0) {
        loadComments(reviewId);
      }
    }
    setExpandedComments(newExpanded);
  };

  const handleToggleReviewLike = async (reviewId) => {
    if (!user) {
      alert(language === 'ko' ? '로그인이 필요합니다.' : 'Please login first.');
      return;
    }

    try {
      const review = getReviewById(reviewId);
      if (!review) {
        console.error('[CharacterDetail] Review not found:', reviewId);
        return;
      }

      // 현재 좋아요 상태 가져오기 (없으면 기본값)
      const currentLike = reviewLikes[reviewId] || { liked: false, count: 0 };
      const newLiked = !currentLike.liked;

      // Always use activityLikeService for consistency
      const activityType = 'character_rating';
      const userId = review.user_id;
      const itemId = review.character_id;

      await import('../services/activityLikeService').then(module =>
        module.activityLikeService.toggleLike(activityType, userId, itemId)
      );

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
    // Feed와 동일한 형식으로 activity key 생성 (character_rating 사용!)
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
      // 로컬 스토리지에 저장 (피드와 동기화)
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
    // SQLite timestamp를 UTC로 파싱
    const date = new Date(dateString.endsWith('Z') ? dateString : dateString + 'Z');
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);

    if (diffInSeconds < 3600) return language === 'ko' ? `${Math.max(1, Math.floor(diffInSeconds / 60))}분 전` : `${Math.max(1, Math.floor(diffInSeconds / 60))}m ago`;
    if (diffInSeconds < 86400) return language === 'ko' ? `${Math.floor(diffInSeconds / 3600)}시간 전` : `${Math.floor(diffInSeconds / 3600)}h ago`;
    if (diffInSeconds < 2592000) return language === 'ko' ? `${Math.floor(diffInSeconds / 86400)}일 전` : `${Math.floor(diffInSeconds / 86400)}d ago`;
    return date.toLocaleDateString(language === 'ko' ? 'ko-KR' : 'en-US');
  };

  // Use imageHelpers function for consistency with list pages
  // This ensures proper fallback chain: R2 .jpg → R2 .png → external URL

  const getCoverUrl = (coverUrl) => {
    if (!coverUrl) return '/placeholder-anime.svg';
    if (coverUrl.startsWith('http')) return coverUrl;
    // Use covers_large for better quality
    const processedUrl = coverUrl.includes('/covers/')
      ? coverUrl.replace('/covers/', '/covers_large/')
      : coverUrl;
    return `${IMAGE_BASE_URL}${processedUrl}`;
  };

  const getBirthday = () => {
    const { date_of_birth_year, date_of_birth_month, date_of_birth_day } = character;
    if (!date_of_birth_month || !date_of_birth_day) return null;

    const parts = [];
    if (date_of_birth_month) parts.push(`${date_of_birth_month}${language === 'ko' ? '월' : '/'}`);
    if (date_of_birth_day) parts.push(`${date_of_birth_day}${language === 'ko' ? '일' : ''}`);
    if (date_of_birth_year) parts.unshift(`${date_of_birth_year}${language === 'ko' ? '년 ' : '-'}`);

    return parts.join(language === 'ko' ? ' ' : '');
  };

  if (loading) {
    return (
      <div className="min-h-screen pt-0 md:pt-16 bg-transparent">
        <Navbar />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8">
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
      <div className="min-h-screen pt-0 md:pt-16 bg-transparent">
        <Navbar />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center py-12">
            <div className="text-xl text-red-600 mb-4">{error || (language === 'ko' ? '캐릭터를 찾을 수 없습니다.' : 'Character not found.')}</div>
            <button
              onClick={() => navigate(-1)}
              className="text-[#A8E6CF] hover:text-blue-700 font-medium"
            >
              ← {language === 'ko' ? '뒤로 가기' : 'Go Back'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-0 md:pt-16 bg-transparent">
      <Navbar />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Mobile Title - Show first on mobile */}
        <div className="lg:hidden mb-6">
          <div className="bg-white rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] p-6">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {character.name_full}
            </h1>
            {character.name_native && character.name_native !== character.name_full && (
              <p className="text-xl text-gray-600">{character.name_native}</p>
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
                  // Fallback chain: R2 .jpg → R2 .png → external URL → placeholder
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
                {character.name_full}
              </h1>
              {character.name_native && character.name_native !== character.name_full && (
                <p className="text-xl text-gray-600 mb-4">{character.name_native}</p>
              )}

              {/* Community Rating */}
              <div className="mb-6 flex gap-8 items-center justify-center">
                {/* 왼쪽: 종합 평점 */}
                <div className="flex flex-col items-center">
                  <div className="text-sm font-medium text-gray-600 mb-3">
                    {language === 'ko' ? '종합 평점' : 'Overall Rating'}
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`text-6xl ${character.site_rating_count > 0 ? 'text-yellow-500' : 'text-gray-300'}`}>★</span>
                    <div>
                      <div className="text-5xl font-bold">
                        {character.site_rating_count > 0 ? character.site_average_rating?.toFixed(1) : '--'}
                      </div>
                      <div className="text-base text-gray-600 mt-1">
                        {character.site_rating_count > 0
                          ? (language === 'ko' ? `${character.site_rating_count}명 평가` : `${character.site_rating_count} ratings`)
                          : (language === 'ko' ? '아직 평가 없음' : 'No ratings yet')
                        }
                      </div>
                    </div>
                  </div>
                </div>

                {/* 오른쪽: 별점 히스토그램 (컴팩트) */}
                <div className="flex-1 max-w-md space-y-0.5">
                  {[5, 4.5, 4, 3.5, 3, 2.5, 2, 1.5, 1, 0.5].map((star) => {
                    const dist = character.site_rating_distribution?.find(d => d.rating === star);
                    const count = dist ? dist.count : 0;
                    const percentage = character.site_rating_count > 0 ? (count / character.site_rating_count) * 100 : 0;

                    return (
                      <div key={star} className="flex items-center gap-1.5 text-xs">
                        <span className={`w-10 text-right font-medium ${character.site_rating_count > 0 ? 'text-yellow-500' : 'text-gray-400'}`}>
                          ★{star.toFixed(1)}
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
                    <span className="font-medium">{language === 'ko' ? '성별:' : 'Gender:'}</span> {character.gender === 'Male' ? (language === 'ko' ? '남성' : 'Male') : character.gender === 'Female' ? (language === 'ko' ? '여성' : 'Female') : character.gender}
                  </div>
                )}

                {getBirthday() && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '생일:' : 'Birthday:'}</span> {getBirthday()}
                  </div>
                )}

                {character.age && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '나이:' : 'Age:'}</span> {character.age}
                  </div>
                )}

                {character.blood_type && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '혈액형:' : 'Blood Type:'}</span> {character.blood_type}
                  </div>
                )}
              </div>

              {/* Description */}
              {character.description && (
                <div className="mt-6">
                  <h3 className="text-xl font-bold mb-4">
                    {language === 'ko' ? '설명' : 'Description'}
                  </h3>
                  <p className="text-gray-700 whitespace-pre-wrap">{character.description}</p>
                </div>
              )}
            </div>

            {/* Character Info - Mobile only (without title) */}
            <div className="lg:hidden bg-white rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] p-6">
              {/* Community Rating */}
              <div className="mb-6 flex gap-8 items-center justify-center">
                {/* 왼쪽: 종합 평점 */}
                <div className="flex flex-col items-center">
                  <div className="text-sm font-medium text-gray-600 mb-3">
                    {language === 'ko' ? '종합 평점' : 'Overall Rating'}
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`text-6xl ${character.site_rating_count > 0 ? 'text-yellow-500' : 'text-gray-300'}`}>★</span>
                    <div>
                      <div className="text-5xl font-bold">
                        {character.site_rating_count > 0 ? character.site_average_rating?.toFixed(1) : '--'}
                      </div>
                      <div className="text-base text-gray-600 mt-1">
                        {character.site_rating_count > 0
                          ? (language === 'ko' ? `${character.site_rating_count}명 평가` : `${character.site_rating_count} ratings`)
                          : (language === 'ko' ? '아직 평가 없음' : 'No ratings yet')
                        }
                      </div>
                    </div>
                  </div>
                </div>

                {/* 오른쪽: 별점 히스토그램 (컴팩트) */}
                <div className="flex-1 max-w-md space-y-0.5">
                  {[5, 4.5, 4, 3.5, 3, 2.5, 2, 1.5, 1, 0.5].map((star) => {
                    const dist = character.site_rating_distribution?.find(d => d.rating === star);
                    const count = dist ? dist.count : 0;
                    const percentage = character.site_rating_count > 0 ? (count / character.site_rating_count) * 100 : 0;

                    return (
                      <div key={star} className="flex items-center gap-1.5 text-xs">
                        <span className={`w-10 text-right font-medium ${character.site_rating_count > 0 ? 'text-yellow-500' : 'text-gray-400'}`}>
                          ★{star.toFixed(1)}
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
                    <span className="font-medium">{language === 'ko' ? '성별:' : 'Gender:'}</span> {character.gender === 'Male' ? (language === 'ko' ? '남성' : 'Male') : character.gender === 'Female' ? (language === 'ko' ? '여성' : 'Female') : character.gender}
                  </div>
                )}
                {character.age && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '나이:' : 'Age:'}</span> {character.age}
                  </div>
                )}
                {character.date_of_birth && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '생일:' : 'Birthday:'}</span> {character.date_of_birth}
                  </div>
                )}
                {character.blood_type && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '혈액형:' : 'Blood Type:'}</span> {character.blood_type}
                  </div>
                )}
                {character.favourites && character.favourites > 0 && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '좋아요:' : 'Favorites:'}</span> {character.favourites.toLocaleString()}
                  </div>
                )}
              </div>

              {/* Description */}
              {character.description && (
                <div className="mt-6">
                  <h3 className="text-xl font-bold mb-4">
                    {language === 'ko' ? '설명' : 'Description'}
                  </h3>
                  <p className="text-gray-700 whitespace-pre-wrap">{character.description}</p>
                </div>
              )}
            </div>

            {/* Anime Appearances */}
            <div className="bg-white rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] p-6">
              <h3 className="text-xl font-bold mb-4">
                {language === 'ko' ? '출연 작품' : 'Appearances'}
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
                          <div className={`absolute top-2 left-2 px-2 py-1 rounded text-xs font-bold ${
                            anime.role === 'MAIN'
                              ? 'bg-red-500 text-white'
                              : 'bg-blue-500 text-white'
                          }`}>
                            {anime.role === 'MAIN' ? (language === 'ko' ? '메인' : 'Main') : (language === 'ko' ? '서브' : 'Supporting')}
                          </div>
                          {/* My Rating Badge */}
                          {anime.my_anime_rating && (
                            <div className="absolute top-2 right-2 bg-yellow-400 text-gray-900 px-2 py-1 rounded text-xs font-bold">
                              ★ {anime.my_anime_rating.toFixed(1)}
                            </div>
                          )}
                        </div>
                        <div className="p-2">
                          <h4 className="font-medium text-sm line-clamp-2 group-hover:text-[#A8E6CF] transition-colors">
                            {getAnimeTitle(anime)}
                          </h4>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <p className="text-gray-600">
                  {language === 'ko' ? '출연 작품이 없습니다.' : 'No anime appearances found.'}
                </p>
              )}
            </div>

            {/* Reviews Section */}
            <div className="bg-white rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-bold">
                  {language === 'ko' ? '리뷰' : 'Reviews'} ({activities.length})
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
                      ? (language === 'ko' ? '취소' : 'Cancel')
                      : (language === 'ko' ? '리뷰 작성' : 'Write Review')
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
                      {language === 'ko' ? '별점' : 'Rating'} *
                    </label>
                    <StarRating
                      rating={reviewData.rating}
                      onRatingChange={(rating) => setReviewData({ ...reviewData, rating })}
                      size="lg"
                      showNumber={true}
                    />
                  </div>

                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {language === 'ko' ? '리뷰 내용' : 'Review Content'} *
                    </label>
                    <textarea
                      value={reviewData.content}
                      onChange={(e) => setReviewData({ ...reviewData, content: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md h-32"
                      placeholder={language === 'ko' ? '이 캐릭터에 대한 당신의 생각을 공유해주세요...' : 'Share your thoughts about this character...'}
                      required
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      {reviewData.content.length} / 5000 {language === 'ko' ? '자' : 'characters'}
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
                        {language === 'ko' ? '스포일러 포함' : 'Contains spoilers'}
                      </span>
                    </label>
                  </div>

                  <button
                    type="submit"
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                  >
                    {isEditingReview
                      ? (language === 'ko' ? '리뷰 수정' : 'Update Review')
                      : (language === 'ko' ? '리뷰 등록' : 'Submit Review')
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
                  {activities.map((activity) => (
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
                  ))}
                </div>
              ) : (
                <p className="text-gray-600">{language === 'ko' ? '아직 리뷰가 없습니다.' : 'No reviews yet.'}</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
