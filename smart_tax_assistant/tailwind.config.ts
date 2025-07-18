import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      keyframes: {
        shimmer: {
          '0%': { transform: 'translateX(-100%) skewX(-12deg)' },
          '100%': { transform: 'translateX(200%) skewX(-12deg)' },
        },
      },
      animation: {
        shimmer: 'shimmer 2.5s infinite',
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}

export default config
