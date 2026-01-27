/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          'SUIT Variable',
          'Pretendard Variable',
          'DM Sans',
          '-apple-system',
          'BlinkMacSystemFont',
          'system-ui',
          'sans-serif',
        ],
      },
      colors: {
        // Use CSS variables for dark mode
        background: 'var(--color-background)',
        surface: 'var(--color-surface)',
        'surface-elevated': 'var(--color-surface-elevated)',
        'surface-hover': 'var(--color-surface-hover)',

        // Input field colors - darker for distinction
        input: {
          DEFAULT: 'var(--color-input)',
          focus: 'var(--color-input-focus)',
        },

        primary: {
          DEFAULT: 'var(--color-primary)',
          dark: 'var(--color-primary-dark)',
          light: 'var(--color-primary-light)',
        },
        secondary: {
          DEFAULT: 'var(--color-secondary)',
          dark: 'var(--color-secondary-dark)',
          light: 'var(--color-secondary-light)',
        },
        accent: {
          DEFAULT: 'var(--color-accent)',
          dark: 'var(--color-accent-dark)',
          light: 'var(--color-accent-light)',
        },
        tertiary: {
          DEFAULT: 'var(--color-tertiary)',
          dark: 'var(--color-tertiary-dark)',
          light: 'var(--color-tertiary-light)',
        },

        text: {
          primary: 'var(--color-text-primary)',
          secondary: 'var(--color-text-secondary)',
          tertiary: 'var(--color-text-tertiary)',
        },

        border: {
          DEFAULT: 'var(--color-border)',
          hover: 'var(--color-border-hover)',
          focus: 'var(--color-border-focus)',
        },

        success: 'var(--color-success)',
        warning: 'var(--color-warning)',
        error: 'var(--color-error)',
        info: 'var(--color-info)',

        // Override default colors for dark mode
        // This allows existing bg-white, text-gray-* classes to work in dark mode
        white: 'var(--color-surface)',
        black: 'var(--color-text-primary)',
        gray: {
          50: 'var(--color-surface-elevated)',
          100: 'var(--color-surface-elevated)',
          200: 'var(--color-surface-hover)',
          300: 'var(--color-border-hover)',
          400: 'var(--color-text-tertiary)',
          500: 'var(--color-text-tertiary)',
          600: 'var(--color-text-secondary)',
          700: 'var(--color-text-secondary)',
          800: 'var(--color-text-primary)',
          900: 'var(--color-text-primary)',
          950: 'var(--color-text-primary)',
        },
      },
    },
  },
  plugins: [],
}
