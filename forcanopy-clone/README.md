# Tower Vision — landing page

A recreation of the [forcanopy.com](https://www.forcanopy.com/) marketing landing
page, re-badged for **AI-Powered Tower Vision Detection & Visualization**. Identical
layout, typography, colour tokens, spacing, breakpoints and micro-animations.

> **Card imagery is placeholder.** The YOLO dataset lives at
> `tower-vision-ai/data/raw` → `data/interim/annotation/images` (gitignored) and is not
> present on the machine this was built on, so `public/img/opt/tower-*.png` are
> locally-drawn placeholders produced by `scripts/make_placeholder_towers.py`. Nothing
> is downloaded and no external URL is used. Re-run the prepare step and point
> `src/lib/data.ts` at the real samples to swap them in.
>
> **The wordmark still reads "CANOPY".** `CanopyLogo.tsx` is 12 baked SVG letterform
> paths with a per-letter bounce animation. Regenerating letterforms would mean
> redesigning the logo, which is out of scope — drop in a replacement SVG and it is a
> one-file change. All *textual* branding (alt, `aria-label`, metadata, footer copy)
> already reads Tower Vision.

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
    Header.tsx      sticky nav — brand, nav links, theme toggle, Get Started,
                    mobile sheet menu
    Hero.tsx        animated gradient hero, squiggle underline, featured card
    HowItWorks.tsx  4-step grid
    RecentTests.tsx snap-scrolling results carousel (arrows + dots); carries
                    id="detection", the Get Started anchor target
    CallToAction.tsx dark CTA band with ripple rings
    Newsletter.tsx  subscribe form
    Footer.tsx      ResizeObserver-driven stacked/row layout
    CookieBanner.tsx storage-event consent banner
    TestCard.tsx    shared card shell + body + featured ribbon
    RippleRings.tsx 7 staggered expanding blob rings
    CanopyLogo.tsx  logo with per-letter bounce animation
    Squiggle.tsx    hand-drawn h1 underline
    Icons.tsx       Remix-style icon set
    Pills.tsx       class / status / detected chips
  lib/
    data.ts         detection results + step content
    ripple.ts       organic blob paths + ring timing
    theme-script.ts pre-paint theme bootstrap
public/
  fonts/            16 woff2 subsets
  img/opt/          card imagery (640 / 828 variants)
  canopy-logo-*.svg
scripts/
  make_placeholder_towers.py  regenerates the placeholder card images
```

## Navigation

The navbar exposes brand, `Detect` / `Visualize` / `How It Works`, the theme toggle
and a single **Get Started** call to action. Search, cart, login and sign-up were
removed. Get Started is an in-page anchor to `#detection` (the existing
detection/results section) — it reuses the pre-existing sign-up button classes
verbatim, and keeps the original `min-[1024px]` visibility so the bar's proportions
are unchanged at every breakpoint.

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
