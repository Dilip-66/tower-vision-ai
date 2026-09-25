import type { DetectionCard } from "@/lib/data";
import { DetectedPill, PanelPill, StatusPill } from "./Pills";

const SHELL =
  "flex h-full w-full max-w-[330px] mx-auto flex-col rounded-[22px] border border-onbackground/10 bg-surface transition-shadow hover:shadow-[0_20px_50px_-34px_rgba(16,29,70,0.6)]";

/** `/img/opt/nerds.webp` -> `/img/opt/nerds-640.webp` */
const sized = (src: string, w: number) =>
  src.replace(/\/([^/]+)\.([a-z0-9]+)$/, `/$1-${w}.$2`);

const srcSetFor = (src: string) =>
  `${sized(src, 640)} 1x, ${sized(src, 828)} 2x`;

const src2xFor = (src: string) => sized(src, 828);

export function TestCardShell({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <div className={`${SHELL} ${className}`}>{children}</div>;
}

export function TestCardBody({ card }: { card: DetectionCard }) {
  return (
    <a
      className="flex flex-1 flex-col p-[18px]"
      href={`/test-requests/${card.id}`}
    >
      <img
        alt={card.alt}
        loading="lazy"
        width={400}
        height={200}
        decoding="async"
        className="mb-3 h-[170px] w-full rounded-[14px] object-cover"
        style={{ color: "transparent" }}
        srcSet={srcSetFor(card.image)}
        src={src2xFor(card.image)}
      />

      <div className="mb-3 flex flex-wrap items-center gap-1.5">
        <PanelPill category={card.category} />
        <StatusPill status={card.status} />
      </div>

      <h2 className="h5 text-[20px]! leading-snug text-onbackground">
        {card.title}
      </h2>
      <p className="text-base! text-onbackground opacity-70 mt-1">
        {card.source}
      </p>

      {card.confidence ? (
        <div className="mt-4">
          <div className="flex items-center gap-2">
            <div className="flex-1 h-2 rounded-full bg-surface2 overflow-hidden">
              <div
                className="h-full rounded-full transition-all bg-categoryFood"
                style={{ width: `${card.confidence.percent}%` }}
              />
            </div>
            <span className="text-xs text-onbackground opacity-70 whitespace-nowrap">
              {card.confidence.percent}%
            </span>
          </div>
          <div className="mt-1 flex items-center justify-between gap-3 text-sm text-onbackground opacity-70">
            <span>{card.confidence.region}</span>
            <span>{card.confidence.note}</span>
          </div>
        </div>
      ) : null}

      {card.detectedOn ? (
        <div className="mt-4">
          <p className="text-xs! font-semibold uppercase tracking-wider text-onbackground opacity-65">
            Detected on
          </p>
          <p className="mt-0.5 text-base! font-semibold text-onbackground">
            <time dateTime="2026-10-27T19:24:40.085Z">{card.detectedOn}</time>
          </p>
        </div>
      ) : null}

      {card.detected && card.detected.length > 0 ? (
        <div className="flex flex-wrap items-center gap-2 mt-4">
          <span className="text-xs font-semibold uppercase tracking-wider text-onbackground opacity-65">
            Detected
          </span>
          {card.detected.map((d) => (
            <DetectedPill key={d.label} label={d.label} />
          ))}
        </div>
      ) : null}

      {card.status === "No Detection" ? (
        <p className="mt-4 text-xs! font-semibold uppercase tracking-wider text-onbackground opacity-65">
          No tower structure detected
        </p>
      ) : null}

      <div className="mt-auto" aria-hidden="true" />

      <div className="mt-3 border-t border-onbackground/10 pt-2.5 text-sm text-onbackground opacity-70">
        {card.footer}
      </div>
    </a>
  );
}

/** The hero "Featured" card — same shell, plus the diagonal ribbon. */
export function FeaturedTestCard({ card }: { card: DetectionCard }) {
  return (
    <div className="relative">
      <div className="featured-ribbon pointer-events-none absolute top-0 left-0 z-10 flex items-center gap-[0.375em] bg-cta px-[1lh] pb-[var(--f)] text-lg leading-[2.6] font-bold text-onCta">
        <svg
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
          width="24"
          height="24"
          fill="currentColor"
          aria-hidden="true"
          className="remixicon h-[1em] w-[1em]"
        >
          <path d="M12.0006 18.26L4.94715 22.2082L6.52248 14.2799L0.587891 8.7918L8.61493 7.84006L12.0006 0.5L15.3862 7.84006L23.4132 8.7918L17.4787 14.2799L19.054 22.2082L12.0006 18.26Z" />
        </svg>
        Featured
      </div>
      <div
        className={`${SHELL} shadow-[0_24px_60px_-36px_rgba(16,29,70,0.5)]`}
      >
        <TestCardBody card={card} />
      </div>
    </div>
  );
}
