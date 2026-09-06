import { afterEach, expect, it, vi } from 'vitest';
import { act, renderHook, waitFor } from '@testing-library/react';
import api from '../src/services/api';
import { useActivities, useActivityPagination } from '../src/hooks/useActivity';
afterEach(() => vi.restoreAllMocks());
const deferred = () => { let resolve; const promise = new Promise(r => { resolve = r; }); return { promise, resolve }; };
it('does not drop a filter change while initial request is pending', async () => {
  const first = deferred(); const second = deferred();
  const get = vi.spyOn(api, 'get').mockReturnValueOnce(first.promise).mockReturnValueOnce(second.promise);
  const { result, rerender } = renderHook(({ followingOnly }) => useActivityPagination({ followingOnly }, 2), { initialProps: { followingOnly: false } });
  await waitFor(() => expect(get).toHaveBeenCalledTimes(1));
  rerender({ followingOnly: true });
  await waitFor(() => expect(get).toHaveBeenCalledTimes(2));
  expect(get.mock.calls[1][0]).toContain('following_only=true');
  await act(async () => second.resolve({ data: { items: [{ id: 2 }], total: 1 } }));
  await act(async () => first.resolve({ data: { items: [{ id: 1 }], total: 1 } }));
  expect(result.current.activities).toEqual([{ id: 2 }]);
});
it('detail activity queries also reject out-of-order old responses', async () => {
  const first = deferred(); const second = deferred();
  const get = vi.spyOn(api, 'get').mockReturnValueOnce(first.promise).mockReturnValueOnce(second.promise);
  const { result, rerender } = renderHook(({ itemId }) => useActivities({ itemId }), { initialProps: { itemId: 1 } });
  await waitFor(() => expect(get).toHaveBeenCalledTimes(1));
  rerender({ itemId: 2 });
  await waitFor(() => expect(get).toHaveBeenCalledTimes(2));
  await act(async () => second.resolve({ data: { items: [{ id: 2 }], total: 1 } }));
  await act(async () => first.resolve({ data: { items: [{ id: 1 }], total: 1 } }));
  expect(result.current.activities).toEqual([{ id: 2 }]);
});
it('exposes request failure without pretending the feed is empty', async () => {
  vi.spyOn(api, 'get').mockRejectedValue(new Error('offline'));
  const { result } = renderHook(() => useActivityPagination({}, 2));
  await waitFor(() => expect(result.current.loading).toBe(false));
  expect(result.current.error).toBeTruthy();
});
