import type { Config } from 'tailwindcss'

export default {
  content: ['./components/**/*.{vue,js,ts}','./pages/**/*.{vue,js,ts}','./app.vue'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter var', 'system-ui', 'sans-serif'],
      },
    }
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ]
} satisfies Config