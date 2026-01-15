import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { userService } from '../services/userService';
import { ratingService } from '../services/ratingService';
import Navbar from '../components/common/Navbar';
import OtakuMeter from '../components/profile/OtakuMeter';
import GenrePreferences from '../components/profile/GenrePreferences';
import RatingHistory from '../components/profile/RatingHistory';

export default function Profile() {
  const { user } = useAuth();
  const { language } = useLanguage();
  const [stats, setStats] = useState(null);
  const [genrePreferences, setGenrePreferences] = useState([]);
  const [ratings, setRatings] = useState([]);
  const [watchTime, setWatchTime] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadProfileData();
  }, []);

  const loadProfileData = async () => {
    try {
      setLoading(true);

      const [statsData, genreData, ratingsData, watchTimeData] = await Promise.all([
        userService.getStats(),
        userService.getGenrePreferences().catch(() => []),
        ratingService.getMyRatings({ limit: 50 }),
        userService.getWatchTime().catch(() => ({ total_minutes: 0 })),
      ]);

      setStats(statsData);
      setGenrePreferences(genreData);
      setRatings(ratingsData.items || []);
      setWatchTime(watchTimeData);
      setLoading(false);
    } catch (err) {
      console.error('Failed to load profile:', err);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen pt-16 bg-transparent">
        <Navbar />
        <div className="flex justify-center items-center h-screen">
          <div className="text-xl text-gray-600">로딩 중...</div>
        </div>
      </div>
    );
  }

  const formatWatchTime = (minutes) => {
    if (!minutes) return '0시간';
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours === 0) return `${mins}분`;
    if (mins === 0) return `${hours}시간`;
    return `${hours}시간 ${mins}분`;
  };

  return (
    <div className="min-h-screen pt-16 bg-transparent">
      <Navbar />

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* User Info Header */}
        <div className="bg-white rounded-xl shadow-[0_2px_12px_rgba(0,0,0,0.08)] border border-gray-200 p-6 mb-6">
          <div className="flex items-center gap-6">
            <div className="w-16 h-16 bg-gradient-to-br from-gray-800 to-gray-600 rounded-full flex items-center justify-center text-white text-xl font-semibold">
              {(user?.display_name || user?.username || 'U')[0].toUpperCase()}
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {user?.display_name || user?.username}
              </h1>
              <p className="text-base text-gray-500">{user?.email}</p>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          {/* Stats Box */}
          {stats && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 flex flex-col">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">통계</h3>
              <div className="grid grid-cols-2 gap-4 flex-1">
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900">
                    {stats.total_rated || 0}
                  </div>
                  <div className="text-sm text-gray-500 mt-1">평가한 애니</div>
                </div>

                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900">
                    {stats.total_want_to_watch || 0}
                  </div>
                  <div className="text-sm text-gray-500 mt-1">{language === 'ko' ? '보고싶어요' : 'Watchlist'}</div>
                </div>

                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900">
                    {stats.average_rating ? stats.average_rating.toFixed(1) : '-'}
                  </div>
                  <div className="text-sm text-gray-500 mt-1">{language === 'ko' ? '평균 평점' : 'Avg Rating'}</div>
                </div>

                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900">
                    {formatWatchTime(watchTime?.total_minutes)}
                  </div>
                  <div className="text-sm text-gray-500 mt-1">시청 시간</div>
                </div>
              </div>
            </div>
          )}

          {/* Otaku Level */}
          {stats && <OtakuMeter score={stats.otaku_score || 0} />}

          {/* Genre Preferences */}
          <GenrePreferences preferences={genrePreferences} />
        </div>

        {/* Rating History - Full Width */}
        <RatingHistory ratings={ratings} />
      </div>
    </div>
  );
}
