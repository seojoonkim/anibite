/**
 * Auth Context
 * Global authentication state management
 */
import { useState, useEffect } from 'react';
import { authService } from '../services/authService';
import { bookmarkService } from '../services/bookmarkService';
import { API_BASE_URL } from '../config/api';

import { AuthContext } from './AuthContext';

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    const timeout = setTimeout(() => controller.abort(), 10000);
    const initAuth = async () => {
      const token = localStorage.getItem('token');
      try {
        if (token) {
          const response = await fetch(`${API_BASE_URL}/api/auth/me`, { headers: { Authorization: `Bearer ${token}` }, signal: controller.signal });
          if (response.ok) {
            const freshUser = await response.json();
            if (active) { setUser(freshUser); localStorage.setItem('user', JSON.stringify(freshUser)); }
          } else if (response.status === 401 || response.status === 403) {
            if (active) { authService.logout(); setUser(null); }
          }
          // Network/server errors never turn cached claims into authenticated privileges.
        }
      } catch {
        if (active) setUser(null);
      } finally {
        clearTimeout(timeout);
        if (active) setLoading(false);
      }
    };
    initAuth();
    return () => { active = false; clearTimeout(timeout); controller.abort(); };
  }, []);

  const login = async (credentials, token = null, userData = null) => {
    try {
      // If token and userData provided (from email verification), use them directly
      if (token && userData) {
        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify(userData));
        // Set user's preferred language (no reload - will apply on next visit)
        if (userData.preferred_language) {
          localStorage.setItem('language', userData.preferred_language);
        }
        setUser(userData);
        return { success: true, user: userData };
      }

      // Otherwise, perform normal login
      const data = await authService.login(credentials);

      // Set user's preferred language (no reload - will apply on next visit)
      if (data.user.preferred_language) {
        localStorage.setItem('language', data.user.preferred_language);
      }

      // Set user
      setUser(data.user);

      // Migrate localStorage bookmarks to server (one-time migration)
      try {
        const migrationKey = `bookmarks_migrated_${data.user.id}`;
        const alreadyMigrated = localStorage.getItem(migrationKey);

        if (!alreadyMigrated) {
          const result = await bookmarkService.migrateLocalBookmarks();
          if (result.migrated > 0) {
            localStorage.setItem(migrationKey, 'true');
            console.log(`✅ Migrated ${result.migrated} bookmarks`);
          }
        }
      } catch (error) {
        console.error('Failed to migrate bookmarks:', error);
      }

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

      // Legacy: User is automatically verified and logged in
      if (data.user) {
        if (data.user.preferred_language) {
          localStorage.setItem('language', data.user.preferred_language);
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

