/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // SiteDiligence brand colors
        navy: {
          DEFAULT: '#1B4F72',
          50:  '#e8f1f8',
          100: '#d1e3f1',
          200: '#a4c7e3',
          300: '#76abd5',
          400: '#498fc7',
          500: '#1B4F72',
          600: '#16405d',
          700: '#103048',
          800: '#0b2133',
          900: '#05111e',
        },
        green: {
          DEFAULT: '#27AE60',
          50:  '#e9f7ef',
          100: '#d4f0df',
          200: '#a9e1be',
          300: '#7ed29e',
          400: '#53c37d',
          500: '#27AE60',
          600: '#1f8b4d',
          700: '#18683a',
          800: '#104526',
          900: '#082213',
        },
        amber: {
          DEFAULT: '#F39C12',
          50:  '#fef8ec',
          100: '#fdf1d9',
          200: '#fbe3b3',
          300: '#f9d58e',
          400: '#f7c768',
          500: '#F39C12',
          600: '#c27d0e',
          700: '#925e0b',
          800: '#613e07',
          900: '#311f04',
        },
        slate: {
          DEFAULT: '#2C3E50',
          50:  '#eaecef',
          100: '#d5d9df',
          200: '#abb3be',
          300: '#808e9e',
          400: '#56687d',
          500: '#2C3E50',
          600: '#233240',
          700: '#1a2530',
          800: '#121920',
          900: '#090c10',
        },
        // shadcn/ui CSS variable tokens
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
    },
  },
  plugins: [],
}
