import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
export default defineConfig({ plugins: [react()], test: { execArgv: ['--no-experimental-webstorage'], environment: 'jsdom', setupFiles: ['./tests/setup.js'], include: ['tests/**/*.test.{js,jsx}', 'src/**/*.test.{js,jsx}'], clearMocks: true, restoreMocks: true } });
