import '@testing-library/jest-dom/vitest';
import { afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
// Use jsdom's origin-scoped Storage, not Node's experimental global Web Storage.
Object.defineProperty(globalThis, 'localStorage', { configurable: true, value: window.localStorage });
Object.defineProperty(globalThis, 'sessionStorage', { configurable: true, value: window.sessionStorage });
afterEach(() => { cleanup(); window.localStorage.clear(); window.sessionStorage.clear(); });
