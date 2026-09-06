/** Small session-memory cache. Never persists personalized payloads to disk. */
export class QueryCache {
  constructor(maxEntries = 100, ttl = 300000) {
    this.maxEntries = maxEntries;
    this.ttl = ttl;
    this.entries = new Map();
    this.inflight = new Map();
    this.version = 0;
  }
  prune() {
    for (const [key, value] of this.entries) if (Date.now() - value.timestamp >= this.ttl) this.entries.delete(key);
    while (this.entries.size > this.maxEntries) this.entries.delete(this.entries.keys().next().value);
  }
  get size() { this.prune(); return this.entries.size; }
  get(key) {
    this.prune();
    const entry = this.entries.get(key);
    if (entry) { this.entries.delete(key); this.entries.set(key, entry); }
    return entry;
  }
  set(key, value) { this.entries.delete(key); this.entries.set(key, value); this.prune(); }
  clear() { this.version++; this.entries.clear(); this.inflight.clear(); }
  async fetch(key, loader) {
    const cached = this.get(key);
    if (cached) return cached.data;
    if (this.inflight.has(key)) return this.inflight.get(key);
    // Hover prefetch is optional: drop excess pending work rather than grow forever.
    if (this.inflight.size >= this.maxEntries) return null;
    const version = this.version;
    const promise = Promise.resolve().then(loader).then(data => {
      if (version === this.version) this.set(key, { data, timestamp: Date.now() });
      return data;
    }).finally(() => { if (this.inflight.get(key) === promise) this.inflight.delete(key); });
    this.inflight.set(key, promise);
    return promise;
  }
}
export const prefetchCache = new QueryCache();
export const browseCache = new QueryCache(20, 120000);
let session;
export function syncCacheSession() {
  const next = localStorage.getItem('token');
  if (session !== next) { session = next; invalidateQueries(); }
}
export function invalidateQueries() { prefetchCache.clear(); browseCache.clear(); }
