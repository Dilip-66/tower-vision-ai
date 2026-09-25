import { RIPPLE_BLOBS, RIPPLE_RINGS } from "@/lib/ripple";

const RING_BASE =
  "hero-card-ripple-ring absolute -left-80 -top-80 h-[40rem] w-[40rem]";

/**
 * Seven concentric, organically-shaped rings that bloom outwards and fade.
 * Each ring has its own negative animation-delay so the pulse is staggered,
 * and `--ring-scale` / `--ring-opacity` tune its final size + resting alpha.
 */
export function RippleRings({ dark = false }: { dark?: boolean }) {
  return (
    <div
      aria-hidden="true"
      className="pointer-events-none absolute left-1/2 top-1/2 -z-10"
    >
      {RIPPLE_RINGS.map((ring) => (
        <div
          key={ring.delay}
          className={dark ? `${RING_BASE} hero-card-ripple-ring--dark` : RING_BASE}
          style={{
            animationDelay: ring.delay,
            ["--ring-scale" as string]: ring.scale,
            ["--ring-opacity" as string]: ring.opacity,
          }}
        >
          <svg viewBox="0 0 200 200" className="h-full w-full" fill="none">
            <path d={RIPPLE_BLOBS[ring.blob]} fill={dark ? "#8b9cf2" : "#a5b4fc"} />
          </svg>
        </div>
      ))}
    </div>
  );
}
