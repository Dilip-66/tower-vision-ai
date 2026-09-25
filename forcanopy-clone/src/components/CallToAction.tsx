import { RippleRings } from "./RippleRings";

export function CallToAction() {
  return (
    <section
      className="relative isolate overflow-hidden bg-cta px-4 sm:px-6"
      style={{ width: "100vw", marginLeft: "calc(-50vw + 50%)" }}
    >
      <div className="mx-auto flex max-w-[1120px] flex-col items-center gap-6 py-20 text-center sm:py-28">
        <h2 className="!text-[clamp(2.25rem,5vw,4rem)] !leading-none text-onCta text-balance">
          Ready to <em>detect</em> tower structures?
        </h2>
        <p className="max-w-[40ch] text-lg text-onCta opacity-70 text-pretty">
          Upload an image and explore AI-powered tower detection and
          visualization.
        </p>
        <div className="relative mt-1">
          <RippleRings dark />
          <a
            className="relative rounded-full bg-onCta px-7 py-4 font-bold text-cta transition-colors hover:bg-accent hover:text-onAccent"
            href="/test-requests/new"
          >
            Start Detection
          </a>
        </div>
      </div>
    </section>
  );
}
