import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { userService } from '../services/userService';
import { useLanguage } from '../context/LanguageContext';
import { getCurrentLevelInfo } from '../utils/otakuLevels';
import { getAvatarUrl as getAvatarUrlHelper } from '../utils/imageHelpers';

export default function Leaderboard() {
  const { language } = useLanguage();
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadLeaderboard();
  }, []);

  const loadLeaderboard = async () => {
    try {
      setLoading(true);
      const data = await userService.getLeaderboard(100);
      setLeaderboard(data || []);
      setLoading(false);
    } catch (err) {
      console.error('Failed to load leaderboard:', err);
      setLoading(false);
    }
  };

  const getAvatarUrl = (avatarUrl) => {
    return getAvatarUrlHelper(avatarUrl) || '/placeholder-avatar.png';
  };

  const toRoman = (num) => {
    const romanNumerals = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X'];
    return romanNumerals[num - 1] || num;
  };

  if (loading) {
    return (
      <div className="min-h-screen pt-0 md:pt-16 bg-transparent">
        <div className="flex justify-center items-center h-screen">
          <div className="text-xl text-gray-600">{language === 'ko' ? '로딩 중...' : 'Loading...'}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-0 md:pt-16 bg-transparent">

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8">
        <div className="bg-white rounded-lg shadow-[0_2px_12px_rgba(0,0,0,0.08)] overflow-hidden">
          <table className="w-full">
            <thead className="bg-gradient-to-r from-gray-50 to-gray-100 border-b-2 border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  {language === 'ko' ? '순위' : 'Rank'}
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  {language === 'ko' ? '사용자' : 'User'}
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  {language === 'ko' ? '등급' : 'Level'}
                </th>
                <th className="hidden md:table-cell px-4 py-3 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  {language === 'ko' ? '애니 평가' : 'Anime Rated'}
                </th>
                <th className="hidden md:table-cell px-4 py-3 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  {language === 'ko' ? '캐릭터 평가' : 'Character Rated'}
                </th>
                <th className="hidden md:table-cell px-4 py-3 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  {language === 'ko' ? '리뷰' : 'Reviews'}
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  {language === 'ko' ? '오타쿠 점수' : 'Otaku Score'}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {leaderboard.map((user, index) => {
                const levelInfo = getCurrentLevelInfo(user.otaku_score);
                const isTopThree = index < 3;
                const rankEmoji = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : '';

                return (
                  <tr
                    key={user.id}
                    className={`hover:bg-gray-50 transition-colors`}
                    style={isTopThree ? {
                      background: index === 0
                        ? 'linear-gradient(to right, rgba(255, 215, 0, 0.15), transparent)' // Gold
                        : index === 1
                        ? 'linear-gradient(to right, rgba(192, 192, 192, 0.15), transparent)' // Silver
                        : 'linear-gradient(to right, rgba(205, 127, 50, 0.15), transparent)' // Bronze
                    } : {}}
                  >
                    {/* Rank */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className={`text-center ${isTopThree ? 'text-2xl' : 'text-lg font-bold text-gray-600'}`}>
                        {rankEmoji || (index + 1)}
                      </div>
                    </td>

                    {/* User */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Link to={`/user/${user.id}`} className="flex items-center gap-3 hover:text-[#A8E6CF] transition-colors">
                        {user.avatar_url ? (
                          <img
                            src={getAvatarUrl(user.avatar_url)}
                            alt={user.display_name || user.username}
                            className={`flex-shrink-0 rounded-full object-cover border ${
                              isTopThree ? 'w-12 h-12 border-2 border-yellow-400' : 'w-10 h-10 border-gray-200'
                            }`}
                            onError={(e) => {
                              e.target.style.display = 'none';
                            }}
                          />
                        ) : (
                          <div
                            className={`flex-shrink-0 rounded-full flex items-center justify-center border ${
                              isTopThree ? 'w-12 h-12 border-2 border-yellow-400' : 'w-10 h-10 border-gray-200'
                            }`}
                            style={{ background: 'linear-gradient(to bottom right, #90B2E4, #638CCC)' }}
                          >
                            <span className={`text-white font-bold ${isTopThree ? 'text-lg' : 'text-sm'}`}>
                              {(user.display_name || user.username || '?').charAt(0).toUpperCase()}
                            </span>
                          </div>
                        )}
                        <div className={`font-semibold text-gray-900 ${isTopThree ? 'text-base' : 'text-sm'}`}>
                          {user.display_name || user.username}
                        </div>
                      </Link>
                    </td>

                    {/* Level */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex text-xs px-2 py-0.5 rounded-full font-semibold ${levelInfo.bgGradient} border ${levelInfo.borderColor}`}>
                        <span style={{ color: levelInfo.color }} className="font-bold">{levelInfo.icon}</span> <span className="text-gray-700">{levelInfo.level} - {toRoman(levelInfo.rank)}</span>
                      </span>
                    </td>

                    {/* Anime Rated */}
                    <td className="hidden md:table-cell px-6 py-4 whitespace-nowrap text-center text-sm text-gray-900">
                      {user.total_rated}
                    </td>

                    {/* Character Rated */}
                    <td className="hidden md:table-cell px-6 py-4 whitespace-nowrap text-center text-sm text-gray-900">
                      {user.total_character_ratings || 0}
                    </td>

                    {/* Reviews */}
                    <td className="hidden md:table-cell px-6 py-4 whitespace-nowrap text-center text-sm text-gray-900">
                      {user.total_reviews || 0}
                    </td>

                    {/* Otaku Score */}
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <div className={`font-bold ${isTopThree ? 'text-xl text-[#FC5185]' : 'text-lg text-gray-900'}`}>
                        {Math.round(user.otaku_score)}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {leaderboard.length === 0 && (
          <div className="text-center py-16">
            <p className="text-gray-600">{language === 'ko' ? '아직 사용자가 없습니다.' : 'No users yet.'}</p>
          </div>
        )}
      </div>
    </div>
  );
}
