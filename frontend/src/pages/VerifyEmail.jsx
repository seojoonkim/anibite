import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { API_BASE_URL } from '../config/api';

export default function VerifyEmail() {
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState('verifying'); // verifying, success, error
  const [message, setMessage] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const verifyEmail = async () => {
      const token = searchParams.get('token');

      if (!token) {
        setStatus('error');
        setMessage('Invalid verification link. No token provided.');
        return;
      }

      try {
        const response = await fetch(`${API_BASE_URL}/api/auth/verify-email?token=${token}`);
        const data = await response.json();

        if (response.ok) {
          setStatus('success');
          setMessage('Email verified successfully! Logging you in...');

          // Log the user in with the returned token and user data
          await login(null, data.access_token, data.user);

          // Redirect to home after 2 seconds
          setTimeout(() => {
            navigate('/');
          }, 2000);
        } else {
          setStatus('error');
          setMessage(data.detail || 'Email verification failed. Please try again.');
        }
      } catch (error) {
        console.error('Verification error:', error);
        setStatus('error');
        setMessage('An error occurred during verification. Please try again later.');
      }
    };

    verifyEmail();
  }, [searchParams, login, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-8">
      <div className="bg-white p-8 rounded-xl shadow-[0_2px_12px_rgba(0,0,0,0.08)] border border-gray-200 w-full max-w-md mx-4">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="flex items-center gap-2 mb-3">
            <svg width="44" height="44" viewBox="0 0 44 44" fill="none" xmlns="http://www.w3.org/2000/svg">
              <defs>
                <linearGradient id="instagramGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" style={{ stopColor: '#833AB4' }} />
                  <stop offset="40%" style={{ stopColor: '#E1306C' }} />
                  <stop offset="70%" style={{ stopColor: '#F77737' }} />
                  <stop offset="100%" style={{ stopColor: '#FCAF45' }} />
                </linearGradient>
              </defs>
              <rect x="2" y="6" width="40" height="32" rx="4" fill="url(#instagramGradient)" />
              <rect x="2" y="6" width="40" height="32" rx="4" stroke="white" strokeWidth="1.5" opacity="0.4" />
              <path
                d="M 10 35 Q 12 34 14 31 Q 16 27 17 24 Q 18 20 19 17 Q 20 14 22 12"
                stroke="white"
                strokeWidth="5"
                strokeLinecap="round"
                fill="none"
              />
              <path
                d="M 22 12 Q 24 14 25 17 Q 26 20 27 24 Q 28 27 30 31 Q 32 34 34 35"
                stroke="white"
                strokeWidth="5"
                strokeLinecap="round"
                fill="none"
              />
              <ellipse cx="22" cy="26" rx="8" ry="3" fill="white" />
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
        </div>

        <h2 className="text-xl font-semibold text-center mb-6 text-gray-800">
          Email Verification
        </h2>

        {/* Status Content */}
        <div className="text-center">
          {status === 'verifying' && (
            <div className="flex flex-col items-center">
              <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-[#4EEAF7] mb-4"></div>
              <p className="text-gray-600">Verifying your email...</p>
            </div>
          )}

          {status === 'success' && (
            <div className="flex flex-col items-center">
              <div className="bg-green-100 rounded-full p-3 mb-4">
                <svg className="w-12 h-12 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <p className="text-green-600 font-semibold text-lg mb-2">Success!</p>
              <p className="text-gray-600">{message}</p>
            </div>
          )}

          {status === 'error' && (
            <div className="flex flex-col items-center">
              <div className="bg-red-100 rounded-full p-3 mb-4">
                <svg className="w-12 h-12 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
              <p className="text-red-600 font-semibold text-lg mb-2">Verification Failed</p>
              <p className="text-gray-600 mb-6">{message}</p>

              <div className="space-y-3">
                <Link
                  to="/login"
                  className="block w-full text-white font-semibold py-3 px-4 rounded-lg transition-all shadow-sm hover:shadow-md text-center"
                  style={{ backgroundColor: '#4EEAF7' }}
                >
                  Go to Login
                </Link>
                <Link
                  to="/register"
                  className="block w-full text-gray-700 font-semibold py-3 px-4 rounded-lg border-2 border-gray-300 hover:bg-gray-50 transition-all text-center"
                >
                  Register Again
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
