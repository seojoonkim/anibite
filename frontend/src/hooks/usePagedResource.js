import { useCallback, useEffect, useReducer, useRef } from 'react';

const initial = { items: [], loading: true, loadingMore: false, error: null, hasMore: true, page: 0, total: 0 };
const unique = items => [...new Map(items.map(item => [item.id, item])).values()];
function reducer(state, action) {
  if (action.type === 'restore') return action.state;
  if (action.type === 'start') return { ...state, loading: action.page === 1, loadingMore: action.page > 1, error: null };
  if (action.type === 'success') return { ...state, items: unique(action.page === 1 ? action.data.items : [...state.items, ...action.data.items]), cacheOwner: action.cacheOwner, cacheKey: action.cacheKey, cacheVersion: action.cacheVersion, page: action.page, total: action.data.total, hasMore: action.data.hasMore, loading: false, loadingMore: false, error: null };
  if (action.type === 'error') return { ...state, loading: false, loadingMore: false, error: action.error };
  if (action.type === 'remove') return { ...state, items: state.items.filter(item => item.id !== action.id) };
  if (action.type === 'idle') return { ...state, loading: false, loadingMore: false };
  return state;
}

/** A request generation owns its results; page cursors commit only on success. */
export function usePagedResource(loadPage, skip = false, { cache, cacheKey, autoFetch = true } = {}) {
  const [state, dispatch] = useReducer(reducer, null, () => cache?.get(cacheKey)?.data.state || initial);
  const active = useRef(null);
  const generation = useRef(0);
  const failedPage = useRef(1);
  const resource = useRef({ loadPage, cache, cacheKey });
  const request = useCallback(async (page, replace = false) => {
    if (skip || (active.current && !replace)) return;
    active.current?.abort();
    const controller = new AbortController();
    active.current = controller;
    const version = ++generation.current;
    failedPage.current = page;
    dispatch({ type: 'start', page });
    try {
      while (version === generation.current && !controller.signal.aborted) {
        const cacheVersion = cache?.version;
        try {
          const data = await loadPage(page, controller.signal);
          if (version !== generation.current || controller.signal.aborted) return;
          if (cacheVersion === cache?.version) {
            dispatch({ type: 'success', page, data, cacheOwner: cache, cacheKey, cacheVersion });
            return;
          }
        } catch (error) {
          if (version !== generation.current || controller.signal.aborted) return;
          if (cacheVersion === cache?.version) {
            dispatch({ type: 'error', error });
            return;
          }
        }
        // An invalidated read cannot commit; rebuild pagination from fresh data.
        page = 1;
        failedPage.current = page;
        dispatch({ type: 'start', page });
      }
    } finally {
      if (version === generation.current) active.current = null;
    }
  }, [loadPage, skip, cache, cacheKey]);
  const cancel = useCallback(() => { ++generation.current; active.current?.abort(); active.current = null; }, []);
  useEffect(() => {
    // Start on a microtask so StrictMode cleanup can cancel before any I/O.
    let mounted = true;
    let frame;
    Promise.resolve().then(() => {
      if (!mounted) return;
      const previous = resource.current;
      const changed = previous.loadPage !== loadPage || previous.cache !== cache || previous.cacheKey !== cacheKey;
      resource.current = { loadPage, cache, cacheKey };
      if (changed) {
        failedPage.current = 1;
        dispatch({ type: 'restore', state: initial });
      }
      const saved = cache?.get(cacheKey)?.data;
      if (skip || !autoFetch) dispatch({ type: 'idle' });
      else if (saved) { dispatch({ type: 'restore', state: saved.state }); frame = requestAnimationFrame(() => window.scrollTo(0, saved.scroll || 0)); }
      else request(1, true);
    });
    return () => { mounted = false; cancelAnimationFrame(frame); cancel(); };
  }, [request, loadPage, skip, cancel, cache, cacheKey, autoFetch]);
  useEffect(() => {
    // Committed/restored state belongs to one cache instance, not just its epoch.
    if (!cache || state.cacheOwner !== cache || state.cacheKey !== cacheKey || state.cacheVersion !== cache.version || state.loading || state.loadingMore || state.error || !state.page) return;
    const savedScroll = cache.get(cacheKey)?.data.scroll || 0;
    cache.set(cacheKey, { timestamp: Date.now(), data: { state, scroll: savedScroll } });
    const rememberScroll = () => { const entry = cache.get(cacheKey); if (entry) entry.data.scroll = window.scrollY; };
    window.addEventListener('scroll', rememberScroll, { passive: true });
    return () => window.removeEventListener('scroll', rememberScroll);
  }, [cache, cacheKey, state]);
  const reset = useCallback(() => request(1, true), [request]);
  const retry = useCallback(() => request(failedPage.current), [request]);
  const loadMore = useCallback(() => { if (state.hasMore && !state.loading && !state.error) return request(state.page + 1); }, [request, state.hasMore, state.loading, state.error, state.page]);
  const remove = useCallback(id => dispatch({ type: 'remove', id }), []);
  return { ...state, reset, retry, loadMore, remove };
}
