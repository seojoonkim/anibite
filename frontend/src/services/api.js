/**
 * Axios API Client
 * Base configuration for API requests
 */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Retry configuration
const MAX_RETRIES = 3;
const RETRY_DELAY_BASE = 1000; // 1 second base delay
const RETRYABLE_STATUS_CODES = [502, 503, 504];

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Helper: delay function
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// Response interceptor: Handle errors with retry logic
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error.config;

    // Initialize retry count
    config.__retryCount = config.__retryCount || 0;

    // Check if we should retry (502, 503, 504 or network error)
    const shouldRetry =
      config.__retryCount < MAX_RETRIES &&
      (RETRYABLE_STATUS_CODES.includes(error.response?.status) || !error.response);

    if (shouldRetry) {
      config.__retryCount += 1;
      const retryDelay = RETRY_DELAY_BASE * config.__retryCount; // 1s, 2s, 3s

      console.log(`[API] Retry ${config.__retryCount}/${MAX_RETRIES} for ${config.url} after ${retryDelay}ms`);

      await delay(retryDelay);
      return api(config);
    }

    // Don't redirect on login/register endpoints - let them handle their own errors
    const isAuthEndpoint = config?.url?.includes('/auth/login') ||
                          config?.url?.includes('/auth/register');

    if (error.response?.status === 401 && !isAuthEndpoint) {
      // Unauthorized - clear token and redirect to login
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
