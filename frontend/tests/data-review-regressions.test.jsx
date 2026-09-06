import { afterEach, expect, it, vi } from 'vitest';
import { act, cleanup, renderHook, waitFor } from '@testing-library/react';
import { usePagedResource } from '../src/hooks/usePagedResource';
import { QueryCache } from '../src/services/queryCache';

const deferred = () => {
  let resolve;
  let reject;
  const promise = new Promise((res, rej) => { resolve = res; reject = rej; });
  return { promise, resolve, reject };
};
afterEach(() => { cleanup(); vi.restoreAllMocks(); });

it.each(['cache key', 'loader'])('clears old resource data when the %s changes and the new read fails', async identity => {
  const next = deferred();
  const oldItems = [{ id: 1 }, { id: 2 }];
  const oldLoader = vi.fn()
    .mockResolvedValueOnce({ items: [oldItems[0]], total: 8, hasMore: true })
    .mockResolvedValueOnce({ items: [oldItems[1]], total: 8, hasMore: true })
    .mockReturnValue(next.promise);
  const newLoader = vi.fn().mockReturnValue(next.promise);
  const cache = new QueryCache();
  const { result, rerender } = renderHook(({ loader, key }) => usePagedResource(loader, false, { cache: identity === 'cache key' ? cache : undefined, cacheKey: key }), {
    initialProps: { loader: oldLoader, key: identity === 'cache key' ? 'old' : undefined },
  });
  await waitFor(() => expect(result.current.page).toBe(1));
  await act(async () => result.current.loadMore());
  expect(result.current.items).toEqual(oldItems);
  expect(result.current.page).toBe(2);
  rerender({ loader: identity === 'loader' ? newLoader : oldLoader, key: identity === 'cache key' ? 'new' : undefined });
  await waitFor(() => expect(identity === 'loader' ? newLoader : oldLoader).toHaveBeenCalledTimes(identity === 'loader' ? 1 : 3));
  const error = new Error('new filter offline');
  await act(async () => next.reject(error));
  expect(result.current.error).toBe(error);
  expect(result.current.items).toEqual([]);
  expect(result.current.page).toBe(0);
  expect(result.current.total).toBe(0);
  expect(result.current.loading).toBe(false);
});

it('refetches when cache instances change at the same key and version without copying old data', async () => {
  vi.spyOn(window, 'scrollTo').mockImplementation(() => {});
  const cacheA = new QueryCache();
  const cacheB = new QueryCache();
  const fresh = deferred();
  const oldItems = [{ id: 1, value: 'resource-A' }];
  const freshItems = [{ id: 2, value: 'resource-B' }];
  const loadPage = vi.fn()
    .mockResolvedValueOnce({ items: oldItems, total: 8, hasMore: true })
    .mockReturnValueOnce(fresh.promise);
  const { result, rerender } = renderHook(({ cache }) => usePagedResource(loadPage, false, { cache, cacheKey: 'fixture' }), {
    initialProps: { cache: cacheA },
  });
  await waitFor(() => expect(cacheA.get('fixture')?.data.state.items).toEqual(oldItems));
  expect(cacheB.version).toBe(cacheA.version);
  rerender({ cache: cacheB });
  // The writing effect runs before the deferred identity reset.
  expect(cacheB.get('fixture')).toBeUndefined();
  await waitFor(() => expect(loadPage).toHaveBeenCalledTimes(2));
  expect(loadPage.mock.calls.map(([page]) => page)).toEqual([1, 1]);
  expect(cacheB.get('fixture')).toBeUndefined();
  expect(result.current.items).toEqual([]);
  expect(result.current.page).toBe(0);
  expect(result.current.total).toBe(0);
  await act(async () => fresh.resolve({ items: freshItems, total: 1, hasMore: false }));
  expect(result.current.items).toEqual(freshItems);
  expect(cacheB.get('fixture').data.state.items).toEqual(freshItems);
  expect(cacheA.get('fixture').data.state.items).toEqual(oldItems);

  // Restoration must retain ownership too, including subsequent local writes.
  rerender({ cache: cacheA });
  await waitFor(() => expect(result.current.items).toEqual(oldItems));
  act(() => result.current.remove(1));
  expect(cacheA.get('fixture').data.state.items).toEqual([]);
  expect(cacheB.get('fixture').data.state.items).toEqual(freshItems);
  expect(loadPage).toHaveBeenCalledTimes(2);
});

it('retains same-resource items and cursor on append failure and retries that page', async () => {
  const error = new Error('append offline');
  const loadPage = vi.fn()
    .mockResolvedValueOnce({ items: [{ id: 1 }], total: 3, hasMore: true })
    .mockRejectedValueOnce(error)
    .mockResolvedValueOnce({ items: [{ id: 2 }], total: 3, hasMore: true });
  const { result } = renderHook(() => usePagedResource(loadPage));
  await waitFor(() => expect(result.current.page).toBe(1));
  await act(async () => result.current.loadMore());
  expect(result.current.error).toBe(error);
  expect(result.current.items).toEqual([{ id: 1 }]);
  expect(result.current.page).toBe(1);
  expect(result.current.total).toBe(3);
  expect(result.current.hasMore).toBe(true);
  expect(result.current.loadingMore).toBe(false);
  await act(async () => result.current.retry());
  expect(loadPage.mock.calls.map(([page]) => page)).toEqual([1, 2, 2]);
  expect(result.current.items).toEqual([{ id: 1 }, { id: 2 }]);
  expect(result.current.page).toBe(2);
  expect(result.current.error).toBeNull();
});

it('preserves same-resource data on deliberate refresh failure', async () => {
  const error = new Error('refresh offline');
  const loadPage = vi.fn()
    .mockResolvedValueOnce({ items: [{ id: 1 }], total: 3, hasMore: true })
    .mockRejectedValueOnce(error);
  const { result } = renderHook(() => usePagedResource(loadPage));
  await waitFor(() => expect(result.current.page).toBe(1));
  await act(async () => result.current.reset());
  expect(result.current.items).toEqual([{ id: 1 }]);
  expect(result.current.page).toBe(1);
  expect(result.current.total).toBe(3);
  expect(result.current.error).toBe(error);
});

it.each(['resolved', 'rejected'])('restarts an invalidated %s append from page one rather than mixing cache epochs', async outcome => {
  const cache = new QueryCache();
  const append = deferred();
  const fresh = deferred();
  const loadPage = vi.fn()
    .mockResolvedValueOnce({ items: [{ id: 1 }], total: 3, hasMore: true })
    .mockReturnValueOnce(append.promise)
    .mockReturnValueOnce(fresh.promise);
  const { result } = renderHook(() => usePagedResource(loadPage, false, { cache, cacheKey: 'fixture' }));
  await waitFor(() => expect(result.current.page).toBe(1));
  act(() => { void result.current.loadMore(); });
  act(() => cache.clear());
  await act(async () => {
    if (outcome === 'rejected') append.reject(new Error('obsolete append failure'));
    else append.resolve({ items: [{ id: 2 }], total: 3, hasMore: true });
  });
  expect(cache.get('fixture')).toBeUndefined();
  expect(result.current.items).toEqual([{ id: 1 }]);
  expect(result.current.error).toBeNull();
  expect(result.current.loading).toBe(true);
  expect(result.current.loadingMore).toBe(false);
  expect(loadPage.mock.calls.map(([page]) => page)).toEqual([1, 2, 1]);
  await act(async () => fresh.resolve({ items: [{ id: 3 }], total: 1, hasMore: false }));
  expect(result.current.items).toEqual([{ id: 3 }]);
  expect(result.current.page).toBe(1);
  expect(result.current.error).toBeNull();
  expect(result.current.loading).toBe(false);
  expect(cache.get('fixture').data.state.items).toEqual([{ id: 3 }]);
});

it('does not recache invalidated committed data after a local removal', async () => {
  const cache = new QueryCache();
  const loadPage = vi.fn().mockResolvedValue({ items: [{ id: 1 }, { id: 2 }], total: 2, hasMore: false });
  const { result } = renderHook(() => usePagedResource(loadPage, false, { cache, cacheKey: 'fixture' }));
  await waitFor(() => expect(result.current.page).toBe(1));
  act(() => cache.clear());
  act(() => result.current.remove(1));
  expect(result.current.items).toEqual([{ id: 2 }]);
  expect(cache.get('fixture')).toBeUndefined();
});

it('rejects an invalidated in-flight page and caches only a fresh read', async () => {
  const cache = new QueryCache();
  const old = deferred();
  const fresh = deferred();
  const loadPage = vi.fn().mockReturnValueOnce(old.promise).mockReturnValueOnce(fresh.promise);
  const { result } = renderHook(() => usePagedResource(loadPage, false, { cache, cacheKey: 'fixture' }));
  await waitFor(() => expect(loadPage).toHaveBeenCalledTimes(1));
  act(() => cache.clear());
  await act(async () => old.resolve({ items: [{ id: 1, value: 'pre-mutation' }], total: 1, hasMore: false }));
  expect(cache.get('fixture')).toBeUndefined();
  expect(result.current.items).toEqual([]);
  await waitFor(() => expect(loadPage).toHaveBeenCalledTimes(2));
  expect(loadPage.mock.calls[1][0]).toBe(1);
  await act(async () => fresh.resolve({ items: [{ id: 2, value: 'fresh' }], total: 1, hasMore: false }));
  expect(result.current.loading).toBe(false);
  expect(result.current.items).toEqual([{ id: 2, value: 'fresh' }]);
  expect(cache.get('fixture').data.state.items).toEqual(result.current.items);
});
