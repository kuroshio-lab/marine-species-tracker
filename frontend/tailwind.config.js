/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: ['class'],
    content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    './node_modules/@kuroshio-lab/ui/**/*.{js,ts,jsx,tsx,mjs}',
    './node_modules/@kuroshio-lab/components/**/*.{js,ts,jsx,tsx,mjs}',
  ],
  theme: {
  	extend: {
  		borderRadius: {
  			lg: 'var(--radius)',
  			md: 'calc(var(--radius) - 2px)',
  			sm: 'calc(var(--radius) - 4px)'
  		},
  		colors: {
        ocean: {
          '50': 'hsl(var(--brand-primary-100))',
          '100': 'hsl(var(--brand-primary-100))',
          '200': 'hsl(var(--neutral-gray-300))',
          '300': 'hsl(var(--brand-primary-300))',
          '400': 'hsl(var(--brand-primary-500))',
          '500': 'hsl(var(--brand-primary-500))',
          '600': 'hsl(var(--brand-primary-700))',
          '700': 'hsl(var(--brand-primary-700))',
          '800': 'hsl(var(--brand-primary-900))',
          '900': 'hsl(var(--brand-primary-900))',
        },
  			background: 'hsl(var(--background))',
  			foreground: 'hsl(var(--foreground))',
  			card: {
  				DEFAULT: 'hsl(var(--card))',
  				foreground: 'hsl(var(--card-foreground))'
  			},
  			popover: {
  				DEFAULT: 'hsl(var(--popover))',
  				foreground: 'hsl(var(--popover-foreground))'
  			},
  			primary: {
  				DEFAULT: 'hsl(var(--primary))',
  				foreground: 'hsl(var(--primary-foreground))'
  			},
  			secondary: {
  				DEFAULT: 'hsl(var(--secondary))',
  				foreground: 'hsl(var(--secondary-foreground))'
  			},
  			muted: {
  				DEFAULT: 'hsl(var(--muted))',
  				foreground: 'hsl(var(--muted-foreground))'
  			},
  			accent: {
  				DEFAULT: 'hsl(var(--accent))',
  				foreground: 'hsl(var(--accent-foreground))',
          eco: 'hsl(var(--accent-eco-500))',
          coral: 'hsl(var(--accent-coral-500))',
          sand: 'hsl(var(--accent-sand-light))',
  			},
  			destructive: {
  				DEFAULT: 'hsl(var(--destructive))',
  				foreground: 'hsl(var(--destructive-foreground))'
  			},
  			border: 'hsl(var(--border))',
  			input: 'hsl(var(--input))',
  			ring: 'hsl(var(--ring))',
  			chart: {
  				'1': 'hsl(var(--chart-1))',
  				'2': 'hsl(var(--chart-2))',
  				'3': 'hsl(var(--chart-3))',
  				'4': 'hsl(var(--chart-4))',
  				'5': 'hsl(var(--chart-5))'
  			},
        // Brand Colors
        brand: {
          'primary-900': 'hsl(var(--brand-primary-900))',
          'primary-700': 'hsl(var(--brand-primary-700))',
          'primary-500': 'hsl(var(--brand-primary-500))',
          'primary-300': 'hsl(var(--brand-primary-300))',
          'primary-100': 'hsl(var(--brand-primary-100))',
        },
        neutral: {
            'gray-900': 'hsl(var(--neutral-gray-900))',
            'gray-700': 'hsl(var(--neutral-gray-700))',
            'gray-500': 'hsl(var(--neutral-gray-500))',
            'gray-300': 'hsl(var(--neutral-gray-300))',
            'gray-100': 'hsl(var(--neutral-gray-100))',
            'white': 'hsl(var(--neutral-white))',
        },
        semantic: {
            'success-500': 'hsl(var(--semantic-success-500))',
            'success-100': 'hsl(var(--semantic-success-100))',
            'warning-500': 'hsl(var(--semantic-warning-500))',
            'warning-100': 'hsl(var(--semantic-warning-100))',
            'error-500': 'hsl(var(--semantic-error-500))',
            'error-100': 'hsl(var(--semantic-error-100))',
        }
  		},
    fontFamily: {
      title: ["var(--font-title)", "sans-serif"],
      subtitle: ["var(--font-subtitle)", "sans-serif"],
      body: ["var(--font-body)", "sans-serif"],
    },
  	}
  },
  plugins: [require("tailwindcss-animate")],
}
