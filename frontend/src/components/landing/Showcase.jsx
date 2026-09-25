import { ArrowRight } from "lucide-react";
import { Reveal } from "./Reveal";

/**
 * Site photos from the project's own inspection dataset.
 * Captions stay factual: source file name only, no invented class labels.
 */
const SITES = [
  { src: "/showcase/SOURCE_0002_frame_00.jpg", name: "SOURCE_0002_frame_00" },
  { src: "/showcase/SOURCE_0004_frame_00.jpg", name: "SOURCE_0004_frame_00" },
  { src: "/showcase/SOURCE_0007_frame_00.jpg", name: "SOURCE_0007_frame_00" },
  { src: "/showcase/SOURCE_0009_frame_00.jpg", name: "SOURCE_0009_frame_00" },
  { src: "/showcase/SOURCE_0003_frame_01.jpg", name: "SOURCE_0003_frame_01" },
  { src: "/showcase/SOURCE_0015_frame_00.jpg", name: "SOURCE_0015_frame_00" },
];

export function Showcase() {
  return (
    <section id="inspections" className="border-t lp-rule py-16 sm:py-24">
      <div className="mx-auto max-w-6xl px-5">
        <Reveal className="flex flex-wrap items-end justify-between gap-6">
          <div className="max-w-xl">
            <p className="lp-eyebrow">Site imagery</p>
            <h2 className="lp-serif mt-4 text-[clamp(1.9rem,3.6vw,2.9rem)] leading-[1.1] tracking-[-0.02em]">
              The photos crews actually{" "}
              <em className="not-italic text-[hsl(var(--lp-blue))]">upload</em>.
            </h2>
          </div>
          <a
            href="#quality"
            className="lp-link inline-flex items-center gap-1.5 text-[13px] text-[hsl(var(--lp-ink-soft))]"
          >
            How images get validated
            <ArrowRight className="h-3.5 w-3.5" />
          </a>
        </Reveal>
      </div>

      <Reveal className="mt-12" delay={80}>
        <div className="lp-marquee-wrap overflow-hidden [mask-image:linear-gradient(90deg,transparent,black_5%,black_95%,transparent)]">
          <div className="lp-marquee">
            {[...SITES, ...SITES].map((site, index) => (
              <figure
                key={index}
                className="lp-card w-[240px] shrink-0 overflow-hidden p-0"
              >
                <img
                  src={site.src}
                  alt={`Site photo ${site.name}`}
                  loading="lazy"
                  className="h-56 w-full bg-[hsl(var(--lp-line))] object-cover"
                />
                <figcaption className="space-y-0.5 px-4 py-3">
                  <p className="text-[12px] font-medium">Site photo</p>
                  <p className="font-mono text-[10px] text-[hsl(var(--lp-ink-soft))]">{site.name}</p>
                </figcaption>
              </figure>
            ))}
          </div>
        </div>
      </Reveal>
    </section>
  );
}
