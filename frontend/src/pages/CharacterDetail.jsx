import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { characterService } from '../services/characterService';
import { characterReviewService } from '../services/characterReviewService';
import { commentLikeService } from '../services/commentLikeService';
import { useLanguage } from '../context/LanguageContext';
import { useAuth } from '../context/AuthContext';
import { getCurrentLevelInfo } from '../utils/otakuLevels';
import * as ActivityUtils from '../utils/activityUtils';
import Navbar from '../components/common/Navbar';
import StarRating from '../components/common/StarRating';
import CharacterRatingWidget from '../components/character/CharacterRatingWidget';
import { API_BASE_URL, IMAGE_BASE_URL } from '../config/api';

export default function CharacterDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { language, getAnimeTitle } = useLanguage();
  const { user } = useAuth();
  const [character, setCharacter] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [myReview, setMyReview] = useState(null);
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [isEditingReview, setIsEditingReview] = useState(false);
  const [reviewData, setReviewData] = useState({ content: '', is_spoiler: false, rating: 0 });
  const [reviewError, setReviewError] = useState('');
  const [reviewSuccess, setReviewSuccess] = useState('');

  // 댓글 관련 state
  const [comments, setComments] = useState({});
  const [newComment, setNewComment] = useState({});
  const [replyText, setReplyText] = useState({});
  const [replyingTo, setReplyingTo] = useState({});
  const [commentLikes, setCommentLikes] = useState({});
  const [expandedComments, setExpandedComments] = useState(new Set());

  // 리뷰 좋아요 및 저장 관련 state
  const [reviewLikes, setReviewLikes] = useState({});
  const [savedActivities, setSavedActivities] = useState(() => {
    const saved = localStorage.getItem('savedActivities');
    return saved ? new Set(JSON.parse(saved)) : new Set();
  });
  const [showEditMenu, setShowEditMenu] = useState(null);

  useEffect(() => {
    loadAllData();
  }, [id, user]);

  const loadAllData = async () => {
    setLoading(true);
    try {
      // 병렬로 모든 데이터 로드
      const promises = [
        characterService.getCharacterDetail(id),
        characterReviewService.getCharacterReviews(id, { limit: 10 })
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
        await characterService.rateCharacter(id, null);
        setCharacter({ ...character, my_rating: null });
        setMyReview(null);
      } else {
        await characterService.rateCharacter(id, rating);
        setCharacter({ ...character, my_rating: rating });
        // 평점 입력 후 내 리뷰 섹션에 바로 표시
        const myReviewData = await characterReviewService.getMyReview(id).catch(() => null);
        if (myReviewData) processMyReview(myReviewData);
      }

      // 병렬로 데이터 새로고침
      const [charData, reviewData] = await Promise.all([
        characterService.getCharacterDetail(id),
        characterReviewService.getCharacterReviews(id, { limit: 10 })
      ]);

      if (charData) setCharacter(charData);
      if (reviewData) processReviews(reviewData);
    } catch (err) {
      console.error('Failed to rate character:', err);
      alert(language === 'ko' ? '평가를 저장하는데 실패했습니다.' : 'Failed to save rating.');
    }
  };

  const handleStatusChange = async (status) => {
    try {
      await characterService.rateCharacter(id, null, status);
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

      // 병렬로 데이터 새로고침
      const [charData, reviewData, myReviewData] = await Promise.all([
        characterService.getCharacterDetail(id),
        characterReviewService.getCharacterReviews(id, { limit: 10 }),
        characterReviewService.getMyReview(id).catch(() => null)
      ]);

      if (charData) setCharacter(charData);
      if (reviewData) processReviews(reviewData);
      if (myReviewData) processMyReview(myReviewData);

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

      // 병렬로 데이터 새로고침
      const [charData, reviewData] = await Promise.all([
        characterService.getCharacterDetail(id),
        characterReviewService.getCharacterReviews(id, { limit: 10 })
      ]);

      if (charData) setCharacter(charData);
      if (reviewData) processReviews(reviewData);

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

      // Check if this is a ratings-only review
      if (ActivityUtils.isRatingsOnly(review)) {
        // Use activity like service for ratings-only
        const activityType = ActivityUtils.getActivityType(review);
        const userId = ActivityUtils.getUserId(review);
        const itemId = ActivityUtils.getItemId(review);

        await import('../services/activityLikeService').then(module =>
          module.activityLikeService.toggleLike(activityType, userId, itemId)
        );
      } else {
        // Use character review service for full reviews
        if (newLiked) {
          await characterReviewService.likeReview(reviewId);
        } else {
          await characterReviewService.unlikeReview(reviewId);
        }
      }

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

  const getAvatarUrl = (url) => {
    if (!url) return null;
    if (url.startsWith('http')) return url;
    return `${import.meta.env.VITE_API_URL || API_BASE_URL}${url}`;
  };

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

  const getImageUrl = (imageUrl, fallbackUrl = null) => {
    if (!imageUrl) return '/placeholder-anime.svg';

    // 외부 URL이 있으면 우선 사용 (대부분의 캐릭터는 외부 URL 사용)
    if (imageUrl.startsWith('http')) return imageUrl;

    // R2 경로 처리 (/ 로 시작하는 경로)
    if (imageUrl.startsWith('/')) {
      return `${IMAGE_BASE_URL}${imageUrl}`;
    }

    // Use covers_large for better quality
    const processedUrl = imageUrl.includes('/covers/')
      ? imageUrl.replace('/covers/', '/covers_large/')
      : imageUrl;
    return `${IMAGE_BASE_URL}${processedUrl}`;
  };

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
                src={getImageUrl(character.image_url)}
                alt={character.name_full}
                className="w-full"
                onError={(e) => {
                  e.target.src = '/placeholder-anime.svg';
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
                  {language === 'ko' ? '리뷰' : 'Reviews'} ({reviews.length + (myReview ? 1 : 0)})
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

              {/* My Review */}
              {myReview && (() => {
                console.log('[CharacterDetail] Rendering myReview section:', {
                  id: myReview.id,
                  user_rating: myReview.user_rating,
                  content: myReview.content ? 'Has content' : 'No content',
                  character_my_rating: character?.my_rating,
                  comments_count: myReview.comments_count
                });
                const myReviewLikeInfo = reviewLikes[myReview.id] || { liked: myReview.user_liked || false, count: myReview.likes_count || 0 };
                const myReviewComments = comments[myReview.id] || [];
                const isMyReviewExpanded = expandedComments.has(myReview.id);
                console.log('[CharacterDetail] myReview - expandedComments:', Array.from(expandedComments));
                console.log('[CharacterDetail] myReview - isMyReviewExpanded:', isMyReviewExpanded);
                console.log('[CharacterDetail] myReview - myReviewComments length:', myReviewComments.length);
                // myReview 데이터의 otaku_score 사용
                const myLevelInfo = getCurrentLevelInfo(myReview.otaku_score || user?.otaku_score || 0);

                return (
                  <div className="mb-6 bg-white rounded-xl shadow-[0_2px_12px_rgba(0,0,0,0.08)] border border-blue-200 p-4">
                    <div className="flex gap-4">
                      {/* 왼쪽: 캐릭터 이미지 */}
                      <Link
                        to={`/character/${id}`}
                        className="flex-shrink-0 hover:opacity-80 transition-opacity cursor-pointer"
                      >
                        <img
                          src={getImageUrl(character?.image_url)}
                          alt={character?.name_full}
                          className="w-16 h-24 object-cover rounded border-2 border-transparent hover:border-[#A8E6CF] transition-all"
                          onError={(e) => {
                            e.target.src = '/placeholder-anime.svg';
                          }}
                        />
                      </Link>

                      {/* 오른쪽: 콘텐츠 */}
                      <div className="flex-1 min-w-0">
                        {/* User Info */}
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-2">
                            {/* User Avatar */}
                            <Link to={`/user/${user?.id}`} className="flex-shrink-0">
                              {myReview.avatar_url ? (
                                <img
                                  src={getAvatarUrl(myReview.avatar_url)}
                                  alt={myReview.display_name || myReview.username}
                                  className="w-8 h-8 rounded-full object-cover border border-gray-200"
                                />
                              ) : (
                                <div className="w-8 h-8 rounded-full flex items-center justify-center border border-gray-200" style={{ background: 'linear-gradient(to bottom right, #90B2E4, #638CCC)' }}>
                                  <span className="text-white text-xs font-bold">
                                    {(myReview.display_name || myReview.username || user?.username || '?').charAt(0).toUpperCase()}
                                  </span>
                                </div>
                              )}
                            </Link>
                            <Link
                              to={`/user/${user?.id}`}
                              className="text-sm font-medium text-gray-700 hover:text-[#A8E6CF] transition-colors"
                            >
                              {myReview.display_name || myReview.username || user?.username}
                            </Link>
                            <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${myLevelInfo.bgColor} ${myLevelInfo.color}`}>
                              {myLevelInfo.icon} {myLevelInfo.level} - {toRoman(myLevelInfo.rank)}
                            </span>
                            <span className="text-sm text-gray-600">
                              {language === 'ko' ? '캐릭터를 평가했어요' : 'rated this character'}
                            </span>
                            <span className="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded font-medium">
                              {language === 'ko' ? '내 리뷰' : 'My Review'}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-gray-500">
                              {getTimeAgo(myReview.created_at)}
                            </span>
                            {/* Edit Menu */}
                            <div className="relative">
                              <button
                                onClick={() => setShowEditMenu(showEditMenu === 'myReview' ? null : 'myReview')}
                                className="text-gray-400 hover:text-gray-600 p-1 rounded-full hover:bg-gray-100"
                              >
                                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                                  <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
                                </svg>
                              </button>
                              {showEditMenu === 'myReview' && (
                                <div className="absolute right-0 mt-1 w-32 bg-white rounded-md shadow-[0_2px_12px_rgba(0,0,0,0.08)] z-10 border border-gray-200">
                                  <button
                                    onClick={() => {
                                      handleEditReview();
                                      setShowEditMenu(null);
                                    }}
                                    className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-t-md"
                                  >
                                    {language === 'ko' ? '수정' : 'Edit'}
                                  </button>
                                  <button
                                    onClick={() => {
                                      handleDeleteReview();
                                      setShowEditMenu(null);
                                    }}
                                    className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded-b-md border-t border-gray-200"
                                  >
                                    {language === 'ko' ? '삭제' : 'Delete'}
                                  </button>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* 캐릭터 이름 */}
                        <Link
                          to={`/character/${id}`}
                          className="block group"
                        >
                          <h3 className="font-semibold text-gray-900 group-hover:text-[#A8E6CF] transition-colors mb-2 group-hover:underline">
                            {character?.name_full}
                          </h3>
                        </Link>

                        {/* Rating */}
                        {(myReview.user_rating || character?.my_rating) && (myReview.user_rating > 0 || character?.my_rating > 0) && (
                          <div className="mb-2">
                            <StarRating rating={myReview.user_rating || character.my_rating} readonly size="sm" />
                          </div>
                        )}

                        {/* Review Content */}
                        {myReview.content && (
                          <p className="text-sm text-gray-700 mb-3">
                            {myReview.content}
                          </p>
                        )}

                        {/* Like, Comment & Save Buttons */}
                        <div className="mt-3 flex items-center justify-between">
                          <div className="flex items-center gap-6">
                            {/* Like Button */}
                            <button
                              onClick={() => handleToggleReviewLike(myReview.id)}
                              className="flex items-center gap-2 transition-all hover:scale-110"
                              style={{
                                color: myReviewLikeInfo.liked ? '#DC2626' : '#6B7280'
                              }}
                            >
                              {myReviewLikeInfo.liked ? (
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                                  <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                                </svg>
                              ) : (
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" xmlns="http://www.w3.org/2000/svg">
                                  <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                                </svg>
                              )}
                              <span className="text-sm font-medium">
                                {language === 'ko' ? '좋아요' : 'Like'}
                                {myReviewLikeInfo.count > 0 && (
                                  <> {myReviewLikeInfo.count}</>
                                )}
                              </span>
                            </button>

                            {/* Comment Button */}
                            <button
                              onClick={() => toggleComments(myReview.id)}
                              className="flex items-center gap-2 transition-all hover:scale-110"
                              style={{ color: '#6B7280' }}
                              onMouseEnter={(e) => {
                                e.currentTarget.style.color = '#8EC5FC';
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
                                {myReview.comments_count > 0 && (
                                  <> {myReview.comments_count}</>
                                )}
                              </span>
                            </button>
                          </div>

                          {/* Save Button */}
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleToggleSaveReview(myReview);
                            }}
                            className="flex items-center gap-2 transition-all hover:scale-110"
                            style={{
                              color: savedActivities.has(`character_rating_${user?.id}_${id}`) ? '#A8E6CF' : '#6B7280'
                            }}
                          >
                            {savedActivities.has(`character_rating_${user?.id}_${id}`) ? (
                              <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                                <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
                              </svg>
                            ) : (
                              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" xmlns="http://www.w3.org/2000/svg">
                                <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
                              </svg>
                            )}
                            {savedActivities.has(`character_rating_${user?.id}_${id}`) && (
                              <span className="text-sm font-medium">1</span>
                            )}
                          </button>
                        </div>

                        {/* Comments Section - Same as Other Reviews */}
                        {isMyReviewExpanded && (
                          <div className="mt-3 pt-3 border-t border-gray-200">
                            {/* Comments List */}
                            {myReviewComments.length > 0 && (
                              <div className="space-y-3 mb-3">
                              {myReviewComments.filter(c => !c.parent_comment_id).map((comment) => {
                            const replies = myReviewComments.filter(r => r.parent_comment_id === comment.id);

                            return (
                              <div key={comment.id}>
                                <div className="flex gap-2">
                                  {comment.avatar_url ? (
                                    <img
                                      src={getAvatarUrl(comment.avatar_url)}
                                      alt={comment.display_name || comment.username}
                                      className="w-6 h-6 rounded-full object-cover"
                                    />
                                  ) : (
                                    <div className="w-6 h-6 rounded-full flex items-center justify-center" style={{ background: 'linear-gradient(to bottom right, #90B2E4, #638CCC)' }}>
                                      <span className="text-white text-[10px] font-bold">
                                        {(comment.display_name || comment.username || '?')[0].toUpperCase()}
                                      </span>
                                    </div>
                                  )}

                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2">
                                      <Link
                                        to={`/user/${comment.user_id}`}
                                        className="text-xs font-medium text-gray-700 hover:text-[#A8E6CF]"
                                      >
                                        {comment.display_name || comment.username}
                                      </Link>
                                      {(() => {
                                        const commentLevelInfo = getCurrentLevelInfo(comment.otaku_score || 0);
                                        return (
                                          <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-semibold ${commentLevelInfo.bgColor} ${commentLevelInfo.color}`}>
                                            {commentLevelInfo.icon} {commentLevelInfo.level} - {toRoman(commentLevelInfo.rank)}
                                          </span>
                                        );
                                      })()}
                                      <span className="text-[10px] text-gray-400">
                                        {getTimeAgo(comment.created_at)}
                                      </span>
                                      {user && user.id === comment.user_id && (
                                        <button
                                          onClick={() => handleDeleteComment(myReview.id, comment.id)}
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
                                          color: comment.user_liked ? '#DC2626' : '#9CA3AF'
                                        }}
                                      >
                                        {comment.user_liked ? (
                                          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                                            <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                                          </svg>
                                        ) : (
                                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" xmlns="http://www.w3.org/2000/svg">
                                            <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                                          </svg>
                                        )}
                                        {comment.likes_count > 0 && (
                                          <span className="text-xs">{comment.likes_count}</span>
                                        )}
                                      </button>
                                      <button
                                        onClick={() => handleReplyClick(myReview.id, comment.id)}
                                        className="text-[10px]"
                                        style={{ color: '#9CA3AF' }}
                                        onMouseEnter={(e) => e.target.style.color = '#8EC5FC'}
                                        onMouseLeave={(e) => e.target.style.color = '#9CA3AF'}
                                      >
                                        {language === 'ko' ? '답글' : 'Reply'}
                                      </button>
                                    </div>

                                    {/* Reply Input */}
                                    {replyingTo[myReview.id] === comment.id && (
                                      <div className="flex gap-2 mt-2">
                                        <input
                                          type="text"
                                          value={replyText[comment.id] || ''}
                                          onChange={(e) => setReplyText(prev => ({
                                            ...prev,
                                            [comment.id]: e.target.value
                                          }))}
                                          onKeyDown={(e) => {
                                            if (e.key === 'Enter' && !e.shiftKey) {
                                              e.preventDefault();
                                              handleSubmitReply(myReview.id, comment.id);
                                            }
                                          }}
                                          placeholder={language === 'ko' ? '답글을 입력하세요...' : 'Write a reply...'}
                                          className="flex-1 px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-[#A8E6CF]"
                                          autoFocus
                                        />
                                        <button
                                          onClick={() => handleSubmitReply(myReview.id, comment.id)}
                                          className="px-3 py-1.5 bg-[#A8E6CF] text-white rounded-lg text-sm hover:bg-[#35a8b0] transition-colors"
                                        >
                                          {language === 'ko' ? '등록' : 'Post'}
                                        </button>
                                      </div>
                                    )}
                                  </div>
                                </div>

                                {/* Replies */}
                                {replies.length > 0 && (
                                  <div className="ml-10 mt-2 space-y-2">
                                    {replies.map((reply) => {
                                      return (
                                        <div key={reply.id} className="flex gap-2">
                                          {reply.avatar_url ? (
                                            <img
                                              src={getAvatarUrl(reply.avatar_url)}
                                              alt={reply.display_name || reply.username}
                                              className="w-6 h-6 rounded-full object-cover"
                                            />
                                          ) : (
                                            <div className="w-6 h-6 rounded-full flex items-center justify-center" style={{ background: 'linear-gradient(to bottom right, #90B2E4, #638CCC)' }}>
                                              <span className="text-white text-[10px] font-bold">
                                                {(reply.display_name || reply.username || '?')[0].toUpperCase()}
                                              </span>
                                            </div>
                                          )}

                                          <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2">
                                              <Link
                                                to={`/user/${reply.user_id}`}
                                                className="text-xs font-medium text-gray-700 hover:text-[#A8E6CF]"
                                              >
                                                {reply.display_name || reply.username}
                                              </Link>
                                              {(() => {
                                                const replyLevelInfo = getCurrentLevelInfo(reply.otaku_score || 0);
                                                return (
                                                  <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-semibold ${replyLevelInfo.bgColor} ${replyLevelInfo.color}`}>
                                                    {replyLevelInfo.icon} {replyLevelInfo.level} - {toRoman(replyLevelInfo.rank)}
                                                  </span>
                                                );
                                              })()}
                                              <span className="text-[10px] text-gray-400">
                                                {getTimeAgo(reply.created_at)}
                                              </span>
                                              {user && user.id === reply.user_id && (
                                                <button
                                                  onClick={() => handleDeleteComment(myReview.id, reply.id)}
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
                                                color: reply.user_liked ? '#DC2626' : '#9CA3AF'
                                              }}
                                            >
                                              {reply.user_liked ? (
                                                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                                                  <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                                                </svg>
                                              ) : (
                                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" xmlns="http://www.w3.org/2000/svg">
                                                  <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                                                </svg>
                                              )}
                                              {reply.likes_count > 0 && (
                                                <span className="text-xs">{reply.likes_count}</span>
                                              )}
                                            </button>
                                          </div>
                                        </div>
                                      );
                                    })}
                                  </div>
                                )}
                              </div>
                            );
                              })}
                              </div>
                            )}

                            {/* Comment Input */}
                            {user && (
                              <div className="flex gap-2">
                                <input
                                  type="text"
                                  value={newComment[myReview.id] || ''}
                                  onChange={(e) => setNewComment(prev => ({ ...prev, [myReview.id]: e.target.value }))}
                                  onKeyPress={(e) => {
                                    if (e.key === 'Enter') {
                                      handleSubmitComment(myReview.id);
                                    }
                                  }}
                                  placeholder={language === 'ko' ? '댓글을 입력하세요...' : 'Write a comment...'}
                                  className="flex-1 px-3 py-1.5 text-xs border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                                <button
                                  onClick={() => handleSubmitComment(myReview.id)}
                                  className="px-3 py-1.5 text-xs text-white rounded-lg transition-colors"
                                  style={{ backgroundColor: '#8EC5FC' }}
                                  onMouseEnter={(e) => e.target.style.backgroundColor = '#638CCC'}
                                  onMouseLeave={(e) => e.target.style.backgroundColor = '#8EC5FC'}
                                >
                                  {language === 'ko' ? '작성' : 'Submit'}
                                </button>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })()}

              {/* Other Reviews */}
              {(() => {
                console.log('[CharacterDetail] Rendering reviews section, reviews:', reviews);
                console.log('[CharacterDetail] reviews.length:', reviews.length);
                return null;
              })()}
              {reviews.length > 0 ? (
                <div className="space-y-4">
                  {reviews.map((review) => {
                    console.log('[CharacterDetail] Rendering review:', review.id, review);
                    const likeInfo = reviewLikes[review.id] || { liked: review.user_liked || false, count: review.likes_count || 0 };
                    const reviewComments = comments[review.id] || [];
                    const isExpanded = expandedComments.has(review.id);
                    const levelInfo = getCurrentLevelInfo(review.otaku_score || 0);

                    return (
                      <div key={review.id} className="bg-white rounded-xl shadow-[0_2px_12px_rgba(0,0,0,0.08)] border border-gray-200 p-4 hover:shadow-[0_2px_12px_rgba(0,0,0,0.08)] transition-all">
                        <div className="flex gap-4">
                          {/* 왼쪽: 캐릭터 이미지 */}
                          <Link
                            to={`/character/${id}`}
                            className="flex-shrink-0 hover:opacity-80 transition-opacity cursor-pointer"
                          >
                            <img
                              src={getImageUrl(character?.image_url)}
                              alt={character?.name_full}
                              className="w-16 h-24 object-cover rounded border-2 border-transparent hover:border-[#A8E6CF] transition-all"
                              onError={(e) => {
                                e.target.src = '/placeholder-anime.svg';
                              }}
                            />
                          </Link>

                          {/* 오른쪽: 콘텐츠 */}
                          <div className="flex-1 min-w-0">
                            {/* User Info */}
                            <div className="flex items-start justify-between mb-2">
                              <div className="flex items-center gap-2">
                                {/* User Avatar */}
                                <Link to={`/user/${review.user_id}`} className="flex-shrink-0">
                                  {review.avatar_url ? (
                                    <img
                                      src={getAvatarUrl(review.avatar_url)}
                                      alt={review.display_name || review.username}
                                      className="w-8 h-8 rounded-full object-cover border border-gray-200"
                                    />
                                  ) : (
                                    <div className="w-8 h-8 rounded-full flex items-center justify-center border border-gray-200" style={{ background: 'linear-gradient(to bottom right, #90B2E4, #638CCC)' }}>
                                      <span className="text-white text-xs font-bold">
                                        {(review.display_name || review.username || '?').charAt(0).toUpperCase()}
                                      </span>
                                    </div>
                                  )}
                                </Link>
                                <Link
                                  to={`/user/${review.user_id}`}
                                  className="text-sm font-medium text-gray-700 hover:text-[#A8E6CF] transition-colors"
                                >
                                  {review.display_name || review.username}
                                </Link>
                                {(() => {
                                  return (
                                    <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${levelInfo.bgGradient} border ${levelInfo.borderColor}`}>
                                      <span style={{ color: levelInfo.color }} className="font-bold">{levelInfo.icon}</span> <span className="text-gray-700">{levelInfo.level} - {toRoman(levelInfo.rank)}</span>
                                    </span>
                                  );
                                })()}
                                <span className="text-sm text-gray-600">
                                  {language === 'ko' ? '캐릭터를 평가했어요' : 'rated this character'}
                                </span>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="text-xs text-gray-500">
                                  {getTimeAgo(review.created_at)}
                                </span>
                                {/* Edit Menu - only for own reviews */}
                                {review.user_id === user?.id && (
                                  <div className="relative">
                                    <button
                                      onClick={() => setShowEditMenu(showEditMenu === `review_${review.id}` ? null : `review_${review.id}`)}
                                      className="text-gray-400 hover:text-gray-600 p-1 rounded-full hover:bg-gray-100"
                                    >
                                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                                        <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
                                      </svg>
                                    </button>
                                    {showEditMenu === `review_${review.id}` && (
                                      <div className="absolute right-0 mt-1 w-32 bg-white rounded-md shadow-[0_2px_12px_rgba(0,0,0,0.08)] z-10 border border-gray-200">
                                        <button
                                          onClick={() => {
                                            handleEditReview();
                                            setShowEditMenu(null);
                                          }}
                                          className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-t-md"
                                        >
                                          {language === 'ko' ? '수정' : 'Edit'}
                                        </button>
                                        <button
                                          onClick={() => {
                                            handleDeleteReview();
                                            setShowEditMenu(null);
                                          }}
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

                            {/* 캐릭터 이름 */}
                            <Link
                              to={`/character/${id}`}
                              className="block group"
                            >
                              <h3 className="font-semibold text-gray-900 group-hover:text-[#A8E6CF] transition-colors mb-2 group-hover:underline">
                                {character?.name_full}
                              </h3>
                            </Link>

                            {/* Rating */}
                            {review.user_rating && review.user_rating > 0 && (
                              <div className="mb-2">
                                <StarRating rating={review.user_rating} readonly size="sm" />
                              </div>
                            )}

                            {/* Review Content */}
                            {review.content && (
                              <p className="text-sm text-gray-700 mb-3">
                                {review.content}
                              </p>
                            )}

                            {/* Like, Comment & Save Buttons */}
                            <div className="mt-3 flex items-center justify-between">
                              <div className="flex items-center gap-6">
                                {/* Like Button */}
                                <button
                                  onClick={() => handleToggleReviewLike(review.id)}
                                  className="flex items-center gap-2 transition-all hover:scale-110"
                                  style={{
                                    color: likeInfo.liked ? '#DC2626' : '#6B7280'
                                  }}
                                >
                                  {likeInfo.liked ? (
                                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                                      <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                                    </svg>
                                  ) : (
                                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" xmlns="http://www.w3.org/2000/svg">
                                      <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                                    </svg>
                                  )}
                                  <span className="text-sm font-medium">
                                    {language === 'ko' ? '좋아요' : 'Like'}
                                    {likeInfo.count > 0 && (
                                      <> {likeInfo.count}</>
                                    )}
                                  </span>
                                </button>

                                {/* Comment Button */}
                                <button
                                  onClick={() => toggleComments(review.id)}
                                  className="flex items-center gap-2 transition-all hover:scale-110"
                                  style={{ color: '#6B7280' }}
                                  onMouseEnter={(e) => {
                                    e.currentTarget.style.color = '#8EC5FC';
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
                                    {review.comments_count > 0 && (
                                      <> {review.comments_count}</>
                                    )}
                                  </span>
                                </button>
                              </div>

                              {/* Save Button */}
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleToggleSaveReview(review);
                                }}
                                className="flex items-center gap-2 transition-all hover:scale-110"
                                style={{
                                  color: savedActivities.has(`character_rating_${review.user_id}_${id}`) ? '#A8E6CF' : '#6B7280'
                                }}
                              >
                                {savedActivities.has(`character_rating_${review.user_id}_${id}`) ? (
                                  <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
                                  </svg>
                                ) : (
                                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
                                  </svg>
                                )}
                                {savedActivities.has(`character_rating_${review.user_id}_${id}`) && (
                                  <span className="text-sm font-medium">1</span>
                                )}
                              </button>
                            </div>

                            {/* Comments Section */}
                            {isExpanded && (
                              <div className="mt-3 pt-3 border-t border-gray-200">
                                {/* Comments List */}
                                {reviewComments.length > 0 && (
                                  <div className="space-y-3 mb-3">
                                  {reviewComments.filter(c => !c.parent_comment_id).map((comment) => {
                                const replies = reviewComments.filter(r => r.parent_comment_id === comment.id);

                                return (
                                  <div key={comment.id}>
                                    <div className="flex gap-2">
                                      {comment.avatar_url ? (
                                        <img
                                          src={getAvatarUrl(comment.avatar_url)}
                                          alt={comment.display_name || comment.username}
                                          className="w-6 h-6 rounded-full object-cover"
                                        />
                                      ) : (
                                        <div className="w-6 h-6 rounded-full flex items-center justify-center" style={{ background: 'linear-gradient(to bottom right, #90B2E4, #638CCC)' }}>
                                          <span className="text-white text-[10px] font-bold">
                                            {(comment.display_name || comment.username || '?')[0].toUpperCase()}
                                          </span>
                                        </div>
                                      )}

                                      <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2">
                                          <Link
                                            to={`/user/${comment.user_id}`}
                                            className="text-xs font-medium text-gray-700 hover:text-[#A8E6CF]"
                                          >
                                            {comment.display_name || comment.username}
                                          </Link>
                                          {(() => {
                                            const commentLevelInfo = getCurrentLevelInfo(comment.otaku_score || 0);
                                            return (
                                              <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-semibold ${commentLevelInfo.bgColor} ${commentLevelInfo.color}`}>
                                                {commentLevelInfo.icon} {commentLevelInfo.level} - {toRoman(commentLevelInfo.rank)}
                                              </span>
                                            );
                                          })()}
                                          <span className="text-[10px] text-gray-400">
                                            {getTimeAgo(comment.created_at)}
                                          </span>
                                          {user && user.id === comment.user_id && (
                                            <button
                                              onClick={() => handleDeleteComment(review.id, comment.id)}
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
                                              color: comment.user_liked ? '#DC2626' : '#9CA3AF'
                                            }}
                                          >
                                            {comment.user_liked ? (
                                              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                                                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                                              </svg>
                                            ) : (
                                              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" xmlns="http://www.w3.org/2000/svg">
                                                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                                              </svg>
                                            )}
                                            {comment.likes_count > 0 && (
                                              <span className="text-xs">{comment.likes_count}</span>
                                            )}
                                          </button>
                                          <button
                                            onClick={() => handleReplyClick(review.id, comment.id)}
                                            className="text-[10px]"
                                            style={{ color: '#9CA3AF' }}
                                            onMouseEnter={(e) => e.target.style.color = '#8EC5FC'}
                                            onMouseLeave={(e) => e.target.style.color = '#9CA3AF'}
                                          >
                                            {language === 'ko' ? '답글' : 'Reply'}
                                          </button>
                                        </div>

                                        {/* Reply Input */}
                                        {replyingTo[review.id] === comment.id && (
                                          <div className="flex gap-2 mt-2">
                                            <input
                                              type="text"
                                              value={replyText[comment.id] || ''}
                                              onChange={(e) => setReplyText(prev => ({
                                                ...prev,
                                                [comment.id]: e.target.value
                                              }))}
                                              onKeyDown={(e) => {
                                                if (e.key === 'Enter' && !e.shiftKey) {
                                                  e.preventDefault();
                                                  handleSubmitReply(review.id, comment.id);
                                                }
                                              }}
                                              placeholder={language === 'ko' ? '답글을 입력하세요...' : 'Write a reply...'}
                                              className="flex-1 px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-[#A8E6CF]"
                                              autoFocus
                                            />
                                            <button
                                              onClick={() => handleSubmitReply(review.id, comment.id)}
                                              className="px-3 py-1.5 bg-[#A8E6CF] text-white rounded-lg text-sm hover:bg-[#35a8b0] transition-colors"
                                            >
                                              {language === 'ko' ? '등록' : 'Post'}
                                            </button>
                                          </div>
                                        )}
                                      </div>
                                    </div>

                                    {/* Replies */}
                                    {replies.length > 0 && (
                                      <div className="ml-10 mt-2 space-y-2">
                                        {replies.map((reply) => {
                                          return (
                                            <div key={reply.id} className="flex gap-2">
                                              {reply.avatar_url ? (
                                                <img
                                                  src={getAvatarUrl(reply.avatar_url)}
                                                  alt={reply.display_name || reply.username}
                                                  className="w-6 h-6 rounded-full object-cover"
                                                />
                                              ) : (
                                                <div className="w-6 h-6 rounded-full flex items-center justify-center" style={{ background: 'linear-gradient(to bottom right, #90B2E4, #638CCC)' }}>
                                                  <span className="text-white text-[10px] font-bold">
                                                    {(reply.display_name || reply.username || '?')[0].toUpperCase()}
                                                  </span>
                                                </div>
                                              )}

                                              <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2">
                                                  <Link
                                                    to={`/user/${reply.user_id}`}
                                                    className="text-xs font-medium text-gray-700 hover:text-[#A8E6CF]"
                                                  >
                                                    {reply.display_name || reply.username}
                                                  </Link>
                                                  {(() => {
                                                    const replyLevelInfo = getCurrentLevelInfo(reply.otaku_score || 0);
                                                    return (
                                                      <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-semibold ${replyLevelInfo.bgColor} ${replyLevelInfo.color}`}>
                                                        {replyLevelInfo.icon} {replyLevelInfo.level} - {toRoman(replyLevelInfo.rank)}
                                                      </span>
                                                    );
                                                  })()}
                                                  <span className="text-[10px] text-gray-400">
                                                    {getTimeAgo(reply.created_at)}
                                                  </span>
                                                  {user && user.id === reply.user_id && (
                                                    <button
                                                      onClick={() => handleDeleteComment(review.id, reply.id)}
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
                                                    color: reply.user_liked ? '#DC2626' : '#9CA3AF'
                                                  }}
                                                >
                                                  {reply.user_liked ? (
                                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                                                      <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                                                    </svg>
                                                  ) : (
                                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" xmlns="http://www.w3.org/2000/svg">
                                                      <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                                                    </svg>
                                                  )}
                                                  {reply.likes_count > 0 && (
                                                    <span className="text-xs">{reply.likes_count}</span>
                                                  )}
                                                </button>
                                              </div>
                                            </div>
                                          );
                                        })}
                                      </div>
                                    )}
                                  </div>
                                );
                                  })}
                                  </div>
                                )}

                                {/* Comment Input */}
                                {user && (
                                  <div className="flex gap-2">
                                    <input
                                      type="text"
                                      value={newComment[review.id] || ''}
                                      onChange={(e) => setNewComment(prev => ({ ...prev, [review.id]: e.target.value }))}
                                      onKeyPress={(e) => {
                                        if (e.key === 'Enter') {
                                          handleSubmitComment(review.id);
                                        }
                                      }}
                                      placeholder={language === 'ko' ? '댓글을 입력하세요...' : 'Write a comment...'}
                                      className="flex-1 px-3 py-1.5 text-xs border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                    <button
                                      onClick={() => handleSubmitComment(review.id)}
                                      className="px-3 py-1.5 text-xs text-white rounded-lg transition-colors"
                                      style={{ backgroundColor: '#8EC5FC' }}
                                      onMouseEnter={(e) => e.target.style.backgroundColor = '#638CCC'}
                                      onMouseLeave={(e) => e.target.style.backgroundColor = '#8EC5FC'}
                                    >
                                      {language === 'ko' ? '작성' : 'Submit'}
                                    </button>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : myReview ? null : (
                <p className="text-gray-600">{language === 'ko' ? '아직 리뷰가 없습니다.' : 'No reviews yet.'}</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
