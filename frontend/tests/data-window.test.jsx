import { afterEach, expect, it, vi } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useVirtualGrid } from '../src/hooks/useVirtualGrid';
import { QueryCache } from '../src/services/queryCache';
afterEach(() => { vi.unstubAllGlobals(); vi.useRealTimers(); });
it('keeps sections usable without IntersectionObserver instead of blanking content', () => {
  vi.stubGlobal('IntersectionObserver', undefined);
  const { result } = renderHook(() => useVirtualGrid([{ id: 'one' }]));
  expect(result.current.isSectionVisible('one')).toBe(true);
});
it('expires cache entries and prevents invalidated inflight reads from resurrecting data', async () => {
  vi.useFakeTimers();
  const cache = new QueryCache(2, 100);
  await cache.fetch('one', async () => 1);
  await vi.advanceTimersByTimeAsync(101);
  expect(cache.get('one')).toBeUndefined();
  let finish;
  const read = cache.fetch('two', () => new Promise(resolve => { finish = resolve; }));
  await Promise.resolve();
  cache.clear(); finish(2); await read;
  expect(cache.get('two')).toBeUndefined();
});
