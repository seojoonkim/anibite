import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { animeService } from '../services/animeService';
import { ratingService } from '../services/ratingService';
import { reviewService } from '../services/reviewService';
import { activityLikeService } from '../services/activityLikeService';
import * as ActivityUtils from '../utils/activityUtils';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import Navbar from '../components/common/Navbar';
import StarRating from '../components/common/StarRating';
import RatingWidget from '../components/anime/RatingWidget';
import { getCurrentLevelInfo } from '../utils/otakuLevels';
import { API_BASE_URL, IMAGE_BASE_URL } from '../config/api';

export default function AnimeDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { getAnimeTitle, language } = useLanguage();
  const [anime, setAnime] = useState(null);
  const [myRating, setMyRating] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [myReview, setMyReview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [isEditingReview, setIsEditingReview] = useState(false);
  const [reviewData, setReviewData] = useState({ content: '', is_spoiler: false, rating: 0 });
  const [reviewError, setReviewError] = useState('');
  const [reviewSuccess, setReviewSuccess] = useState('');

  // 피드 형식 상태 추가
  const [reviewLikes, setReviewLikes] = useState({});
  const [expandedComments, setExpandedComments] = useState(new Set());
  const [comments, setComments] = useState({});
  const [newComment, setNewComment] = useState({});
  const [replyingTo, setReplyingTo] = useState({});
  const [replyText, setReplyText] = useState({});
  const [showEditMenu, setShowEditMenu] = useState(null);
  const [failedImages, setFailedImages] = useState(new Set());
  const [savedActivities, setSavedActivities] = useState(new Set());

  // Activity Key 생성 (피드와 동일한 형식)
  const getActivityKey = (review) => {
    return ActivityUtils.getActivityKey(review);
  };

  // 리뷰 객체 가져오기 (통합 유틸리티용)
  const getReviewById = (reviewId) => {
    if (myReview && myReview.id === reviewId) {
      return myReview;
    }
    return reviews.find(r => r.id === reviewId);
  };

  // 로마 숫자 변환 함수
  const toRoman = (num) => {
    const romanNumerals = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X'];
    return romanNumerals[num - 1] || num;
  };

  useEffect(() => {
    loadAllData();
  }, [id]);

  const loadAllData = async () => {
    setLoading(true);
    setError(null);

    try {
      // 애니메이션 기본 정보 먼저 로드 (가장 중요)
      const animeData = await animeService.getAnimeById(id);

      if (!animeData) {
        setError('애니메이션을 찾을 수 없습니다.');
        setLoading(false);
        return;
      }

      // 애니메이션 정보 설정
      setAnime(animeData);

      // 나머지 데이터는 병렬로 로드 (실패해도 괜찮음)
      const [myRatingData, reviewData, myReviewData] = await Promise.all([
        user ? ratingService.getUserRating(id).catch(() => null) : Promise.resolve(null),
        reviewService.getAnimeReviews(id, { limit: 10 }).catch(() => ({ items: [] })),
        user ? reviewService.getMyReview(id).catch(() => null) : Promise.resolve(null)
      ]);

      // 내 평점
      if (myRatingData) {
        setMyRating(myRatingData);
      }

      // 리뷰 목록
      if (reviewData) {
        processReviews(reviewData);
      }

      // 내 리뷰
      if (myReviewData) {
        processMyReview(myReviewData);
      }
    } catch (err) {
      console.error('Failed to load anime data:', err);
      setError(`데이터를 불러오는데 실패했습니다: ${err.message || '알 수 없는 오류'}`);
    } finally {
      setLoading(false);
    }
  };

  // 컴포넌트 마운트 시 저장된 활동 로드 (피드와 동기화)
  useEffect(() => {
    const saved = localStorage.getItem('savedActivities');
    if (saved) {
      setSavedActivities(new Set(JSON.parse(saved)));
    }
  }, []);

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
    setReviews(data.items || []);

    // 좋아요/댓글 정보 초기화
    const newReviewLikes = {};
    const newComments = {};
    const newExpandedComments = new Set();
    const commentsToLoad = [];

    (data.items || []).forEach(review => {
      newReviewLikes[review.id] = {
        liked: review.user_liked || false,
        count: review.likes_count || 0
      };
      newComments[review.id] = [];

      // 댓글이 있으면 자동으로 펼치기
      if (review.comments_count > 0) {
        newExpandedComments.add(review.id);
        commentsToLoad.push(review); // review 객체 자체를 전달
      }
    });

    setReviewLikes(newReviewLikes);
    setComments(newComments);
    setExpandedComments(newExpandedComments);

    // 댓글 병렬 로드
    if (commentsToLoad.length > 0) {
      Promise.all(commentsToLoad.map(review => loadReviewComments(review))); // review 객체 전달
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
        loadReviewComments(data);
      }
    }
  };

  // 피드 형식 핸들러 함수들
  const loadReviewComments = async (reviewOrId) => {
    try {
      // review 객체가 직접 전달되었는지, ID만 전달되었는지 확인
      const review = typeof reviewOrId === 'object' ? reviewOrId : getReviewById(reviewOrId);
      const reviewId = typeof reviewOrId === 'object' ? reviewOrId.id : reviewOrId;

      if (!review) return;

      const data = await ActivityUtils.loadComments(review);

      setComments(prev => ({
        ...prev,
        [reviewId]: data.items || []
      }));
    } catch (err) {
      console.error('Failed to load comments:', err);
    }
  };

  const toggleComments = (reviewId) => {
    const newExpanded = new Set(expandedComments);
    if (newExpanded.has(reviewId)) {
      newExpanded.delete(reviewId);
    } else {
      newExpanded.add(reviewId);
      // 댓글이 아직 로드되지 않았으면 로드
      if (!comments[reviewId] || comments[reviewId].length === 0) {
        loadReviewComments(reviewId);
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
      if (!review) return;

      const currentLike = reviewLikes[reviewId];
      const newLiked = !currentLike.liked;

      // Use activityLikeService with activity_type, activity_user_id, item_id
      await activityLikeService.toggleLike('anime_rating', review.user_id, review.anime_id);

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

  const handleSubmitComment = async (reviewId) => {
    if (!user) {
      alert(language === 'ko' ? '로그인이 필요합니다.' : 'Please login first.');
      return;
    }

    const commentText = newComment[reviewId];
    if (!commentText?.trim()) return;

    try {
      const review = getReviewById(reviewId);
      if (!review) return;

      await ActivityUtils.createComment(review, commentText);

      setNewComment(prev => ({ ...prev, [reviewId]: '' }));
      loadReviewComments(reviewId);

      // 리뷰 목록 새로고침 (댓글 수 업데이트)
      const reviewData = await reviewService.getAnimeReviews(id, { limit: 10 });
      if (reviewData) processReviews(reviewData);
    } catch (err) {
      console.error('[AnimeDetail] Failed to create comment:', err);
      alert(language === 'ko' ? '댓글 작성에 실패했습니다.' : 'Failed to create comment.');
    }
  };

  const handleDeleteComment = async (reviewId, commentId) => {
    if (!confirm(language === 'ko' ? '댓글을 삭제하시겠습니까?' : 'Delete this comment?')) return;

    try {
      const review = getReviewById(reviewId);
      if (!review) return;

      await ActivityUtils.deleteComment(review, commentId);

      loadReviewComments(review);

      // 댓글 수 업데이트
      const reviewData = await reviewService.getAnimeReviews(id, { limit: 10 });
      if (reviewData) processReviews(reviewData);
    } catch (err) {
      console.error('Failed to delete comment:', err);
      alert(language === 'ko' ? '댓글 삭제에 실패했습니다.' : 'Failed to delete comment.');
    }
  };

  const handleToggleCommentLike = async (reviewId, commentId) => {
    if (!user) {
      alert(language === 'ko' ? '로그인이 필요합니다.' : 'Please login first.');
      return;
    }

    try {
      await ActivityUtils.toggleCommentLike(commentId);
      loadReviewComments(reviewId);
    } catch (err) {
      console.error('Failed to toggle comment like:', err);
    }
  };

  const handleToggleSaveReview = (review) => {
    const activityKey = getActivityKey(review);
    setSavedActivities(prev => {
      const newSet = new Set(prev);
      if (newSet.has(activityKey)) {
        newSet.delete(activityKey);
      } else {
        newSet.add(activityKey);
      }
      // 로컬 스토리지에 저장 (피드와 동기화)
      localStorage.setItem('savedActivities', JSON.stringify([...newSet]));
      return newSet;
    });
  };

  const handleReplyClick = (reviewId, commentId) => {
    setReplyingTo(prev => ({
      ...prev,
      [reviewId]: prev[reviewId] === commentId ? null : commentId
    }));
  };

  const handleSubmitReply = async (reviewId, parentCommentId) => {
    if (!user) {
      alert(language === 'ko' ? '로그인이 필요합니다.' : 'Please login first.');
      return;
    }

    const replyContent = replyText[`${reviewId}-${parentCommentId}`];
    if (!replyContent?.trim()) return;

    try {
      const review = getReviewById(reviewId);
      if (!review) return;

      await ActivityUtils.createReply(review, parentCommentId, replyContent);

      setReplyText(prev => ({ ...prev, [`${reviewId}-${parentCommentId}`]: '' }));
      setReplyingTo(prev => ({ ...prev, [reviewId]: null }));
      loadReviewComments(reviewId);

      // 댓글 수 업데이트
      const reviewData = await reviewService.getAnimeReviews(id, { limit: 10 });
      if (reviewData) processReviews(reviewData);
    } catch (err) {
      console.error('Failed to create reply:', err);
      alert(language === 'ko' ? '답글 작성에 실패했습니다.' : 'Failed to create reply.');
    }
  };

  const getAvatarUrl = (url) => {
    if (!url) return null;
    if (url.startsWith('http')) return url;
    return `${import.meta.env.VITE_API_URL || API_BASE_URL}${url}`;
  };

  const handleAvatarError = (e, userId) => {
    setFailedImages(prev => new Set([...prev, userId]));
  };

  const getTimeAgo = (timestamp) => {
    const now = new Date();
    // SQLite timestamp를 UTC로 파싱
    const past = new Date(timestamp.endsWith('Z') ? timestamp : timestamp + 'Z');
    const diffInSeconds = Math.floor((now - past) / 1000);

    if (diffInSeconds < 3600) return language === 'ko' ? `${Math.max(1, Math.floor(diffInSeconds / 60))}분 전` : `${Math.max(1, Math.floor(diffInSeconds / 60))}m ago`;
    if (diffInSeconds < 86400) return language === 'ko' ? `${Math.floor(diffInSeconds / 3600)}시간 전` : `${Math.floor(diffInSeconds / 3600)}h ago`;
    if (diffInSeconds < 604800) return language === 'ko' ? `${Math.floor(diffInSeconds / 86400)}일 전` : `${Math.floor(diffInSeconds / 86400)}d ago`;
    return past.toLocaleDateString(language === 'ko' ? 'ko-KR' : 'en-US');
  };

  const handleEditReview = () => {
    if (myReview) {
      setReviewData({
        content: myReview.content,
        is_spoiler: myReview.is_spoiler,
        rating: myRating?.rating || 0
      });
      setIsEditingReview(true);
      setShowReviewForm(true);
    }
  };

  const handleDeleteReview = async () => {
    if (!confirm(language === 'ko' ? '리뷰를 삭제하시겠습니까?' : 'Delete this review?')) return;

    try {
      await reviewService.deleteReview(myReview.id);
      setMyReview(null);
      setReviewSuccess(language === 'ko' ? '리뷰가 삭제되었습니다.' : 'Review deleted successfully.');

      // 리뷰 목록 새로고침
      const reviewData = await reviewService.getAnimeReviews(id, { limit: 10 });
      if (reviewData) processReviews(reviewData);

      setTimeout(() => setReviewSuccess(''), 3000);
    } catch (err) {
      console.error('Failed to delete review:', err);
      setReviewError(language === 'ko' ? '리뷰 삭제에 실패했습니다.' : 'Failed to delete review.');
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

    try {
      if (isEditingReview && myReview) {
        // 수정 시: 별점은 별도로 저장하고 리뷰만 수정
        if (reviewData.rating && (!myRating || myRating.rating !== reviewData.rating)) {
          const ratingResult = await ratingService.rateAnime(parseInt(id), { rating: reviewData.rating, status: 'RATED' });
          setMyRating(ratingResult);
        }

        await reviewService.updateReview(myReview.id, {
          content: reviewData.content,
          is_spoiler: reviewData.is_spoiler
        });
        setReviewSuccess(language === 'ko' ? '리뷰가 수정되었습니다.' : 'Review updated successfully.');
      } else {
        // 새로 작성: 별점과 리뷰를 한 번에 전송
        await reviewService.createReview({
          anime_id: parseInt(id),
          content: reviewData.content,
          is_spoiler: reviewData.is_spoiler,
          rating: reviewData.rating  // 별점을 리뷰 API에 함께 전송
        });

        // 리뷰 생성 후 별점 상태 업데이트
        const ratingResult = await ratingService.getMyRating(parseInt(id));
        if (ratingResult) setMyRating(ratingResult);

        setReviewSuccess(language === 'ko' ? '리뷰가 작성되었습니다.' : 'Review submitted successfully.');
      }

      setReviewData({ content: '', is_spoiler: false, rating: 0 });
      setShowReviewForm(false);
      setIsEditingReview(false);

      // 병렬로 데이터 새로고침
      const [animeData, reviewData, myReviewData] = await Promise.all([
        animeService.getAnimeById(id),
        reviewService.getAnimeReviews(id, { limit: 10 }),
        reviewService.getMyReview(id).catch(() => null)
      ]);

      if (animeData) setAnime(animeData);
      if (reviewData) processReviews(reviewData);
      if (myReviewData) processMyReview(myReviewData);

      setTimeout(() => setReviewSuccess(''), 3000);
    } catch (err) {
      console.error('리뷰 제출 실패:', err);
      setReviewError(
        language === 'ko'
          ? err.response?.data?.detail || '리뷰 작성에 실패했습니다.'
          : err.response?.data?.detail || 'Failed to submit review.'
      );
    }
  };

  const handleRate = async (rating, status) => {
    try {
      await ratingService.rateAnime(id, { rating, status });

      // 병렬로 데이터 새로고침
      const [myRatingData, animeData] = await Promise.all([
        ratingService.getUserRating(id).catch(() => null),
        animeService.getAnimeById(id)
      ]);

      if (myRatingData) setMyRating(myRatingData);
      if (animeData) setAnime(animeData);
    } catch (err) {
      console.error('Failed to rate:', err);
      alert(language === 'ko' ? '평가를 저장하는데 실패했습니다.' : 'Failed to save rating.');
    }
  };

  const handleStatusChange = async (status) => {
    try {
      if (status === null) {
        await ratingService.deleteRating(id);
        setMyRating(null);
      } else {
        const result = await ratingService.rateAnime(id, { status });
        setMyRating(result);
      }

      // 통계 새로고침
      const animeData = await animeService.getAnimeById(id);
      if (animeData) setAnime(animeData);
    } catch (err) {
      console.error('Failed to update status:', err);
      alert('상태 변경에 실패했습니다.');
    }
  };

  const getImageUrl = (imageUrl) => {
    if (!imageUrl) return '/placeholder-anime.svg';
    if (imageUrl.startsWith('http')) return imageUrl;
    // Use covers_large for better quality
    const processedUrl = imageUrl.includes('/covers/')
      ? imageUrl.replace('/covers/', '/covers_large/')
      : imageUrl;
    return `${IMAGE_BASE_URL}${processedUrl}`;
  };

  if (loading) {
    return (
      <div className="min-h-screen pt-0 md:pt-16 bg-transparent">
        <Navbar />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8">
          <div className="flex flex-col lg:flex-row gap-8 animate-pulse">
            {/* Cover Image Skeleton */}
            <div className="lg:w-80 flex-shrink-0">
              <div className="w-full h-96 bg-gray-200 rounded-xl"></div>
            </div>
            {/* Info Skeleton */}
            <div className="flex-1">
              <div className="h-8 w-3/4 bg-gray-200 rounded mb-4"></div>
              <div className="h-6 w-1/2 bg-gray-200 rounded mb-6"></div>
              <div className="space-y-3 mb-6">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="h-4 w-full bg-gray-200 rounded"></div>
                ))}
              </div>
              <div className="flex gap-2 mb-6">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-10 w-24 bg-gray-200 rounded"></div>
                ))}
              </div>
            </div>
          </div>
          {/* Characters Skeleton */}
          <div className="mt-8">
            <div className="h-6 w-32 bg-gray-200 rounded mb-4"></div>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div key={i} className="bg-white rounded-lg p-2">
                  <div className="w-full h-40 bg-gray-200 rounded mb-2"></div>
                  <div className="h-4 bg-gray-200 rounded"></div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !anime) {
    return (
      <div className="min-h-screen pt-0 md:pt-16 bg-transparent">
        <Navbar />
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {error || '애니메이션을 찾을 수 없습니다.'}
          </div>
          <button
            onClick={() => navigate('/')}
            className="mt-4 text-blue-500 hover:text-[#A8E6CF]"
          >
            ← 홈으로 돌아가기
          </button>
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
            <h1 className="text-3xl font-bold mb-2">{getAnimeTitle(anime)}</h1>
            {language === 'ko' && anime.title_korean && anime.title_romaji && (
              <h2 className="text-xl text-gray-500">{anime.title_romaji}</h2>
            )}
            {language === 'en' && anime.title_english && anime.title_romaji && anime.title_english !== anime.title_romaji && (
              <h2 className="text-xl text-gray-500">{anime.title_romaji}</h2>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column: Cover and Rating Widget */}
          <div className="lg:col-span-1 space-y-6">
            <div className="bg-white rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] overflow-hidden">
              <img
                src={getImageUrl(anime.cover_image_url)}
                alt={getAnimeTitle(anime)}
                className="w-full"
                onError={(e) => {
                  e.target.src = '/placeholder-anime.svg';
                }}
              />
            </div>

            <RatingWidget
              animeId={id}
              currentRating={myRating}
              onRate={handleRate}
              onStatusChange={handleStatusChange}
            />
          </div>

          {/* Right Column: Details */}
          <div className="lg:col-span-2 space-y-6">
            {/* Title and Basic Info - Desktop only */}
            <div className="hidden lg:block bg-white rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] p-6">
              <h1 className="text-3xl font-bold mb-2">{getAnimeTitle(anime)}</h1>
              {language === 'ko' && anime.title_korean && anime.title_romaji && (
                <h2 className="text-xl text-gray-500 mb-4">{anime.title_romaji}</h2>
              )}
              {language === 'en' && anime.title_english && anime.title_romaji && anime.title_english !== anime.title_romaji && (
                <h2 className="text-xl text-gray-500 mb-4">{anime.title_romaji}</h2>
              )}

              {/* AniPass 사이트 평가 */}
              <div className="mb-6 flex gap-8 items-center justify-center">
                {/* 왼쪽: 종합 평점 */}
                <div className="flex flex-col items-center">
                  <div className="text-sm font-medium text-gray-600 mb-3">
                    {language === 'ko' ? '종합 평점' : 'Overall Rating'}
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`text-6xl ${anime.site_rating_count > 0 ? 'text-yellow-500' : 'text-gray-300'}`}>★</span>
                    <div>
                      <div className="text-5xl font-bold">
                        {anime.site_rating_count > 0 ? anime.site_average_rating?.toFixed(1) : '--'}
                      </div>
                      <div className="text-base text-gray-600 mt-1">
                        {anime.site_rating_count > 0
                          ? (language === 'ko' ? `${anime.site_rating_count}명 평가` : `${anime.site_rating_count} ratings`)
                          : (language === 'ko' ? '아직 평가 없음' : 'No ratings yet')
                        }
                      </div>
                    </div>
                  </div>
                </div>

                {/* 오른쪽: 별점 히스토그램 (컴팩트) */}
                <div className="flex-1 max-w-md space-y-0.5">
                  {[5, 4.5, 4, 3.5, 3, 2.5, 2, 1.5, 1, 0.5].map((star) => {
                    const dist = anime.site_rating_distribution?.find(d => d.rating === star);
                    const count = dist ? dist.count : 0;
                    const percentage = anime.site_rating_count > 0 ? (count / anime.site_rating_count) * 100 : 0;

                    return (
                      <div key={star} className="flex items-center gap-1.5 text-xs">
                        <span className={`w-10 text-right font-medium ${anime.site_rating_count > 0 ? 'text-yellow-500' : 'text-gray-400'}`}>
                          ★{star.toFixed(1)}
                        </span>
                        <div className="flex-1 bg-gray-200 rounded-full h-2 overflow-hidden">
                          <div
                            className={`h-2 rounded-full transition-all duration-500 ${anime.site_rating_count > 0 ? 'bg-yellow-500' : 'bg-gray-300'}`}
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

              <div className="grid grid-cols-2 gap-4 text-sm">
                {anime.status && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '방영 상태:' : 'Status:'}</span> {anime.status}
                  </div>
                )}
                {anime.format && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '포맷:' : 'Format:'}</span> {anime.format}
                  </div>
                )}
                {anime.episodes && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '에피소드:' : 'Episodes:'}</span> {anime.episodes}{language === 'ko' ? '화' : ''}
                  </div>
                )}
                {anime.duration && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '러닝타임:' : 'Duration:'}</span> {anime.duration}min
                  </div>
                )}
                {anime.start_date && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '방영 시작:' : 'Start Date:'}</span> {anime.start_date}
                  </div>
                )}
                {anime.season && anime.season_year && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '시즌:' : 'Season:'}</span> {anime.season} {anime.season_year}
                  </div>
                )}
                {anime.source && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '원작:' : 'Source:'}</span> {anime.source}
                  </div>
                )}
                {anime.country_of_origin && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '국가:' : 'Country:'}</span> {anime.country_of_origin}
                  </div>
                )}
              </div>

              {anime.genres && anime.genres.length > 0 && (
                <div className="mt-4">
                  <span className="font-medium text-sm">{language === 'ko' ? '장르:' : 'Genres:'}</span>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {anime.genres.map((genre) => (
                      <span
                        key={genre}
                        className="bg-blue-50 text-blue-700 px-3 py-1 rounded-full text-sm"
                      >
                        {genre}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {anime.studios && anime.studios.length > 0 && (
                <div className="mt-4">
                  <span className="font-medium text-sm">{language === 'ko' ? '제작사:' : 'Studios:'}</span>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {anime.studios.map((studio, idx) => (
                      <span
                        key={idx}
                        className="bg-gray-100 text-gray-800 px-3 py-1 rounded text-sm"
                      >
                        {studio.name || studio}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {anime.tags && anime.tags.length > 0 && (
                <div className="mt-4">
                  <span className="font-medium text-sm">{language === 'ko' ? '태그:' : 'Tags:'}</span>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {anime.tags.slice(0, 10).map((tag, idx) => (
                      <span
                        key={idx}
                        className="bg-purple-50 text-purple-700 px-2 py-1 rounded text-xs"
                        title={tag.description}
                      >
                        {tag.name}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Basic Info - Mobile only (without title) */}
            <div className="lg:hidden bg-white rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] p-6">
              {/* AniPass 사이트 평가 */}
              <div className="mb-6 flex gap-8 items-center justify-center">
                {/* 왼쪽: 종합 평점 */}
                <div className="flex flex-col items-center">
                  <div className="text-sm font-medium text-gray-600 mb-3">
                    {language === 'ko' ? '종합 평점' : 'Overall Rating'}
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`text-6xl ${anime.site_rating_count > 0 ? 'text-yellow-500' : 'text-gray-300'}`}>★</span>
                    <div>
                      <div className="text-5xl font-bold">
                        {anime.site_rating_count > 0 ? anime.site_average_rating?.toFixed(1) : '--'}
                      </div>
                      <div className="text-base text-gray-600 mt-1">
                        {anime.site_rating_count > 0
                          ? (language === 'ko' ? `${anime.site_rating_count}명 평가` : `${anime.site_rating_count} ratings`)
                          : (language === 'ko' ? '아직 평가 없음' : 'No ratings yet')
                        }
                      </div>
                    </div>
                  </div>
                </div>

                {/* 오른쪽: 별점 히스토그램 (컴팩트) */}
                <div className="flex-1 max-w-md space-y-0.5">
                  {[5, 4.5, 4, 3.5, 3, 2.5, 2, 1.5, 1, 0.5].map((star) => {
                    const dist = anime.site_rating_distribution?.find(d => d.rating === star);
                    const count = dist ? dist.count : 0;
                    const percentage = anime.site_rating_count > 0 ? (count / anime.site_rating_count) * 100 : 0;

                    return (
                      <div key={star} className="flex items-center gap-1.5 text-xs">
                        <span className={`w-10 text-right font-medium ${anime.site_rating_count > 0 ? 'text-yellow-500' : 'text-gray-400'}`}>
                          ★{star.toFixed(1)}
                        </span>
                        <div className="flex-1 bg-gray-200 rounded-full h-2 overflow-hidden">
                          <div
                            className={`h-2 rounded-full transition-all duration-500 ${anime.site_rating_count > 0 ? 'bg-yellow-500' : 'bg-gray-300'}`}
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

              <div className="grid grid-cols-2 gap-4 text-sm">
                {anime.status && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '방영 상태:' : 'Status:'}</span> {anime.status}
                  </div>
                )}
                {anime.format && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '포맷:' : 'Format:'}</span> {anime.format}
                  </div>
                )}
                {anime.episodes && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '에피소드:' : 'Episodes:'}</span> {anime.episodes}{language === 'ko' ? '화' : ''}
                  </div>
                )}
                {anime.duration && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '러닝타임:' : 'Duration:'}</span> {anime.duration}min
                  </div>
                )}
                {anime.start_date && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '방영 시작:' : 'Start Date:'}</span> {anime.start_date}
                  </div>
                )}
                {anime.season && anime.season_year && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '시즌:' : 'Season:'}</span> {anime.season} {anime.season_year}
                  </div>
                )}
                {anime.source && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '원작:' : 'Source:'}</span> {anime.source}
                  </div>
                )}
                {anime.country_of_origin && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '국가:' : 'Country:'}</span> {anime.country_of_origin}
                  </div>
                )}
              </div>

              {anime.genres && anime.genres.length > 0 && (
                <div className="mt-4">
                  <span className="font-medium text-sm">{language === 'ko' ? '장르:' : 'Genres:'}</span>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {anime.genres.map((genre) => (
                      <span
                        key={genre}
                        className="bg-blue-50 text-blue-700 px-3 py-1 rounded-full text-sm"
                      >
                        {genre}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {anime.studios && anime.studios.length > 0 && (
                <div className="mt-4">
                  <span className="font-medium text-sm">{language === 'ko' ? '제작사:' : 'Studios:'}</span>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {anime.studios.map((studio, idx) => (
                      <span
                        key={idx}
                        className="bg-gray-100 text-gray-800 px-3 py-1 rounded text-sm"
                      >
                        {studio.name || studio}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {anime.tags && anime.tags.length > 0 && (
                <div className="mt-4">
                  <span className="font-medium text-sm">{language === 'ko' ? '태그:' : 'Tags:'}</span>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {anime.tags.slice(0, 10).map((tag, idx) => (
                      <span
                        key={idx}
                        className="bg-purple-50 text-purple-700 px-2 py-1 rounded text-xs"
                        title={tag.description}
                      >
                        {tag.name}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Synopsis */}
            {anime.description && (
              <div className="bg-white rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] p-6">
                <h3 className="text-xl font-bold mb-4">{language === 'ko' ? '줄거리' : 'Synopsis'}</h3>
                <p className="text-gray-700 whitespace-pre-line">{anime.description}</p>
              </div>
            )}

            {/* Characters & Voice Actors */}
            {anime.characters && anime.characters.length > 0 && (
              <div className="bg-white rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] p-6">
                <h3 className="text-xl font-bold mb-4">{language === 'ko' ? '캐릭터 & 성우' : 'Characters & Voice Actors'}</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {anime.characters.map((char, idx) => (
                    <div key={idx} className="flex items-center gap-4 p-3 border border-gray-200 rounded-lg hover:shadow-[0_2px_12px_rgba(0,0,0,0.08)] transition-shadow">
                      <div
                        className="flex items-center gap-3 flex-1 cursor-pointer"
                        onClick={() => navigate(`/character/${char.character_id}`)}
                      >
                        <div className="relative">
                          <img
                            src={getImageUrl(char.character_image)}
                            alt={char.character_name}
                            className="w-16 h-16 rounded-full object-cover"
                            onError={(e) => {
                              e.target.src = '/placeholder-anime.svg';
                            }}
                          />
                          {/* Role Badge */}
                          {char.character_role && (
                            <div className={`absolute -bottom-1 -right-1 px-1.5 py-0.5 rounded text-xs font-bold`} style={{
                              backgroundColor: char.character_role === 'MAIN' ? '#A8E6CF' : char.character_role === 'SUPPORTING' ? '#364F6B' : '#ECF0F1',
                              color: char.character_role === 'BACKGROUND' ? '#364F6B' : 'white'
                            }}>
                              {char.character_role === 'MAIN'
                                ? (language === 'ko' ? '주연' : 'Main')
                                : char.character_role === 'SUPPORTING'
                                ? (language === 'ko' ? '조연' : 'Supporting')
                                : (language === 'ko' ? '엑스트라' : 'Extra')}
                            </div>
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="font-medium text-sm truncate hover:text-[#A8E6CF] transition-colors">{char.character_name}</h4>
                          <p className="text-xs text-gray-400">{language === 'ko' ? '캐릭터' : 'Character'}</p>
                        </div>
                      </div>
                      {char.voice_actor_name && (
                        <div className="flex items-center gap-3 flex-1 border-l border-gray-200 pl-3">
                          <img
                            src={getImageUrl(char.voice_actor_image)}
                            alt={char.voice_actor_name}
                            className="w-16 h-16 rounded-full object-cover"
                            onError={(e) => {
                              e.target.src = '/placeholder-anime.svg';
                            }}
                          />
                          <div className="flex-1 min-w-0">
                            <h4 className="font-medium text-sm truncate">{char.voice_actor_name}</h4>
                            <p className="text-xs text-gray-500">{language === 'ko' ? '성우' : 'Voice Actor'}</p>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Staff */}
            {anime.staff && anime.staff.length > 0 && (
              <div className="bg-white rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] p-6">
                <h3 className="text-xl font-bold mb-4">{language === 'ko' ? '제작진' : 'Staff'}</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  {anime.staff.map((staff, idx) => (
                    <div key={idx} className="flex flex-col items-center text-center p-3 border border-gray-200 rounded-lg hover:shadow-[0_2px_12px_rgba(0,0,0,0.08)] transition-shadow">
                      <img
                        src={getImageUrl(staff.image_url)}
                        alt={staff.name_full}
                        className="w-20 h-20 rounded-full object-cover mb-2"
                        onError={(e) => {
                          e.target.src = '/placeholder-anime.svg';
                        }}
                      />
                      <h4 className="font-medium text-sm truncate w-full">{staff.name_full}</h4>
                      <p className="text-xs text-gray-500 truncate w-full">{staff.role}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recommendations */}
            {anime.recommendations && anime.recommendations.length > 0 && (
              <div className="bg-white rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] p-6">
                <h3 className="text-xl font-bold mb-4">{language === 'ko' ? '추천 애니메이션' : 'Recommendations'}</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {anime.recommendations.map((rec) => (
                    <div
                      key={rec.id}
                      onClick={() => navigate(`/anime/${rec.id}`)}
                      className="cursor-pointer group"
                    >
                      <div className="aspect-[2/3] bg-gray-200 rounded-lg overflow-hidden mb-2 shadow-[0_2px_12px_rgba(0,0,0,0.08)] group-hover:shadow-[0_4px_16px_rgba(0,0,0,0.12)] transition-shadow">
                        <img
                          src={getImageUrl(rec.cover_image_url)}
                          alt={getAnimeTitle(rec)}
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            e.target.src = '/placeholder-anime.svg';
                          }}
                        />
                      </div>
                      <h4 className="font-medium text-sm line-clamp-2 group-hover:text-[#A8E6CF] transition-colors">
                        {getAnimeTitle(rec)}
                      </h4>
                      {rec.site_rating_count > 0 && (
                        <div className="flex items-center gap-1 text-xs text-gray-600 mt-1">
                          <span className="text-yellow-500">★</span>
                          <span>{rec.site_average_rating.toFixed(1)}</span>
                          <span className="text-gray-400">({rec.site_rating_count})</span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* External Links */}
            {anime.external_links && anime.external_links.length > 0 && (
              <div className="bg-white rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] p-6">
                <h3 className="text-xl font-bold mb-4">{language === 'ko' ? '외부 링크' : 'External Links'}</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {anime.external_links.map((link, idx) => (
                    <a
                      key={idx}
                      href={link.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 p-3 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors"
                    >
                      <span className="text-2xl">🔗</span>
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-sm truncate">{link.site}</h4>
                        <p className="text-xs text-gray-500">{link.type}</p>
                      </div>
                      <span className="text-gray-400">→</span>
                    </a>
                  ))}
                </div>
              </div>
            )}

            {/* Reviews */}
            <div className="bg-white rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-bold">
                  {language === 'ko' ? '리뷰' : 'Reviews'} ({reviews.length})
                </h3>
                {!myReview && (
                  <button
                    onClick={() => {
                      if (!showReviewForm) {
                        setReviewData({
                          content: '',
                          is_spoiler: false,
                          rating: myRating?.rating || 0
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
                      placeholder={language === 'ko' ? '이 작품에 대한 당신의 생각을 공유해주세요...' : 'Share your thoughts about this anime...'}
                      required
                    />
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

              {reviews.length > 0 ? (
                <div className="space-y-4">
                  {reviews.map((review) => {
                    const likeInfo = reviewLikes[review.id] || { liked: review.user_liked || false, count: review.likes_count || 0 };
                    const reviewComments = comments[review.id] || [];
                    const isExpanded = expandedComments.has(review.id);
                    const levelInfo = getCurrentLevelInfo(review.otaku_score || 0);

                    // Use review data directly from backend (includes avatar_url, username, display_name)
                    const isMyReview = review.user_id === user?.id;

                    return (
                      <div key={review.id} className="bg-white rounded-xl shadow-[0_2px_12px_rgba(0,0,0,0.08)] border border-gray-200 p-4 hover:shadow-[0_2px_12px_rgba(0,0,0,0.08)] transition-all">
                        <div className="flex gap-4">
                          {/* 왼쪽: 작품 이미지 */}
                          <Link
                            to={`/anime/${id}`}
                            className="flex-shrink-0 hover:opacity-80 transition-opacity cursor-pointer"
                          >
                            <img
                              src={getImageUrl(anime?.cover_image_url)}
                              alt={getAnimeTitle(anime)}
                              className="w-16 h-24 object-cover rounded border-2 border-transparent hover:border-[#A8E6CF] transition-all"
                              onError={(e) => {
                                e.target.src = '/placeholder-anime.svg';
                              }}
                            />
                          </Link>

                          {/* 오른쪽: 콘텐츠 */}
                          <div className="flex-1 min-w-0">
                            {/* User Info - Feed와 완전히 동일한 구조 */}
                            <div className="flex items-start justify-between mb-2">
                              <div className="flex items-center gap-2">
                                {/* User Avatar */}
                                <Link to={`/user/${review.user_id}`} className="flex-shrink-0">
                                  {review.avatar_url ? (
                                    <img
                                      src={getAvatarUrl(review.avatar_url)}
                                      alt={review.display_name || review.username}
                                      className="w-8 h-8 rounded-full object-cover border border-gray-200"
                                      onError={(e) => handleAvatarError(e, review.user_id)}
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
                                  {language === 'ko' ? '작품을 평가했어요' : 'rated this anime'}
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

                            {/* 작품 제목 */}
                            <Link
                              to={`/anime/${id}`}
                              className="block group"
                            >
                              <h3 className="font-semibold text-gray-900 group-hover:text-[#A8E6CF] transition-colors mb-2 group-hover:underline">
                                {getAnimeTitle(anime)}
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

                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleToggleSaveReview(review);
                                }}
                                className="flex items-center gap-2 transition-all hover:scale-110"
                                style={{
                                  color: savedActivities.has(getActivityKey(review)) ? '#A8E6CF' : '#6B7280'
                                }}
                              >
                                {savedActivities.has(getActivityKey(review)) ? (
                                  <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
                                  </svg>
                                ) : (
                                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
                                  </svg>
                                )}
                                {savedActivities.has(getActivityKey(review)) && (
                                  <span className="text-sm font-medium">1</span>
                                )}
                              </button>
                            </div>

                            {/* Comments Section - Feed와 동일한 구조 */}
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
                                                onClick={() => handleToggleCommentLike(review.id, comment.id)}
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
                                                  value={replyText[`${review.id}-${comment.id}`] || ''}
                                                  onChange={(e) => setReplyText(prev => ({
                                                    ...prev,
                                                    [`${review.id}-${comment.id}`]: e.target.value
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
                                                      onClick={() => handleToggleCommentLike(review.id, reply.id)}
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

                                {/* Comment Input - Feed와 동일한 위치 */}
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
