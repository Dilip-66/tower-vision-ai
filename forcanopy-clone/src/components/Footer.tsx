"use client";

import { useLayoutEffect, useRef, useState } from "react";

const FOOTER_LINK =
  "shrink-0 whitespace-nowrap text-[13px]! font-semibold text-onbackground/65 transition-colors hover:text-accent";

/**
 * The reference build decides between a stacked and a single-row footer with a
 * ResizeObserver: as soon as `logo + 20px gap + all nav links on one line`
 * fits inside the container, it flips to `justify-between`.
 */
export function Footer({ year = 2026 }: { year?: number }) {
  const container = useRef<HTMLDivElement>(null);
  const brand = useRef<HTMLDivElement>(null);
  const nav = useRef<HTMLElement>(null);
  const [isRow, setIsRow] = useState(false);

  useLayoutEffect(() => {
    const c = container.current;
    const b = brand.current;
    const n = nav.current;
    if (!c || !b || !n) return;

    const measure = () => {
      const available = c.clientWidth;
      const brandWidth = b.getBoundingClientRect().width;
      const links = Array.from(n.children) as HTMLElement[];
      let linksWidth = 0;
      for (const link of links) linksWidth += link.getBoundingClientRect().width;
      if (links.length > 1) linksWidth += (links.length - 1) * 18; // gap-x-[18px]
      setIsRow(brandWidth + 20 + linksWidth <= available);
    };

    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(c);
    return () => ro.disconnect();
  }, []);

  return (
    <footer className="mt-auto">
      <div className="mx-auto max-w-[1120px] px-4 sm:px-6">
        <div className="border-t border-onbackground/10 pb-[40px] pt-[28px]">
          <div
            ref={container}
            className={`flex gap-[20px] ${
              isRow
                ? "flex-row items-center justify-between text-left"
                : "flex-col items-center text-center"
            }`}
          >
            <div
              ref={brand}
              className="flex shrink-0 items-center gap-[12px]"
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                alt="Canopy"
                width={138}
                height={24}
                decoding="async"
                className="dark-hidden h-[18px] w-auto"
                style={{ color: "transparent" }}
                src="/canopy-logo-light.svg"
              />
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                alt="Canopy"
                width={138}
                height={24}
                decoding="async"
                className="light-hidden h-[18px] w-auto"
                style={{ color: "transparent" }}
                src="/canopy-logo-dark.svg"
              />
              <span className="whitespace-nowrap text-[13px]! font-sans! font-semibold text-onbackground/80">
                Confidence in your food.
              </span>
            </div>

            <nav
              ref={nav}
              aria-label="Footer"
              className={`flex flex-wrap items-center gap-x-[18px] gap-y-2 ${
                isRow ? "justify-end" : "justify-center"
              }`}
            >
              {FOOTER_LINKS.map((l) => (
                <a key={l.href} className={FOOTER_LINK} href={l.href}>
                  {l.label}
                </a>
              ))}
            </nav>
          </div>

          <p
            className={`mt-[20px] text-[13px]! leading-normal text-onbackground/65 text-pretty ${
              isRow ? "text-left" : "text-center"
            }`}
          >
            © {year} Canopy. All names, logos, and brands appearing on this site
            are the property of their respective owners. Canopy and its
            products and services are not endorsed by, sponsored by, or
            affiliated with these third parties. Any use of such names is for
            identification purposes only.
          </p>
        </div>
      </div>
    </footer>
  );
}

const FOOTER_LINKS = [
  { href: "/recalls", label: "Recalls" },
  { href: "/regulations", label: "Regulation Standards" },
  { href: "/team", label: "Meet the team" },
  { href: "/feedback", label: "Feedback" },
  { href: "/privacy", label: "Privacy Policy" },
  { href: "/tou", label: "Terms of Use" },
  { href: "/accessibility", label: "Accessibility" },
  { href: "mailto:join@forcanopy.com", label: "Contact" },
];
