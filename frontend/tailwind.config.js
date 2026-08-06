/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './app.html', './roadmap.html', './src/**/*.js'],
  theme: {
    extend: {
      colors: {
        // Superficie clara de lectura
        paper: '#F0F2EF',
        card: '#FFFFFF',
        line: '#DCE0D9',
        // Rail oscuro de instrumentos
        rail: {
          DEFAULT: '#12161C',
          raise: '#1A212B',
          line: '#28303C',
          text: '#A7B0BC',
        },
        ink: {
          DEFAULT: '#1B2430',
          soft: '#5C6672',
        },
        petrol: {
          DEFAULT: '#0E5E6F',
          dark: '#0A4A58',
          bright: '#3E8FA3',
          pale: '#E2EEF1',
        },
        signal: {
          DEFAULT: '#C77B21',
          pale: '#F8EEDD',
        },
        danger: '#B3402E',
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'system-ui', 'sans-serif'],
        sans: ['"Inter"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      boxShadow: {
        card: '0 1px 2px rgba(18, 22, 28, 0.05), 0 4px 16px rgba(18, 22, 28, 0.06)',
        lift: '0 4px 8px rgba(18, 22, 28, 0.08), 0 12px 32px rgba(18, 22, 28, 0.10)',
      },
    },
  },
  plugins: [],
};
