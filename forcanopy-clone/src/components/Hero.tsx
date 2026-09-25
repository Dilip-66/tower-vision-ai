import { FEATURED } from "@/lib/data";
import { RippleRings } from "./RippleRings";
import { SearchIcon } from "./Icons";
import { Squiggle } from "./Squiggle";
import { FeaturedTestCard } from "./TestCard";

export function Hero() {
  return (
    <section
      className="animated-hero-gradient relative overflow-hidden px-4 pb-14 pt-[120px] sm:px-6 sm:pb-20 sm:pt-[150px]"
      style={{
        width: "100vw",
        marginLeft: "calc(-50vw + 50%)",
        marginTop: -88,
      }}
    >
      <div className="relative z-10 mx-auto max-w-[1120px] grid grid-cols-1 items-center gap-10 lg:grid-cols-[minmax(0,1fr)_auto] lg:gap-12">
        <div className="flex flex-col gap-6">
          <p className="text-xs! font-bold uppercase tracking-[0.14em] text-onbackground/65">
            Canopy · Crowdfunded contaminant testing
          </p>

          <h1 className="!text-[clamp(2.5rem,5.6vw,4.75rem)] !leading-[1.02] text-onbackground text-balance max-lg:text-[clamp(2.5rem,8vw,4.75rem)]!">
            <span className="relative inline-block">
              Independent
              <Squiggle />
            </span>{" "}
            lab testing, funded by{" "}
            <span className="px-1 text-onHighlightGold box-decoration-clone [background-image:linear-gradient(var(--highlightGold),var(--highlightGold))] bg-no-repeat [background-size:100%_0.8em] [background-position:0_82%]">
              everyone
            </span>
          </h1>

          <p className="text-lg text-onbackground opacity-80 text-pretty lg:max-w-[46ch]">
            Food labels list ingredients—not contaminants. Browse active test
            campaigns and pledge alongside others to fund testing at
            independent, qualified third-party labs—neutral scientists with no
            stake in the results.
          </p>

          <form
            action="/search"
            method="get"
            role="search"
            className="flex w-full items-center gap-2 rounded-2xl lg:max-w-[520px] border border-onbackground/10 bg-surface py-1.5 pl-4 pr-1.5 shadow-[0_8px_30px_-22px_rgba(16,29,70,0.4)]"
          >
            <SearchIcon className="remixicon h-4 w-4 shrink-0 text-onbackground opacity-65" />
            <input
              type="search"
              placeholder="Search all test requests"
              aria-label="Search all test requests"
              className="w-full min-w-0 bg-transparent pt-[13px] pb-[7px] text-[15px]! text-onbackground placeholder:text-onbackground/65 focus:outline-none"
              name="q"
            />
            <button
              type="submit"
              className="shrink-0 cursor-pointer rounded-xl bg-cta px-4 py-2.5 text-sm font-bold text-onCta transition-colors hover:bg-accent hover:text-onAccent"
            >
              Search
            </button>
          </form>

          <div>
            <a
              className="border-b-2 border-accent pb-0.5 text-[15px]! font-bold text-onbackground transition-colors hover:text-accent"
              href="/about"
            >
              Learn more about how it works →
            </a>
          </div>
        </div>

        <div className="w-fit max-w-full mx-auto lg:mx-0 flex flex-col items-center">
          <div className="relative w-fit max-w-full">
            <RippleRings />
            <div className="w-[330px] max-w-full">
              <FeaturedTestCard card={FEATURED} />
            </div>
          </div>
          <a
            className="inline-flex items-center mt-3 text-lg text-onbackground opacity-80 underline underline-offset-2 hover:opacity-100"
            href="/search?status=active"
          >
            Browse all open test requests →
          </a>
        </div>
      </div>
    </section>
  );
}
