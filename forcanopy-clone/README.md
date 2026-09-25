# Canopy — landing page clone

A pixel-perfect recreation of the [forcanopy.com](https://www.forcanopy.com/) marketing
landing page: identical layout, typography, colour tokens, spacing, breakpoints and
micro-animations, rebuilt from scratch.

## Stack

- **Next.js 16** (App Router) + **React 19**
- **Tailwind CSS v4** with a hand-rebuilt `@theme` that mirrors the original token scale
  (spacing, type scale, radii, weights, the full `background / surface / cta / accent /
  category* / status*` palette, and a complete `data-theme="dark"` palette)
- Self-hosted **Figtree**, **Geist Mono** and **Playfair Display** variable fonts
  (same `@font-face` unicode-range splits + size-adjusted fallbacks as the original)

## Running it

```bash
npm install
npm run dev     # http://localhost:3000
npm run build && npm start
```

## Structure

```
src/
  app/
    globals.css     design tokens, light/dark palettes, keyframes, base rules
    layout.tsx      metadata + pre-paint theme script
    page.tsx        page composition
  components/
    Header.tsx      sticky nav, desktop links, inline search, mobile sheet menu
    Hero.tsx        animated gradient hero, squiggle underline, featured card
    HowItWorks.tsx  4-step grid
    RecentTests.tsx snap-scrolling results carousel (arrows + dots)
    CallToAction.tsx dark CTA band with ripple rings
    Newsletter.tsx  subscribe form
    Footer.tsx      ResizeObserver-driven stacked/row layout
    CookieBanner.tsx storage-event consent banner
    TestCard.tsx    shared card shell + body + featured ribbon
    RippleRings.tsx 7 staggered expanding blob rings
    CanopyLogo.tsx  logo with per-letter bounce animation
    Squiggle.tsx    hand-drawn h1 underline
    Icons.tsx       Remix-style icon set
    Pills.tsx       panel / status / detected chips
  lib/
    data.ts         test-request + step content
    ripple.ts       organic blob paths + ring timing
    theme-script.ts pre-paint theme bootstrap
public/
  fonts/            16 woff2 subsets
  img/opt/          product imagery (640 / 828 variants)
  canopy-logo-*.svg
```

## Fidelity notes

The original ships several `!`-important type utilities because its base rules sit
*outside* any cascade layer (`p { font-size: 14px }` beats the layered `text-lg`). That
behaviour is reproduced exactly — do not "clean up" the `text-*!` classes.

Animations reproduced verbatim:

| effect | timing |
| --- | --- |
| Hero gradient drift | `30s ease-in-out infinite` |
| Ripple rings | `8s ease-out infinite`, delays `0 … -6.86s`, `--ring-scale` 1.2 → 5.7 |
| Logo letter bounce | `5s infinite`, 0→4% up `-4px`, per-letter delays `0 … 0.55s` |
| Nav sheet open | `height/border-radius` 500ms, menu `opacity/transform` 400ms + 150ms delay |
| Dot colour | `transition-colors` |
| `prefers-reduced-motion` | all of the above disabled |

Root font size is `16px`, stepping to `20px` at `≥768px` — so `max-w-4xl` resolves to
exactly `1120px` on desktop, which is what the `max-w-[1120px]` container relies on.
