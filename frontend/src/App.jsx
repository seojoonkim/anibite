import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { LanguageProvider } from './context/LanguageContext';
import ScrollToTop from './components/common/ScrollToTop';
import Login from './pages/Login';
import Register from './pages/Register';
import VerifyEmail from './pages/VerifyEmail';
import EmailSent from './pages/EmailSent';
import ResendVerification from './pages/ResendVerification';
import Feed from './pages/Feed';
import Rate from './pages/Rate';
import RateCharacters from './pages/RateCharacters';
import WriteReviews from './pages/WriteReviews';
import Browse from './pages/Browse';
import Leaderboard from './pages/Leaderboard';
import AnimeDetail from './pages/AnimeDetail';
import CharacterDetail from './pages/CharacterDetail';
import MyAniPass from './pages/MyAniPass';
import Settings from './pages/Settings';

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

function AppRoutes() {
  return (
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
        path="/user/:userId"
        element={
          <ProtectedRoute>
            <MyAniPass />
          </ProtectedRoute>
        }
      />
    </Routes>
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
