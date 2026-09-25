import { ArrowRight } from "lucide-react";
import { useState } from "react";
import { Link } from "../../lib/router";
import { Reveal } from "./Reveal";

export function CTASection() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);

  function handleSubmit(event) {
    event.preventDefault();
    if (!email) return;
    setSent(true);
  }

  return (
    <section className="border-t lp-rule py-20 sm:py-28">
      <div className="mx-auto max-w-6xl px-5">
        <Reveal>
          <div className="rounded-2xl border lp-rule px-6 py-14 text-center sm:px-14">
            <div className="relative">
              <h2 className="lp-serif mx-auto max-w-2xl text-[clamp(2rem,4.4vw,3.2rem)] leading-[1.08] tracking-[-0.02em]">
                Curious what&apos;s in{" "}
                <em className="not-italic text-[hsl(var(--lp-blue))]">your</em> next site photo?
              </h2>
              <p className="mx-auto mt-5 max-w-lg text-[15px] leading-relaxed text-[hsl(var(--lp-ink-soft))]">
                Open the dashboard and run a detection in under a minute. No account, no setup.
              </p>

              <div className="mt-9 flex flex-wrap items-center justify-center gap-3">
                <Link to="/app" className="lp-btn lp-btn-primary">
                  Start an inspection
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <a href="#how-it-works" className="lp-btn lp-btn-ghost">
                  Read how it works
                </a>
              </div>

              <div className="mx-auto mt-14 max-w-md">
                <p className="lp-eyebrow">Stay in the loop</p>
                <p className="mt-2 text-[13px] text-[hsl(var(--lp-ink-soft))]">
                  Get model updates and new detection classes in your inbox.
                </p>

                <form onSubmit={handleSubmit} className="mt-4 flex flex-col gap-2 sm:flex-row">
                  <label htmlFor="cta-email" className="sr-only">
                    Email address
                  </label>
                  <input
                    id="cta-email"
                    type="email"
                    required
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    placeholder="you@company.com"
                    className="lp-input flex-1"
                  />
                  <button type="submit" className="lp-btn lp-btn-primary">
                    Subscribe
                  </button>
                </form>

                {sent && (
                  <p className="mt-2.5 text-[12px] text-emerald-700">Thanks — you&apos;re on the list.</p>
                )}
              </div>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
