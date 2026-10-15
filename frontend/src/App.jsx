import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { lazy, Suspense, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { AuthProvider } from './context/AuthProvider';
import { useAuth } from './context/AuthContext';
import { LanguageProvider } from './context/LanguageProvider';
import { LogoWiggleProvider } from './context/LogoWiggleProvider';
import ScrollToTop from './components/common/ScrollToTop';
import Navbar from './components/common/Navbar';
import ErrorBoundary from './components/common/ErrorBoundary';

// Lazy load all pages for code splitting (reduces initial bundle size)
const Login = lazy(() => import('./pages/Login'));
const Register = lazy(() => import('./pages/Register'));
const VerifyEmail = lazy(() => import('./pages/VerifyEmail'));
const EmailSent = lazy(() => import('./pages/EmailSent'));
const ResendVerification = lazy(() => import('./pages/ResendVerification'));
const loadFeed = () => import('./pages/Feed');
const Feed = lazyWithPreload(loadFeed);
const loadRate = () => import('./pages/Rate');
const Rate = lazyWithPreload(loadRate);
const RateCharacters = lazy(() => import('./pages/RateCharacters'));
const WriteReviews = lazy(() => import('./pages/WriteReviews'));
const loadBrowse = () => import('./pages/Browse');
const Browse = lazyWithPreload(loadBrowse);
const Leaderboard = lazy(() => import('./pages/Leaderboard'));
const AnimeDetail = lazy(() => import('./pages/AnimeDetail'));
const CharacterDetail = lazy(() => import('./pages/CharacterDetail'));
const loadMyAniPass = () => import('./pages/MyAniPass');
const MyAniPass = lazyWithPreload(loadMyAniPass);
const Settings = lazy(() => import('./pages/Settings'));
const AdminEditor = lazy(() => import('./pages/AdminEditor'));
const BackupLogs = lazy(() => import('./pages/BackupLogs'));

// React.lazy suspends on first render even when the chunk is already downloaded, and React
// then throttles the fallback→content reveal (~300ms). Once preloaded, render the module directly.
function lazyWithPreload(load) {
  let Loaded = null;
  const preload = () => load().then(mod => { Loaded = mod.default; return mod; });
  const Lazy = lazy(preload);
  function MenuPage(props) {
    return Loaded ? <Loaded {...props} /> : <Lazy {...props} />;
  }
  MenuPage.preload = preload;
  return MenuPage;
}

// Main menu pages (평가·피드·발견·내 서재): download their code while the browser is idle,
// so switching menus never waits on a chunk fetch.
const MENU_PAGES = [Rate, Feed, Browse, MyAniPass];
function preloadMenuPages() {
  return Promise.allSettled(MENU_PAGES.map(page => page.preload()));
}

// Protected Route Component
const ProtectedRoute = ({ children, admin = false }) => {
  const { isAuthenticated, loading, user } = useAuth();
  const location = useLocation();

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">
      <div className="text-xl">Loading...</div>
    </div>;
  }

  if (!isAuthenticated) return <Navigate to="/login" replace state={{ from: location.pathname + location.search + location.hash }} />;
  if (admin && user?.is_admin !== true) return <section className="recovery-page"><h1>403 · 접근 권한이 없습니다</h1><a href="/browse">작품 둘러보기</a></section>;
  return children;
};

// Loading component for Suspense fallback - only shows below navbar
const PageLoader = () => (
  <div className="pt-12 flex items-center justify-center" style={{ minHeight: 'calc(100vh - 3rem)' }}>
    <div className="text-xl text-gray-600">Loading...</div>
  </div>
);

function AppRoutes() {
  const location = useLocation();
  const publicPaths = ['/login', '/register', '/verify-email', '/email-sent', '/resend-verification'];
  const noNavbarPaths = ['/admin'];
  const isPublicPage = publicPaths.includes(location.pathname);
  const showNavbar = !isPublicPage && !noNavbarPaths.includes(location.pathname);

  // Warm the other menu pages once the current page has rendered.
  useEffect(() => {
    if (!showNavbar) return undefined;
    const idle = window.requestIdleCallback || (cb => setTimeout(cb, 1200));
    const cancel = window.cancelIdleCallback || clearTimeout;
    const handle = idle(() => { preloadMenuPages(); });
    return () => cancel(handle);
  }, [showNavbar]);

  // 스크롤 성능 최적화 - 스크롤 시 hover 효과 비활성화
  useEffect(() => {
    let scrollTimeout;

    const handleScroll = () => {
      // 스크롤 중임을 표시
      document.body.classList.add('scrolling');

      // 스크롤 멈춘 후 100ms 뒤에 클래스 제거
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(() => {
        document.body.classList.remove('scrolling');
      }, 100);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });

    return () => {
      window.removeEventListener('scroll', handleScroll);
      clearTimeout(scrollTimeout);
    };
  }, []);

  return (
    <>
      {/* Show Navbar on all authenticated pages except admin - render to body via portal */}
      {showNavbar && createPortal(<Navbar />, document.body)}

      {/* Mobile web version banner - only on authenticated pages */}
      <a href="#main-content" className="skip-link">본문으로 건너뛰기</a>

      <main id="main-content" className={showNavbar ? 'app-content' : undefined} tabIndex={-1}><ErrorBoundary key={location.pathname}><Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/verify-email" element={<VerifyEmail />} />
          <Route path="/email-sent" element={<EmailSent />} />
          <Route path="/resend-verification" element={<ResendVerification />} />
        <Route
          path="/"
          element={<Navigate to="/browse" replace />}
        />
        <Route
          path="/feed"
          element={
            <ProtectedRoute>
              <Feed />
            </ProtectedRoute>
          }
        />
        <Route
          path="/rate"
          element={
            <ProtectedRoute>
              <Rate />
            </ProtectedRoute>
          }
        />
        <Route
          path="/rate-characters"
          element={
            <ProtectedRoute>
              <RateCharacters />
            </ProtectedRoute>
          }
        />
        <Route
          path="/write-reviews"
          element={
            <ProtectedRoute>
              <WriteReviews />
            </ProtectedRoute>
          }
        />
        <Route
          path="/browse"
          element={
            <Browse />
          }
        />
        <Route
          path="/leaderboard"
          element={
            <ProtectedRoute>
              <Leaderboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/anime/:id"
          element={
            <AnimeDetail />
          }
        />
        <Route
          path="/character/:id"
          element={
            <CharacterDetail />
          }
        />
        <Route
          path="/my-anipass"
          element={
            <ProtectedRoute>
              <MyAniPass />
            </ProtectedRoute>
          }
        />
        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <Settings />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <ProtectedRoute admin>
              <AdminEditor />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/backup"
          element={
            <ProtectedRoute admin>
              <BackupLogs />
            </ProtectedRoute>
          }
        />
        <Route
          path="/user/:userId"
          element={
            <ProtectedRoute>
              <MyAniPass />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<section className="recovery-page"><h1>404 · 페이지를 찾을 수 없습니다</h1><p>주소를 확인하거나 다른 작품을 찾아보세요.</p><a href="/browse" className="button-primary">작품 둘러보기</a></section>} />
      </Routes>
      </Suspense></ErrorBoundary></main>
    </>
  );
}

function App() {
  return (
    <AuthProvider>
      <LanguageProvider>
        <LogoWiggleProvider>
          <BrowserRouter>
            <ScrollToTop />
            <AppRoutes />
          </BrowserRouter>
        </LogoWiggleProvider>
      </LanguageProvider>
    </AuthProvider>
  );
}

export default App;
