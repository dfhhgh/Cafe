import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        espresso: '#20130f',
        crema: '#f3dfbf',
        latte: '#d8b98a',
        caramel: '#c47a37',
        mocha: '#593521',
        roast: '#130d0b',
        foam: '#fff6e6'
      },
      boxShadow: {
        cafe: '0 24px 80px rgba(20, 10, 4, 0.45)'
      }
    }
  },
  plugins: []
} satisfies Config;
