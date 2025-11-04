import type { Config } from 'tailwindcss';

export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Space Grotesk"', 'system-ui', 'sans-serif']
      },
      colors: {
        brand: {
          50: '#ecfeff',
          100: '#cffafe',
          500: '#0ea5e9',
          700: '#0369a1',
          900: '#0b1120'
        }
      },
      boxShadow: {
        glow: '0 0 45px rgba(14, 165, 233, 0.35)'
      }
    }
  },
  plugins: []
} satisfies Config;
