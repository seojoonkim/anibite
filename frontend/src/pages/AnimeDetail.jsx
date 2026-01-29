import { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { animeService } from '../services/animeService';
import { ratingService } from '../services/ratingService';
import { reviewService } from '../services/reviewService';
import { activityService } from '../services/activityService';
import { useActivities } from '../hooks/useActivity';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { getPrefetchedData } from '../hooks/usePrefetch';
import * as ActivityUtils from '../utils/activityUtils';
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
    activities: otherActivities,
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

  // Combine myRating/myReview with other activities
  const activities = useMemo(() => {
    const allActivities = [...otherActivities];

    // If user has rating, add it to the top (if not already in the list)
    if (myRating && user) {
      const myActivityIndex = allActivities.findIndex(a => a.user_id === user.id);

      if (myActivityIndex === -1 && (myRating.rating || myReview)) {
        // Create activity object for my rating/review
        const myActivity = {
          id: `my-activity-${id}`,
          user_id: user.id,
          username: user.username,
          display_name: user.display_name,
          avatar_url: user.avatar_url,
          activity_type: 'anime_rating',
          item_id: parseInt(id),
          item_title: anime?.title_romaji,
          item_title_korean: anime?.title_korean,
          item_image: anime?.cover_image_url,
          rating: myRating.rating,
          review_content: myReview?.content || null,
          review_title: myReview?.title || null,
          is_spoiler: myReview?.is_spoiler || false,
          activity_time: myReview?.created_at || myRating.created_at || new Date().toISOString(),
          likes_count: myReview?.likes_count || 0,
          comments_count: myReview?.comments_count || 0,
          user_liked: false,
          otaku_score: user.otaku_score || 0
        };

        // Add to the beginning
        allActivities.unshift(myActivity);
      }
    }

    return allActivities;
  }, [otherActivities, myRating, myReview, user, id, anime]);

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
      // Check for prefetched data first
      const prefetched = getPrefetchedData('anime', id, user?.id);

      if (prefetched) {
        // Use prefetched data for instant display
        if (prefetched.anime) {
          setAnime(prefetched.anime);
          setLoading(false);
        }
        if (prefetched.myRating) {
          setMyRating(prefetched.myRating);
        }
        if (prefetched.myReview) {
          processMyReview(prefetched.myReview);
        }
        return; // Skip API calls, data is already fresh from prefetch
      }

      // 1단계: 애니메이션 기본 정보 먼저 로드하고 즉시 표시
      const animeData = await animeService.getAnimeById(id);

      if (!animeData) {
        setError('애니메이션을 찾을 수 없습니다.');
        setLoading(false);
        return;
      }

      // 기본 정보 설정하고 즉시 화면 표시
      setAnime(animeData);
      setLoading(false); // 여기서 로딩 해제 - 기본 정보 바로 표시

      // 2단계: 내 평점/리뷰를 백그라운드에서 로드 (화면에 이미 표시 됨)
      if (user) {
        const [myRatingData, myReviewData] = await Promise.all([
          ratingService.getUserRating(id).catch(() => null),
          reviewService.getMyReview(id).catch(() => null)
        ]);

        // 내 평점
        if (myRatingData) {
          setMyRating(myRatingData);
        }

        // 내 리뷰
        if (myReviewData) {
          processMyReview(myReviewData);
        }
      }

      // 3단계: 다른 사람들의 활동은 useActivities hook에서 자동으로 로드됨
    } catch (err) {
      console.error('Failed to load anime data:', err);
      setError(`데이터를 불러오는데 실패했습니다: ${err.message || '알 수 없는 오류'}`);
      setLoading(false);
    }
  };

  // 컴포넌트 마운트 시 저장된 활동 로드 (하드코딩 임시)
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

    // 좋아요 상태 정보 초기화
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
        commentsToLoad.push(review); // review 객체 전체를 전달
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

      // 내 리뷰에 댓글이 있으면 자동으로 펼치기 로드
      if (data.comments_count > 0) {
        setExpandedComments(prev => new Set([...prev, data.id]));
        loadReviewComments(data);
      }
    }
  };

  // 새로운 형식 핸들링 함수로
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
      alert(language === 'ko' ? '로그인이 필요합니다.' : language === 'ja' ? 'ログインが必要です。' : 'Please login first.');
      return;
    }

    try {
      const review = getReviewById(reviewId);
      if (!review) return;

      const currentLike = reviewLikes[reviewId];
      const newLiked = !currentLike.liked;

      // Use activityService with activity_id
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

  const handleSubmitComment = async (reviewId) => {
    if (!user) {
      alert(language === 'ko' ? '로그인이 필요합니다.' : language === 'ja' ? 'ログインが必要です。' : 'Please login first.');
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
      alert(language === 'ko' ? '댓글 작성에 실패했습니다.' : language === 'ja' ? 'コメント作成に失敗しました。' : 'Failed to create comment.');
    }
  };

  const handleDeleteComment = async (reviewId, commentId) => {
    if (!confirm(language === 'ko' ? '댓글을 삭제하시겠습니까?' : language === 'ja' ? 'このコメントを削除しますか？' : 'Delete this comment?')) return;

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
      alert(language === 'ko' ? '댓글 삭제에 실패했습니다.' : language === 'ja' ? 'コメント削除に失敗しました。' : 'Failed to delete comment.');
    }
  };

  const handleToggleCommentLike = async (reviewId, commentId) => {
    if (!user) {
      alert(language === 'ko' ? '로그인이 필요합니다.' : language === 'ja' ? 'ログインが必要です。' : 'Please login first.');
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
      // 로컬 스토리지에 저장 (하드코딩 임시)
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
      alert(language === 'ko' ? '로그인이 필요합니다.' : language === 'ja' ? 'ログインが必要です。' : 'Please login first.');
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
      alert(language === 'ko' ? '답글 작성에 실패했습니다.' : language === 'ja' ? '返信作成に失敗しました。' : 'Failed to create reply.');
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

    if (diffInSeconds < 3600) return language === 'ko' ? `${Math.max(1, Math.floor(diffInSeconds / 60))}분 전` : language === 'ja' ? `${Math.max(1, Math.floor(diffInSeconds / 60))}分前` : `${Math.max(1, Math.floor(diffInSeconds / 60))}m ago`;
    if (diffInSeconds < 86400) return language === 'ko' ? `${Math.floor(diffInSeconds / 3600)}시간 전` : language === 'ja' ? `${Math.floor(diffInSeconds / 3600)}時間前` : `${Math.floor(diffInSeconds / 3600)}h ago`;
    if (diffInSeconds < 604800) return language === 'ko' ? `${Math.floor(diffInSeconds / 86400)}일 전` : language === 'ja' ? `${Math.floor(diffInSeconds / 86400)}日前` : `${Math.floor(diffInSeconds / 86400)}d ago`;
    return past.toLocaleDateString(language === 'ko' ? 'ko-KR' : language === 'ja' ? 'ja-JP' : 'en-US');
  };

  const handleEditReview = () => {
    if (myReview) {
      setReviewData({
        content: myReview.content,
        is_spoiler: myReview.is_spoiler,
        rating: myReview?.user_rating || myRating?.rating || 0
      });
      setIsEditingReview(true);
      setShowReviewForm(true);
    }
  };

  const handleDeleteReview = async () => {
    if (!confirm(language === 'ko' ? '리뷰를 삭제하시겠습니까?' : language === 'ja' ? 'このレビューを削除しますか？' : 'Delete this review?')) return;

    try {
      await reviewService.deleteReview(myReview.id);
      setMyReview(null);
      setReviewSuccess(language === 'ko' ? '리뷰가 삭제되었습니다.' : language === 'ja' ? 'レビューが削除されました。' : 'Review deleted successfully.');

      // anime stats를 업데이트 (전체 리프레시 없이)
      const animeData = await animeService.getAnimeById(id);
      if (animeData) setAnime(animeData);

      // Refresh activities list
      await refetchActivities();

      setTimeout(() => setReviewSuccess(''), 3000);
    } catch (err) {
      console.error('Failed to delete review:', err);
      setReviewError(language === 'ko' ? '리뷰 삭제에 실패했습니다.' : language === 'ja' ? 'レビュー削除に失敗しました。' : 'Failed to delete review.');
    }
  };

  const handleSubmitReview = async (e) => {
    e.preventDefault();
    setReviewError('');
    setReviewSuccess('');

    if (reviewData.rating === 0 || !reviewData.rating) {
      setReviewError(language === 'ko' ? '별점을 선택해주세요.' : language === 'ja' ? '評価を選択してください。' : 'Please select a rating.');
      return;
    }

    if (!reviewData.content.trim()) {
      setReviewError(language === 'ko' ? '리뷰 내용을 입력해주세요.' : language === 'ja' ? 'レビュー内容を入力してください。' : 'Please enter review content.');
      return;
    }

    try {
      if (isEditingReview && myReview) {
        // 수정 시 rating을 리뷰 API에 함께 전송
        await reviewService.updateReview(myReview.id, {
          content: reviewData.content,
          is_spoiler: reviewData.is_spoiler,
          rating: reviewData.rating  // 별점도 함께 전송
        });
        setReviewSuccess(language === 'ko' ? '리뷰가 수정되었습니다.' : language === 'ja' ? 'レビューが編集されました。' : 'Review updated successfully.');
      } else {
        // 새로 작성: 별점과 리뷰를 한번에 전송
        await reviewService.createReview({
          anime_id: parseInt(id),
          content: reviewData.content,
          is_spoiler: reviewData.is_spoiler,
          rating: reviewData.rating  // 별점을 리뷰 API에 함께 전송
        });

        setReviewSuccess(language === 'ko' ? '리뷰가 작성되었습니다.' : language === 'ja' ? 'レビューが作成されました。' : 'Review submitted successfully.');
      }

      setReviewData({ content: '', is_spoiler: false, rating: 0 });
      setShowReviewForm(false);
      setIsEditingReview(false);

      // 로컬 state를 업데이트 (전체 리프레시 없이)
      if (isEditingReview) {
        // 리뷰 수정: myReview, myRating, anime 업데이트
        const [updatedMyReview, updatedMyRating, updatedAnime] = await Promise.all([
          reviewService.getMyReview(id).catch(() => null),
          ratingService.getUserRating(id).catch(() => null),
          animeService.getAnimeById(id).catch(() => null)
        ]);

        if (updatedMyReview) setMyReview(updatedMyReview);
        if (updatedMyRating) setMyRating(updatedMyRating);
        if (updatedAnime) setAnime(updatedAnime);

        // Refresh activities list to update review list immediately
        await refetchActivities();
      } else {
        // 새 리뷰 작성: myReview, myRating과 anime stats를 업데이트
        const [myReviewData, myRatingData, animeData] = await Promise.all([
          reviewService.getMyReview(id).catch(() => null),
          ratingService.getUserRating(id).catch(() => null),
          animeService.getAnimeById(id)
        ]);

        if (myReviewData) setMyReview(myReviewData);
        if (myRatingData) setMyRating(myRatingData);
        if (animeData) setAnime(animeData);
      }

      setTimeout(() => setReviewSuccess(''), 3000);
    } catch (err) {
      console.error('리뷰 제출 실패:', err);
      setReviewError(
        language === 'ko'
          ? err.response?.data?.detail || '리뷰 작성에 실패했습니다.'
          : language === 'ja'
          ? err.response?.data?.detail || 'レビュー作成に失敗しました。'
          : err.response?.data?.detail || 'Failed to submit review.'
      );
    }
  };

  const handleRate = async (rating, status) => {
    try {
      await ratingService.rateAnime(id, { rating, status });

      // 병렬로 데이터 새로고침 (리뷰 목록 포함)
      const [myRatingData, animeData, reviewData] = await Promise.all([
        ratingService.getUserRating(id).catch(() => null),
        animeService.getAnimeById(id),
        reviewService.getAnimeReviews(id, { page: 1, page_size: 10 })
      ]);

      if (myRatingData) setMyRating(myRatingData);
      if (animeData) setAnime(animeData);
      if (reviewData) {
        setReviews(reviewData.items || []);
      }

      // Update myReview rating if it exists
      if (myReview) {
        setMyReview({
          ...myReview,
          user_rating: rating
        });
      }
    } catch (err) {
      console.error('Failed to rate:', err);
      alert(language === 'ko' ? '평점 저장에 실패했습니다.' : language === 'ja' ? '評価の保存に失敗しました。' : 'Failed to save rating.');
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

  // SVG Star icon component
  const StarIcon = ({ className = "w-6 h-6", filled = true }) => (
    <svg className={className} viewBox="0 0 20 20" fill={filled ? "url(#star-gradient-detail)" : "currentColor"}>
      <defs>
        <linearGradient id="star-gradient-detail" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style={{ stopColor: '#F5C842', stopOpacity: 1 }} />
          <stop offset="50%" style={{ stopColor: '#E8B835', stopOpacity: 1 }} />
          <stop offset="100%" style={{ stopColor: '#D9A828', stopOpacity: 1 }} />
        </linearGradient>
      </defs>
      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
    </svg>
  );

  const getImageUrl = (imageUrl) => {
    if (!imageUrl) return '/placeholder-anime.svg';

    // Handle AniList character images - convert to R2
    if (imageUrl.includes('anilist.co') && imageUrl.includes('/character/')) {
      // AniList pattern: /character/large/b{id}- or /character/large/n{id}-
      const match = imageUrl.match(/\/[bn](\d+)-/);
      if (match && match[1]) {
        const characterId = match[1];
        return `${IMAGE_BASE_URL}/images/characters/${characterId}.jpg`;
      }
    }

    // Handle AniList staff/voice actor images - convert to R2
    if (imageUrl.includes('anilist.co') && imageUrl.includes('/staff/')) {
      // AniList pattern: /staff/large/n{id}- or /staff/large/b{id}-
      const match = imageUrl.match(/\/[bn](\d+)-/);
      if (match && match[1]) {
        const staffId = match[1];
        return `${IMAGE_BASE_URL}/images/staff/${staffId}.jpg`;
      }
    }

    // External URLs (AniList, etc) - use placeholder
    if (imageUrl.startsWith('http')) return '/placeholder-anime.svg';

    // Use covers_large for better quality
    const processedUrl = imageUrl.includes('/covers/')
      ? imageUrl.replace('/covers/', '/covers_large/')
      : imageUrl;
    return `${IMAGE_BASE_URL}${processedUrl}`;
  };

  // Get character image URL - use character_id as fallback when image is null
  const getCharacterImageUrl = (char) => {
    if (char.character_image) {
      return getImageUrl(char.character_image);
    }
    // Fallback: try R2 path using character_id
    if (char.character_id) {
      return `${IMAGE_BASE_URL}/images/characters/${char.character_id}.jpg`;
    }
    return '/placeholder-anime.svg';
  };

  // Get voice actor image URL - use voice_actor_id as fallback when image is null
  const getVoiceActorImageUrl = (char) => {
    if (char.voice_actor_image) {
      return getImageUrl(char.voice_actor_image);
    }
    // Fallback: try R2 path using voice_actor_id
    if (char.voice_actor_id) {
      return `${IMAGE_BASE_URL}/images/staff/${char.voice_actor_id}.jpg`;
    }
    return '/placeholder-anime.svg';
  };

  if (loading) {
    return (
      <div className="min-h-screen pt-10 md:pt-12 bg-transparent">
        <div className="max-w-[1180px] mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8">
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
      <div className="min-h-screen pt-10 md:pt-12 bg-transparent">
        <div className="max-w-[1180px] mx-auto px-4 py-8">
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {error || '애니메이션을 찾을 수 없습니다.'}
          </div>
          <button
            onClick={() => navigate('/')}
            className="mt-4 text-blue-500 hover:text-[#5BB5F5]"
          >
            홈으로 돌아가기
          </button>
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

              {/* AniPass 스타일 평점 */}
              <div className="mb-6 flex gap-8 items-center justify-center">
                {/* 왼쪽: 종합 평점 */}
                <div className="flex flex-col items-center">
                  <div className="text-sm font-medium text-gray-600 mb-3">
                    {language === 'ko' ? '종합 평점' : language === 'ja' ? '総合評価' : 'Overall Rating'}
                  </div>
                  <div className="flex items-center gap-3">
                    <StarIcon className={`w-14 h-14 ${anime.site_rating_count > 0 ? '' : 'text-gray-300'}`} filled={anime.site_rating_count > 0} />
                    <div>
                      <div className="text-5xl font-bold">
                        {anime.site_rating_count > 0 ? anime.site_average_rating?.toFixed(1) : '--'}
                      </div>
                      <div className="text-base text-gray-600 mt-1">
                        {anime.site_rating_count > 0
                          ? (language === 'ko' ? `${anime.site_rating_count}개 평가` : language === 'ja' ? `${anime.site_rating_count}件の評価` : `${anime.site_rating_count} ratings`)
                          : (language === 'ko' ? '아직 평가 없음' : language === 'ja' ? 'まだ評価がありません' : 'No ratings yet')
                        }
                      </div>
                    </div>
                  </div>
                </div>

                {/* 오른쪽: 별점 히스토그램(컴팩트) */}
                <div className="flex-1 max-w-md space-y-0.5">
                  {[5, 4.5, 4, 3.5, 3, 2.5, 2, 1.5, 1, 0.5].map((star) => {
                    const dist = anime.site_rating_distribution?.find(d => d.rating === star);
                    const count = dist ? dist.count : 0;
                    const percentage = anime.site_rating_count > 0 ? (count / anime.site_rating_count) * 100 : 0;

                    return (
                      <div key={star} className="flex items-center gap-1.5 text-xs">
                        <span className={`w-12 text-right font-medium flex items-center justify-end gap-0.5 ${anime.site_rating_count > 0 ? '' : 'text-gray-400'}`}>
                          <StarIcon className="w-3 h-3" filled={anime.site_rating_count > 0} />
                          <span>{star.toFixed(1)}</span>
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
                    <span className="font-medium">{language === 'ko' ? '방영 상태:' : language === 'ja' ? '放送状態:' : 'Status:'}</span> {anime.status}
                  </div>
                )}
                {anime.format && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '포맷:' : language === 'ja' ? 'フォーマット:' : 'Format:'}</span> {anime.format}
                  </div>
                )}
                {anime.episodes && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '에피소드:' : language === 'ja' ? 'エピソード:' : 'Episodes:'}</span> {anime.episodes}{language === 'ko' ? '화' : language === 'ja' ? '話' : ''}
                  </div>
                )}
                {anime.duration && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '러닝타임:' : language === 'ja' ? '放送時間:' : 'Duration:'}</span> {anime.duration}min
                  </div>
                )}
                {anime.start_date && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '방영 시작:' : language === 'ja' ? '放送開始:' : 'Start Date:'}</span> {anime.start_date}
                  </div>
                )}
                {anime.season && anime.season_year && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '시즌:' : language === 'ja' ? 'シーズン:' : 'Season:'}</span> {anime.season} {anime.season_year}
                  </div>
                )}
                {anime.source && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '원작:' : language === 'ja' ? '原作:' : 'Source:'}</span> {anime.source}
                  </div>
                )}
                {anime.country_of_origin && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '국가:' : language === 'ja' ? '国:' : 'Country:'}</span> {anime.country_of_origin}
                  </div>
                )}
              </div>

              {anime.genres && anime.genres.length > 0 && (
                <div className="mt-4">
                  <span className="font-medium text-sm">{language === 'ko' ? '장르:' : language === 'ja' ? 'ジャンル:' : 'Genres:'}</span>
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
                  <span className="font-medium text-sm">{language === 'ko' ? '제작사:' : language === 'ja' ? 'スタジオ:' : 'Studios:'}</span>
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
                  <span className="font-medium text-sm">{language === 'ko' ? '태그:' : language === 'ja' ? 'タグ:' : 'Tags:'}</span>
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
              {/* AniPass 스타일 평점 */}
              <div className="mb-6 flex gap-8 items-center justify-center">
                {/* 왼쪽: 종합 평점 */}
                <div className="flex flex-col items-center">
                  <div className="text-sm font-medium text-gray-600 mb-3">
                    {language === 'ko' ? '종합 평점' : language === 'ja' ? '総合評価' : 'Overall Rating'}
                  </div>
                  <div className="flex items-center gap-3">
                    <StarIcon className={`w-14 h-14 ${anime.site_rating_count > 0 ? '' : 'text-gray-300'}`} filled={anime.site_rating_count > 0} />
                    <div>
                      <div className="text-5xl font-bold">
                        {anime.site_rating_count > 0 ? anime.site_average_rating?.toFixed(1) : '--'}
                      </div>
                      <div className="text-base text-gray-600 mt-1">
                        {anime.site_rating_count > 0
                          ? (language === 'ko' ? `${anime.site_rating_count}개 평가` : language === 'ja' ? `${anime.site_rating_count}件の評価` : `${anime.site_rating_count} ratings`)
                          : (language === 'ko' ? '아직 평가 없음' : language === 'ja' ? 'まだ評価がありません' : 'No ratings yet')
                        }
                      </div>
                    </div>
                  </div>
                </div>

                {/* 오른쪽: 별점 히스토그램(컴팩트) */}
                <div className="flex-1 max-w-md space-y-0.5">
                  {[5, 4.5, 4, 3.5, 3, 2.5, 2, 1.5, 1, 0.5].map((star) => {
                    const dist = anime.site_rating_distribution?.find(d => d.rating === star);
                    const count = dist ? dist.count : 0;
                    const percentage = anime.site_rating_count > 0 ? (count / anime.site_rating_count) * 100 : 0;

                    return (
                      <div key={star} className="flex items-center gap-1.5 text-xs">
                        <span className={`w-12 text-right font-medium flex items-center justify-end gap-0.5 ${anime.site_rating_count > 0 ? '' : 'text-gray-400'}`}>
                          <StarIcon className="w-3 h-3" filled={anime.site_rating_count > 0} />
                          <span>{star.toFixed(1)}</span>
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
                    <span className="font-medium">{language === 'ko' ? '방영 상태:' : language === 'ja' ? '放送状態:' : 'Status:'}</span> {anime.status}
                  </div>
                )}
                {anime.format && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '포맷:' : language === 'ja' ? 'フォーマット:' : 'Format:'}</span> {anime.format}
                  </div>
                )}
                {anime.episodes && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '에피소드:' : language === 'ja' ? 'エピソード:' : 'Episodes:'}</span> {anime.episodes}{language === 'ko' ? '화' : language === 'ja' ? '話' : ''}
                  </div>
                )}
                {anime.duration && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '러닝타임:' : language === 'ja' ? '放送時間:' : 'Duration:'}</span> {anime.duration}min
                  </div>
                )}
                {anime.start_date && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '방영 시작:' : language === 'ja' ? '放送開始:' : 'Start Date:'}</span> {anime.start_date}
                  </div>
                )}
                {anime.season && anime.season_year && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '시즌:' : language === 'ja' ? 'シーズン:' : 'Season:'}</span> {anime.season} {anime.season_year}
                  </div>
                )}
                {anime.source && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '원작:' : language === 'ja' ? '原作:' : 'Source:'}</span> {anime.source}
                  </div>
                )}
                {anime.country_of_origin && (
                  <div>
                    <span className="font-medium">{language === 'ko' ? '국가:' : language === 'ja' ? '国:' : 'Country:'}</span> {anime.country_of_origin}
                  </div>
                )}
              </div>

              {anime.genres && anime.genres.length > 0 && (
                <div className="mt-4">
                  <span className="font-medium text-sm">{language === 'ko' ? '장르:' : language === 'ja' ? 'ジャンル:' : 'Genres:'}</span>
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
                  <span className="font-medium text-sm">{language === 'ko' ? '제작사:' : language === 'ja' ? 'スタジオ:' : 'Studios:'}</span>
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
                  <span className="font-medium text-sm">{language === 'ko' ? '태그:' : language === 'ja' ? 'タグ:' : 'Tags:'}</span>
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
                <h3 className="text-xl font-bold mb-4">{language === 'ko' ? '줄거리' : language === 'ja' ? 'あらすじ' : 'Synopsis'}</h3>
                <p className="text-gray-700 whitespace-pre-line">{anime.description}</p>
              </div>
            )}

            {/* Characters & Voice Actors */}
            {anime.characters && anime.characters.length > 0 && (
              <div className="bg-white rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] p-6">
                <h3 className="text-xl font-bold mb-4">{language === 'ko' ? '캐릭터 & 성우' : language === 'ja' ? 'キャラクター & 声優' : 'Characters & Voice Actors'}</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {anime.characters.map((char, idx) => (
                    <div key={idx} className="flex items-center gap-4 p-3 border border-gray-200 rounded-lg hover:shadow-[0_2px_12px_rgba(0,0,0,0.08)] transition-shadow">
                      <div
                        className="flex items-center gap-3 flex-1 cursor-pointer"
                        onClick={() => navigate(`/character/${char.character_id}`)}
                      >
                        <div className="relative">
                          <img
                            src={getCharacterImageUrl(char)}
                            alt={char.character_name}
                            className="w-16 h-16 rounded-full object-cover"
                            onError={(e) => {
                              if (e.target.src !== '/placeholder-anime.svg') {
                                e.target.src = '/placeholder-anime.svg';
                              }
                            }}
                          />
                          {/* Role Badge */}
                          {char.character_role && (
                            <div className={`absolute -bottom-1 -right-1 px-1.5 py-0.5 rounded text-xs font-bold`} style={{
                              backgroundColor: char.character_role === 'MAIN' ? '#A8E6CF' : char.character_role === 'SUPPORTING' ? '#364F6B' : '#ECF0F1',
                              color: char.character_role === 'BACKGROUND' ? '#364F6B' : 'white'
                            }}>
                              {char.character_role === 'MAIN'
                                ? (language === 'ko' ? '주연' : language === 'ja' ? 'メイン' : 'Main')
                                : char.character_role === 'SUPPORTING'
                                ? (language === 'ko' ? '조연' : language === 'ja' ? 'サポート' : 'Supporting')
                                : (language === 'ko' ? '엑스트라' : language === 'ja' ? 'エキストラ' : 'Extra')}
                            </div>
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="font-medium text-sm truncate hover:text-[#5BB5F5] transition-colors">{language === 'ko' && char.character_name_korean ? char.character_name_korean : char.character_name}</h4>
                          <p className="text-xs text-gray-400">{language === 'ko' ? '캐릭터' : language === 'ja' ? 'キャラクター' : 'Character'}</p>
                        </div>
                      </div>
                      {char.voice_actor_name && (
                        <div className="flex items-center gap-3 flex-1 border-l border-gray-200 pl-3">
                          <img
                            src={getVoiceActorImageUrl(char)}
                            alt={char.voice_actor_name}
                            className="w-16 h-16 rounded-full object-cover"
                            onError={(e) => {
                              if (e.target.src !== '/placeholder-anime.svg') {
                                e.target.src = '/placeholder-anime.svg';
                              }
                            }}
                          />
                          <div className="flex-1 min-w-0">
                            <h4 className="font-medium text-sm truncate">{char.voice_actor_name}</h4>
                            <p className="text-xs text-gray-500">{language === 'ko' ? '성우' : language === 'ja' ? '声優' : 'Voice Actor'}</p>
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
                <h3 className="text-xl font-bold mb-4">{language === 'ko' ? '제작진' : language === 'ja' ? 'スタッフ' : 'Staff'}</h3>
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
                <h3 className="text-xl font-bold mb-4">{language === 'ko' ? '추천 애니메이션' : language === 'ja' ? 'おすすめアニメ' : 'Recommendations'}</h3>
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
                      <h4 className="font-medium text-sm line-clamp-2 group-hover:text-[#5BB5F5] transition-colors">
                        {getAnimeTitle(rec)}
                      </h4>
                      {rec.site_rating_count > 0 && (
                        <div className="flex items-center gap-1 text-xs text-gray-600 mt-1">
                          <StarIcon className="w-3 h-3" filled={true} />
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
                <h3 className="text-xl font-bold mb-4">{language === 'ko' ? '외부 링크' : language === 'ja' ? '外部リンク' : 'External Links'}</h3>
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
                  {language === 'ko' ? '리뷰' : language === 'ja' ? 'レビュー' : 'Reviews'} ({activities.length})
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
                      ? (language === 'ko' ? '취소' : language === 'ja' ? 'キャンセル' : 'Cancel')
                      : (language === 'ko' ? '리뷰 작성' : language === 'ja' ? 'レビュー作成' : 'Write Review')
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
                      {language === 'ko' ? '별점' : language === 'ja' ? '評価' : 'Rating'} *
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
                      {language === 'ko' ? '리뷰 내용' : language === 'ja' ? 'レビュー内容' : 'Review Content'} *
                    </label>
                    <textarea
                      value={reviewData.content}
                      onChange={(e) => setReviewData({ ...reviewData, content: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md h-32"
                      placeholder={language === 'ko' ? '이 작품에 대한 당신의 생각을 공유해주세요...' : language === 'ja' ? 'この作品についてのあなたの考えをシェアしてください...' : 'Share your thoughts about this anime...'}
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
                        {language === 'ko' ? '스포일러 포함' : language === 'ja' ? 'ネタバレ含む' : 'Contains spoilers'}
                      </span>
                    </label>
                  </div>

                  <button
                    type="submit"
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                  >
                    {isEditingReview
                      ? (language === 'ko' ? '리뷰 수정' : language === 'ja' ? 'レビュー編集' : 'Update Review')
                      : (language === 'ko' ? '리뷰 등록' : language === 'ja' ? 'レビュー作成' : 'Submit Review')
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
                        context="anime_page"
                        onUpdate={refetchActivities}
                        onEditContent={(activity, mode) => {
                          // Only allow editing own content
                          if (user && activity.user_id === user.id) {
                            if (mode === 'add_review' || !myReview) {
                              // Open review form for adding review
                              setReviewData({
                                content: '',
                                is_spoiler: false,
                                rating: myRating?.rating || 0
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
                            if (myReview) {
                              // Delete review (and associated rating)
                              await handleDeleteReview();
                            } else if (myRating) {
                              // Delete rating only
                              if (!confirm(language === 'ko' ? '평점을 삭제하시겠습니까?' : language === 'ja' ? 'この評価を削除しますか？' : 'Delete this rating?')) return;

                              try {
                                await ratingService.deleteRating(id);
                                setMyRating(null);

                                // Refresh data
                                const animeData = await animeService.getAnimeById(id);
                                if (animeData) setAnime(animeData);
                                await refetchActivities();
                              } catch (err) {
                                console.error('Failed to delete rating:', err);
                                alert(language === 'ko' ? '평점 삭제에 실패했습니다.' : language === 'ja' ? '評価削除に失敗しました。' : 'Failed to delete rating.');
                              }
                            }
                          }
                        }}
                      />
                    );
                  })}
                </div>
              ) : (
                <p className="text-gray-600">{language === 'ko' ? '아직 리뷰가 없습니다.' : language === 'ja' ? 'まだレビューがありません。' : 'No reviews yet.'}</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
