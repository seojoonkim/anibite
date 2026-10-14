import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
// Note: do NOT force recharts into a manual chunk. Doing so pulled shared deps
// (react-is, clsx, ...) into that chunk and made every page modulepreload ~350 kB
// of chart code. Rollup's automatic splitting keeps recharts on the profile page only.
export default defineConfig({
  plugins: [react()],
  build: {
    target: 'es2020',
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (/\/node_modules\/(react|react-dom|scheduler|react-router|react-router-dom)\//.test(id)) return 'react-vendor';
        },
      },
    },
  },
})
