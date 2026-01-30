import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import GoogleSignInButton from '../components/GoogleSignInButton';

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

        <h2 className="text-xl font-semibold text-center mb-6 text-gray-800">Sign Up</h2>

        {/* Google Sign-In */}
        <div className="mb-6">
          <GoogleSignInButton onError={setError} />

          {/* Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500">Or continue with email</span>
            </div>
          </div>
        </div>

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
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#47B5FF] focus:border-transparent transition-all text-sm"
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
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#47B5FF] focus:border-transparent transition-all text-sm"
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
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#47B5FF] focus:border-transparent transition-all text-sm"
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
                    ? 'bg-[#47B5FF] text-white shadow-sm'
                    : 'bg-white text-gray-700 hover:bg-gray-100'
                  }`}
              >
                🇰🇷 한국어
              </button>
              <button
                type="button"
                onClick={() => setFormData({ ...formData, preferred_language: 'en' })}
                className={`flex-1 py-2.5 px-3 rounded-lg font-semibold text-sm transition-all ${formData.preferred_language === 'en'
                    ? 'bg-[#47B5FF] text-white shadow-sm'
                    : 'bg-white text-gray-700 hover:bg-gray-100'
                  }`}
              >
                🇺🇸 English
              </button>
              <button
                type="button"
                onClick={() => setFormData({ ...formData, preferred_language: 'ja' })}
                className={`flex-1 py-2.5 px-3 rounded-lg font-semibold text-sm transition-all ${formData.preferred_language === 'ja'
                    ? 'bg-[#47B5FF] text-white shadow-sm'
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
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#47B5FF] focus:border-transparent transition-all text-sm"
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
            {loading ? 'Creating account...' : 'Sign Up'}
          </button>
        </form>

        <p className="text-center mt-6 text-gray-600 text-sm">
          Already have an account?{' '}
          <Link to="/login" className="font-semibold hover:underline" style={{ color: '#47B5FF' }}>
            Login
          </Link>
        </p>
      </div>
    </div>
  );
}
