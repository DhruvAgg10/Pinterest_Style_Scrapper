/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './client/src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#0a0a0b',
        surface: '#111114',
        elevated: '#1a1a1f',
        line: '#26262d',
        muted: '#8a8a94',
        accent: {
          DEFAULT: '#c8a15a', // warm gold — editorial fashion
          soft: '#e6d0a3',
        },
      },
      fontFamily: {
        display: ['"Playfair Display"', 'Georgia', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        glow: '0 0 40px -10px rgba(200,161,90,0.35)',
        card: '0 20px 60px -20px rgba(0,0,0,0.6)',
      },
      keyframes: {
        shimmer: {
          '100%': { transform: 'translateX(100%)' },
        },
        'fade-up': {
          '0%': { opacity: 0, transform: 'translateY(12px)' },
          '100%': { opacity: 1, transform: 'translateY(0)' },
        },
      },
      animation: {
        shimmer: 'shimmer 1.5s infinite',
        'fade-up': 'fade-up 0.5s ease-out both',
      },
    },
  },
  plugins: [],
};
