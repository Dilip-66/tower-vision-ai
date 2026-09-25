"use client";

import { useEffect, useRef, useState } from "react";
import { TowerVisionLogo } from "./TowerVisionLogo";

const NAV_LINKS = [
  { href: "/search?status=active", label: "Detect" },
  { href: "/test-results", label: "Visualize" },
  { href: "/about", label: "How It Works" },
];

const DESKTOP_LINK =
  "font-semibold text-[15px]! transition-colors whitespace-nowrap border-b-2 pb-[2px] pt-1 border-transparent text-onbackground/70 hover:text-accent";

const MOBILE_LINK =
  "rounded-lg px-5 py-2.5 font-title text-[36px]! font-semibold tracking-[-0.02em] text-onbackground transition-colors hover:text-accent ";

export function Header() {
  const [open, setOpen] = useState(false);
  const [dark, setDark] = useState(false);
  const closeRef = useRef<HTMLButtonElement>(null);

  // Sync the toggle with whatever the inline head script already applied.
  useEffect(() => {
    setDark(document.documentElement.getAttribute("data-theme") === "dark");
  }, []);

  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    if (open) closeRef.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const toggleTheme = () => {
    const next = dark ? "light" : "dark";
    setDark(!dark);
    document.documentElement.setAttribute("data-theme", next);
    try {
      localStorage.setItem("theme", next);
    } catch {}
  };

  return (
    <header className="sticky top-0 z-50 h-[88px] px-3 sm:px-6">
      <div className="relative mx-auto h-full max-w-[1120px]">
        <nav
          aria-label="Primary"
          className={`absolute inset-x-0 top-[12px] flex flex-col overflow-hidden border border-onbackground/10 shadow-[0_8px_30px_-18px_rgba(16,29,70,0.35)] backdrop-blur-md transition-[height,border-radius,background-color] duration-500 ease-[cubic-bezier(0.4,0,0.2,1)] ${
            open
              ? "h-[calc(100dvh-24px)] rounded-3xl bg-background"
              : "h-[64px] rounded-[18px] bg-background/85"
          }`}
        >
          <div className="flex h-[64px] shrink-0 items-center gap-4 pl-[18px] pr-3">
            <a className="shrink-0" href="/">
              <TowerVisionLogo />
            </a>

            <div className="hidden min-[1024px]:flex min-[1024px]:items-center min-[1024px]:gap-[22px] min-[1180px]:gap-[26px]">
              {NAV_LINKS.map((l) => (
                <a key={l.href} className={DESKTOP_LINK} href={l.href}>
                  {l.label}
                </a>
              ))}
            </div>

            <div className="ml-auto flex shrink-0 items-center gap-[10px]">
              <button
                type="button"
                aria-label={dark ? "Switch to light theme" : "Switch to dark theme"}
                title={dark ? "Switch to light theme" : "Switch to dark theme"}
                onClick={toggleTheme}
                className="flex h-[38px] shrink-0 cursor-pointer items-center gap-2 rounded-xl border border-onbackground/10 px-3 text-[13px]! font-semibold text-onbackground/65 transition-colors hover:border-onbackground hover:text-onbackground"
              >
                <span
                  aria-hidden="true"
                  className="inline-block h-[10px] w-[10px] rounded-full bg-onbackground shadow-[inset_3px_-2px_0_0_var(--background)]"
                />
                <span className="hidden capitalize min-[1180px]:inline">
                  {dark ? "dark" : "light"}
                </span>
              </button>

              <div className="hidden min-[1024px]:flex min-[1024px]:items-center min-[1024px]:gap-[10px]">
                <a
                  className="font-semibold text-[15px]! transition-colors whitespace-nowrap rounded-xl bg-cta px-[18px] py-[10px] font-bold text-onCta hover:bg-accent hover:text-onAccent"
                  href="#detection"
                  onClick={() => setOpen(false)}
                >
                  Get Started
                </a>
              </div>

              <button
                onClick={() => setOpen((v) => !v)}
                className="flex h-[38px] w-[38px] shrink-0 cursor-pointer flex-col items-center justify-center gap-[5px] rounded-xl border border-onbackground/10 text-onbackground min-[1024px]:hidden"
                aria-label={open ? "Close menu" : "Open menu"}
                aria-expanded={open}
                aria-controls="mobile-nav-menu"
              >
                <span
                  aria-hidden="true"
                  className={`block h-[2px] w-[18px] rounded-full bg-onbackground transition-transform duration-300 ${
                    open ? "translate-y-[7px] rotate-45" : ""
                  }`}
                />
                <span
                  aria-hidden="true"
                  className={`block h-[2px] w-[18px] rounded-full bg-onbackground transition-opacity duration-200 ${
                    open ? "opacity-0" : ""
                  }`}
                />
                <span
                  aria-hidden="true"
                  className={`block h-[2px] w-[18px] rounded-full bg-onbackground transition-transform duration-300 ${
                    open ? "-translate-y-[7px] -rotate-45" : ""
                  }`}
                />
              </button>
            </div>
          </div>

          <div
            id="mobile-nav-menu"
            role="dialog"
            aria-modal="true"
            aria-label="Site menu"
            aria-hidden={!open}
            inert={!open}
            className={`flex flex-1 flex-col items-center justify-center gap-1 overflow-y-auto px-8 transition-[opacity,transform] min-[1024px]:hidden ${
              open
                ? "pointer-events-auto translate-y-0 opacity-100 duration-400 delay-150"
                : "pointer-events-none translate-y-4 opacity-0 duration-150"
            }`}
          >
            {NAV_LINKS.map((l) => (
              <a key={l.href} className={MOBILE_LINK} href={l.href}>
                {l.label}
              </a>
            ))}
            <a
              className="mt-5 rounded-[14px] bg-cta px-7 py-4 text-[16px]! font-bold text-onCta transition-colors hover:bg-accent hover:text-onAccent"
              href="#detection"
              onClick={() => setOpen(false)}
            >
              Get Started
            </a>
            <button
              ref={closeRef}
              type="button"
              onClick={() => setOpen(false)}
              className="sr-only focus:not-sr-only focus:mt-4 focus:cursor-pointer focus:rounded-lg focus:px-4 focus:py-2 focus:text-[14px]! focus:font-semibold focus:text-onbackground focus:outline-2 focus:outline-accent"
            >
              Close menu
            </button>
          </div>
        </nav>
      </div>
    </header>
  );
}
