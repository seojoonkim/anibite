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
          <Link to="/feed" className="flex items-center gap-2 mb-3 hover:opacity-80 transition-opacity">
            <img
              src="/logo.svg"
              alt="AniBite Logo"
              className="w-11 h-11 object-contain"
            />
            <h1 className="text-3xl font-bold text-gray-900">AniBite</h1>
          </Link>
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
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#47B5FF] focus:border-transparent transition-all text-sm"
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
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#47B5FF] focus:border-transparent transition-all text-sm"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full text-white font-semibold py-3 px-4 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm hover:shadow-md"
            style={{ backgroundColor: '#47B5FF' }}
            onMouseEnter={(e) => {
              if (!loading) e.target.style.backgroundColor = '#2378D5';
            }}
            onMouseLeave={(e) => {
              e.target.style.backgroundColor = '#47B5FF';
            }}
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <p className="text-center mt-6 text-gray-600 text-sm">
          Don't have an account?{' '}
          <Link to="/register" className="font-semibold hover:underline" style={{ color: '#47B5FF' }}>
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}
