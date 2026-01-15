/**
 * Auth Context
 * Global authentication state management
 */
import { createContext, useState, useContext, useEffect } from 'react';
import { authService } from '../services/authService';
import { API_BASE_URL } from '../config/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Initialize auth state from localStorage and refresh from API
    const initAuth = async () => {
      const storedUser = authService.getStoredUser();
      const token = localStorage.getItem('token');

      if (storedUser && token) {
        const hasOtakuScore = storedUser.otaku_score !== undefined && storedUser.otaku_score !== null;

        // If otaku_score exists, set user immediately to avoid flicker
        if (hasOtakuScore) {
          setUser(storedUser);
        }

        // Fetch latest user data from API (includes otaku_score)
        try {
          const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });

          if (response.ok) {
            const freshUserData = await response.json();
            setUser(freshUserData);
            localStorage.setItem('user', JSON.stringify(freshUserData));
          } else if (!hasOtakuScore) {
            // If API fails and we don't have otaku_score, still set stored user
            setUser(storedUser);
          }
        } catch (err) {
          console.error('Failed to refresh user data:', err);
          // If API fails and we don't have otaku_score, still set stored user
          if (!hasOtakuScore) {
            setUser(storedUser);
          }
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const login = async (credentials, token = null, userData = null) => {
    try {
      // If token and userData provided (from email verification), use them directly
      if (token && userData) {
        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify(userData));
        // Set user's preferred language
        if (userData.preferred_language) {
          localStorage.setItem('language', userData.preferred_language);
          window.location.reload(); // Reload to apply language change
        }
        setUser(userData);
        return { success: true, user: userData };
      }

      // Otherwise, perform normal login
      const data = await authService.login(credentials);
      // Set user's preferred language
      if (data.user.preferred_language) {
        localStorage.setItem('language', data.user.preferred_language);
        window.location.reload(); // Reload to apply language change
      }
      setUser(data.user);
      return { success: true, user: data.user };
    } catch (error) {
      console.error('Login error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Login failed',
      };
    }
  };

  const register = async (userData) => {
    try {
      const data = await authService.register(userData);

      // New registration flow: Email verification required
      // Backend returns { message, email, username } instead of { access_token, user }
      if (data.message && data.email) {
        // Registration successful, but email verification needed
        return {
          success: true,
          requiresVerification: true,
          email: data.email,
          username: data.username,
          message: data.message
        };
      }

      // Legacy: User is automatically verified and logged in (shouldn't happen anymore)
      if (data.user) {
        if (data.user.preferred_language) {
          localStorage.setItem('language', data.user.preferred_language);
          window.location.reload();
        }
        setUser(data.user);
        return { success: true, user: data.user };
      }

      return { success: false, error: 'Unknown registration response' };
    } catch (error) {
      console.error('Register error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Registration failed',
      };
    }
  };

  const logout = () => {
    authService.logout();
    setUser(null);
    // Clear otaku_score cache
    localStorage.removeItem('cached_otaku_score');
  };

  const updateUser = (updatedUser) => {
    setUser(updatedUser);
    // Update stored user in localStorage
    const token = localStorage.getItem('token');
    if (token) {
      localStorage.setItem('user', JSON.stringify(updatedUser));
    }
  };

  const value = {
    user,
    loading,
    login,
    register,
    logout,
    updateUser,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
