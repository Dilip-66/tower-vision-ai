import { Link } from "../../lib/router";
import { Menu, Moon, Sun, X } from "lucide-react";
import { useEffect, useState } from "react";
import { cn } from "../../lib/utils";

const NAV = [
  { label: "Product", href: "#how-it-works" },
  { label: "Inspections", href: "#inspections" },
  { label: "Quality gate", href: "#quality" },
  { label: "Pricing", href: "#pricing" },
];

export function LandingHeader() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  const [dark, setDark] = useState(false);

  useEffect(() => {
    function onScroll() {
      setScrolled(window.scrollY > 12);
    }

    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle("lp-dark", dark);
  }, [dark]);

  return (
    <header
      className={cn(
        "fixed inset-x-0 top-0 z-50 transition-all duration-300",
        scrolled
          ? "border-b lp-rule bg-[hsl(var(--lp-bg)/0.85)] backdrop-blur-md"
          : "border-b border-transparent"
      )}
    >
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-6 px-5">
        <Link to="/" className="flex items-center gap-2.5">
          <span className="flex h-7 w-7 items-center justify-center rounded-md bg-[hsl(var(--lp-blue))] text-white">
            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M12 3v18M7 21h10M8 8h8M6 13h12M9 3h6" />
            </svg>
          </span>
          <span className="lp-serif text-[17px] font-medium tracking-tight">Tower Vision AI</span>
        </Link>
        <nav className="hidden items-center gap-7 md:flex">
          {NAV.map((item) => (
            <a key={item.label} href={item.href} className="lp-link text-[13px] text-[hsl(var(--lp-ink-soft))] hover:text-[hsl(var(--lp-ink))]">
              {item.label}
            </a>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setDark((v) => !v)}
            aria-label="Toggle theme"
            className="hidden h-9 w-9 items-center justify-center rounded-full lp-rule text-[hsl(var(--lp-ink-soft))] transition-colors hover:text-[hsl(var(--lp-ink))] sm:flex"
          >
            {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>

          <Link to="/app" className="lp-btn lp-btn-primary hidden h-9 px-4 text-[13px] sm:inline-flex">
            Open dashboard
          </Link>

          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            aria-label="Toggle menu"
            className="flex h-9 w-9 items-center justify-center rounded-full lp-rule md:hidden"
          >
            {open ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {open && (
        <div className="border-t lp-rule bg-[hsl(var(--lp-bg))] md:hidden">
          <div className="mx-auto flex max-w-6xl flex-col gap-1 px-5 py-4">
            {NAV.map((item) => (
              <a
                key={item.label}
                href={item.href}
                onClick={() => setOpen(false)}
                className="rounded-md px-2 py-2 text-sm text-[hsl(var(--lp-ink-soft))] hover:bg-[hsl(var(--lp-surface))]"
              >
                {item.label}
              </a>
            ))}
            <Link to="/app" className="lp-btn lp-btn-primary mt-2">
              Open dashboard
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
