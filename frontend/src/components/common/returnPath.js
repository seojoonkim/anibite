// Never accept protocol-relative, encoded separators, controls or auth loops.
export function safeReturnPath(value, fallback = '/browse') {
 if (value && typeof value === 'object') value = `${value.pathname || ''}${value.search || ''}${value.hash || ''}`;
 if (typeof value !== 'string' || !value.startsWith('/') || value.startsWith('//') || (value.includes('\\') || [...value].some(char => char.charCodeAt(0) <= 32)) || /%2f|%5c|%0[0-9a-f]/i.test(value)) return fallback;
 try { const url = new URL(value, 'https://anibite.com'); return url.origin === 'https://anibite.com' && !/^\/(login|register)(\/|$)/.test(url.pathname) ? value : fallback; } catch { return fallback; }
}
