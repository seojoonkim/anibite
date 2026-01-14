import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { animeService } from '../services/animeService';
import { ratingService } from '../services/ratingService';
import { reviewService } from '../services/reviewService';
import { activityService } from '../services/activityService';
import { useActivities } from '../hooks/useActivity';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import * as ActivityUtils from '../utils/activityUtils';
import Navbar from '../components/common/Navbar';
import StarRating from '../components/common/StarRating';
import RatingWidget from '../components/anime/RatingWidget';
import ActivityCard from '../components/activity/ActivityCard';
import { getCurrentLevelInfo } from '../utils/otakuLevels';
import { API_BASE_URL, IMAGE_BASE_URL } from '../config/api';

export default function AnimeDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { getAnimeTitle, language } = useLanguage();
  const [anime, setAnime] = useState(null);
  const [myRating, setMyRating] = useState(null);
  const [myReview, setMyReview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [isEditingReview, setIsEditingReview] = useState(false);
  const [reviewData, setReviewData] = useState({ content: '', is_spoiler: false, rating: 0 });
  const [reviewError, setReviewError] = useState('');
  const [reviewSuccess, setReviewSuccess] = useState('');
  const [failedImages, setFailedImages] = useState(new Set());
  const [showEditMenu, setShowEditMenu] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [reviewLikes, setReviewLikes] = useState({});
  const [comments, setComments] = useState({});
  const [expandedComments, setExpandedComments] = useState(new Set());
  const [savedActivities, setSavedActivities] = useState(new Set());

  // Use unified activities hook
  const {
    activities,
    loading: activitiesLoading,
    refetch: refetchActivities
  } = useActivities(
    {
      activityType: 'anime_rating',
      itemId: id,
      limit: 50,
      offset: 0
    },
    {
      autoFetch: true
    }
  );

  // Debug: Log activities when they change
  useEffect(() => {
    console.log('[AnimeDetail] activities loaded:', activities.length, activities);
  }, [activities]);


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
      const [myRatingData, myReviewData] = await Promise.all([
        user ? ratingService.getUserRating(id).catch(() => null) : Promise.resolve(null),
        user ? reviewService.getMyReview(id).catch(() => null) : Promise.resolve(null)
      ]);

      // 내 평점
      if (myRatingData) {
        setMyRating(myRatingData);
      }

      // 내 리뷰
      if (myReviewData) {
        processMyReview(myReviewData);
      }

      // 다른 사람들의 활동은 useActivities hook에서 자동으로 로드됨
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
      const reviewData = await reviewService.getAnimeReviews(id, { page: 1, page_size: 10 });
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
      const reviewData = await reviewService.getAnimeReviews(id, { page: 1, page_size: 10 });
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
      const reviewData = await reviewService.getAnimeReviews(id, { page: 1, page_size: 10 });
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
      const reviewData = await reviewService.getAnimeReviews(id, { page: 1, page_size: 10 });
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
        reviewService.getAnimeReviews(id, { page: 1, page_size: 10 }),
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
                  {language === 'ko' ? '리뷰' : 'Reviews'} ({activities.length})
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

              {activities.length > 0 ? (
                <div className="space-y-4">
                  {activities.map((activity) => (
                    <ActivityCard
                      key={activity.id}
                      activity={activity}
                      context="anime_page"
                      onUpdate={refetchActivities}
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
