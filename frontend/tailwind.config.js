/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        agent: {
          bg: '#F7F8FA',
          bgSubtle: '#F1F3F6',
          card: '#FFFFFF',
          border: '#E2E8F0',
          borderSubtle: '#EDF2F7',
          navy: '#172554',
          navyDark: '#111A2E',
          navyLight: '#1E3A8A',
          blue: '#3155D9',
          violet: '#6D5BD0',
          gold: '#B89B5E',
          goldLight: '#DFD1A7',
          emerald: '#15805F',
          amber: '#D97706',
          rose: '#DC2626',
          text: {
            primary: '#18202F',
            secondary: '#596273',
            muted: '#87909F',
          }
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      }
    },
  },
  plugins: [],
}

