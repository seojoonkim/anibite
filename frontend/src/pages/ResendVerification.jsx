import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { authService } from '../services/authService';

export default function ResendVerification() {
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState(location.state?.email || '');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await authService.resendVerification(email);
      setSuccess(true);

      // Redirect to login after 3 seconds
      setTimeout(() => {
        navigate('/login');
      }, 3000);
    } catch (err) {
      setLoading(false);
      if (err.response?.status === 404) {
        setError('등록되지 않은 이메일입니다.');
      } else if (err.response?.status === 400) {
        const detail = err.response.data?.detail || '';
        if (detail.includes('already verified')) {
          setError('이미 인증된 계정입니다. 로그인해주세요.');
        } else {
          setError('인증 이메일 전송에 실패했습니다.');
        }
      } else {
        setError('인증 이메일 전송에 실패했습니다.');
      }
    }
  };

  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-blue-100 flex items-center justify-center px-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8">
          <div className="text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-10 h-10 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              이메일 전송 완료!
            </h2>
            <p className="text-gray-600 mb-4">
              <span className="font-medium">{email}</span> 으로<br />
              새로운 인증 이메일을 보내드렸습니다.
            </p>
            <p className="text-sm text-gray-500">
              잠시 후 로그인 페이지로 이동합니다...
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-blue-100 flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            인증 이메일 재전송
          </h1>
          <p className="text-gray-600 text-sm">
            등록하신 이메일 주소를 입력해주세요
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
              이메일
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-1 focus:ring-blue-500 focus:border-transparent"
              placeholder="your@email.com"
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !email}
            className="w-full py-2.5 px-4 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            style={{ backgroundColor: '#3498DB', color: 'white' }}
            onMouseEnter={(e) => !e.target.disabled && (e.target.style.backgroundColor = '#2C7CB8')}
            onMouseLeave={(e) => !e.target.disabled && (e.target.style.backgroundColor = '#3498DB')}
          >
            {loading ? '전송 중...' : '인증 이메일 재전송'}
          </button>

          <button
            type="button"
            onClick={() => navigate('/login')}
            className="w-full py-2.5 px-4 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg font-medium transition-colors"
          >
            로그인 페이지로
          </button>
        </form>
      </div>
    </div>
  );
}
