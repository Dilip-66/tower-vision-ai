import { Reveal } from "./Reveal";

/**
 * Editorial list instead of an icon-card grid.
 * Hairline rules + index numbers read as documentation, not marketing filler.
 */
const CAPABILITIES = [
  {
    n: "01",
    title: "Single endpoint",
    body: "POST a file to one REST route and get structured detection JSON back. No SDK, no queue.",
  },
  {
    n: "02",
    title: "Two classes, counted",
    body: "Supporting and monopole towers are tallied separately, with per-class average confidence.",
  },
  {
    n: "03",
    title: "Boxes you can trace",
    body: "Every prediction carries a score and coordinates, so a number is never just a number.",
  },
  {
    n: "04",
    title: "Evidence you can file",
    body: "Download the annotated image for a report, a ticket or a handover pack.",
  },
  {
    n: "05",
    title: "Session history",
    body: "Runs stay listed with image, type, confidence and pass or fail status.",
  },
];

export function Features() {
  return (
    <section id="pricing" className="border-t lp-rule py-16 sm:py-24">
      <div className="mx-auto max-w-6xl px-5">
        <div className="grid gap-12 lg:grid-cols-[0.8fr_1.2fr] lg:gap-16">
          <Reveal>
            <p className="lp-eyebrow">Capabilities</p>
            <h2 className="lp-serif mt-4 text-[clamp(1.9rem,3.6vw,2.9rem)] leading-[1.1] tracking-[-0.02em]">
              Built for the person who has to{" "}
              <em className="not-italic text-[hsl(var(--lp-blue))]">sign it off</em>.
            </h2>
            <p className="mt-5 max-w-sm text-[14px] leading-relaxed text-[hsl(var(--lp-ink-soft))]">
              Field teams capture. The pipeline decides. Supervisors get a record they can defend.
            </p>
          </Reveal>

          <div>
            {CAPABILITIES.map((item, index) => (
              <Reveal key={item.n} delay={index * 60}>
                <div className="group grid grid-cols-[auto_1fr] gap-x-5 gap-y-1 border-t lp-rule py-6 transition-colors hover:bg-[hsl(var(--lp-surface))]">
                  <span className="font-mono text-[11px] tabular-nums text-[hsl(var(--lp-blue))]">
                    {item.n}
                  </span>
                  <div>
                    <h3 className="text-[15px] font-medium">{item.title}</h3>
                    <p className="mt-1.5 max-w-md text-[13px] leading-relaxed text-[hsl(var(--lp-ink-soft))]">
                      {item.body}
                    </p>
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
