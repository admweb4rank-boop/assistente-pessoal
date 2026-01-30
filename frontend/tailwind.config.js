/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Base colors (V2 - Easy·A inspired)
        dark: {
          bg: {
            primary: '#0A0B0E',
            secondary: '#13141A',
            tertiary: '#1A1B23',
            elevated: '#22232E',
          },
          text: {
            primary: '#FFFFFF',
            secondary: '#A3A3B8',
            tertiary: '#6B6B80',
            disabled: '#4A4A5C',
          },
          border: 'rgba(255, 255, 255, 0.08)',
          borderHover: 'rgba(255, 255, 255, 0.15)',
        },
        
        // Brand purple spectrum
        brand: {
          purple: {
            50: '#FAF5FF',
            100: '#F3E8FF',
            200: '#E9D5FF',
            300: '#D8B4FE',
            400: '#C084FC',
            500: '#A855F7',
            600: '#9333EA',
            700: '#7E22CE',
            800: '#6B21A8',
            900: '#581C87',
          },
          blue: {
            400: '#60A5FA',
            500: '#3B82F6',
            600: '#2563EB',
          },
        },
        
        // Accent colors (vibrant)
        accent: {
          green: {
            400: '#34D399',
            500: '#10B981',
            600: '#059669',
          },
          lime: {
            400: '#D4FF00',
            500: '#CAFF00',
            600: '#B8E600',
          },
          blue: {
            400: '#60A5FA',
            500: '#3B82F6',
            600: '#2563EB',
          },
          pink: {
            400: '#F472B6',
            500: '#EC4899',
            600: '#DB2777',
          },
          yellow: {
            400: '#FBBF24',
            500: '#F59E0B',
            600: '#D97706',
          },
          red: {
            400: '#F87171',
            500: '#EF4444',
            600: '#DC2626',
          },
        },
      },
      
      fontSize: {
        'display-2xl': ['72px', { lineHeight: '90px', fontWeight: '700', letterSpacing: '-0.02em' }],
        'display-xl': ['60px', { lineHeight: '72px', fontWeight: '700', letterSpacing: '-0.02em' }],
        'display-lg': ['48px', { lineHeight: '60px', fontWeight: '700', letterSpacing: '-0.01em' }],
      },
      
      borderRadius: {
        '2xl': '24px',
        '3xl': '32px',
      },
      
      boxShadow: {
        'glass-sm': '0 2px 8px rgba(0, 0, 0, 0.4)',
        'glass': '0 4px 16px rgba(0, 0, 0, 0.5)',
        'glass-lg': '0 8px 32px rgba(0, 0, 0, 0.6)',
        'glow-purple': '0 0 20px rgba(168, 85, 247, 0.4), 0 0 40px rgba(168, 85, 247, 0.2)',
        'glow-green': '0 0 20px rgba(16, 185, 129, 0.4), 0 0 40px rgba(16, 185, 129, 0.2)',
        'glow-lime': '0 0 20px rgba(202, 255, 0, 0.4), 0 0 40px rgba(202, 255, 0, 0.2)',
        'glow-blue': '0 0 20px rgba(59, 130, 246, 0.4), 0 0 40px rgba(59, 130, 246, 0.2)',
        'glow-pink': '0 0 20px rgba(236, 72, 153, 0.4), 0 0 40px rgba(236, 72, 153, 0.2)',
        'glow-red': '0 0 20px rgba(239, 68, 68, 0.4), 0 0 40px rgba(239, 68, 68, 0.2)',
        'glow-yellow': '0 0 20px rgba(245, 158, 11, 0.4), 0 0 40px rgba(245, 158, 11, 0.2)',
      },
      
      backgroundImage: {
        'gradient-purple-blue': 'linear-gradient(135deg, #A855F7 0%, #3B82F6 100%)',
        'gradient-purple-green': 'linear-gradient(135deg, #A855F7 0%, #10B981 100%)',
        'gradient-purple-pink': 'linear-gradient(135deg, #A855F7 0%, #EC4899 100%)',
        'gradient-green-blue': 'linear-gradient(135deg, #10B981 0%, #3B82F6 100%)',
        'gradient-dark-purple': 'linear-gradient(135deg, #1A1B23 0%, #2D1B69 100%)',
        'gradient-lime-green': 'linear-gradient(135deg, #CAFF00 0%, #10B981 100%)',
      },
      
      animation: {
        'float': 'float 6s ease-in-out infinite',
        'glow-pulse': 'glow-pulse 2s ease-in-out infinite',
        'slide-up': 'slide-up 0.5s ease-out',
        'slide-down': 'slide-down 0.5s ease-out',
        'slide-left': 'slide-left 0.5s ease-out',
        'slide-right': 'slide-right 0.5s ease-out',
        'fade-in': 'fade-in 0.6s ease-out',
        'scale-in': 'scale-in 0.4s ease-out',
        'shimmer': 'shimmer 2s linear infinite',
        'spin-slow': 'spin 3s linear infinite',
        'bounce-slow': 'bounce 3s infinite',
      },
      
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-20px)' },
        },
        'glow-pulse': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' },
        },
        'slide-up': {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        'slide-down': {
          '0%': { transform: 'translateY(-20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        'slide-left': {
          '0%': { transform: 'translateX(20px)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        'slide-right': {
          '0%': { transform: 'translateX(-20px)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'scale-in': {
          '0%': { transform: 'scale(0.9)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-1000px 0' },
          '100%': { backgroundPosition: '1000px 0' },
        },
      },
    },
  },
  plugins: [],
}
