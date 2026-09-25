import { Reveal } from "./Reveal";

const STEPS = [
  {
    n: "01",
    title: "Capture",
    body: "Snap a field photo of the tower. No app install, no field forms.",
  },
  {
    n: "02",
    title: "Validate",
    body: "A quality gate checks sharpness, exposure and resolution before any inference runs.",
  },
  {
    n: "03",
    title: "Detect",
    body: "YOLO11n classifies supporting and monopole structures and scores every prediction.",
  },
  {
    n: "04",
    title: "Review",
    body: "Get bounding boxes, per-class confidence and an annotated image ready for reporting.",
  },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="border-t lp-rule py-16 sm:py-24">
      <div className="mx-auto max-w-6xl px-5">
        <Reveal className="max-w-2xl">
          <p className="lp-eyebrow">How it works</p>
          <h2 className="lp-serif mt-4 text-[clamp(1.9rem,3.6vw,2.9rem)] leading-[1.1] tracking-[-0.02em]">
            Photo in, verified{" "}
            <em className="not-italic text-[hsl(var(--lp-blue))]">evidence</em> out.
          </h2>
        </Reveal>

        <div className="mt-12">
          {STEPS.map((step, index) => (
            <Reveal key={step.n} delay={index * 60}>
              <div className="grid gap-2 border-t lp-rule py-6 sm:grid-cols-[80px_200px_1fr] sm:items-baseline sm:gap-6">
                <span className="font-mono text-[11px] tabular-nums text-[hsl(var(--lp-blue))]">
                  {step.n}
                </span>
                <h3 className="lp-serif text-[20px] leading-snug">{step.title}</h3>
                <p className="max-w-lg text-[13px] leading-relaxed text-[hsl(var(--lp-ink-soft))]">
                  {step.body}
                </p>
              </div>
            </Reveal>
          ))}
          <div className="border-t lp-rule" />
        </div>
      </div>
    </section>
  );
}
