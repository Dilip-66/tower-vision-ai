"use client";

import { useCallback, useSyncExternalStore } from "react";
import { ShieldIcon } from "./Icons";

const STORAGE_KEY = "cookie_consent";

const hasNoConsent = () => !localStorage.getItem(STORAGE_KEY);

/** Mirrors the reference implementation: a storage-event driven banner that is
 *  server-rendered as `null` and appears on hydration. */
export function CookieBanner() {
  const subscribe = useCallback((onChange: () => void) => {
    window.addEventListener("storage", onChange);
    return () => window.removeEventListener("storage", onChange);
  }, []);

  const showBanner = useSyncExternalStore(
    subscribe,
    hasNoConsent,
    () => false
  );

  if (!showBanner) return null;

  const decide = (value: "accepted" | "rejected") => {
    localStorage.setItem(STORAGE_KEY, value);
    window.dispatchEvent(new StorageEvent("storage"));
  };

  return (
    <div className="fixed inset-x-0 bottom-4 z-50 flex justify-center px-4">
      <div className="flex w-full max-w-4xl flex-row items-center justify-between gap-4 rounded-full border border-surface2 bg-surface px-6 py-3 shadow-lg sm:gap-6">
        <div className="flex items-center gap-3">
          <ShieldIcon />
          <p className="!text-xs text-onbackground opacity-80">
            Help us help you — privacy-friendly analytics, no cookies.{" "}
            <a
              className="!text-xs font-medium text-cta underline hover:opacity-80"
              href="/privacy"
            >
              Privacy Policy
            </a>
            .
          </p>
        </div>
        <div className="flex shrink-0 flex-col gap-2 sm:flex-row sm:gap-3">
          <button
            onClick={() => decide("rejected")}
            className="rounded-full border border-surface2 px-4 py-2 !text-xs text-onbackground transition-opacity hover:opacity-80"
          >
            Reject
          </button>
          <button
            onClick={() => decide("accepted")}
            className="rounded-full bg-cta px-4 py-2 !text-xs text-onCta transition-opacity hover:opacity-90"
          >
            Accept
          </button>
        </div>
      </div>
    </div>
  );
}
