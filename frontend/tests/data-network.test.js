import { beforeEach, afterEach, expect, it, vi } from 'vitest';
import axios from 'axios';
import api from '../src/services/api';
import { animeService } from '../src/services/animeService';
beforeEach(() => vi.stubGlobal('localStorage', { getItem: vi.fn(), removeItem: vi.fn(), clear: vi.fn() }));
afterEach(() => { vi.useRealTimers(); vi.restoreAllMocks(); vi.unstubAllGlobals(); });
it('adapts catalog page and supported sort contract', async () => {
  const get = vi.spyOn(api, 'get').mockResolvedValue({ data: { items: [] } });
  await animeService.getAnimeList({ page: 2, limit: 20, sort: 'rating_desc' });
  expect(get.mock.calls[0][1].params).toEqual({ page: 2, page_size: 20, sort_by: 'score' });
});
it('bounds request time and handles configless errors unchanged', async () => {
  expect(api.defaults.timeout).toBe(15000);
  const error = new Error('setup failed');
  await expect(api.interceptors.response.handlers[0].rejected(error)).rejects.toBe(error);
});
it('honors Retry-After on safe reads and cancels backoff promptly', async () => {
  vi.useFakeTimers();
  const controller = new AbortController();
  const adapter = vi.fn(config => Promise.reject(new axios.AxiosError('busy', 'ERR_BAD_RESPONSE', config, null, { status: 429, headers: { 'retry-after': '2' } })));
  const outcome = api.get('/fixture/read', { adapter, signal: controller.signal }).catch(e => e);
  await vi.advanceTimersByTimeAsync(1500);
  expect(adapter).toHaveBeenCalledTimes(1);
  controller.abort();
  await vi.advanceTimersByTimeAsync(1);
  expect(axios.isCancel(await outcome)).toBe(true);
  expect(adapter).toHaveBeenCalledTimes(1);
});
it('preserves the intended internal route on authenticated 401 but not 403', async () => {
  const location = { pathname: '/anime/7', search: '?tab=reviews', hash: '#review-3', href: '' };
  vi.stubGlobal('window', { location });
  localStorage.getItem.mockReturnValue('fixture');
  const reject = api.interceptors.response.handlers[0].rejected;
  await reject({ config: { url: '/api/me', method: 'get', headers: { Authorization: 'Bearer fixture' } }, response: { status: 403 } }).catch(() => {});
  expect(location.href).toBe('');
  await reject({ config: { url: '/api/me', method: 'get', headers: { Authorization: 'Bearer fixture' } }, response: { status: 401 } }).catch(() => {});
  expect(location.href).toBe('/login?returnTo=%2Fanime%2F7%3Ftab%3Dreviews%23review-3');
  vi.unstubAllGlobals();
  vi.stubGlobal('localStorage', { clear: vi.fn() });
});
it('never retries a mutation after response loss', async () => {
  vi.useFakeTimers();
  const adapter = vi.fn(config => Promise.reject(new axios.AxiosError('lost', 'ERR_NETWORK', config)));
  const outcome = api.post('/fixture/posts', {}, { adapter }).catch(e => e);
  await vi.runAllTimersAsync();
  expect(await outcome).toBeInstanceOf(Error);
  expect(adapter).toHaveBeenCalledTimes(1);
});
