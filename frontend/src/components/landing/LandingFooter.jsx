import { Link } from "../../lib/router";

const COLUMNS = [
  { title: "Product", links: ["Dashboard", "Inspections", "Analytics", "Quality gate"] },
  { title: "Company", links: ["About", "Contact", "Careers"] },
  { title: "Legal", links: ["Privacy", "Terms", "Accessibility"] },
];

export function LandingFooter() {
  return (
    <footer className="border-t lp-rule">
      <div className="mx-auto max-w-6xl px-5 py-14">
        <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <div className="flex items-center gap-2.5">
              <span className="flex h-7 w-7 items-center justify-center rounded-md bg-[hsl(var(--lp-blue))] text-white">
                <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                  <path d="M12 3v18M7 21h10M8 8h8M6 13h12M9 3h6" />
                </svg>
              </span>
              <span className="lp-serif text-[17px] font-medium">Tower Vision AI</span>
            </div>
            <p className="mt-4 max-w-xs text-[13px] leading-relaxed text-[hsl(var(--lp-ink-soft))]">
              AI-assisted telecom tower component detection with image quality validation.
            </p>
          </div>

          {COLUMNS.map((column) => (
            <div key={column.title}>
              <p className="text-[12px] font-medium uppercase tracking-[0.14em] text-[hsl(var(--lp-ink-soft))]">
                {column.title}
              </p>
              <ul className="mt-4 space-y-2.5">
                {column.links.map((item) => (
                  <li key={item}>
                    <span className="lp-link cursor-pointer text-[13px] text-[hsl(var(--lp-ink-soft))] hover:text-[hsl(var(--lp-ink))]">
                      {item}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-12 flex flex-col items-start justify-between gap-3 border-t lp-rule pt-6 sm:flex-row sm:items-center">
          <p className="text-[12px] text-[hsl(var(--lp-ink-soft))]">
            © {new Date().getFullYear()} Tower Vision AI. All rights reserved.
          </p>
          <Link
            to="/app"
            className="lp-link text-[12px] text-[hsl(var(--lp-ink-soft))] hover:text-[hsl(var(--lp-ink))]"
          >
            Open dashboard →
          </Link>
        </div>
      </div>
    </footer>
  );
}
