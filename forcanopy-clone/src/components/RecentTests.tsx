"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { RECENT } from "@/lib/data";
import { TestCardBody, TestCardShell } from "./TestCard";

const ARROW =
  "inline-flex h-11 w-11 items-center justify-center rounded-full border border-onbackground/15 bg-transparent text-onbackground transition-colors hover:border-onbackground disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:border-onbackground/15 cursor-pointer";

export function RecentTests() {
  const scroller = useRef<HTMLUListElement>(null);
  const [atStart, setAtStart] = useState(false);
  const [atEnd, setAtEnd] = useState(false);
  const [active, setActive] = useState(0);

  const sync = useCallback(() => {
    const el = scroller.current;
    if (!el) return;
    const max = el.scrollWidth - el.clientWidth;
    setAtStart(el.scrollLeft > 1);
    setAtEnd(el.scrollLeft < max - 1);

    const count = el.querySelectorAll("li").length;
    const ratio = max > 0 ? el.scrollLeft / max : 0;
    setActive(count > 1 ? Math.round(ratio * (count - 1)) : 0);
  }, []);

  /** jump to a dot: proportional position, then the snap container settles it */
  const goTo = useCallback((index: number) => {
    const el = scroller.current;
    if (!el) return;
    const count = el.querySelectorAll("li").length;
    const max = el.scrollWidth - el.clientWidth;
    el.scrollTo({
      left: count > 1 ? (index / (count - 1)) * max : 0,
      behavior: "smooth",
    });
  }, []);

  /** arrows page by one card */
  const step = useCallback((direction: number) => {
    const el = scroller.current;
    if (!el) return;
    const li = el.querySelector("li");
    const amount = li ? li.getBoundingClientRect().width + 24 : el.clientWidth;
    el.scrollBy({ left: amount * direction, behavior: "smooth" });
  }, []);

  useEffect(() => {
    sync();
    window.addEventListener("resize", sync);
    return () => window.removeEventListener("resize", sync);
  }, [sync, RECENT.length]);

  return (
    <section
      id="detection"
      className="mx-auto flex max-w-[1120px] flex-col gap-8 px-4 py-14 sm:px-6 sm:py-20"
    >
      <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
        <div className="flex max-w-[60ch] flex-col gap-3">
          <p className="text-xs! font-bold uppercase tracking-[0.14em] text-onbackground/65">
            Detection results
          </p>
          <h2 className="text-onbackground text-balance">
            Detect tower structures with <em>AI</em>
          </h2>
          <p className="text-onbackground opacity-80">
            Turn model predictions into clear visual results with bounding
            boxes, detected classes, and confidence scores displayed directly on
            the image.{" "}
            <a
              className="border-b-2 border-accent pb-0.5 font-bold text-onbackground transition-colors hover:text-accent"
              href="/test-results"
            >
              Browse detections →
            </a>
          </p>
        </div>
        <a
          className="inline-flex shrink-0 items-center justify-center self-start whitespace-nowrap rounded-xl bg-cta px-5 py-3 text-sm font-bold text-onCta transition-colors hover:bg-accent hover:text-onAccent sm:self-auto"
          href="/test-requests/new"
        >
          + Upload Image
        </a>
      </div>

      <div className="relative">
        <ul
          ref={scroller}
          onScroll={sync}
          tabIndex={0}
          aria-label="Detection results"
          className="flex gap-6 overflow-x-auto snap-x snap-mandatory scroll-smooth pb-2 -mx-1 px-1 focus:outline-none focus-visible:ring-2 focus-visible:ring-cta focus-visible:ring-offset-2 focus-visible:ring-offset-background rounded-lg"
        >
          {RECENT.map((card) => (
            <li
              key={card.id}
              className="snap-start shrink-0 basis-[85%] sm:basis-[45%] lg:basis-[31%]"
            >
              <TestCardShell>
                <TestCardBody card={card} />
              </TestCardShell>
            </li>
          ))}
        </ul>

        <div className="flex items-center justify-between mt-3">
          <button
            type="button"
            onClick={() => step(-1)}
            disabled={!atStart}
            aria-label="Previous detections"
            className={ARROW}
          >
            <span aria-hidden="true">←</span>
          </button>

          <div className="flex items-center gap-2">
            {RECENT.map((card, i) => (
              <button
                key={card.id}
                type="button"
                onClick={() => goTo(i)}
                aria-label={`Go to detection ${i + 1}`}
                aria-current={i === active}
                className="flex h-6 w-6 items-center justify-center rounded-full cursor-pointer"
              >
                <span
                  aria-hidden="true"
                  className={`block h-2.5 w-2.5 rounded-full transition-colors ${
                    i === active
                      ? "bg-accent"
                      : "bg-onbackground/25 hover:bg-onbackground/50"
                  }`}
                />
              </button>
            ))}
          </div>

          <button
            type="button"
            onClick={() => step(1)}
            disabled={!atEnd}
            aria-label="Next detections"
            className={ARROW}
          >
            <span aria-hidden="true">→</span>
          </button>
        </div>
      </div>
    </section>
  );
}
