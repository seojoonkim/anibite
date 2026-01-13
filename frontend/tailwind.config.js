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
        // 파스텔 색상 테마
        primary: {
          50: '#F0F9FF',
          100: '#E0F2FE',
          200: '#BAE6FD',
          300: '#7DD3FC',
          400: '#38BDF8',
          500: '#8EC5FC', // 메인 파스텔 블루
          600: '#0284C7',
          700: '#0369A1',
          800: '#075985',
          900: '#0C4A6E',
        },
        secondary: {
          50: '#F0FDF4',
          100: '#DCFCE7',
          200: '#BBF7D0',
          300: '#86EFAC',
          400: '#4ADE80',
          500: '#A8E6CF', // 파스텔 민트
          600: '#16A34A',
          700: '#15803D',
          800: '#166534',
          900: '#14532D',
        },
        accent: {
          50: '#FFF1F2',
          100: '#FFE4E6',
          200: '#FECDD3',
          300: '#FDA4AF',
          400: '#FB7185',
          500: '#FFB6C1', // 파스텔 핑크
          600: '#E11D48',
          700: '#BE123C',
          800: '#9F1239',
          900: '#881337',
        },
        lavender: '#E6E6FA', // 라벤더 파스텔
        peach: '#FFDAB9', // 피치 파스텔
        mint: '#B5EAD7', // 민트 파스텔
        rose: '#FFD1DC', // 로즈 파스텔
        sky: '#B4E4FF', // 스카이 파스텔
      },
    },
  },
  plugins: [],
}
