/**
 * Google Sign-In Button Component
 * Handles Google OAuth login/registration with custom styling
 */
import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { API_BASE_URL } from '../config/api';

const GoogleSignInButton = ({ onError }) => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const buttonRef = useRef(null);

  useEffect(() => {
    // Load Google Sign-In script
    if (window.google) {
      initializeGoogleSignIn();
      return;
    }

    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = initializeGoogleSignIn;
    document.body.appendChild(script);

    return () => {
      const existingScript = document.querySelector('script[src="https://accounts.google.com/gsi/client"]');
      if (existingScript) {
        document.body.removeChild(existingScript);
      }
    };
  }, []);

  const initializeGoogleSignIn = () => {
    if (!window.google || !buttonRef.current) return;

    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

    window.google.accounts.id.initialize({
      client_id: clientId,
      callback: handleCredentialResponse,
    });

    window.google.accounts.id.renderButton(
      buttonRef.current,
      {
        theme: 'outline',
        size: 'large',
        width: buttonRef.current.offsetWidth,
        text: 'continue_with',
        shape: 'rectangular',
        logo_alignment: 'left',
      }
    );
  };

  const handleCredentialResponse = async (response) => {
    try {
      const preferredLanguage = localStorage.getItem('language') || 'en';

      const apiResponse = await fetch(`${API_BASE_URL}/api/auth/google`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          credential: response.credential,
          preferred_language: preferredLanguage,
        }),
      });

      const data = await apiResponse.json();

      if (!apiResponse.ok) {
        throw new Error(data.detail || 'Google login failed');
      }

      await login(null, data.access_token, data.user);
      navigate('/');
    } catch (error) {
      console.error('Google login error:', error);
      if (onError) {
        onError(error.message || 'Failed to sign in with Google');
      }
    }
  };

  return (
    <div className="w-full">
      <div
        ref={buttonRef}
        className="w-full flex items-center justify-center"
        style={{ minHeight: '44px' }}
      />
    </div>
  );
};

export default GoogleSignInButton;
