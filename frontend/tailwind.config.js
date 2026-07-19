/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        accent: { DEFAULT: '#6c5ce7', light: '#a29bfe', dark: '#5541d7' },
        surface: { DEFAULT: 'rgba(255,255,255,0.08)', hover: 'rgba(255,255,255,0.12)' },
      },
      backdropBlur: { glass: '20px' },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.4s ease-out',
      },
    },
  },
  plugins: [],
}
