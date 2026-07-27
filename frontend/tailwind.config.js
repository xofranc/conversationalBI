/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.js'],
  theme: {
    extend: {
      colors: {
        paper: '#F2F3EF',
        card: '#FFFFFF',
        ink: {
          DEFAULT: '#1B1E23',
          soft: '#5A6068',
        },
        leaf: {
          DEFAULT: '#1E6B4F',
          dark: '#185A42',
          bright: '#3E9C71',
          pale: '#E4EFE9',
        },
        amber: {
          DEFAULT: '#B97A0F',
          pale: '#F7EEDA',
        },
        line: '#E3E5DF',
      },
      fontFamily: {
        sans: ['"IBM Plex Sans"', 'system-ui', 'sans-serif'],
        serif: ['"IBM Plex Serif"', 'Georgia', 'serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'monospace'],
      },
      boxShadow: {
        card: '0 1px 2px rgba(27, 30, 35, 0.05), 0 4px 16px rgba(27, 30, 35, 0.06)',
        lift: '0 4px 8px rgba(27, 30, 35, 0.08), 0 12px 32px rgba(27, 30, 35, 0.10)',
      },
    },
  },
  plugins: [],
};
