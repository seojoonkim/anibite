/**
 * Authentication Service
 * Login, Register, Get current user
 */
import api from './api';

export const authService = {
  /**
   * Register new user
   */
  async register(userData) {
    const response = await api.post('/api/auth/register', userData);
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
    }
    return response.data;
  },

  /**
   * Login
   */
  async login(credentials) {
    const response = await api.post('/api/auth/login', credentials);
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
    }
    return response.data;
  },

  /**
   * Logout
   */
  logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },

  /**
   * Get current user from API
   */
  async getCurrentUser() {
    const response = await api.get('/api/auth/me');
    return response.data;
  },

  /**
   * Get stored user from localStorage
   */
  getStoredUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated() {
    return !!localStorage.getItem('token');
  },

  /**
   * Verify email with token
   */
  async verifyEmail(token) {
    const response = await api.get(`/api/auth/verify-email?token=${token}`);
    return response.data;
  },

  /**
   * Resend verification email
   */
  async resendVerification(email) {
    const response = await api.post('/api/auth/resend-verification', { email });
    return response.data;
  },
};
