import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { authService } from '../services/authService';
import { useAuth } from '../context/AuthContext';

export default function VerifyEmail() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { login } = useAuth();
  const [status, setStatus] = useState('verifying'); // verifying, success, error
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    const token = searchParams.get('token');

    if (!token) {
      setStatus('error');
      setErrorMessage('인증 토큰이 없습니다.');
      return;
    }

    verifyEmail(token);
  }, [searchParams]);

  const verifyEmail = async (token) => {
    try {
      const response = await authService.verifyEmail(token);

      // Auto login with the returned token
      if (response.access_token) {
        // Call login function with token and user data directly
        await login(null, response.access_token, response.user);
        setStatus('success');

        // Redirect to home after 2 seconds
        setTimeout(() => {
          navigate('/');
        }, 2000);
      }
    } catch (error) {
      setStatus('error');
      if (error.response?.status === 400) {
        const detail = error.response.data?.detail || '';
        if (detail.includes('expired')) {
          setErrorMessage('인증 링크가 만료되었습니다. 새로운 인증 이메일을 요청해주세요.');
        } else if (detail.includes('already verified')) {
          setErrorMessage('이미 인증된 계정입니다.');
        } else {
          setErrorMessage('유효하지 않은 인증 링크입니다.');
        }
      } else {
        setErrorMessage('인증 처리 중 오류가 발생했습니다.');
      }
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-blue-100 flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8">
        {status === 'verifying' && (
          <div className="text-center">
            <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              이메일 인증 중...
            </h2>
            <p className="text-gray-600">
              잠시만 기다려주세요.
            </p>
          </div>
        )}

        {status === 'success' && (
          <div className="text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-10 h-10 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              인증 완료! 🎉
            </h2>
            <p className="text-gray-600 mb-4">
              이메일 인증이 완료되었습니다.
            </p>
            <p className="text-sm text-gray-500">
              잠시 후 홈으로 이동합니다...
            </p>
          </div>
        )}

        {status === 'error' && (
          <div className="text-center">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-10 h-10 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              인증 실패
            </h2>
            <p className="text-gray-600 mb-6">
              {errorMessage}
            </p>
            <div className="flex flex-col gap-3">
              <button
                onClick={() => navigate('/login')}
                className="w-full py-2.5 px-4 rounded-lg font-medium transition-colors"
                style={{ backgroundColor: '#3498DB', color: 'white' }}
                onMouseEnter={(e) => (e.target.style.backgroundColor = '#2C7CB8')}
                onMouseLeave={(e) => (e.target.style.backgroundColor = '#3498DB')}
              >
                로그인 페이지로
              </button>
              {errorMessage.includes('만료') && (
                <button
                  onClick={() => navigate('/resend-verification')}
                  className="w-full py-2.5 px-4 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg font-medium transition-colors"
                >
                  인증 이메일 재전송
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
