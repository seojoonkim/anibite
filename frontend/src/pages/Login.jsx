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
        setError('이메일 인증이 완료되지 않았습니다.');
      } else {
        setError(result.error);
      }
    }

    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500">
      <div className="bg-white p-8 rounded-2xl shadow-2xl w-96">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-2">
            AniPass
          </h1>
          <p className="text-gray-600">당신의 애니메이션 여정</p>
        </div>
        <h2 className="text-2xl font-bold text-center mb-6 text-gray-800">로그인</h2>

        {error && (
          <div className={`px-4 py-3 rounded mb-4 ${
            emailNotVerified
              ? 'bg-yellow-100 border border-yellow-400 text-yellow-800'
              : 'bg-red-100 border border-red-400 text-red-700'
          }`}>
            <p className="mb-2">{error}</p>
            {emailNotVerified && (
              <button
                onClick={() => navigate('/resend-verification', { state: { email: userEmail } })}
                className="text-sm underline hover:no-underline"
              >
                인증 이메일 재전송하기 →
              </button>
            )}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-bold mb-2">
              {language === 'ko' ? '아이디 또는 이메일' : 'ID or Email'}
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder={language === 'ko' ? '아이디 또는 이메일을 입력하세요' : 'Enter your ID or email'}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
              required
            />
            <p className="text-xs text-gray-500 mt-1">
              {language === 'ko' ? '회원가입 시 입력한 아이디 또는 이메일로 로그인할 수 있습니다' : 'You can login with your ID or email'}
            </p>
          </div>

          <div className="mb-6">
            <label className="block text-gray-700 text-sm font-bold mb-2">
              {language === 'ko' ? '비밀번호' : 'Password'}
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={language === 'ko' ? '비밀번호를 입력하세요' : 'Enter your password'}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded focus:outline-none disabled:opacity-50"
          >
            {loading ? (language === 'ko' ? '로그인 중...' : 'Logging in...') : (language === 'ko' ? '로그인' : 'Login')}
          </button>
        </form>

        <p className="text-center mt-4 text-gray-600">
          {language === 'ko' ? '계정이 없으신가요?' : "Don't have an account?"}{' '}
          <Link to="/register" className="text-blue-500 hover:text-[#364F6B]">
            {language === 'ko' ? '회원가입' : 'Register'}
          </Link>
        </p>
      </div>
    </div>
  );
}
