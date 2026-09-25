import { Gauge, Layers, ShieldCheck, Timer } from "lucide-react";
import { Reveal } from "./Reveal";

const METRICS = [
  { label: "Sharpness (Laplacian)", value: "142.8" },
  { label: "Mean brightness", value: "118.4" },
  { label: "Resolution", value: "1280 × 960" },
  { label: "Dark pixel ratio", value: "4.2%" },
];

const CHECKS = [
  "File decodes and matches a supported format",
  "Resolution clears the minimum inspection size",
  "Sharpness sits above the blur threshold",
  "Exposure falls inside the acceptable range",
];

export function QualitySection() {
  return (
    <section id="quality" className="border-t lp-rule py-16 sm:py-24">
      <div className="mx-auto max-w-6xl px-5">
        <div className="grid gap-12 lg:grid-cols-2 lg:items-center lg:gap-16">
          <Reveal>
            <p className="lp-eyebrow">Quality gate</p>
            <h2 className="lp-serif mt-4 text-[clamp(1.9rem,3.6vw,2.9rem)] leading-[1.1] tracking-[-0.02em]">
              A blurred photo never reaches the{" "}
              <em className="not-italic text-[hsl(var(--lp-blue))]">model</em>.
            </h2>
            <p className="mt-5 max-w-md text-[15px] leading-relaxed text-[hsl(var(--lp-ink-soft))]">
              Dark, blurry or undersized uploads are turned away before inference, with a reason the
              crew can act on. Confidence numbers then mean something.
            </p>

            <ul className="mt-8 space-y-3">
              {CHECKS.map((check, index) => (
                <Reveal key={check} as="li" delay={index * 70} className="flex items-start gap-3">
                  <span className="mt-[3px] font-mono text-[11px] tabular-nums text-[hsl(var(--lp-blue))]">
                    0{index + 1}
                  </span>
                  <span className="text-[14px] leading-relaxed">{check}</span>
                </Reveal>
              ))}
            </ul>
          </Reveal>

          <Reveal delay={120}>
            <div className="lp-card overflow-hidden p-0">
              <div className="flex items-center justify-between border-b lp-rule px-4 py-3">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-[hsl(var(--lp-blue))]" />
                  <span className="text-[13px] font-medium">Image quality</span>
                </div>
                <span className="rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-0.5 text-[11px] font-medium text-emerald-700">
                  Passed
                </span>
              </div>

              <div className="grid grid-cols-3 gap-px bg-[hsl(var(--lp-line))]">
                <Stat icon={Timer} label="Latency" value="1.4s" />
                <Stat icon={Layers} label="Model" value="YOLO11n" />
                <Stat icon={Gauge} label="Threshold" value="0.25" />
              </div>

              <dl className="grid grid-cols-2 gap-px border-t lp-rule bg-[hsl(var(--lp-line))]">
                {METRICS.map((metric) => (
                  <div key={metric.label} className="bg-[hsl(var(--lp-surface))] px-4 py-3.5">
                    <dt className="text-[11px] text-[hsl(var(--lp-ink-soft))]">{metric.label}</dt>
                    <dd className="mt-0.5 text-[15px] font-medium tabular-nums">{metric.value}</dd>
                  </div>
                ))}
              </dl>
            </div>
          </Reveal>
        </div>
      </div>
    </section>
  );
}

function Stat({ icon: Icon, label, value }) {
  return (
    <div className="bg-[hsl(var(--lp-surface))] px-4 py-3.5">
      <Icon className="h-3.5 w-3.5 text-[hsl(var(--lp-blue))]" aria-hidden="true" />
      <p className="mt-1.5 text-[11px] text-[hsl(var(--lp-ink-soft))]">{label}</p>
      <p className="text-[14px] font-medium tabular-nums">{value}</p>
    </div>
  );
}
