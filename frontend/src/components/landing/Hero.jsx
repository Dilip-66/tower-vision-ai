import { ArrowRight, ScanSearch } from "lucide-react";
import { Link } from "../../lib/router";
import { Reveal } from "./Reveal";

export function Hero() {
  return (
    <section className="pt-28 pb-16 sm:pt-36 sm:pb-24">
      <div className="mx-auto max-w-6xl px-5">
        <div className="grid items-start gap-12 lg:grid-cols-[1.1fr_0.9fr] lg:gap-16">
          <div>
            <Reveal>
              <p className="lp-eyebrow">Tower inspection</p>
            </Reveal>

            <Reveal delay={60}>
              <h1 className="lp-serif mt-5 text-[clamp(2.5rem,5.6vw,4.2rem)] font-normal leading-[1.03] tracking-[-0.02em]">
                Every tower site,
                <br />
                read from a{" "}
                <em className="not-italic text-[hsl(var(--lp-blue))]">single photo</em>.
              </h1>
            </Reveal>

            <Reveal delay={110}>
              <p className="mt-6 max-w-lg text-[15px] leading-relaxed text-[hsl(var(--lp-ink-soft))]">
                Field crews upload a site photo. The quality gate checks it, YOLO11n finds the
                structures, and the dashboard returns supporting and monopole counts with a confidence
                score for every box.
              </p>
            </Reveal>

            <Reveal delay={160}>
              <div className="mt-8 flex flex-wrap items-center gap-3">
                <Link to="/app" className="lp-btn lp-btn-primary">
                  <ScanSearch className="h-4 w-4" />
                  Run an inspection
                </Link>
                <a href="#how-it-works" className="lp-btn lp-btn-ghost">
                  How it works
                  <ArrowRight className="h-4 w-4" />
                </a>
              </div>
            </Reveal>
          </div>

          <Reveal delay={120}>
            <figure className="lp-card overflow-hidden p-0">
              <img
                src="/showcase/SOURCE_0111_frame_00_annotated.jpg"
                alt="YOLO11n detection on a monopole tower"
                className="w-full object-cover"
              />
              <figcaption className="flex items-baseline justify-between gap-4 border-t lp-rule px-4 py-3">
                <span className="text-[12px] font-medium">Real model output</span>
                <span className="font-mono text-[11px] text-[hsl(var(--lp-ink-soft))]">
                  monopole_tower · 0.87
                </span>
              </figcaption>
            </figure>
          </Reveal>
        </div>
      </div>
    </section>
  );
}
