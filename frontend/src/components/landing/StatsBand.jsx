import { Reveal } from "./Reveal";

const STATS = [
  { value: "2", label: "Tower classes" },
  { value: "640", label: "Inference size (px)" },
  { value: "0.25", label: "Confidence floor" },
  { value: "5", label: "Pipeline stages" },
];

export function StatsBand() {
  return (
    <section className="border-y lp-rule">
      <div className="mx-auto grid max-w-6xl grid-cols-2 gap-y-8 px-5 py-9 lg:grid-cols-4 lg:divide-x lg:divide-[hsl(var(--lp-line))]">
        {STATS.map((stat, index) => (
          <Reveal key={stat.label} delay={index * 70} className="lg:px-8 first:lg:pl-0">
            <p className="lp-serif text-[clamp(1.7rem,2.8vw,2.2rem)] leading-none tracking-[-0.02em] text-[hsl(var(--lp-blue))]">
              {stat.value}
            </p>
            <p className="mt-2 text-[12px] text-[hsl(var(--lp-ink-soft))]">{stat.label}</p>
          </Reveal>
        ))}
      </div>
    </section>
  );
}
