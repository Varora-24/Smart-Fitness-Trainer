/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['../app/**/*.py', '../core/**/*.py'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'bg-secondary': '#0F172A',
        'surface-container': '#201f21',
        'primary-container': '#d4af37',
        'primary': '#f2ca50',
        'text-primary': '#F8FAFC',
        'text-secondary': '#A1A1AA',
        'text-muted': '#71717A',
        'surface': '#131315',
        'glass-surface': 'rgba(255, 255, 255, 0.04)',
        'background': '#131315',
        'border-subtle': 'rgba(255, 255, 255, 0.08)',
        'secondary': '#a2e7ff',
        'secondary-container': '#00d2fd',
        'error': '#EF4444',
        'glass-elevated': 'rgba(255, 255, 255, 0.07)',
        'tertiary': '#53e97d',
        'tertiary-container': '#2ecc64'
      },
      fontFamily: {
        'label-md': ['Inter'],
        'body-md': ['Inter'],
        'section-title': ['Inter'],
        'headline-lg': ['Inter'],
        'metadata': ['Inter'],
        'card-title': ['Inter'],
        'body-sm': ['Inter'],
        'display-metric': ['Inter'],
        'headline-lg-mobile': ['Inter']
      }
    }
  }
}