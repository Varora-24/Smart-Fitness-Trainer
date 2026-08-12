---
name: Arogya Vision Alpha
colors:
  surface: '#131315'
  surface-dim: '#131315'
  surface-bright: '#39393b'
  surface-container-lowest: '#0e0e10'
  surface-container-low: '#1c1b1d'
  surface-container: '#201f21'
  surface-container-high: '#2a2a2c'
  surface-container-highest: '#353437'
  on-surface: '#e5e1e4'
  on-surface-variant: '#d0c5af'
  inverse-surface: '#e5e1e4'
  inverse-on-surface: '#313032'
  outline: '#99907c'
  outline-variant: '#4d4635'
  surface-tint: '#e9c349'
  primary: '#f2ca50'
  on-primary: '#3c2f00'
  primary-container: '#d4af37'
  on-primary-container: '#554300'
  inverse-primary: '#735c00'
  secondary: '#a2e7ff'
  on-secondary: '#003642'
  secondary-container: '#00d2fd'
  on-secondary-container: '#005669'
  tertiary: '#53e97d'
  on-tertiary: '#003915'
  tertiary-container: '#2ecc64'
  on-tertiary-container: '#005020'
  error: '#EF4444'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffe088'
  primary-fixed-dim: '#e9c349'
  on-primary-fixed: '#241a00'
  on-primary-fixed-variant: '#574500'
  secondary-fixed: '#b4ebff'
  secondary-fixed-dim: '#3cd7ff'
  on-secondary-fixed: '#001f27'
  on-secondary-fixed-variant: '#004e5f'
  tertiary-fixed: '#6bff8f'
  tertiary-fixed-dim: '#4ae176'
  on-tertiary-fixed: '#002109'
  on-tertiary-fixed-variant: '#005321'
  background: '#131315'
  on-background: '#e5e1e4'
  surface-variant: '#353437'
  bg-secondary: '#0F172A'
  text-primary: '#F8FAFC'
  text-secondary: '#A1A1AA'
  text-muted: '#71717A'
  glass-surface: rgba(255, 255, 255, 0.04)
  glass-elevated: rgba(255, 255, 255, 0.07)
  border-subtle: rgba(255, 255, 255, 0.08)
typography:
  display-metric:
    fontFamily: Inter
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
  section-title:
    fontFamily: Inter
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 28px
  card-title:
    fontFamily: Inter
    fontSize: 17px
    fontWeight: '600'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.01em
  metadata:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  sidebar-width: 260px
  header-height: 72px
  container-padding-mobile: 16px
  container-padding-desktop: 32px
---

## Brand & Style

The design system embodies a "Sophisticated Fusion" — a premium intersection of high-performance technology and organic wellness. It is designed to evoke a sense of calm intelligence and "Silent Wealth," moving away from aggressive fitness tropes toward a refined, AI-driven mentorship experience.

The visual style is **Glassmorphism**, characterized by deep tonal layering, frosted surfaces, and vibrant telemetry accents. The interface acts as a high-fidelity "Heads-Up Display" (HUD) for the athlete, prioritizing clarity of data through breathable layouts and luminous depth. 

**Key Principles:**
- **Technological Precision:** Sharp AI feedback and telemetry using Cyan.
- **Organic Premium:** Subtle wellness cues and traditional "Gold" accents.
- **Atmospheric Depth:** A deep, dark environment that allows performance metrics to glow and command attention.

## Colors

The palette is anchored in a **Deep Dark** theme to minimize visual fatigue and maximize the vibrance of AI insights.

- **Primary (Brand Gold):** Reserved for core brand expression, active navigation states, and high-value wellness achievements.
- **Secondary (AI Cyan):** Used exclusively for technology-driven feedback, computer vision overlays, and real-time telemetry.
- **Neutral (Base Surfaces):** The primary background is nearly black to create an infinite canvas, while secondary surfaces use a deep navy tint to provide structural depth.
- **Semantic Colors:** Success (Green) and Error (Red) are strictly functional, used to communicate form accuracy and critical alerts.

## Typography

This design system utilizes **Inter** across all levels to maintain a clean, utilitarian aesthetic that feels modern and readable. 

Hierarchy is established through extreme scale—large, bold metrics provide "at-a-glance" readability during intense physical activity, while body and metadata text remain compact and efficient. For data-heavy views, use `display-metric` for counts and scores to ensure they dominate the visual field.

## Layout & Spacing

The system follows a strict **8px spacing rhythm**. 

**Desktop Layout:**
- A fixed **Sidebar** (260px) facilitates high-level navigation.
- A **Header** (72px) houses contextual actions and profile status.
- Content is organized in a fluid grid with a 12-column structure, using 24px gutters.

**Mobile Layout:**
- The sidebar collapses into a bottom navigation bar or a hamburger menu.
- Side margins reduce to 16px.
- Metrics and cards reflow into a single-column vertical stack to maintain legibility.

**Component Density:**
- Cards utilize `lg` (24px) internal padding to maintain a premium, spacious feel. 
- Form elements and buttons use `md` (16px) padding for optimal touch targets (min 44px).

## Elevation & Depth

Depth is created through **Glassmorphism** and tonal stacking rather than traditional heavy shadows.

- **Surface Layers:** The background `#0B0B0D` is the lowest level. Secondary containers use `#0F172A` to create "wells."
- **Glass Surfaces:** Foreground cards use `rgba(255, 255, 255, 0.04)` with a `backdrop-filter: blur(12px)`.
- **Borders:** Every glass surface must have a 1px solid border of `rgba(255, 255, 255, 0.08)` to define the edge against dark backgrounds.
- **Luminous Glows:** Active states and AI components utilize a soft outer glow (`box-shadow`) using a low-opacity version of the Cyan or Gold accents to simulate light emission.

## Shapes

The shape language is organic yet structured. Large container elements (cards, modal surfaces) use a generous **18–24px radius** to feel approachable and "human." 

Interactive elements like buttons and inputs use a slightly sharper **12px radius** to denote clickability and precision. Status badges and tags utilize a **Pill-shaped** (999px) radius for immediate recognition as categorical metadata.

## Components

### Buttons & CTAs
- **Primary:** Solid Brand Gold background with dark text. Apply a subtle gold glow on hover.
- **AI Action:** Solid AI Cyan background. Reserved for "Start Tracking" or "AI Analysis."
- **Secondary/Glass:** Ghost buttons with the standard glass background and border.

### Cards
- Use the standard glass surface with 24px padding. 
- Titles should be `card-title` in `text-primary`.
- In telemetry cards, the primary metric should use `display-metric` in AI Cyan.

### Inputs & Fields
- Backgrounds use `glass-elevated` for better contrast.
- 1px border that turns AI Cyan on focus.
- Placeholder text uses `text-muted`.

### AI Telemetry Overlays
- **Skeleton Tracking:** 2px solid lines in AI Cyan for joints and segments.
- **Form Feedback:** Arcs and alignment markers shift to Success Green when correct, or Error Red with a "pulsing" animation when corrected movement is required.

### Lists
- Minimalist dividers using `border-subtle`.
- High contrast between primary label (`text-primary`) and metadata (`text-muted`).