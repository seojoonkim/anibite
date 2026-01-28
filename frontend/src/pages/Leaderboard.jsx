import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { userService } from '../services/userService';
import { useLanguage } from '../context/LanguageContext';
import { getCurrentLevelInfo } from '../utils/otakuLevels';
import { getAvatarUrl as getAvatarUrlHelper } from '../utils/imageHelpers';
import DefaultAvatar from '../components/common/DefaultAvatar';

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
      <div className="min-h-screen pt-10 md:pt-12 bg-transparent">
        <div className="flex justify-center items-center h-screen">
          <div className="text-xl text-text-secondary">{language === 'ko' ? '로딩 중...' : language === 'ja' ? '読み込み中...' : 'Loading...'}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-10 md:pt-12 bg-transparent">

      <div className="max-w-[1180px] mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8">
        <div className="bg-surface rounded-lg shadow-lg border border-border overflow-hidden">
          <table className="w-full">
            <thead className="bg-surface-elevated border-b border-border">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">
                  {language === 'ko' ? '순위' : language === 'ja' ? 'ランキング' : 'Rank'}
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">
                  {language === 'ko' ? '사용자' : language === 'ja' ? 'ユーザー' : 'User'}
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">
                  {language === 'ko' ? '등급' : language === 'ja' ? 'レベル' : 'Level'}
                </th>
                <th className="hidden md:table-cell px-4 py-3 text-center text-xs font-semibold text-text-secondary uppercase tracking-wider">
                  {language === 'ko' ? '애니 평가' : language === 'ja' ? 'アニメ評価' : 'Anime Rated'}
                </th>
                <th className="hidden md:table-cell px-4 py-3 text-center text-xs font-semibold text-text-secondary uppercase tracking-wider">
                  {language === 'ko' ? '캐릭터 평가' : language === 'ja' ? 'キャラクター評価' : 'Character Rated'}
                </th>
                <th className="hidden md:table-cell px-4 py-3 text-center text-xs font-semibold text-text-secondary uppercase tracking-wider">
                  {language === 'ko' ? '리뷰' : language === 'ja' ? 'レビュー' : 'Reviews'}
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-text-secondary uppercase tracking-wider">
                  {language === 'ko' ? '오타쿠 점수' : language === 'ja' ? 'オタクスコア' : 'Otaku Score'}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {leaderboard.map((user, index) => {
                const levelInfo = getCurrentLevelInfo(user.otaku_score, language);
                const isTopThree = index < 3;
                const rankEmoji = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : '';

                return (
                  <tr
                    key={user.id}
                    className={`hover:bg-surface-hover transition-colors`}
                    style={isTopThree ? {
                      background: index === 0
                        ? 'linear-gradient(to right, rgba(240, 180, 41, 0.15), transparent)' // Gold (accent color)
                        : index === 1
                        ? 'linear-gradient(to right, rgba(168, 181, 196, 0.1), transparent)' // Silver
                        : 'linear-gradient(to right, rgba(205, 127, 50, 0.12), transparent)' // Bronze
                    } : {}}
                  >
                    {/* Rank */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className={`text-center ${isTopThree ? 'text-2xl' : 'text-lg font-bold text-text-secondary'}`}>
                        {rankEmoji || (index + 1)}
                      </div>
                    </td>

                    {/* User */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Link to={`/user/${user.id}`} className="flex items-center gap-3 hover:text-primary transition-colors">
                        {user.avatar_url ? (
                          <img
                            src={getAvatarUrl(user.avatar_url)}
                            alt={user.display_name || user.username}
                            className={`flex-shrink-0 rounded-full object-cover border ${
                              isTopThree ? 'w-12 h-12 border-2 border-accent' : 'w-10 h-10 border-border'
                            }`}
                            onError={(e) => {
                              e.target.style.display = 'none';
                            }}
                          />
                        ) : (
                          <DefaultAvatar
                            username={user.username}
                            displayName={user.display_name}
                            size={isTopThree ? 'lg' : 'md'}
                            className={isTopThree ? 'w-12 h-12 border-2 border-accent' : 'w-10 h-10'}
                          />
                        )}
                        <div className={`font-semibold text-text-primary ${isTopThree ? 'text-base' : 'text-sm'}`}>
                          {user.display_name || user.username}
                        </div>
                      </Link>
                    </td>

                    {/* Level */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex text-xs px-2 py-0.5 rounded-full font-semibold ${levelInfo.bgGradient} border ${levelInfo.borderColor}`}>
                        <span style={{ color: levelInfo.color }} className="font-bold">{levelInfo.icon}</span> <span className="text-text-secondary">{levelInfo.level} - {toRoman(levelInfo.rank)}</span>
                      </span>
                    </td>

                    {/* Anime Rated */}
                    <td className="hidden md:table-cell px-6 py-4 whitespace-nowrap text-center text-sm text-text-primary">
                      {user.total_rated}
                    </td>

                    {/* Character Rated */}
                    <td className="hidden md:table-cell px-6 py-4 whitespace-nowrap text-center text-sm text-text-primary">
                      {user.total_character_ratings || 0}
                    </td>

                    {/* Reviews */}
                    <td className="hidden md:table-cell px-6 py-4 whitespace-nowrap text-center text-sm text-text-primary">
                      {user.total_reviews || 0}
                    </td>

                    {/* Otaku Score */}
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <div className={`font-bold ${isTopThree ? 'text-xl text-secondary' : 'text-lg text-text-primary'}`}>
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
            <p className="text-text-secondary">{language === 'ko' ? '아직 사용자가 없습니다.' : language === 'ja' ? 'まだユーザーがいません。' : 'No users yet.'}</p>
          </div>
        )}
      </div>
    </div>
  );
}
