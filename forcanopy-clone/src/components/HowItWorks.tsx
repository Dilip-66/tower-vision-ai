import { STEPS } from "@/lib/data";

export function HowItWorks() {
  return (
    <section
      aria-label="How it works"
      className="border-y border-onbackground/5 bg-surface px-4 sm:px-6"
      style={{ width: "100vw", marginLeft: "calc(-50vw + 50%)" }}
    >
      <div className="mx-auto flex max-w-[1120px] flex-col gap-10 py-14 sm:py-20">
        <div className="flex max-w-[60ch] flex-col gap-3">
          <p className="text-xs! font-bold uppercase tracking-[0.14em] text-onbackground/65">
            How it works
          </p>
          <h2 className="text-onbackground text-balance">
            From a question on the shelf to <em>published lab data.</em>
          </h2>
        </div>

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((s) => (
            <div
              key={s.n}
              className="flex flex-col gap-3 rounded-[22px] bg-background p-7"
            >
              <div className="text-xs! font-bold tracking-[0.12em] text-accent">
                {s.n}
              </div>
              <div className="text-[20px]! font-extrabold tracking-[-0.02em] text-onbackground">
                {s.title}
              </div>
              <p className="text-base! leading-normal text-onbackground opacity-80 text-pretty">
                {s.body}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
