import { afterEach, expect, it, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import api from '../src/services/api';
import { usePrefetch, getPrefetchedData, clearPrefetchCache } from '../src/hooks/usePrefetch';
afterEach(() => { clearPrefetchCache(); vi.restoreAllMocks(); vi.useRealTimers(); });
it('deduplicates inflight hover reads and bounds retained entries', async () => {
  const get = vi.spyOn(api, 'get').mockImplementation(async url => ({ data: { id: url } }));
  const { result } = renderHook(() => usePrefetch());
  await act(async () => Promise.all([result.current.prefetchAnimeDetail(1), result.current.prefetchAnimeDetail(1)]));
  expect(get).toHaveBeenCalledTimes(1);
  for (let id = 2; id <= 110; id++) await result.current.prefetchAnimeDetail(id);
  expect(result.current.prefetchCache.size).toBeLessThanOrEqual(100);
  expect(getPrefetchedData('anime', 1)).toBeNull();
});
it('invalidates hover cache on successful mutations and session scope changes', async () => {
  vi.spyOn(api, 'get').mockResolvedValue({ data: { id: 1 } });
  const { result } = renderHook(() => usePrefetch());
  await result.current.prefetchAnimeDetail(1);
  const adapter = async config => ({ data: {}, status: 200, headers: {}, config });
  await api.post('/fixture/rating', {}, { adapter });
  expect(getPrefetchedData('anime', 1)).toBeNull();
  await result.current.prefetchAnimeDetail(1);
  localStorage.setItem('token', 'isolated-fixture-session');
  await api.get('/fixture/session', { adapter });
  expect(getPrefetchedData('anime', 1)).toBeNull();
});
