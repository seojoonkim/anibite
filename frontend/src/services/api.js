/**
 * Axios API Client
 * Base configuration for API requests
 */
import axios from 'axios';
import { invalidateQueries, syncCacheSession } from './queryCache';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Retry configuration
const MAX_RETRIES = 3;
const RETRY_DELAY_BASE = 1000; // 1 second base delay
const RETRYABLE_STATUS_CODES = [0, 408, 429, 500, 502, 503, 504]; // Include timeout, rate limit, and server errors

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Add auth token
api.interceptors.request.use(
  (config) => {
    syncCacheSession();
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
const delay = (ms, signal) => new Promise((resolve, reject) => {
  const abort = () => { clearTimeout(timer); reject(new axios.CanceledError()); };
  const timer = setTimeout(() => { signal?.removeEventListener('abort', abort); resolve(); }, ms);
  if (signal?.aborted) abort();
  else signal?.addEventListener('abort', abort, { once: true });
});

// Response interceptor: Handle errors with retry logic
api.interceptors.response.use(
  (response) => {
    if (!['get', 'head', 'options'].includes(response.config?.method?.toLowerCase())) invalidateQueries();
    return response;
  },
  async (error) => {
    const config = error.config;
    if (!config || axios.isCancel(error) || config.signal?.aborted) return Promise.reject(error);

    // Initialize retry count
    config.__retryCount = config.__retryCount || 0;

    // Check if we should retry (network error, CORS error, or server error)
    // CORS errors appear as network errors with no response
    const isNetworkOrCorsError = !error.response || error.message?.includes('Network Error');
    const isRetryableStatus = RETRYABLE_STATUS_CODES.includes(error.response?.status);
    const shouldRetry = ['get', 'head'].includes(config.method?.toLowerCase()) && !axios.isCancel(error) && !config.signal?.aborted && config.__retryCount < MAX_RETRIES && (isNetworkOrCorsError || isRetryableStatus);

    if (shouldRetry) {
      config.__retryCount += 1;
      const retryAfter = error.response?.headers?.['retry-after'];
      const seconds = Number(retryAfter);
      const requested = retryAfter == null ? NaN : Number.isFinite(seconds) ? seconds * 1000 : Date.parse(retryAfter) - Date.now();
      const retryDelay = Number.isFinite(requested) && requested >= 0 && requested <= 30000 ? requested : RETRY_DELAY_BASE * config.__retryCount;

      console.log(`[API] Retry ${config.__retryCount}/${MAX_RETRIES} for ${config.url} after ${retryDelay}ms`);

      await delay(retryDelay, config.signal);
      return api(config);
    }

    // Don't redirect on login/register endpoints - let them handle their own errors
    const isAuthEndpoint = config?.url?.includes('/auth/login') ||
                          config?.url?.includes('/auth/register');

    if (error.response?.status === 401 && !isAuthEndpoint && config.headers?.Authorization) {
      // Unauthorized - clear token and redirect to login
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      invalidateQueries();
      const intended = `${window.location.pathname}${window.location.search}${window.location.hash}`;
      const internal = intended.startsWith('/') && !intended.startsWith('//') && !intended.includes('\\') ? intended : '/';
      if (window.location.pathname !== '/login') window.location.href = `/login?returnTo=${encodeURIComponent(internal)}`;
    }
    return Promise.reject(error);
  }
);

export default api;
