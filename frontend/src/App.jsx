import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { lazy, Suspense, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { LanguageProvider } from './context/LanguageContext';
import ScrollToTop from './components/common/ScrollToTop';
import Navbar from './components/common/Navbar';

// Lazy load all pages for code splitting (reduces initial bundle size)
const Login = lazy(() => import('./pages/Login'));
const Register = lazy(() => import('./pages/Register'));
const VerifyEmail = lazy(() => import('./pages/VerifyEmail'));
const EmailSent = lazy(() => import('./pages/EmailSent'));
const ResendVerification = lazy(() => import('./pages/ResendVerification'));
const Feed = lazy(() => import('./pages/Feed'));
const Rate = lazy(() => import('./pages/Rate'));
const RateCharacters = lazy(() => import('./pages/RateCharacters'));
const WriteReviews = lazy(() => import('./pages/WriteReviews'));
const Browse = lazy(() => import('./pages/Browse'));
const Leaderboard = lazy(() => import('./pages/Leaderboard'));
const AnimeDetail = lazy(() => import('./pages/AnimeDetail'));
const CharacterDetail = lazy(() => import('./pages/CharacterDetail'));
const MyAniPass = lazy(() => import('./pages/MyAniPass'));
const Settings = lazy(() => import('./pages/Settings'));
const AdminEditor = lazy(() => import('./pages/AdminEditor'));

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">
      <div className="text-xl">Loading...</div>
    </div>;
  }

  return isAuthenticated ? children : <Navigate to="/login" />;
};

// Loading component for Suspense fallback - only shows below navbar
const PageLoader = () => (
  <div className="pt-16 flex items-center justify-center" style={{ minHeight: 'calc(100vh - 4rem)' }}>
    <div className="text-xl text-gray-600">Loading...</div>
  </div>
);

function AppRoutes() {
  const location = useLocation();
  const publicPaths = ['/login', '/register', '/verify-email', '/email-sent', '/resend-verification'];
  const isPublicPage = publicPaths.includes(location.pathname);

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
      {/* Show Navbar on all authenticated pages - render to body via portal */}
      {!isPublicPage && createPortal(<Navbar />, document.body)}

      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/verify-email" element={<VerifyEmail />} />
          <Route path="/email-sent" element={<EmailSent />} />
          <Route path="/resend-verification" element={<ResendVerification />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Rate />
            </ProtectedRoute>
          }
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
            <ProtectedRoute>
              <Browse />
            </ProtectedRoute>
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
            <ProtectedRoute>
              <AnimeDetail />
            </ProtectedRoute>
          }
        />
        <Route
          path="/character/:id"
          element={
            <ProtectedRoute>
              <CharacterDetail />
            </ProtectedRoute>
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
            <ProtectedRoute>
              <AdminEditor />
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
      </Routes>
      </Suspense>
    </>
  );
}

function App() {
  return (
    <AuthProvider>
      <LanguageProvider>
        <BrowserRouter>
          <ScrollToTop />
          <AppRoutes />
        </BrowserRouter>
      </LanguageProvider>
    </AuthProvider>
  );
}

export default App;
