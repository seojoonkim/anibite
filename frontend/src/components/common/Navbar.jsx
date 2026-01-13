import { useState, useEffect, useRef } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { userService } from '../../services/userService';
import { notificationService } from '../../services/notificationService';
import { getCurrentLevelInfo } from '../../utils/otakuLevels';
import NotificationDropdown from './NotificationDropdown';
import { API_BASE_URL, IMAGE_BASE_URL } from '../../config/api';

export default function Navbar() {
  const { user, logout } = useAuth();
  const { language, toggleLanguage, t } = useLanguage();
  const navigate = useNavigate();
  const location = useLocation();
  const [showLangMenu, setShowLangMenu] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNotificationDropdown, setShowNotificationDropdown] = useState(false);
  const [otakuScore, setOtakuScore] = useState(0);
  const [unreadCount, setUnreadCount] = useState(0);
  const [lastCheckTime, setLastCheckTime] = useState(null);
  const notificationRef = useRef(null);

  const toRoman = (num) => {
    const romanNumerals = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X'];
    return romanNumerals[num - 1] || num;
  };

  useEffect(() => {
    const fetchUserStats = async () => {
      if (user) {
        try {
          const stats = await userService.getStats();
          setOtakuScore(stats.otaku_score || 0);
        } catch (err) {
          console.error('Failed to fetch user stats:', err);
        }
      }
    };

    fetchUserStats();
  }, [user]);

  // 드롭다운 바깥 클릭 시 닫기
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (notificationRef.current && !notificationRef.current.contains(event.target)) {
        setShowNotificationDropdown(false);
      }
    };

    if (showNotificationDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showNotificationDropdown]);

  useEffect(() => {
    const fetchUnreadCount = async () => {
      if (user) {
        try {
          const count = await notificationService.getUnreadCount();
          setUnreadCount(count);
        } catch (err) {
          console.error('Failed to fetch unread count:', err);
        }
      }
    };

    fetchUnreadCount();
    // Poll every 30 seconds
    const interval = setInterval(fetchUnreadCount, 30000);
    return () => clearInterval(interval);
  }, [user]);

  const isActive = (path) => {
    return location.pathname === path || (path === '/rate' && location.pathname === '/');
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
    setShowUserMenu(false);
  };

  const handleSettings = () => {
    navigate('/settings');
    setShowUserMenu(false);
  };

  const handleNotificationClick = (e) => {
    e.stopPropagation();
    setShowNotificationDropdown(!showNotificationDropdown);
    // 다른 메뉴 닫기
    setShowLangMenu(false);
    setShowUserMenu(false);
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationService.markAllAsRead();
      setUnreadCount(0);
      // 현재 시간을 lastCheckTime으로 설정
      setLastCheckTime(new Date().toISOString());
    } catch (err) {
      console.error('Failed to mark all notifications as read:', err);
    }
  };

  const handleMyAnipass = () => {
    navigate('/my-anipass');
    setShowUserMenu(false);
  };

  const handleLanguageChange = (lang) => {
    if (lang !== language) {
      toggleLanguage();
    }
    setShowLangMenu(false);
  };

  const getAvatarUrl = (avatarUrl) => {
    if (!avatarUrl) return null;
    // 외부 URL은 그대로 사용
    if (avatarUrl.startsWith('http')) return avatarUrl;
    // /uploads로 시작하면 API 서버 (파일 업로드)
    if (avatarUrl.startsWith('/uploads')) {
      return `${import.meta.env.VITE_API_URL || API_BASE_URL}${avatarUrl}`;
    }
    // 그 외는 IMAGE_BASE_URL (R2, 캐릭터 이미지)
    return `${IMAGE_BASE_URL}${avatarUrl}`;
  };

  const menuItems = [
    {
      path: '/feed',
      labelKo: '피드',
      labelEn: 'Feed',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
        </svg>
      )
    },
    {
      path: '/rate',
      label: t('rate'),
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
        </svg>
      )
    },
    {
      path: '/rate-characters',
      label: t('rateCharacter'),
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      )
    },
    {
      path: '/write-reviews',
      label: t('writeReview'),
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
        </svg>
      )
    },
    {
      path: '/browse',
      label: t('browse'),
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      )
    },
    {
      path: '/leaderboard',
      labelKo: '리더보드',
      labelEn: 'Leaderboard',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      )
    },
  ];

  return (
    <>
      {/* Desktop & Mobile Top Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 h-16" style={{
        backgroundColor: '#FFFFFF',
        borderBottom: '1px solid #DBDBDB'
      }}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center h-16 relative">
            {/* Logo */}
            <div className="flex items-center" style={{ width: '200px' }}>
              <Link to="/feed" className="flex items-center gap-3 text-2xl font-bold text-black hover:opacity-60 transition-opacity group">
                {/* AniPass Logo Icon */}
                <div className="relative">
                  <svg width="44" height="44" viewBox="0 0 44 44" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                      <linearGradient id="instagramGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style={{ stopColor: '#833AB4' }} />
                        <stop offset="40%" style={{ stopColor: '#E1306C' }} />
                        <stop offset="70%" style={{ stopColor: '#F77737' }} />
                        <stop offset="100%" style={{ stopColor: '#FCAF45' }} />
                      </linearGradient>
                    </defs>
                    {/* Card Background with gradient */}
                    <rect x="2" y="6" width="40" height="32" rx="4" fill="url(#instagramGradient)" className="group-hover:opacity-90 transition-opacity" />

                    {/* Border */}
                    <rect x="2" y="6" width="40" height="32" rx="4" stroke="white" strokeWidth="1.5" opacity="0.4" />

                    {/* Letter A - Bubble/Rounded Style */}
                    {/* Left side - very rounded */}
                    <path
                      d="M 10 35 Q 12 34 14 31 Q 16 27 17 24 Q 18 20 19 17 Q 20 14 22 12"
                      stroke="white"
                      strokeWidth="5"
                      strokeLinecap="round"
                      fill="none"
                      className=""
                    />
                    {/* Right side - very rounded */}
                    <path
                      d="M 22 12 Q 24 14 25 17 Q 26 20 27 24 Q 28 27 30 31 Q 32 34 34 35"
                      stroke="white"
                      strokeWidth="5"
                      strokeLinecap="round"
                      fill="none"
                      className=""
                    />
                    {/* Cross bar - bubble style */}
                    <ellipse
                      cx="22" cy="26"
                      rx="8" ry="3"
                      fill="white"
                      className=""
                    />

                    {/* Star Icon - Simple & Cute */}
                    <g className="group-hover:scale-110 transition-transform origin-center">
                      <path
                        d="M 22 4.5 L 24.5 10 L 30 11 L 26 15 L 27 20.5 L 22 17.5 L 17 20.5 L 18 15 L 14 11 L 19.5 10 Z"
                        fill="#FCAF45"
                        stroke="white"
                        strokeWidth="1.2"
                        strokeLinejoin="round"
                        className=""
                      />
                    </g>
                  </svg>
                </div>
                <span className="">AniPass</span>
              </Link>
            </div>

            {/* Desktop Center Menu - Hidden on Mobile - Absolutely Centered */}
            <div className="hidden md:flex items-center space-x-1 absolute left-1/2 -translate-x-1/2 flex-nowrap">
              {menuItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`px-3 py-2 rounded-md text-sm font-semibold transition-colors whitespace-nowrap ${
                    isActive(item.path)
                      ? 'bg-[#3797F0] text-white'
                      : 'text-black hover:text-gray-500 hover:bg-gray-100'
                  }`}
                >
                  {item.labelKo ? (language === 'ko' ? item.labelKo : item.labelEn) : item.label}
                </Link>
              ))}
            </div>

            {/* Right Side - Language & User */}
            <div className="flex items-center space-x-2 ml-auto pl-8" style={{ minWidth: '300px', justifyContent: 'flex-end' }}>
              {/* Language Dropdown */}
              <div className="relative">
                <button
                  onClick={() => setShowLangMenu(!showLangMenu)}
                  className="text-[#262626] hover:text-black px-3 py-2 rounded-md text-xs font-medium transition-colors flex items-center gap-1"
                  style={{ minWidth: '70px' }}
                >
                  <span>{language === 'ko' ? 'KO' : 'EN'}</span>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {showLangMenu && (
                  <div className="absolute right-0 mt-2 w-24 bg-white rounded-md shadow-[0_4px_16px_rgba(0,0,0,0.12)] z-50">
                    <button
                      onClick={() => handleLanguageChange('ko')}
                      className="block w-full text-left px-4 py-2 text-xs text-gray-700 hover:bg-gray-100 rounded-t-md"
                    >
                      KO
                    </button>
                    <button
                      onClick={() => handleLanguageChange('en')}
                      className="block w-full text-left px-4 py-2 text-xs text-gray-700 hover:bg-gray-100 rounded-b-md"
                    >
                      EN
                    </button>
                  </div>
                )}
              </div>

              {/* Notification Bell */}
              {user && (
                <div className="relative" ref={notificationRef}>
                  <button
                    onClick={handleNotificationClick}
                    className={`relative text-[#262626] hover:bg-gray-100 p-2 rounded-md transition-colors flex items-center ${
                      showNotificationDropdown ? 'bg-gray-100' : ''
                    }`}
                    style={{ minWidth: '40px' }}
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                    </svg>
                    {unreadCount > 0 && (
                      <span className="absolute -top-1 -right-1 bg-[#FF3040] text-white text-xs font-bold rounded-full min-w-[20px] h-5 flex items-center justify-center px-1 animate-pulse">
                        {unreadCount > 99 ? '99+' : unreadCount}
                      </span>
                    )}
                  </button>

                  {/* Notification Dropdown */}
                  <NotificationDropdown
                    isOpen={showNotificationDropdown}
                    onClose={() => setShowNotificationDropdown(false)}
                    unreadCount={unreadCount}
                    onMarkAllRead={handleMarkAllRead}
                    lastCheckTime={lastCheckTime}
                  />
                </div>
              )}

              {user && (
                <div className="relative">
                  <button
                    onClick={() => setShowUserMenu(!showUserMenu)}
                    className="text-[#262626] hover:text-black hover:bg-gray-100 text-sm font-medium px-3 py-2 rounded-md transition-colors flex items-center gap-2"
                    style={{ minWidth: '160px' }}
                  >
                    {user.avatar_url ? (
                      <img
                        src={getAvatarUrl(user.avatar_url)}
                        alt={user.display_name || user.username}
                        className="w-8 h-8 rounded-full object-cover border border-[#DBDBDB]"
                        onError={(e) => {
                          e.target.style.display = 'none';
                        }}
                      />
                    ) : (
                      <div className="w-8 h-8 rounded-full flex items-center justify-center border border-[#DBDBDB]" style={{ backgroundColor: '#FAFAFA' }}>
                        <span className="text-[#262626] text-sm font-bold">
                          {(user.display_name || user.username || '?').charAt(0).toUpperCase()}
                        </span>
                      </div>
                    )}
                    <span className="text-base font-medium">{user.display_name || user.username}</span>
                    {(() => {
                      const levelInfo = getCurrentLevelInfo(otakuScore);
                      return (
                        <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${levelInfo.bgGradient} border ${levelInfo.borderColor} hidden sm:inline-flex`}>
                          <span style={{ color: levelInfo.color }} className="font-bold">{levelInfo.icon}</span>
                          <span className="text-gray-700">{toRoman(levelInfo.rank)}</span>
                        </span>
                      );
                    })()}
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>

                  {showUserMenu && (
                    <div className="absolute right-0 mt-2 w-52 bg-white rounded-md shadow-[0_4px_16px_rgba(0,0,0,0.12)] z-50" style={{ borderColor: '#DBDBDB', borderWidth: '1px' }}>
                      <button
                        onClick={handleMyAnipass}
                        className="block w-full text-left px-4 py-3 text-sm font-medium rounded-t-md transition-colors"
                        style={{
                          backgroundColor: '#FAFAFA',
                          color: '#262626',
                          borderBottom: '1px solid #DBDBDB'
                        }}
                        onMouseEnter={(e) => e.target.style.backgroundColor = '#F0F0F0'}
                        onMouseLeave={(e) => e.target.style.backgroundColor = '#FAFAFA'}
                      >
                        <div className="flex items-center gap-2">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                          </svg>
                          <span>내 애니패스</span>
                        </div>
                      </button>
                      <button
                        onClick={handleSettings}
                        className="block w-full text-left px-4 py-2 text-xs text-gray-700 hover:bg-gray-100 transition-colors"
                      >
                        <div className="flex items-center gap-2">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          </svg>
                          <span>설정</span>
                        </div>
                      </button>
                      <button
                        onClick={handleLogout}
                        className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded-b-md transition-colors"
                      >
                        <div className="flex items-center gap-2">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                          </svg>
                          <span>로그아웃</span>
                        </div>
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Mobile Bottom Navigation - Only visible on mobile */}
      <div className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-[0_4px_16px_rgba(0,0,0,0.12)] z-50">
        <div className="grid grid-cols-6 h-16">
          {menuItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex flex-col items-center justify-center gap-0.5 transition-colors ${
                isActive(item.path)
                  ? 'bg-[#3797F0] text-white'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              {item.icon}
              <span className="text-[10px] font-medium">
                {item.labelKo ? (language === 'ko' ? item.labelKo : item.labelEn) : item.label}
              </span>
            </Link>
          ))}
        </div>
      </div>

      {/* Spacer for mobile bottom nav */}
      <div className="md:hidden h-16" />
    </>
  );
}
