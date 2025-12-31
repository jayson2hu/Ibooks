/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
        './src/components/**/*.{js,ts,jsx,tsx,mdx}',
        './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    ],
    theme: {
        extend: {
            colors: {
                primary: {
                    DEFAULT: '#6366f1',
                    dark: '#4f46e5',
                    light: '#818cf8',
                },
                secondary: '#8b5cf6',
                accent: '#ec4899',
            },
            animation: {
                'blob': 'blob 7s infinite',
                'fadeIn': 'fadeIn 0.5s ease-out',
                'fadeInUp': 'fadeInUp 0.6s ease-out',
                'slideInLeft': 'slideInLeft 0.5s ease-out',
                'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                'shimmer': 'shimmer 2s infinite',
            },
            keyframes: {
                blob: {
                    '0%': {
                        transform: 'translate(0px, 0px) scale(1)',
                    },
                    '33%': {
                        transform: 'translate(30px, -50px) scale(1.1)',
                    },
                    '66%': {
                        transform: 'translate(-20px, 20px) scale(0.9)',
                    },
                    '100%': {
                        transform: 'translate(0px, 0px) scale(1)',
                    },
                },
                fadeIn: {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                fadeInUp: {
                    '0%': {
                        opacity: '0',
                        transform: 'translateY(20px)',
                    },
                    '100%': {
                        opacity: '1',
                        transform: 'translateY(0)',
                    },
                },
                slideInLeft: {
                    '0%': {
                        opacity: '0',
                        transform: 'translateX(-20px)',
                    },
                    '100%': {
                        opacity: '1',
                        transform: 'translateX(0)',
                    },
                },
                shimmer: {
                    '0%': {
                        backgroundPosition: '-1000px 0',
                    },
                    '100%': {
                        backgroundPosition: '1000px 0',
                    },
                },
            },
            transitionDuration: {
                '250': '250ms',
            },
            transitionTimingFunction: {
                'smooth': 'cubic-bezier(0.4, 0, 0.2, 1)',
            },
        },
    },
    plugins: [],
}
