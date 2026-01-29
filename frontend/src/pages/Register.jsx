import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Register() {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    passwordConfirm: '',
    display_name: '',
    preferred_language: 'en',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // 비밀번호 확인
    if (formData.password !== formData.passwordConfirm) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);

    const { passwordConfirm, ...registerData } = formData;
    const result = await register(registerData);

    if (result.success) {
      if (result.requiresVerification) {
        // Email verification required - redirect to email sent page
        navigate('/email-sent', {
          state: {
            email: result.email,
            username: result.username
          }
        });
      } else {
        // Registration successful and auto-logged in (legacy flow)
        navigate('/');
      }
    } else {
      setError(result.error);
    }

    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-8">
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

        <h2 className="text-xl font-semibold text-center mb-6 text-gray-800">Sign Up</h2>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-semibold mb-2">
              Username *
            </label>
            <input
              type="text"
              name="username"
              value={formData.username}
              onChange={handleChange}
              placeholder="Choose a username"
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#4A8AC9] focus:border-transparent transition-all text-sm"
              required
              minLength={3}
            />
          </div>

          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-semibold mb-2">
              Email *
            </label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="Enter your email"
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#4A8AC9] focus:border-transparent transition-all text-sm"
              required
            />
          </div>

          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-semibold mb-2">
              Display Name
            </label>
            <input
              type="text"
              name="display_name"
              value={formData.display_name}
              onChange={handleChange}
              placeholder="How should we call you?"
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#4A8AC9] focus:border-transparent transition-all text-sm"
            />
          </div>

          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-semibold mb-2">
              Preferred Language / 선호 언어 / 言語 *
            </label>
            <div className="flex items-center gap-2 p-3 border border-gray-300 rounded-lg bg-gray-50">
              <button
                type="button"
                onClick={() => setFormData({ ...formData, preferred_language: 'ko' })}
                className={`flex-1 py-2.5 px-3 rounded-lg font-semibold text-sm transition-all ${formData.preferred_language === 'ko'
                    ? 'bg-[#4A8AC9] text-white shadow-sm'
                    : 'bg-white text-gray-700 hover:bg-gray-100'
                  }`}
              >
                🇰🇷 한국어
              </button>
              <button
                type="button"
                onClick={() => setFormData({ ...formData, preferred_language: 'en' })}
                className={`flex-1 py-2.5 px-3 rounded-lg font-semibold text-sm transition-all ${formData.preferred_language === 'en'
                    ? 'bg-[#4A8AC9] text-white shadow-sm'
                    : 'bg-white text-gray-700 hover:bg-gray-100'
                  }`}
              >
                🇺🇸 English
              </button>
              <button
                type="button"
                onClick={() => setFormData({ ...formData, preferred_language: 'ja' })}
                className={`flex-1 py-2.5 px-3 rounded-lg font-semibold text-sm transition-all ${formData.preferred_language === 'ja'
                    ? 'bg-[#4A8AC9] text-white shadow-sm'
                    : 'bg-white text-gray-700 hover:bg-gray-100'
                  }`}
              >
                🇯🇵 日本語
              </button>
            </div>
          </div>

          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-semibold mb-2">
              Password * (min. 8 characters)
            </label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Create a password"
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#4A8AC9] focus:border-transparent transition-all text-sm"
              required
              minLength={8}
            />
          </div>

          <div className="mb-6">
            <label className="block text-gray-700 text-sm font-semibold mb-2">
              Confirm Password *
            </label>
            <input
              type="password"
              name="passwordConfirm"
              value={formData.passwordConfirm}
              onChange={handleChange}
              placeholder="Confirm your password"
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#4A8AC9] focus:border-transparent transition-all text-sm"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full text-white font-semibold py-3 px-4 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm hover:shadow-md"
            style={{ backgroundColor: '#4A8AC9' }}
            onMouseEnter={(e) => {
              if (!loading) e.target.style.backgroundColor = '#2378D5';
            }}
            onMouseLeave={(e) => {
              e.target.style.backgroundColor = '#4A8AC9';
            }}
          >
            {loading ? 'Creating account...' : 'Sign Up'}
          </button>
        </form>

        <p className="text-center mt-6 text-gray-600 text-sm">
          Already have an account?{' '}
          <Link to="/login" className="font-semibold hover:underline" style={{ color: '#4A8AC9' }}>
            Login
          </Link>
        </p>
      </div>
    </div>
  );
}
