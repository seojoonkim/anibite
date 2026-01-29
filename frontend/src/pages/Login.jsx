import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [emailNotVerified, setEmailNotVerified] = useState(false);
  const [userEmail, setUserEmail] = useState('');
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const { language } = useLanguage();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setEmailNotVerified(false);
    setLoading(true);

    const result = await login({ username, password });

    if (result.success) {
      navigate('/');
    } else {
      // Check if error is due to email not verified
      if (result.error && result.error.toLowerCase().includes('not verified')) {
        setEmailNotVerified(true);
        setUserEmail(username.includes('@') ? username : '');
        setError('Email verification is not complete.');
      } else {
        setError(result.error);
      }
    }

    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white p-8 rounded-xl shadow-[0_2px_12px_rgba(0,0,0,0.08)] border border-gray-200 w-full max-w-md mx-4">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="flex items-center gap-2 mb-3">
            {/* AniBite Logo Icon */}
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
              <rect x="2" y="6" width="40" height="32" rx="4" fill="url(#instagramGradient)" />

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
              />
              {/* Right side - very rounded */}
              <path
                d="M 22 12 Q 24 14 25 17 Q 26 20 27 24 Q 28 27 30 31 Q 32 34 34 35"
                stroke="white"
                strokeWidth="5"
                strokeLinecap="round"
                fill="none"
              />
              {/* Cross bar - bubble style */}
              <ellipse
                cx="22" cy="26"
                rx="8" ry="3"
                fill="white"
              />

              {/* Star Icon - Simple & Cute */}
              <path
                d="M 22 4.5 L 24.5 10 L 30 11 L 26 15 L 27 20.5 L 22 17.5 L 17 20.5 L 18 15 L 14 11 L 19.5 10 Z"
                fill="#FCAF45"
                stroke="white"
                strokeWidth="1.2"
                strokeLinejoin="round"
              />
            </svg>
            <h1 className="text-3xl font-bold text-gray-900">AniBite</h1>
          </div>
          <p className="text-gray-600 text-center">Your Anime Journey</p>
        </div>

        <h2 className="text-xl font-semibold text-center mb-6 text-gray-800">Login</h2>

        {error && (
          <div className={`px-4 py-3 rounded mb-4 ${emailNotVerified
              ? 'bg-yellow-100 border border-yellow-400 text-yellow-800'
              : 'bg-red-100 border border-red-400 text-red-700'
            }`}>
            <p className="mb-2">{error}</p>
            {emailNotVerified && (
              <button
                onClick={() => navigate('/resend-verification', { state: { email: userEmail } })}
                className="text-sm underline hover:no-underline"
              >
                Resend verification email →
              </button>
            )}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="mb-5">
            <label className="block text-gray-700 text-sm font-semibold mb-2">
              Username or Email
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter your username or email"
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#5BB5F5] focus:border-transparent transition-all text-sm"
              required
            />
            <p className="text-xs text-gray-500 mt-1.5">
              You can login with your username or email
            </p>
          </div>

          <div className="mb-6">
            <label className="block text-gray-700 text-sm font-semibold mb-2">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#5BB5F5] focus:border-transparent transition-all text-sm"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full text-white font-semibold py-3 px-4 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm hover:shadow-md"
            style={{ backgroundColor: '#5BB5F5' }}
            onMouseEnter={(e) => {
              if (!loading) e.target.style.backgroundColor = '#2378D5';
            }}
            onMouseLeave={(e) => {
              e.target.style.backgroundColor = '#5BB5F5';
            }}
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <p className="text-center mt-6 text-gray-600 text-sm">
          Don't have an account?{' '}
          <Link to="/register" className="font-semibold hover:underline" style={{ color: '#5BB5F5' }}>
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}
