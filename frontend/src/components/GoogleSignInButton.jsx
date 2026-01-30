/**
 * Google Sign-In Button Component
 * Handles Google OAuth login/registration
 */
import { GoogleLogin } from '@react-oauth/google';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { API_BASE_URL } from '../config/api';

const GoogleSignInButton = ({ onError }) => {
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSuccess = async (credentialResponse) => {
    try {
      // Get user's preferred language from localStorage
      const preferredLanguage = localStorage.getItem('language') || 'en';

      // Send the credential (ID token) to backend
      const response = await fetch(`${API_BASE_URL}/api/auth/google`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          credential: credentialResponse.credential,
          preferred_language: preferredLanguage,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Google login failed');
      }

      // Login with token and user data
      await login(null, data.access_token, data.user);

      // Navigate to home
      navigate('/');
    } catch (error) {
      console.error('Google login error:', error);
      if (onError) {
        onError(error.message || 'Failed to sign in with Google');
      }
    }
  };

  const handleError = () => {
    console.error('Google OAuth error');
    if (onError) {
      onError('Failed to sign in with Google');
    }
  };

  return (
    <div className="w-full">
      <GoogleLogin
        onSuccess={handleSuccess}
        onError={handleError}
        theme="outline"
        size="large"
        width="100%"
        text="signin_with"
        shape="rectangular"
      />
    </div>
  );
};

export default GoogleSignInButton;
